require('dotenv').config();
const Echo = require('laravel-echo');
const Pusher = require('pusher-js');
const axios = require('axios');
const screenshot = require('screenshot-desktop');
const os = require('os');
const { v4: uuidv4 } = require('uuid');

// Configuration
// In a real build, these would be injected or read from a config file
const CONFIG = {
    REVERB_APP_KEY: 'a7qy9jbsjkitzx8sgtie',
    REVERB_HOST: 'localhost',
    REVERB_PORT: 8080,
    API_URL: 'http://localhost/api', // Adjust if server is elsewhere
    AGENT_ID: uuidv4(), // Generate a new ID each run, or persist it
    SCREENSHOT_INTERVAL: 1000 // ms
};

console.log(`Starting Agent with ID: ${CONFIG.AGENT_ID}`);

// Setup Pusher/Echo for Reverb
// Reverb uses Pusher protocol. In Node.js, we need to pass a custom client or use pusher-js directly.
// laravel-echo expects a 'Pusher' client available.

global.Pusher = Pusher;

const echo = new Echo({
    broadcaster: 'reverb',
    key: CONFIG.REVERB_APP_KEY,
    wsHost: CONFIG.REVERB_HOST,
    wsPort: CONFIG.REVERB_PORT,
    wssPort: CONFIG.REVERB_PORT, // For local http
    forceTLS: false,
    disableStats: true,
    enabledTransports: ['ws', 'wss'],
});

// Register Agent via API
async function register() {
    try {
        await axios.post(`${CONFIG.API_URL}/agent/register`, {
            id: CONFIG.AGENT_ID,
            hostname: os.hostname(),
            ip: getLocalIP(),
            os: os.type() + ' ' + os.release(),
            username: os.userInfo().username,
            type: os.type().includes('Windows') ? 'PC' : 'Laptop' // Simple heuristic, better to check battery if possible
        });
        console.log('Registered successfully');
    } catch (e) {
        console.error('Registration failed:', e.message);
        setTimeout(register, 5000); // Retry
    }
}

function getLocalIP() {
    const interfaces = os.networkInterfaces();
    for (const name of Object.keys(interfaces)) {
        for (const iface of interfaces[name]) {
            if (iface.family === 'IPv4' && !iface.internal) {
                return iface.address;
            }
        }
    }
    return '127.0.0.1';
}

// Start Streaming
let streaming = true;
async function streamLoop() {
    if (!streaming) return;

    try {
        const imgBuffer = await screenshot({ format: 'jpg' });
        // Send to API
        await axios.post(`${CONFIG.API_URL}/agent/screen`, {
            id: CONFIG.AGENT_ID,
            image: imgBuffer.toString('base64')
        });
        // console.log('Screen sent');
    } catch (e) {
        console.error('Screen capture/send failed:', e.message);
    }

    setTimeout(streamLoop, CONFIG.SCREENSHOT_INTERVAL);
}

// Remote control libraries (nut.js / robotjs) failed to install on this environment.
// Control logic is disabled.
// const { mouse, keyboard, Point, Button } = require('@nut-tree/nut-js');

// Listen for commands
echo.channel(`agent.${CONFIG.AGENT_ID}`)
    .listen('AgentCommandSent', (e) => {
        console.log('Command received:', e.command);
        handleCommand(e.command);
    });

async function handleCommand(cmd) {
    console.log('Remote control command received but driver is not installed:', cmd);
}

// Main startup
register().then(() => {
    streamLoop();
});
