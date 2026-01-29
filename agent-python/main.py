import sys
import time
import json
import socket
import platform
import uuid
import base64
import logging
import threading
import requests
import mss
import os
import winreg
from pystray import Icon, Menu, MenuItem
from PIL import Image, ImageDraw

# Determine App Data path for logs
app_data = os.getenv('APPDATA')
log_path = os.path.join(app_data, 'AgentMonitoring', 'agent.log')
config_file_path = os.path.join(app_data, 'AgentMonitoring', 'config.json')

if not os.path.exists(os.path.dirname(log_path)):
    os.makedirs(os.path.dirname(log_path))

# Setup logging to file
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_path),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger()

# Default Configuration
CONFIG = {
    'AGENT_ID': str(uuid.uuid4()),
    'SCREENSHOT_INTERVAL': 0.1,
    'API_URL': None,  # Will be fetched from user
}

def load_or_create_config():
    """Load config from AppData, or prompt user for server URL"""
    global CONFIG
    
    if os.path.exists(config_file_path):
        try:
            with open(config_file_path, 'r') as f:
                saved_config = json.load(f)
                CONFIG.update(saved_config)
                logger.info(f"Loaded config from {config_file_path}")
                return True
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
    
    # First time run - ask for server URL
    logger.info("First time setup...")
    try:
        import tkinter as tk
        from tkinter import simpledialog
        
        root = tk.Tk()
        root.withdraw()
        
        server_url = simpledialog.askstring(
            "Agent Setup",
            "Enter your monitoring server URL:\n(e.g., https://remote.dyanaf.com)",
            initialvalue="https://"
        )
        
        root.destroy()
        
        if server_url:
            server_url = server_url.rstrip('/')
            CONFIG['API_URL'] = f"{server_url}/api"
            
            # Save config
            with open(config_file_path, 'w') as f:
                json.dump(CONFIG, f, indent=4)
            
            logger.info(f"Config saved to {config_file_path}")
            return True
        else:
            logger.error("No server URL provided. Exiting.")
            return False
            
    except Exception as e:
        logger.error(f"Setup error: {e}")
        return False

def install_startup():
    """Adds the executable to the Windows Registry for auto-start"""
    try:
        if getattr(sys, 'frozen', False):
            exe_path = sys.executable
        else:
            exe_path = os.path.abspath(__file__)

        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(key, "AgentMonitoring", 0, winreg.REG_SZ, exe_path)
        winreg.CloseKey(key)
        logger.info("Added to startup registry.")
    except Exception as e:
        logger.error(f"Failed to add to startup: {e}")

def get_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return '127.0.0.1'

def register_agent():
    try:
        payload = {
            'id': CONFIG['AGENT_ID'],
            'hostname': socket.gethostname(),
            'ip': get_ip(),
            'os': f"{platform.system()} {platform.release()}",
            'username': os.getlogin(),
            'type': 'PC' if 'Windows' in platform.system() else 'Laptop'
        }
        # Fallback for username
        if not payload['username']:
             payload['username'] = os.environ.get('USERNAME', 'User')

        response = requests.post(f"{CONFIG['API_URL']}/agent/register", json=payload, timeout=10)
        logger.info(f"Register Response: {response.status_code}")
        if response.status_code == 200:
            logger.info("Agent registered successfully")
            return True
        else:
            logger.error(f"Registration failed: {response.text}")
            return False
    except Exception as e:
        logger.error(f"Registration error: {e}")
        return False

def send_heartbeat():
    """Send periodic heartbeat"""
    while True:
        try:
            requests.post(f"{CONFIG['API_URL']}/agent/heartbeat", json={'id': CONFIG['AGENT_ID']}, timeout=5)
        except Exception as e:
            logger.error(f"Heartbeat error: {e}")
        time.sleep(30)  # Every 30 seconds

# Global persistent session
SESSION = requests.Session()

# Frame Manager for Async Upload
class FrameManager:
    def __init__(self):
        self.latest_frame = None
        self.lock = threading.Lock()
        self.last_uploaded_ts = 0
        self.running = True

FRAME_MANAGER = FrameManager()

