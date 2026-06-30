import sys
import time
import json
import threading
import numpy as np
import websocket
import pygame
import struct
from collections import deque
from PyQt5 import QtCore, QtGui, QtWidgets
import pyqtgraph as pg

# --- CONFIGURATION ---
SERVER_IP = "192.168.1.10"
WS_URL = f"ws://{SERVER_IP}:8000/ws/laptop_controller"

MAX_RPM = 60
WHEEL_DIAMETER = 0.234
TRACK_WIDTH = 10.0 
MAX_V = (MAX_RPM * 2 * np.pi / 60.0) * (WHEEL_DIAMETER / 2.0)

V_TAU = 0.40  
W_TAU = 0.35  
UPDATE_HZ = 50 
DEADBAND = 0.05

class CommsThread(QtCore.QThread):
    ack_signal = QtCore.pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.ws = None
        self.connected = False
        self.latest_v = 0.0
        self.latest_w = 0.0

    def run(self):
        while True:
            try:
                self.ws = websocket.WebSocketApp(WS_URL, 
                                                 on_open=self.on_open, 
                                                 on_message=self.on_message)
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

    def update_drive(self, v, w):
        self.latest_v = v; self.latest_w = w

    def broadcast_event(self, evt_type, code, value):
        """Maintains functionality for Stitcher and Nano programs"""
        if self.connected and self.ws:
            # Topic 'snapshot' for the stitcher program
            if code == "BTN_WEST" and value == 1:
                msg = {"topic": "snapshot", "from": "laptop_controller", "payload": {}}
                self.ws.send(json.dumps(msg))
            
            # General event for other listeners
            msg = {
                "topic": "gamepad_event", 
                "from": "laptop_controller", 
                "payload": {"type": evt_type, "code": code, "value": value}
            }
            try: self.ws.send(json.dumps(msg))
            except: pass

    def sender_loop(self):
        while self.connected:
            try: 
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
        self.setWindowTitle("EXTRA Terrestrial Command Center")
        self.resize(800, 500)
        
        self.curr_v = 0.0; self.curr_w = 0.0
        self.target_v = 0.0; self.target_w = 0.0
        self.last_t = time.time()

        central = QtWidgets.QWidget(); self.setCentralWidget(central)
        layout = QtWidgets.QVBoxLayout(central)
        
        self.plot = pg.PlotWidget(title="Live Telemetry - Car Physics Mode")
        self.v_curve = self.plot.plot(pen='g', name="V (m/s)")
        self.w_curve = self.plot.plot(pen='r', name="W (rad/s)")
        self.v_hist = deque([0]*200, maxlen=200)
        self.w_hist = deque([0]*200, maxlen=200)
        layout.addWidget(self.plot)
        
        self.lbl_status = QtWidgets.QLabel("Status: Connecting...")
        layout.addWidget(self.lbl_status)

        self.comms = CommsThread()
        self.comms.ack_signal.connect(self.lbl_status.setText)
        self.comms.start()

        pygame.init(); pygame.joystick.init()
        self.js = pygame.joystick.Joystick(0) if pygame.joystick.get_count() > 0 else None
        if self.js: self.js.init()

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_loop)
        self.timer.start(int(1000 / UPDATE_HZ))

    def update_loop(self):
        dt = time.time() - self.last_t
        self.last_t = time.time()
        if not self.js: return

        for event in pygame.event.get():
            if event.type == pygame.JOYBUTTONDOWN:
                self.comms.broadcast_event("Button", f"BTN_{event.button}", 1)
            elif event.type == pygame.JOYBUTTONUP:
                self.comms.broadcast_event("Button", f"BTN_{event.button}", 0)

        # 1. Inputs
        raw_rt = (self.js.get_axis(5) + 1) / 2.0
        raw_lt = (self.js.get_axis(4) + 1) / 2.0
        throttle = raw_rt - raw_lt
        steer = -self.js.get_axis(0)

        # 2. Car-Like Physics
        if abs(throttle) < DEADBAND: throttle = 0.0
        target_v = throttle * MAX_V

        if abs(target_v) < 0.02:
            target_w = 0.0
        else:
            curvature_gain = 2.0 / TRACK_WIDTH
            target_w = steer * abs(target_v) * curvature_gain

        # 3. Smoothing
        self.curr_v += (target_v - self.curr_v) * (1.0 - np.exp(-dt / V_TAU))
        self.curr_w += (target_w - self.curr_w) * (1.0 - np.exp(-dt / W_TAU))
        
        self.comms.update_drive(self.curr_v, self.curr_w)
        
        self.v_hist.append(self.curr_v); self.w_hist.append(self.curr_w)
        self.v_curve.setData(np.array(self.v_hist))
        self.w_curve.setData(np.array(self.w_hist))

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    gui = RoverController(); gui.show()
    sys.exit(app.exec_())
