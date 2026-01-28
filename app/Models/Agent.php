<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;

class Agent extends Model
{
    use HasFactory;

    protected $fillable = ['uuid', 'hostname', 'ip', 'os', 'username', 'type', 'last_seen_at'];

    protected $casts = [
        'last_seen_at' => 'datetime',
    ];
}
