<?php

namespace App\Events;

use Illuminate\Broadcasting\Channel;
use Illuminate\Broadcasting\InteractsWithSockets;
use Illuminate\Contracts\Broadcasting\ShouldBroadcast;
use Illuminate\Foundation\Events\Dispatchable;
use Illuminate\Queue\SerializesModels;

class AgentCommandSent implements ShouldBroadcast
{
    use Dispatchable, InteractsWithSockets, SerializesModels;

    public $agentId;
    public $command;

    public function __construct($agentId, $command)
    {
        $this->agentId = $agentId;
        $this->command = $command;
    }

    public function broadcastOn()
    {
        return new Channel('agent.' . $this->agentId);
    }
}