def capture_loop():
    """Captures screen at high FPS (30+)"""
    with mss.mss() as sct:
        monitor = sct.monitors[1]
        import io
        
        while FRAME_MANAGER.running:
            try:
                start_time = time.time()
                
                # fast capture
                sct_img = sct.grab(monitor)
                img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
                img.thumbnail((800, 600))
                
                # DEBUG: Draw Timestamp on image
                draw = ImageDraw.Draw(img)
                import datetime
                timestamp_str = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
                draw.text((10, 10), f"DEBUG: {timestamp_str}", fill="red")
                
                buffer = io.BytesIO()
                img.save(buffer, format="JPEG", quality=30)
                img_str = base64.b64encode(buffer.getvalue()).decode('utf-8')
                
                with FRAME_MANAGER.lock:
                    FRAME_MANAGER.latest_frame = (img_str, time.time())
                
                # Target 30 FPS for capture (approx 0.033s per frame)
                elapsed = time.time() - start_time
                sleep_time = max(0, 0.033 - elapsed)
                time.sleep(sleep_time)
                
            except Exception as e:
                logger.error(f"Capture Error: {e}")
                time.sleep(1)

def upload_loop():
    """Uploads the latest available frame as fast as possible"""
    last_sent_ts = 0
    
    while FRAME_MANAGER.running:
        try:
            frame_data = None
            frame_ts = 0
            
            with FRAME_MANAGER.lock:
                if FRAME_MANAGER.latest_frame:
                    frame_data, frame_ts = FRAME_MANAGER.latest_frame
            
            # If new frame is available, upload it
            if frame_data and frame_ts > last_sent_ts:
                last_sent_ts = frame_ts
                
                # Use persistent session
                SESSION.post(f"{CONFIG['API_URL']}/agent/screen", json={
                    'id': CONFIG['AGENT_ID'],
                    'image': frame_data
                }, timeout=5)
                
            else:
                # No new frame yet, short sleep to prevent busy loop
                time.sleep(0.01)
                
        except Exception as e:
            logger.error(f"Upload Error: {e}")
            time.sleep(1)

def start_screen_streaming():
    t_capture = threading.Thread(target=capture_loop, daemon=True)
    t_upload = threading.Thread(target=upload_loop, daemon=True)
    t_capture.start()
    t_upload.start()

def start_websocket_client():
    """Connect to Reverb/Pusher WebSocket with Polling Fallback"""
    import websocket
    import simplejson as json
    import threading
    
    # 1. Fetch Config
    try:
        response = requests.get(f"{CONFIG['API_URL']}/agent/config", timeout=10)
        if response.status_code != 200:
            logger.error(f"Failed to fetch config: {response.status_code}")
            start_fallback_polling()
            return
        
        ws_config = response.json()
        APP_KEY = ws_config.get('reverb_app_key')
        HOST = ws_config.get('reverb_host')
        PORT = ws_config.get('reverb_port')
        SCHEME = ws_config.get('reverb_scheme')
        
        # Override if localhost (fix for misconfigured server environment)
        if HOST in ['localhost', '127.0.0.1', '0.0.0.0']:
            logger.warning("Detected localhost config, overriding with production values...")
            HOST = 'remote.dyanaf.com'
            PORT = 443
            SCHEME = 'https'
            
        logger.info(f"Reverb Config: {HOST}:{PORT} (Key: {APP_KEY})")
        
        if not APP_KEY:
            logger.error("Reverb App Key missing!")
            start_fallback_polling()
            return

    except Exception as e:
        logger.error(f"Error fetching WS config: {e}")
        start_fallback_polling()
        return

    # 2. WebSocket Logic
    ws_url = f"{'wss' if SCHEME == 'https' else 'ws'}://{HOST}:{PORT}/app/{APP_KEY}?protocol=7&client=python-agent&version=1.0.0"
    
    def on_message(ws, message):
        try:
            payload = json.loads(message)
            event = payload.get('event')
            data = payload.get('data')
            
            if isinstance(data, str):
                try:
                    data = json.loads(data)
                except:
                    pass

            if event == 'pusher:connection_established':
                ws.send(json.dumps({
                    'event': 'pusher:subscribe',
                    'data': {
                        'channel': f"agent.{CONFIG['AGENT_ID']}"
                    }
                }))
                logger.info(f"Subscribed to agent.{CONFIG['AGENT_ID']}")
                
            elif event == 'App\\Events\\AgentCommandSent':
                command = data.get('command')
                if command:
                    process_command(command)
                    
            elif event == 'pusher:ping':
                 ws.send(json.dumps({'event': 'pusher:pong'}))

        except Exception as e:
            logger.error(f"WS Message Error: {e}")

    def on_error(ws, error):
        logger.error(f"WS Error: {error}")

    def on_close(ws, close_status_code, close_msg):
        logger.info("WS Closed. Switching to polling fallback...")
        # If WS fails, we fallback to polling in a separate thread/loop
        # Avoid blocking this thread
        threading.Thread(target=start_fallback_polling, daemon=True).start()

    def on_open(ws):
        logger.info("WS Connected")

    # 3. Connection Loop
    try:
        ws = websocket.WebSocketApp(ws_url,
                                  on_open=on_open,
                                  on_message=on_message,
                                  on_error=on_error,
                                  on_close=on_close)
        ws.run_forever()
    except Exception as e:
        logger.error(f"WS Connection Failed: {e}")
        start_fallback_polling()

