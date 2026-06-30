import time
import json
import websocket
import threading
from inputs import get_gamepad

# --- CONFIGURATION ---
SERVER_IP = "192.168.1.10"
SERVER_PORT = 8000
WS_URL = f"ws://{SERVER_IP}:{SERVER_PORT}/ws/laptop_controller"

def on_open(ws):
    print("✅ Gamepad Publisher Connected to Relay")

def on_error(ws, error):
    print(f"❌ Connection Error: {error}")

def run_publisher():
    ws = websocket.WebSocketApp(WS_URL, on_open=on_open, on_error=on_error)
    ws_thread = threading.Thread(target=ws.run_forever, daemon=True)
    ws_thread.start()

    print("🎮 Polling Gamepad... (Routing data to drive_logic)")

    while True:
        try:
            events = get_gamepad()
            for event in events:
                if event.code == "SYN_REPORT": continue

                # Prepare the raw event message with the explicit "to" address
                msg = {
                    "to": "drive_logic",    # <--- ADDED ROUTING ADDRESS
                    "topic": "gamepad_event",
                    "from": "laptop_controller",
                    "payload": {
                        "type": event.ev_type,
                        "code": event.code,
                        "value": event.state
                    }
                }

                # Special Trigger: Snapshot (The Stitcher Logic)
                if event.code == "BTN_WEST" and event.state == 1:
                    snapshot_msg = {
                        "to": "pro_stitcher", 
                        "topic": "snapshot", 
                        "from": "laptop_controller", 
                        "payload": {}
                    }
                    if ws.sock and ws.sock.connected:
                        ws.send(json.dumps(snapshot_msg))

                # Send general event to drive_logic
                if ws.sock and ws.sock.connected:
                    ws.send(json.dumps(msg))

        except Exception as e:
            print(f"Gamepad disconnected: {e}")
            time.sleep(2)

if __name__ == "__main__":
    run_publisher()
