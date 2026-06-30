import sys
import time
import json
import threading
import numpy as np
import websocket
from inputs import get_gamepad
from PyQt5 import QtCore, QtGui, QtWidgets
import pyqtgraph as pg

# ================= CONFIGURATION =================
SERVER_IP = "192.168.1.10"
SERVER_PORT = 8000
WS_URL = f"ws://{SERVER_IP}:{SERVER_PORT}/ws/laptop_controller"

# Physics Constants
MAX_RPM = 60
WHEEL_DIAMETER = 0.234
TRACK_WIDTH = 0.892
MAX_V = (MAX_RPM * 2 * np.pi / 60.0) * (WHEEL_DIAMETER / 2.0)
MAX_W = (2 * MAX_V) / TRACK_WIDTH
V_TAU = 0.25 
W_TAU = 0.15 
UPDATE_HZ = 20 

class GamepadThread(QtCore.QThread):
    drive_signal = QtCore.pyqtSignal(float, float) 
    arm_signal = QtCore.pyqtSignal(str)            
    event_signal = QtCore.pyqtSignal(dict)         

    def run(self):
        print("🎮 MASTER COMMANDER ACTIVE")
        
        # --- DRIVE VARIABLES ---
        fwd_val = 0.0   
        steer_val = 0.0 

        # --- ARM VARIABLES ---
        # Index: 0=Base, 1=Gripper, 2=Roll, 3=Pitch, 4=Elbow, 5=Shoulder
        motors = [(0, 0) for _ in range(6)]
        SPEED_BASE = 150; SPEED_ELBOW = 150 
        SPEED_WRIST = 120; SPEED_GRIPPER = 255; SPEED_SHOULDER = 1 

        while True:
            try:
                events = get_gamepad()
                dirty_arm = False 

                for event in events:
                    if event.code == "SYN_REPORT": continue

                    # [1] BROADCAST RAW EVENT
                    if event.ev_type != 'Sync':
                        self.event_signal.emit({
                            "type": event.ev_type, "code": event.code, "value": event.state
                        })

                    # ================= DRIVE LOGIC =================
                    if event.code == "ABS_X": 
                        raw = (event.state - 128) / 128.0 
                        steer_val = 0.0 if abs(raw) < 0.1 else raw
                    
                    elif event.code == "ABS_Y":
                        raw = (event.state - 128) / 128.0
                        fwd_val = -raw if abs(raw) > 0.1 else 0.0

                    # ================= ARM LOGIC (Fixed Face Buttons) =================
                    # Shoulder (Y/A)
                    elif event.code == "BTN_NORTH": # Y Button
                        motors[5] = (1, SPEED_SHOULDER) if event.state else (0, 0); dirty_arm = True
                    elif event.code == "BTN_SOUTH": # A Button
                        motors[5] = (-1, SPEED_SHOULDER) if event.state else (0, 0); dirty_arm = True

                    # Base (X/B)
                    elif event.code == "BTN_WEST":  # X Button
                        motors[0] = (-1, SPEED_BASE) if event.state else (0, 0); dirty_arm = True
                    elif event.code == "BTN_EAST":  # B Button
                        motors[0] = (1, SPEED_BASE) if event.state else (0, 0); dirty_arm = True

                    # Gripper (Select/Start)
                    elif event.code == "BTN_SELECT": 
                        motors[1] = (1, SPEED_GRIPPER) if event.state else (0,0); dirty_arm = True
                    elif event.code == "BTN_START":  
                        motors[1] = (-1, SPEED_GRIPPER) if event.state else (0,0); dirty_arm = True

                    # Elbow (Bumpers)
                    elif event.code == "BTN_TL": 
                        motors[4] = (-1, SPEED_ELBOW) if event.state else (0,0); dirty_arm = True
                    elif event.code == "BTN_TR": 
                        motors[4] = (1, SPEED_ELBOW) if event.state else (0,0); dirty_arm = True

                    # Wrist (Right Stick)
                    elif event.code == "ABS_RX":
                        val = (event.state - 128) / 128.0
                        if val > 0.5:    motors[2] = (1, SPEED_WRIST)
                        elif val < -0.5: motors[2] = (-1, SPEED_WRIST)
                        else:            motors[2] = (0, 0); dirty_arm = True

                    elif event.code == "ABS_Z": # Or ABS_RY depending on controller
                        val = (event.state - 128) / 128.0
                        if val > 0.5:    motors[3] = (-1, SPEED_WRIST) 
                        elif val < -0.5: motors[3] = (1, SPEED_WRIST) 
                        else:            motors[3] = (0, 0); dirty_arm = True

                # --- SEND SIGNALS ---
                target_v = fwd_val * MAX_V
                target_w = -steer_val * MAX_W 
                self.drive_signal.emit(target_v, target_w)

                if dirty_arm:
                    payload = "<" + "|".join(f"{d},{p}" for d, p in motors) + ">"
                    self.arm_signal.emit(payload)

            except Exception: pass

