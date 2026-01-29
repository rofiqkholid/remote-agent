<!DOCTYPE html>
<html lang="{{ str_replace('_', '-', app()->getLocale()) }}">

<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta name="csrf-token" content="{{ csrf_token() }}">

    <title>Dashboard Monitoring Agen</title>

    <!-- Tailwind CSS (CDN) -->
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        body {
            font-family: 'Inter', sans-serif;
        }
    </style>

    <!-- Laravel Reverb / Echo Setup -->
    @vite(['resources/js/app.js'])
</head>

<body class="bg-gray-50 text-gray-900">
    <div id="app" class="min-h-screen flex flex-col">
        <!-- Header -->
        <header class="bg-white border-b border-gray-200">
            <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
                <div class="flex items-center gap-2">
                    <svg class="w-8 h-8 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"></path>
                    </svg>
                    <span class="font-bold text-xl tracking-tight">Monitoring</span>
                </div>
                <div class="text-sm font-medium">
                    Status: <span id="connection-status" class="text-yellow-600">Menghubungkan...</span>
                </div>
            </div>
        </header>

        <!-- Main Content -->
        <main class="flex-grow max-w-7xl mx-auto w-full px-4 sm:px-6 lg:px-8 py-8">
            <div class="bg-white shadow-sm rounded-lg border border-gray-200 overflow-hidden">
                <div class="overflow-x-auto">
                    <table class="min-w-full divide-y divide-gray-200">
                        <thead class="bg-gray-50">
                            <tr>
                                <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">#</th>
                                <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">COMPUTER NAME</th>
                                <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">DEVICE TYPE</th>
                                <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">USER</th>
                                <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">STATUS</th>
                                <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">POWER</th>
                                <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">IP ADDRESS</th>
                                <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">LAST SEEN</th>
                                <th scope="col" class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">ACTIONS</th>
                            </tr>
                        </thead>
                        <tbody id="agents-table-body" class="bg-white divide-y divide-gray-200">
                            <!-- Rows injected by JS -->
                            <tr>
                                <td colspan="9" class="px-6 py-10 text-center text-gray-500">
                                    Menunggu agen terhubung...
                                </td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </main>

        <!-- Remote View Modal -->
        <div id="remote-modal" class="fixed inset-0 z-50 flex items-center justify-center bg-gray-900 hidden">
            <div class="bg-white w-full h-full flex flex-col">
                <!-- Toolbar -->
                <div class="bg-white px-6 py-3 flex justify-between items-center shadow-sm z-10 border-b border-gray-200">
                    <div class="flex items-center gap-4">
                        <div class="p-2 bg-indigo-50 rounded-lg text-indigo-600">
                            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"></path>
                            </svg>
                        </div>
                        <div>
                            <h3 class="text-lg font-bold text-gray-900">Remote Control: <span id="modal-hostname">...</span></h3>
                            <div class="text-xs text-green-600 font-medium flex items-center gap-1">
                                <span class="w-1.5 h-1.5 rounded-full bg-green-500"></span> Monitor & Control
                            </div>
                        </div>
                    </div>

                    <div class="flex items-center gap-6">
                        <!-- Toggle -->
                        <div class="flex items-center gap-3">
                            <label for="input-control-toggle" class="relative inline-flex items-center cursor-pointer">
                                <input type="checkbox" id="input-control-toggle" class="sr-only peer" onchange="toggleInputControl(this)">
                                <div class="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-indigo-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-indigo-600"></div>
                                <span class="ml-3 text-sm font-medium text-gray-700">Enable Input Control</span>
                            </label>
                        </div>

                        <div class="h-6 w-px bg-gray-300"></div>

                        <!-- Actions -->
                        <div class="flex items-center gap-2">
                            <button onclick="toggleFullScreen()" class="flex items-center gap-2 px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors">
                                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 4l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4"></path>
                                </svg>
                                Full Screen
                            </button>
                            <button onclick="closeRemoteModal()" class="flex items-center gap-2 px-4 py-2 text-sm font-medium text-red-600 bg-red-50 border border-red-200 rounded-lg hover:bg-red-100 transition-colors">
                                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                                </svg>
                                Close Session
                            </button>
                        </div>
                    </div>
                </div>

                <!-- Screen Area -->
                <div class="flex-grow bg-gray-100 relative flex items-center justify-center overflow-auto focus:outline-none" id="remote-screen-container" tabindex="0">
                    <img id="remote-screen-img" src="" alt="Remote Screen"
                        class="max-h-[85vh] object-contain shadow-md ring-1 ring-gray-900/5 select-none"
                        draggable="false">
                    <div id="modal-loading-msg" class="absolute text-gray-400 font-medium animate-pulse">Waiting for stream...</div>
                </div>
            </div>
        </div>
    </div>

    <script>
        const agents = {};
        let activeAgentId = null;
        let inputControlEnabled = false;
        let lastMouseMoveTime = 0;

        document.addEventListener('DOMContentLoaded', () => {
            console.log('UI Loaded');
            fetchAgents();
            setupPolling();
            setupInputListeners();
        });

        function setupInputListeners() {
            const container = document.getElementById('remote-screen-container');
            const img = document.getElementById('remote-screen-img');

            // Mouse Move (Throttled)
            img.addEventListener('mousemove', (e) => {
                if (!inputControlEnabled || !activeAgentId) return;
                const now = Date.now();
                if (now - lastMouseMoveTime < 100) return; // 100ms throttle
                lastMouseMoveTime = now;

                sendInput({
                    type: 'move',
                    x: e.offsetX / img.width, // Relative 0-1
                    y: e.offsetY / img.height
                });
            });

            // Click
            img.addEventListener('click', (e) => {
                if (!inputControlEnabled || !activeAgentId) return;
                sendInput({
                    type: 'click',
                    x: e.offsetX / img.width,
                    y: e.offsetY / img.height
                });
            });

            // Keyboard
            window.addEventListener('keydown', (e) => {
                if (!inputControlEnabled || !activeAgentId || document.getElementById('remote-modal').classList.contains('hidden')) return;

                // Prevent default browser actions for some keys
                if (['Tab', 'Alt', 'F5', 'F11', 'F12'].includes(e.key)) e.preventDefault();

                sendInput({
                    type: 'type',
                    text: e.key
                });
            });
        }

        function sendInput(command) {
            if (!activeAgentId) return;
            fetch('/api/agent/command', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRF-TOKEN': document.querySelector('meta[name="csrf-token"]').getAttribute('content')
                },
                body: JSON.stringify({
                    agentId: activeAgentId,
                    command: command
                })
            }).catch(err => console.error('Input error:', err));
        }

        function toggleInputControl(el) {
            inputControlEnabled = el.checked;
            const container = document.getElementById('remote-screen-container');
            if (inputControlEnabled) {
                container.focus();
                container.style.cursor = 'crosshair';
            } else {
                container.style.cursor = 'default';
            }
        }

        function toggleFullScreen() {
            if (!document.fullscreenElement) {
                document.getElementById('remote-modal').requestFullscreen().catch(err => {
                    alert(`Error attempting to enable full-screen mode: ${err.message} (${err.name})`);
                });
            } else {
                document.exitFullscreen();
            }
        }

        function fetchAgents() {
            fetch('/api/agents')
                .then(response => response.json())
                .then(data => {
                    console.log('Fetched agents:', data);
                    data.forEach(agent => {
                        addOrUpdateAgent(agent.uuid, agent);
                    });
                })
                .catch(error => console.error('Error fetching agents:', error));
        }

        function setupPolling() {
            document.getElementById('connection-status').innerText = 'Mode: Polling (3s)';
            document.getElementById('connection-status').className = 'text-blue-600 font-semibold';

            // Initial fetch
            fetchAgents();

            // Poll every 3 seconds
            setInterval(() => {
                fetchAgents();
            }, 3000);
        }

        function addOrUpdateAgent(id, info) {
            agents[id] = {
                ...info,
                lastSeen: Date.now()
            };
            renderTable();
        }

        function removeAgent(id) {
            delete agents[id];
            renderTable();
        }

        function renderTable() {
            const tbody = document.getElementById('agents-table-body');
            tbody.innerHTML = '';

            if (Object.keys(agents).length === 0) {
                tbody.innerHTML = '<tr><td colspan="9" class="px-6 py-10 text-center text-gray-500">Menunggu agen terhubung...</td></tr>';
                return;
            }

            let index = 1;
            Object.entries(agents).forEach(([id, agent]) => {
                const tr = document.createElement('tr');
                tr.className = 'hover:bg-gray-50 transition-colors group';

                // Mock Power data
                const power = (Math.random() * 10 + 5).toFixed(2);

                // Calculate Status
                const lastSeenDate = new Date(agent.last_seen_at);
                const now = new Date();
                const diffSeconds = Math.floor((now - lastSeenDate) / 1000);
                const isOnline = diffSeconds < 60; // 60 seconds threshold

                let statusHtml = '';
                if (isOnline) {
                    statusHtml = `
                        <span class="px-2.5 py-0.5 inline-flex text-xs leading-4 font-semibold rounded-full bg-green-100 text-green-800 border border-green-200">
                            Online
                        </span>`;
                } else {
                    statusHtml = `
                        <span class="px-2.5 py-0.5 inline-flex text-xs leading-4 font-semibold rounded-full bg-gray-100 text-gray-800 border border-gray-200">
                            Offline
                        </span>`;
                }

                // Calculate Relative Time
                let timeString = 'Just now';
                if (diffSeconds >= 60) {
                    const mins = Math.floor(diffSeconds / 60);
                    if (mins < 60) {
                        timeString = `${mins}m ago`;
                    } else {
                        const hours = Math.floor(mins / 60);
                        if (hours < 24) {
                            timeString = `${hours}h ago`;
                        } else {
                            timeString = lastSeenDate.toLocaleDateString();
                        }
                    }
                }

                tr.innerHTML = `
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${index++}</td>
                    <td class="px-6 py-4 whitespace-nowrap">
                        <div class="text-sm font-bold text-gray-900">${agent.hostname || 'Unknown'}</div>
                        <div class="text-xs text-gray-500">ID: ${id.substring(0,8)}</div>
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${agent.type || 'PC'}</td>
                    <td class="px-6 py-4 whitespace-nowrap">
                        <div class="text-sm text-gray-900 font-medium">${agent.username || 'User'}</div>
                        <div class="text-xs text-gray-500">Staff</div>
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap">
                        ${statusHtml}
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-amber-600 font-bold flex items-center gap-1">
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path></svg>
                        ${power} W
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500 font-mono">
                        ${agent.ip || '0.0.0.0'}
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        ${timeString}
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                        <button onclick="openRemoteModal('${id}')" class="text-indigo-600 hover:text-indigo-900 bg-indigo-50 hover:bg-indigo-100 p-2 rounded-full transition-colors mx-auto" title="Start Remote Session">
                            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"></path></svg>
                        </button>
                         <button class="text-gray-400 hover:text-gray-600 p-2 rounded-full hover:bg-gray-100 ml-2" title="Settings">
                           <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"></path></svg>
                        </button>
                    </td>
                `;
                tbody.appendChild(tr);
            });
        }

        function openRemoteModal(id) {
            activeAgentId = id;
            document.getElementById('remote-modal').classList.remove('hidden');
            document.getElementById('modal-hostname').innerText = agents[id]?.hostname || id;
            document.getElementById('modal-loading-msg').style.display = 'block';
            document.getElementById('remote-screen-img').style.display = 'none';

            // Reset controls
            document.getElementById('input-control-toggle').checked = false;
            toggleInputControl(document.getElementById('input-control-toggle'));

            // MJPEG Stream (works without WebSocket)
            const img = document.getElementById('remote-screen-img');
            img.src = `/api/agent/${id}/stream`;

            // Show image when loaded (stream starts)
            img.onload = () => {
                document.getElementById('modal-loading-msg').style.display = 'none';
                img.style.display = 'block';
            };
        }

        function closeRemoteModal() {
            document.getElementById('remote-modal').classList.add('hidden');
            if (document.fullscreenElement) {
                document.exitFullscreen();
            }
            // Stop the stream by clearing the src
            const img = document.getElementById('remote-screen-img');
            img.src = '';
            activeAgentId = null;
        }
    </script>
</body>

</html>