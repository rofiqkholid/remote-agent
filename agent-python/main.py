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
    'SCREENSHOT_INTERVAL': 3.0,
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

def stream_screen():
    with mss.mss() as sct:
        monitor = sct.monitors[1] 
        while True:
            try:
                sct_img = sct.grab(monitor)
                import io
                img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
                img.thumbnail((800, 600))
                
                buffer = io.BytesIO()
                img.save(buffer, format="JPEG", quality=40)
                img_str = base64.b64encode(buffer.getvalue()).decode('utf-8')
                
                requests.post(f"{CONFIG['API_URL']}/agent/screen", json={
                    'id': CONFIG['AGENT_ID'],
                    'image': img_str
                }, timeout=5)
                
            except Exception as e:
                logger.error(f"Stream Error: {e}")
                time.sleep(5)
            
            time.sleep(CONFIG['SCREENSHOT_INTERVAL'])

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
    
    # Start screenshot thread
    t_screen = threading.Thread(target=stream_screen, daemon=True)
    t_screen.start()
    
    # Start heartbeat thread
    t_heartbeat = threading.Thread(target=send_heartbeat, daemon=True)
    t_heartbeat.start()
    
    # System tray icon
    icon_image = create_icon_image()
    menu = Menu(MenuItem('Quit', on_quit))
    icon = Icon("AgentMonitoring", icon_image, "Agent Monitoring", menu)
    
    logger.info("Agent running in system tray...")
    icon.run()

if __name__ == "__main__":
    main()
