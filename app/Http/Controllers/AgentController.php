<?php

namespace App\Http\Controllers;

use Illuminate\Http\Request;
use App\Events\AgentRegistered;
use App\Events\AgentScreenUpdated;
use App\Events\AgentOffline;
use App\Models\Agent;
use Illuminate\Support\Facades\Cache; // Fix lint


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

        // Store image in Cache for 30 seconds
        \Cache::put('agent_screen_' . $data['id'], $data['image'], 30);

        // Broadcast notification only (lightweight)
        broadcast(new AgentScreenUpdated($data['id'], 'AVAILABLE'));

        return response()->json(['status' => 'ok']);
    }

    public function getScreenImage($id)
    {
        $image = \Cache::get('agent_screen_' . $id);
        if (!$image) {
            return response('No signal', 404);
        }
        // Return raw image bytes if it was sent as raw, but here it's base64 string.
        // If the frontend expects base64 in JSON, we can return that.
        // Or better, serve it as an image response for img src directly.

        // Decoding base64 to serve as real image
        $imageBlob = base64_decode($image);
        return response($imageBlob)->header('Content-Type', 'image/jpeg');
    }

    public function stream($id)
    {
        // Disable timeout for streaming
        set_time_limit(0);

        return response()->stream(function () use ($id) {
            $lastHash = null;
            while (true) {
                $image = \Cache::get('agent_screen_' . $id);

                if (connection_aborted()) {
                    break;
                }

                if ($image) {
                    $hash = md5($image);
                    if ($hash !== $lastHash) {
                        $lastHash = $hash;
                        $data = base64_decode($image);

                        echo "--frame\r\n";
                        echo "Content-Type: image/jpeg\r\n\r\n";
                        echo $data;
                        echo "\r\n";

                        if (ob_get_level() > 0) ob_flush();
                        flush();
                    }
                }

                usleep(50000); // 20 FPS check
            }
        }, 200, [
            'Content-Type' => 'multipart/x-mixed-replace; boundary=frame',
            'Cache-Control' => 'no-cache',
            'Connection' => 'keep-alive',
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
}
