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
import pyautogui
import mss
import pysher
import os
import winreg

# Determine App Data path for logs
app_data = os.getenv('APPDATA')
log_path = os.path.join(app_data, 'AgentMonitoring', 'agent.log')
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
    'REVERB_APP_KEY': 'a7qy9jbsjkitzx8sgtie',
    'REVERB_HOST': '127.0.0.1',
    'REVERB_PORT': 8080,
    'API_URL': 'http://127.0.0.1:8000/api',
    'AGENT_ID': str(uuid.uuid4()),
    'SCREENSHOT_INTERVAL': 3.0,
    'REVERB_SCHEME': 'http'
}

# Load Config from file if exists (next to executable)
if getattr(sys, 'frozen', False):
    exe_dir = os.path.dirname(sys.executable)
else:
    exe_dir = os.path.dirname(os.path.abspath(__file__))

config_path = os.path.join(exe_dir, 'config.json')

if not os.path.exists(config_path):
    # Try parent directory (useful for dev: agent-python/../config.json)
    parent_config = os.path.join(os.path.dirname(exe_dir), 'config.json')
    if os.path.exists(parent_config):
        config_path = parent_config

if os.path.exists(config_path):
    try:
        with open(config_path, 'r') as f:
            user_config = json.load(f)
            CONFIG.update(user_config)
            logger.info(f"Loaded config from {config_path}")
    except Exception as e:
        logger.error(f"Failed to load config: {e}")
else:
    logger.warning(f"No config.json found at {config_path} (or parent), using defaults.")

logger.info(f"Using Server: {CONFIG['REVERB_HOST']}")


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

        response = requests.post(f"{CONFIG['API_URL']}/agent/register", json=payload)
        logger.info(f"Register Response: {response.status_code} - {response.text}")
        if response.status_code == 200:
            logger.info("Agent registered successfully")
            return True
        else:
            logger.error(f"Registration failed: {response.text}")
            return False
    except Exception as e:
        logger.error(f"Registration error: {e}")
        return False

def stream_screen():
    with mss.mss() as sct:
        monitor = sct.monitors[1] 
        while True:
            try:
                sct_img = sct.grab(monitor)
                import io
                from PIL import Image
                img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
                img.thumbnail((800, 600))
                
                buffer = io.BytesIO()
                img.save(buffer, format="JPEG", quality=40)
                img_str = base64.b64encode(buffer.getvalue()).decode('utf-8')
                
                requests.post(f"{CONFIG['API_URL']}/agent/screen", json={
                    'id': CONFIG['AGENT_ID'],
                    'image': img_str
                })
                # Logger verbose maybe? limit it
                # logger.info("Sent screen frame")
                
            except Exception as e:
                logger.error(f"Stream Error: {e}")
                time.sleep(5) # Wait a bit on error
            
            time.sleep(CONFIG['SCREENSHOT_INTERVAL'])

def handle_command(data):
    try:
        if isinstance(data, str):
            cmd = json.loads(data)
        else:
            cmd = data
        cmd_data = cmd.get('command', {}) if 'command' in cmd else cmd
        
        if not cmd_data: return

        # Get Screen Size for coordinate mapping
        screen_width, screen_height = pyautogui.size()

        if cmd_data.get('type') == 'move':
            # Relative coordinates (0-1)
            x_ratio = cmd_data.get('x', 0)
            y_ratio = cmd_data.get('y', 0)
            target_x = int(x_ratio * screen_width)
            target_y = int(y_ratio * screen_height)
            pyautogui.moveTo(target_x, target_y)

        elif cmd_data.get('type') == 'click':
            x_ratio = cmd_data.get('x')
            y_ratio = cmd_data.get('y')
            if x_ratio is not None and y_ratio is not None:
                target_x = int(x_ratio * screen_width)
                target_y = int(y_ratio * screen_height)
                pyautogui.click(target_x, target_y)
            else:
                 pyautogui.click()

        elif cmd_data.get('type') == 'type':
             text = cmd_data.get('text')
             # Map some special keys if needed, or rely on pyautogui support
             if text == 'Enter': pyautogui.press('enter')
             elif text == 'Backspace': pyautogui.press('backspace')
             elif text:
                 if len(text) == 1:
                     pyautogui.write(text)
                 else:
                     # Handle special keys sent as 'ArrowUp' etc by browser
                     key_map = {
                         'ArrowUp': 'up', 'ArrowDown': 'down', 'ArrowLeft': 'left', 'ArrowRight': 'right',
                         'Escape': 'esc', 'Tab': 'tab', 'Delete': 'delete'
                     }
                     pyautogui.press(key_map.get(text, text.lower()))

    except Exception as e:
        logger.error(f"Command error: {e}")

def main():
    # Auto-register startup on run
    install_startup()
    
    logger.info(f"Starting Agent {CONFIG['AGENT_ID']}")
    
    if not register_agent():
        pass # Continue anyway to try later?

    secure_connection = (CONFIG.get('REVERB_SCHEME', 'http') == 'https')

    pusher = pysher.Pusher(
        key=CONFIG['REVERB_APP_KEY'],
        cluster='mt1',
        custom_host=CONFIG['REVERB_HOST'],
        secure=secure_connection,
        port=CONFIG['REVERB_PORT']
    )
    
    def connect_handler(data):
        logger.info("Connected to Reverb")
        channel = pusher.subscribe(f"agent.{CONFIG['AGENT_ID']}")
        channel.bind('AgentCommandSent', handle_command)
        
    pusher.connection.bind('pusher:connection_established', connect_handler)
    pusher.connect()
    
    t = threading.Thread(target=stream_screen)
    t.daemon = True
    t.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pusher.disconnect()

if __name__ == "__main__":
    main()
