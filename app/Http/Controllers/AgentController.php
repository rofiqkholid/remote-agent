<?php

namespace App\Http\Controllers;

use Illuminate\Http\Request;
use App\Events\AgentRegistered;
use App\Events\AgentScreenUpdated;
use App\Events\AgentOffline;
use App\Models\Agent;
use Illuminate\Support\Facades\Cache;
use Illuminate\Support\Facades\Log;


class AgentController extends Controller
{
    public function index()
    {
        return response()->json(Agent::all());
    }

    public function register(Request $request)
    {
        $data = $request->validate([
            'id' => 'required|string',
            'hostname' => 'required|string',
            'ip' => 'nullable|string',
            'os' => 'nullable|string',
            'username' => 'nullable|string',
            'type' => 'nullable|string',
        ]);

        $agent = Agent::updateOrCreate(
            ['uuid' => $data['id']],
            [
                'hostname' => $data['hostname'],
                'ip' => $data['ip'] ?? null,
                'os' => $data['os'] ?? null,
                'username' => $data['username'] ?? null,
                'type' => $data['type'] ?? 'PC',
                'last_seen_at' => now(),
            ]
        );

        broadcast(new AgentRegistered($data['id'], $data));
        return response()->json(['status' => 'registered']);
    }

    public function screenUpdate(Request $request)
    {
        // \Log::info("Screen update received for " . $request->id); // Log is heavy for streams
        $data = $request->validate([
            'id' => 'required|string',
            'image' => 'required|string', // Base64
        ]);

        // Update last seen
        Agent::where('uuid', $data['id'])->update(['last_seen_at' => now()]);

        // Store image directly in storage for performance (bypass Cache overhead)
        $path = storage_path('app/agent_frames/' . $data['id'] . '.jpg');
        // Ensure directory exists
        if (!file_exists(dirname($path))) {
            mkdir(dirname($path), 0755, true);
        }

        // Decode and save raw bytes to avoid decoding on read
        // The agent sends base64, we decode it here once.
        $imageBytes = base64_decode($data['image']);
        file_put_contents($path, $imageBytes);

        // Broadcast notification only (lightweight)
        broadcast(new AgentScreenUpdated($data['id'], 'AVAILABLE'));

        return response()->json(['status' => 'ok']);
    }

    public function getScreenImage($id)
    {
        // Read from file storage
        $path = storage_path('app/agent_frames/' . $id . '.jpg');
        if (!file_exists($path)) {
            return response('No signal', 404);
        }
        return response()->file($path, ['Content-Type' => 'image/jpeg']);
    }

    public function stream($id)
    {
        // Disable timeout for streaming (may not work on shared hosting)
        @set_time_limit(0);
        @ini_set('max_execution_time', '0');

        // Close session to prevent locking other requests
        if (session_status() === PHP_SESSION_ACTIVE) {
            session_write_close();
        }

        return response()->stream(function () use ($id) {
            $lastHash = null;
            $startTime = time();
            $maxDuration = 120; // 2 minutes max to avoid hosting timeout

            // Clean output buffer to ensure immediately flushing
            while (ob_get_level() > 0) {
                ob_end_flush();
            }
            ob_implicit_flush(1);

            try {
                // Send initial boundary immediately to establish connection
                echo "--frame\r\n";
                echo "Content-Type: image/jpeg\r\n\r\n";

                // Send a minimal placeholder if no data
                $placeholder = base64_decode('/9j/4AAQSkZJRgABAQEAAAAAAAD/2wBDAAEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQH/2wBDAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQH/wAARCAABAAEDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAv/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/8QAFQEBAQAAAAAAAAAAAAAAAAAAAAX/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIRAxEAPwA2AA//2Q==');
                echo $placeholder;
                echo "\r\n";
                flush();

                while (true) {
                    // Check connection and timeout
                    if (connection_aborted() || (time() - $startTime) > $maxDuration) {
                        break;
                    }

                    $path = storage_path('app/agent_frames/' . $id . '.jpg');
                    clearstatcache(true, $path); // Clear cache to get fresh modification time

                    if (file_exists($path)) {
                        $mtime = filemtime($path);
                        if ($mtime !== $lastHash) { // Use mtime as hash
                            $lastHash = $mtime;
                            $data = file_get_contents($path);

                            echo "--frame\r\n";
                            echo "Content-Type: image/jpeg\r\n";
                            echo "Content-Length: " . strlen($data) . "\r\n\r\n";
                            echo $data;
                            echo "\r\n";

                            // Aggressive flushing
                            while (ob_get_level() > 0) {
                                ob_end_flush();
                            }
                            flush();
                        }
                    }

                    usleep(10000); // 10ms check (High Performance)
                }
            } catch (\Exception $e) {
                // Log error for debugging
                \Log::error('Stream error: ' . $e->getMessage());
            }
        }, 200, [
            'Content-Type' => 'multipart/x-mixed-replace; boundary=frame',
            'Cache-Control' => 'no-cache, no-store, must-revalidate',
            'Pragma' => 'no-cache',
            'Expires' => '0',
            'X-Accel-Buffering' => 'no'
        ]);
    }

    public function heartbeat(Request $request)
    {
        $id = $request->input('id');
        if ($id) {
            Agent::where('uuid', $id)->update(['last_seen_at' => now()]);
        }
        return response()->json(['status' => 'ok']);
    }

    public function sendCommand(Request $request)
    {
        $data = $request->validate([
            'agentId' => 'required|string',
            'command' => 'required|array'
        ]);

        // 1. Broadcast to Reverb (Primary)
        broadcast(new \App\Events\AgentCommandSent($data['agentId'], $data['command']));

        // 2. Queue for Polling (Fallback)
        $key = 'agent_commands_' . $data['agentId'];
        $commands = Cache::get($key, []);
        $commands[] = $data['command'];
        Cache::put($key, $commands, 10); // Keep for 10 seconds

        return response()->json(['status' => 'sent']);
    }

    public function getCommands($id)
    {
        $key = 'agent_commands_' . $id;
        $commands = Cache::get($key);

        if (!empty($commands)) {
            Cache::forget($key);
            return response()->json(['commands' => $commands]);
        }

        return response()->json(['commands' => []]);
    }

    public function getConfig()
    {
        // Expose public config for the agent
        // Fallback to production URL if config is localhost (dev env issue)
        $host = config('reverb.apps.apps.0.options.host');
        if ($host === 'localhost' || $host === '0.0.0.0') {
            return response()->json([
                'reverb_app_key' => config('reverb.apps.apps.0.key'),
                'reverb_host' => 'remote.dyanaf.com',
                'reverb_port' => 443,
                'reverb_scheme' => 'https',
            ]);
        }

        return response()->json([
            'reverb_app_key' => config('reverb.apps.apps.0.key'),
            'reverb_host' => $host,
            'reverb_port' => config('reverb.apps.apps.0.options.port'),
            'reverb_scheme' => config('reverb.apps.apps.0.options.scheme'),
        ]);
    }
}
