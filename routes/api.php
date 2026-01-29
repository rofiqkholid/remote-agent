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
    Route::get('/{id}/commands', [AgentController::class, 'getCommands']); // Poll fallback
});

Route::get('/agent/config', [AgentController::class, 'getConfig']);
Route::post('/agent/command', [AgentController::class, 'sendCommand']);