POLLING_ACTIVE = False
def start_fallback_polling():
    global POLLING_ACTIVE
    if POLLING_ACTIVE:
        return
    POLLING_ACTIVE = True
    
    logger.info("Starting Polling Fallback (2s interval)...")
    
    while True:
        try:
            # Fix: Add /agent prefix to match route group
            response = requests.get(f"{CONFIG['API_URL']}/agent/{CONFIG['AGENT_ID']}/commands", timeout=10)
            if response.status_code == 200:
                data = response.json()
                commands = data.get('commands', [])
                
                for cmd in commands:
                    process_command(cmd)
                        
        except Exception as e:
            logger.error(f"Poll error: {e}")
            time.sleep(5)
            
        time.sleep(2.0) # 2s Poll Interval to reduce spam

def process_command(cmd):
    """Execute command using pyautogui"""
    import pyautogui
    try:
        logger.info(f"Executing command: {cmd}")
        cmd_type = cmd.get('type')
        
        if cmd_type == 'move':
            x = float(cmd.get('x'))
            y = float(cmd.get('y'))
            screen_width, screen_height = pyautogui.size()
            target_x = int(x * screen_width)
            target_y = int(y * screen_height)
            pyautogui.moveTo(target_x, target_y)
            
        elif cmd_type == 'click':
            x = float(cmd.get('x'))
            y = float(cmd.get('y'))
            screen_width, screen_height = pyautogui.size()
            target_x = int(x * screen_width)
            target_y = int(y * screen_height)
            pyautogui.click(target_x, target_y)
            
        elif cmd_type == 'type':
            text = cmd.get('text')
            if text:
                if len(text) > 1 and text in pyautogui.KEY_NAMES:
                    pyautogui.press(text)
                else:
                    pyautogui.write(text)
                    
    except Exception as e:
        logger.error(f"Command Error: {e}")


def create_icon_image():
    """Create a simple icon for system tray"""
    width = 64
    height = 64
    image = Image.new('RGB', (width, height), color='blue')
    dc = ImageDraw.Draw(image)
    dc.rectangle([(16, 16), (48, 48)], fill='white')
    return image

def on_quit(icon, item):
    """Quit the application"""
    logger.info("Agent stopping...")
    icon.stop()
    os._exit(0)

def main():
    # Load config
    if not load_or_create_config():
        sys.exit(1)
    
    # Auto-register startup on run
    install_startup()
    
    logger.info(f"Starting Agent {CONFIG['AGENT_ID']}")
    logger.info(f"API URL: {CONFIG['API_URL']}")
    
    if not register_agent():
        logger.warning("Agent registration failed, will retry...")
    
    # Start screen streaming threads (Capture + Upload)
    start_screen_streaming()
    
    # Start heartbeat thread
    t_heartbeat = threading.Thread(target=send_heartbeat, daemon=True)
    t_heartbeat.start()

    # Start WebSocket client thread (Reverb/Pusher)
    t_ws = threading.Thread(target=start_websocket_client, daemon=True)
    t_ws.start()
    
    # System tray icon
    icon_image = create_icon_image()
    menu = Menu(MenuItem('Quit', on_quit))
    icon = Icon("AgentMonitoring", icon_image, "Agent Monitoring", menu)
    
    logger.info("Agent running in system tray...")
    icon.run()

if __name__ == "__main__":
    main()
