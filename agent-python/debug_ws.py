import requests
import websocket
import simplejson as json
import time
import os

def test_ws():
    # 1. Load Agent Config to get UUID
    try:
        config_path = os.path.expandvars(r'%APPDATA%\AgentMonitoring\config.json')
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                file_config = json.load(f)
                AGENT_ID = file_config.get('AGENT_ID') # Key is uppercase
                print(f"Loaded Agent ID: {AGENT_ID}")
        else:
            print("Config not found, generating temp UUID")
            import uuid
            AGENT_ID = str(uuid.uuid4())
            
    except Exception as e:
        print(f"Could not load config: {e}")
        import uuid
        AGENT_ID = str(uuid.uuid4())

    # 2. Fetch Reverb Config
    CONFIG_URL = "https://remote.dyanaf.com/api" # Hardcoded from config.json view earlier
    print(f"Fetching config from {CONFIG_URL}...")
    
    try:
        response = requests.get(f"{CONFIG_URL}/agent/config", timeout=10, verify=False)
        print(f"Status Code: {response.status_code}")
        print(f"Response Content: {response.text}")
        ws_config = response.json()
        APP_KEY = ws_config.get('reverb_app_key')
        HOST = ws_config.get('reverb_host')
        PORT = ws_config.get('reverb_port')
        SCHEME = ws_config.get('reverb_scheme')
        
        # Override if localhost (fix for misconfigured server)
        if HOST in ['localhost', '127.0.0.1', '0.0.0.0']:
            print("Detected localhost config, overriding with production values...")
            HOST = 'remote.dyanaf.com'
            PORT = 8080
            SCHEME = 'http' # Try WS on 8080
        
        with open('debug_ws.log', 'w') as f:
            f.write(f"Reverb Config:\nHOST: {HOST}\nPORT: {PORT}\nSCHEME: {SCHEME}\nKEY: {APP_KEY}\n")
            
        print(f"Reverb Config: {HOST}:{PORT} Key: {APP_KEY}")
    except Exception as e:
        print(f"Failed to fetch config: {e}")
        return

    # 3. Connect
    ws_url = f"{'wss' if SCHEME == 'https' else 'ws'}://{HOST}:{PORT}/app/{APP_KEY}?protocol=7&client=python-agent&version=1.0.0"
    print(f"Connecting to {ws_url}")

    def on_message(ws, message):
        print(f"Received: {message}")
        payload = json.loads(message)
        event = payload.get('event')
        
        if event == 'pusher:connection_established':
            print("Connected! Subscribing...")
            ws.send(json.dumps({
                'event': 'pusher:subscribe',
                'data': {
                    'channel': f"agent.{AGENT_ID}"
                }
            }))
        elif event == 'pusher:error':
            print(f"Pusher Error: {message}")

    def on_error(ws, error):
        print(f"Error: {error}")

    def on_close(ws, status, msg):
        print(f"Closed: {status} {msg}")

    ws = websocket.WebSocketApp(ws_url, on_message=on_message, on_error=on_error, on_close=on_close)
    ws.run_forever()

if __name__ == "__main__":
    test_ws()