class CommsThread(QtCore.QThread):
    ack_signal = QtCore.pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.ws = None; self.connected = False; self.running = True
        self.latest_v = 0.0; self.latest_w = 0.0

    def run(self):
        while self.running:
            try:
                self.ws = websocket.WebSocketApp(WS_URL, on_open=self.on_open, on_message=self.on_message)
                self.ws.run_forever()
                time.sleep(2)
            except: time.sleep(2)

    def on_open(self, ws):
        self.connected = True
        threading.Thread(target=self.sender_loop, daemon=True).start()

    def on_message(self, ws, message):
        try:
            data = json.loads(message)
            if data.get("topic") == "ack": self.ack_signal.emit(f"ACK: {data['payload']}")
        except: pass

    def update_drive(self, v, w):
        self.latest_v = v; self.latest_w = w

    def send_arm_packet(self, packet_str):
        if self.connected:
            try: self.ws.send(json.dumps({"to": "arm_bridge", "from": "laptop", "topic": "arm_data", "payload": packet_str}))
            except: pass

    def broadcast_event(self, evt):
        if self.connected:
            if evt['code'] == "BTN_WEST" and evt['value'] == 1:
                try: self.ws.send(json.dumps({"topic": "snapshot", "from": "laptop", "payload": {}}))
                except: pass
            try: self.ws.send(json.dumps({"topic": "gamepad_event", "from": "laptop", "payload": evt}))
            except: pass

    def sender_loop(self):
        while self.connected and self.running:
            try: 
                msg = {"to": "drive_bridge", "from": "laptop", "topic": "drive_data", "payload": {"v": self.latest_v, "w": self.latest_w}}
                self.ws.send(json.dumps(msg))
            except: self.connected = False; break
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
        self.plot = pg.PlotWidget(title="Live Telemetry"); self.plot.setYRange(-1.5, 1.5); self.plot.addLegend()
        self.v_curve = self.plot.plot(pen='g', name="V"); self.w_curve = self.plot.plot(pen='r', name="W")
        self.v_hist = [0]*100; self.w_hist = [0]*100
        layout.addWidget(self.plot)
        self.lbl = QtWidgets.QLabel("Status: Connecting..."); layout.addWidget(self.lbl)

        self.comms = CommsThread()
        self.comms.ack_signal.connect(self.lbl.setText)
        self.comms.start()

        self.gp = GamepadThread()
        self.gp.drive_signal.connect(self.update_targets)
        self.gp.arm_signal.connect(self.comms.send_arm_packet)
        self.gp.event_signal.connect(self.comms.broadcast_event) 
        self.gp.start()

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.physics_loop); self.timer.start(int(1000/UPDATE_HZ))

    def update_targets(self, v, w): self.target_v = v; self.target_w = w

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
    app = QtWidgets.QApplication(sys.argv); gui = RoverController(); gui.show(); sys.exit(app.exec_())
