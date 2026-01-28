import requests
import time
import base64
import random
import io
from PIL import Image, ImageDraw

# Configuration
API_URL = "http://127.0.0.1:8000/api"
AGENT_ID = "test-stream-debug" # Using a dedicated ID for this test

def create_dummy_image(color):
    img = Image.new('RGB', (800, 600), color=color)
    d = ImageDraw.Draw(img)
    d.text((10,10), f"DEBUG STREAM {time.time()}", fill=(255,255,255))
    
    buffer = io.BytesIO()
    img.save(buffer, format="JPEG", quality=50)
    return base64.b64encode(buffer.getvalue()).decode('utf-8')

# 1. Register Debug Agent
print(f"Registering Debug Agent {AGENT_ID}...")
requests.post(f"{API_URL}/agent/register", json={
    'id': AGENT_ID,
    'hostname': "DEBUG-STREAMER",
    'ip': "127.0.0.1",
    'os': "DebugOS",
    'username': "Tester",
    'type': "Test"
})

print("Starting Stream Simulation (Press Ctrl+C to stop)...")
colors = [(255,0,0), (0,255,0), (0,0,255), (255,255,0)]

try:
    while True:
        color = random.choice(colors)
        img_str = create_dummy_image(color)
        
        start = time.time()
        resp = requests.post(f"{API_URL}/agent/screen", json={
            'id': AGENT_ID,
            'image': img_str
        })
        end = time.time()
        
        print(f"Sent frame. Status: {resp.status_code}. Time: {end-start:.3f}s")
        time.sleep(1) # Slow stream
except KeyboardInterrupt:
    print("Stopped.")
