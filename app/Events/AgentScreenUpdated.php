<?php

namespace App\Events;

use Illuminate\Broadcasting\Channel;
use Illuminate\Broadcasting\InteractsWithSockets;
use Illuminate\Contracts\Broadcasting\ShouldBroadcastNow;
use Illuminate\Foundation\Events\Dispatchable;
use Illuminate\Queue\SerializesModels;

class AgentScreenUpdated implements ShouldBroadcastNow
{
    use Dispatchable, InteractsWithSockets, SerializesModels;

    public $agentId;
    public $image; // Base64 encoded image

    public function __construct($agentId, $image)
    {
        $this->agentId = $agentId;
        $this->image = $image;
    }

    public function broadcastOn()
    {
        return new Channel('agent.' . $this->agentId);
    }
}
