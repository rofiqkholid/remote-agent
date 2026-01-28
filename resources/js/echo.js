import Echo from 'laravel-echo';

import Pusher from 'pusher-js';
window.Pusher = Pusher;

const isExposed = window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1';
const host = isExposed ? window.location.hostname : (import.meta.env.VITE_REVERB_HOST || 'localhost');
const port = isExposed ? 443 : (import.meta.env.VITE_REVERB_PORT ?? 80);
const useTLS = isExposed || (import.meta.env.VITE_REVERB_SCHEME ?? 'https') === 'https';

window.Echo = new Echo({
    broadcaster: 'reverb',
    key: import.meta.env.VITE_REVERB_APP_KEY,
    wsHost: host,
    wsPort: port,
    wssPort: port,
    forceTLS: useTLS,
    enabledTransports: ['ws', 'wss'],
    disableStats: true,
});
