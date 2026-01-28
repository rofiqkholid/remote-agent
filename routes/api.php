<?php

use Illuminate\Http\Request;
use Illuminate\Support\Facades\Route;
use App\Http\Controllers\AgentController;

Route::get('/user', function (Request $request) {
    return $request->user();
})->middleware('auth:sanctum');

Route::get('/agents', [AgentController::class, 'index']);

Route::prefix('agent')->group(function () {
    Route::post('/register', [AgentController::class, 'register']);
    // Route::get('/agents', ... removed from here
    Route::post('/screen', [AgentController::class, 'screenUpdate']);
    Route::get('/{id}/image', [AgentController::class, 'getScreenImage']);
    Route::get('/{id}/stream', [AgentController::class, 'stream']); // MJPEG Stream
    Route::post('/heartbeat', [AgentController::class, 'heartbeat']);

});

Route::post('/agent/command', function (Request $request) {
    // This endpoint is for the DASHBOARD to send commands to the AGENT
    $targetId = $request->input('agentId');
    $command = $request->except('agentId');

    broadcast(new \App\Events\AgentCommandSent($targetId, $command));

    // For now, let's assume we implement AgentCommandSent next or use a generic event
    return response()->json(['status' => 'sent']);
});
