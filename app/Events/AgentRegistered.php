<?php

namespace App\Events;

use Illuminate\Broadcasting\Channel;
use Illuminate\Broadcasting\InteractsWithSockets;
use Illuminate\Contracts\Broadcasting\ShouldBroadcast;
use Illuminate\Foundation\Events\Dispatchable;
use Illuminate\Queue\SerializesModels;

class AgentRegistered implements ShouldBroadcast
{
    use Dispatchable, InteractsWithSockets, SerializesModels;

    public $agentId;
    public $info;

    public function __construct($agentId, $info)
    {
        $this->agentId = $agentId;
        $this->info = $info;
    }

    public function broadcastOn()
    {
        return new Channel('agents');
    }
}
