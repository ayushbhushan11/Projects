import sys
import time
import json
import threading
import numpy as np
import websocket
from inputs import get_gamepad
from PyQt5 import QtCore, QtGui, QtWidgets
import pyqtgraph as pg

# --- CONFIGURATION ---
SERVER_IP = "192.168.1.10"
SERVER_PORT = 8000
WS_URL = f"ws://{SERVER_IP}:{SERVER_PORT}/ws/laptop_controller"

# Physics Constants
MAX_RPM = 60
WHEEL_DIAMETER = 0.234
TRACK_WIDTH = 10
MAX_V = (MAX_RPM * 2 * np.pi / 60.0) * (WHEEL_DIAMETER / 2.0)
MAX_W = ((2 * MAX_V) / TRACK_WIDTH)*0.5

V_TAU = 0.25 
W_TAU = 0.4
UPDATE_HZ = 20 

class GamepadThread(QtCore.QThread):
    drive_signal = QtCore.pyqtSignal(float, float)
    event_signal = QtCore.pyqtSignal(dict)

    def run(self):
        rt_val = 0.0    
        lt_val = 0.0    
        steer_val = 0.0 
        
        print("🎮 Master Gamepad Thread Started")
        print("🔍 DEBUG MODE: Move sticks/buttons to see their 'Code' in the terminal.")

        while True:
            try:
                events = get_gamepad()
                for event in events:
                    if event.code == "SYN_REPORT": continue

                    # --- MAPPING MONITOR (For future expansion) ---
                    # This tells you exactly what to call the buttons for your arm/sensors
                    if event.ev_type != 'Sync':
                        print(f"DEBUG -> Code: {event.code} | Value: {event.state}")

                    # 1. DRIVE LOGIC (FIXED FOR 0-128-255 MAPPING)
                    if event.code == "ABS_X":
                        # Logic from lap_guy2: 128 is middle, 0 left, 255 right
                        raw = (event.state - 128) / 128.0 
                        steer_val = 0.0 if abs(raw) < 0.1 else raw
                        
                    elif event.code in ["ABS_RZ", "ABS_GAS"]:
                        rt_val = event.state / 255.0
                    elif event.code in ["ABS_Z", "ABS_BRAKE"]:
                        lt_val = event.state / 255.0
                    
                    # 2. BROADCAST LOGIC (For Stitcher, Nano, etc.)
                    self.event_signal.emit({
                        "type": event.ev_type,
                        "code": event.code,
                        "value": event.state
                    })

                # Target Physics Calculation
                target_v = (rt_val - lt_val) * MAX_V
                target_w = -steer_val * MAX_W 
                self.drive_signal.emit(target_v, target_w)
                
            except Exception as e:
                print(f"Gamepad Error: {e}")
                time.sleep(1)

class CommsThread(QtCore.QThread):
    ack_signal = QtCore.pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.ws = None
        self.connected = False
        self.running = True
        self.latest_v = 0.0
        self.latest_w = 0.0

    def run(self):
        while self.running:
            try:
                self.ws = websocket.WebSocketApp(WS_URL, 
                                                 on_open=self.on_open, 
                                                 on_message=self.on_message, 
                                                 on_error=self.on_error)
                self.ws.run_forever()
                time.sleep(2)
            except: time.sleep(2)

    def on_open(self, ws):
        self.connected = True
        print("✅ Connected to Relay Server")
        threading.Thread(target=self.sender_loop, daemon=True).start()

    def on_message(self, ws, message):
        data = json.loads(message)
        if data.get("topic") == "ack":
            self.ack_signal.emit(f"Rover ACK: {data['payload']}")

    def on_error(self, ws, error):
        self.connected = False
        self.ack_signal.emit("Disconnected")

    def update_drive(self, v, w):
        self.latest_v = v; self.latest_w = w

    def broadcast_event(self, evt):
        if self.connected and self.ws:
            # Topic 'snapshot' for the sticher2.py
            if evt['code'] == "BTN_WEST" and evt['value'] == 1:
                msg = {"topic": "snapshot", "from": "laptop_controller", "payload": {}}
                self.ws.send(json.dumps(msg))
            
            # General 'gamepad_event' for rover_brain.py / Nano
            msg = {
                "topic": "gamepad_event", 
                "from": "laptop_controller", 
                "payload": evt
            }
            try: self.ws.send(json.dumps(msg))
            except: pass

    def sender_loop(self):
        while self.connected and self.running:
            try: 
                # TARGETING THE RADXA BRIDGE
                msg = {
                    "to": "radxa_rover",
                    "from": "laptop_controller",
                    "topic": "drive_data",
                    "payload": {"v": self.latest_v, "w": self.latest_w}
                }
                self.ws.send(json.dumps(msg))
            except: 
                self.connected = False
                break
            time.sleep(1.0 / UPDATE_HZ)

class RoverController(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Mars Rover Command Center")
        self.resize(800, 500)
        
        self.curr_v = 0.0; self.curr_w = 0.0
        self.target_v = 0.0; self.target_w = 0.0
        self.last_t = time.time()

        central = QtWidgets.QWidget(); self.setCentralWidget(central)
        layout = QtWidgets.QVBoxLayout(central)
        
        # Plot Setup
        self.plot = pg.PlotWidget(title="Live Telemetry Output")
        self.plot.setYRange(-1.5, 1.5)
        self.plot.addLegend()
        self.v_curve = self.plot.plot(pen='g', name="Velocity (V)")
        self.w_curve = self.plot.plot(pen='r', name="Radian (W)")
        self.v_hist = [0]*100; self.w_hist = [0]*100
        layout.addWidget(self.plot)
        
        self.lbl_status = QtWidgets.QLabel("Status: Connecting to Server...")
        self.lbl_status.setFont(QtGui.QFont("Courier New", 12))
        self.lbl_status.setStyleSheet("color: #66fcf1; background-color: #0b0c10; padding: 5px;")
        layout.addWidget(self.lbl_status)

        self.comms = CommsThread()
        self.comms.ack_signal.connect(self.lbl_status.setText)
        self.comms.start()

        self.gp = GamepadThread()
        self.gp.drive_signal.connect(self.update_targets)
        self.gp.event_signal.connect(self.comms.broadcast_event)
        self.gp.start()

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.physics_loop)
        self.timer.start(int(1000 / UPDATE_HZ))

    def update_targets(self, v, w):
        self.target_v = v; self.target_w = w

    def physics_loop(self):
        now = time.time(); dt = now - self.last_t; self.last_t = now
        alpha_v = 1.0 - np.exp(-dt / V_TAU); alpha_w = 1.0 - np.exp(-dt / W_TAU)
        
        self.curr_v += (self.target_v - self.curr_v) * alpha_v
        self.curr_w += (self.target_w - self.curr_w) * alpha_w
        
        self.comms.update_drive(self.curr_v, self.curr_w)
        
        self.v_hist.pop(0); self.w_hist.pop(0)
        self.v_hist.append(self.curr_v); self.w_hist.append(self.curr_w)
        self.v_curve.setData(self.v_hist); self.w_curve.setData(self.w_hist)

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    gui = RoverController(); gui.show()
    sys.exit(app.exec_())
