import sys
import time
import json
import struct
import numpy as np
import websocket
from threading import Thread
from PyQt5 import QtCore, QtWidgets
import pyqtgraph as pg
from collections import deque

# ===============================
# Physical Parameters
# ===============================
MAX_V = 0.368          
TRACK_WIDTH = 10       
UPDATE_HZ = 50         
V_TAU = 0.40           
W_TAU = 0.35
DEADBAND = 0.05

# ===============================
# Network Configuration
# ===============================
SERVER_IP = "192.168.1.10" 
WS_URL = f"ws://{SERVER_IP}:8000/ws/drive_logic"

class DriveSubscriber(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Rover Drive Logic & Telemetry")
        self.resize(800, 500)
        
        self.target_v, self.target_w = 0.0, 0.0
        self.curr_v, self.curr_w = 0.0, 0.0
        self.rt, self.lt, self.steer = 0.0, 0.0, 0.0
        self.last_t = time.time()

        # ================= UI =================
        central = QtWidgets.QWidget()
        self.setCentralWidget(central)
        layout = QtWidgets.QVBoxLayout(central)

        self.plot = pg.PlotWidget(title="Real-time Kinematics (V=Green, W=Red)")
        self.plot.addLegend()
        layout.addWidget(self.plot)

        self.v_curve = self.plot.plot(pen='g', name="V (m/s)")
        self.w_curve = self.plot.plot(pen='r', name="W (rad/s)")

        self.v_hist = deque([0]*200, maxlen=200)
        self.w_hist = deque([0]*200, maxlen=200)

        # ================= WebSocket =================
        self.ws = websocket.WebSocketApp(WS_URL, 
                                         on_message=self.on_message,
                                         on_open=self.on_open,
                                         on_error=self.on_error)
        Thread(target=self.ws.run_forever, daemon=True).start()

        # ================= Timer =================
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_physics)
        self.timer.start(int(1000 / UPDATE_HZ))

    def on_open(self, ws):
        print("✅ Drive Logic Subscribed")

    def on_error(self, ws, error):
        print(f"❌ Connection Error: {error}")

    def on_message(self, ws, message):
        try:
            data = json.loads(message)
            if data.get("topic") == "gamepad_event":
                payload = data["payload"]
                code = payload["code"]
                val = payload["value"]

                if code == "ABS_X":
                    raw = (val - 128) / 128.0 
                    self.steer = 0.0 if abs(raw) < DEADBAND else raw
                elif code in ["ABS_RZ", "ABS_GAS"]:
                    self.rt = val / 255.0
                elif code in ["ABS_Z", "ABS_BRAKE"]:
                    self.lt = val / 255.0

        except Exception as e:
            pass 

    def update_physics(self):
        dt = time.time() - self.last_t
        self.last_t = time.time()

        throttle = self.rt - self.lt
        self.target_v = throttle * MAX_V

        if abs(self.target_v) < 0.02:
            self.target_w = 0.0
        else:
            curvature_gain = 2.0 / TRACK_WIDTH
            self.target_w = -self.steer * abs(self.target_v) * curvature_gain

        alpha_v = 1.0 - np.exp(-dt / V_TAU)
        alpha_w = 1.0 - np.exp(-dt / W_TAU)

        self.curr_v += (self.target_v - self.curr_v) * alpha_v
        self.curr_w += (self.target_w - self.curr_w) * alpha_w

        if self.ws.sock and self.ws.sock.connected:
            # 1. To STM32
            bin_packet = struct.pack('<Bff', 0xAA, self.curr_v, self.curr_w)
            self.ws.send(bin_packet, opcode=websocket.ABNF.OPCODE_BINARY)
            
            # 2. To Dashboard
            dash_packet = {
                "to": "dashboard_client",   # <--- ADDED ROUTING ADDRESS
                "from": "laptop_controller",
                "topic": "drive_data",
                "payload": {"v": self.curr_v, "w": self.curr_w}
            }
            self.ws.send(json.dumps(dash_packet))

        self.v_hist.append(self.curr_v)
        self.w_hist.append(self.curr_w)
        self.v_curve.setData(np.array(self.v_hist))
        self.w_curve.setData(np.array(self.w_hist))
        
        print(f"V: {self.curr_v:+.3f} m/s | W: {self.curr_w:+.3f} rad/s", end='\r')

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = DriveSubscriber()
    window.show()
    sys.exit(app.exec_())
