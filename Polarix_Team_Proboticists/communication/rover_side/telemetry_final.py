import asyncio
import websockets
import json
import subprocess
import serial

# ================= CONFIGURATION =================
SERVER_IP = "192.168.1.10"
SERVER_PORT = 8000
CLIENT_ID = "rover"
GAMEPAD_SENDER_ID = "laptop_controller" # UPDATED ID
SERIAL_PORT_STM     = '/dev/ttyUSB0'
BAUD_RATE           = 115200

ANTENNA_IP = "192.168.1.253"
OID_SNR = "1.3.6.1.4.1.11863.20.1.4.1.0"
BASE_STATION_IP = "192.168.1.254"

# ================= GLOBAL CACHE =================
LATEST_RSSI = -99
LATEST_PING = 999

def get_real_rssi_from_snr():
    try:
        cmd = ["snmpget", "-v", "2c", "-c", "public", "-O", "qv", ANTENNA_IP, OID_SNR]
        output = subprocess.check_output(cmd, stderr=subprocess.STDOUT, universal_newlines=True)
        snr_val = int(output.strip().replace("Gauge32: ", ""))
        return max(min(-90 + snr_val, -30), -99)
    except:
        return -99

def read_ping():
    try:
        cmd = ["ping", "-c", "1", "-W", "1", BASE_STATION_IP]
        output = subprocess.check_output(cmd, stderr=subprocess.STDOUT, universal_newlines=True)
        if "time=" in output:
            return int(float(output.split("time=")[1].split(" ")[0]))
    except:
        return 999
    return 999

def read_cpu_temp():
    try:
        with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
            return round(int(f.read().strip()) / 1000, 1)
    except:
        return 0

async def listen_to_gamepad(ws, ser_stm):
    print("🎮 SIF Listener Started...")
    async for message in ws:
        try:
            data = json.loads(message)
            # Checking for laptop_controller and gamepad_event
            if data.get("from") == GAMEPAD_SENDER_ID and data.get("topic") == "gamepad_event":
                payload = data.get("payload", {})
                if payload.get("value") == 1:
                    code = payload.get("code")
                    if code == "BTN_THUMBL":
                        if ser_stm: ser_stm.write(b'L')
                    elif code == "BTN_THUMBR":
                        if ser_stm: ser_stm.write(b'R')
        except:
            pass

async def send_telemetry():
    uri = f"ws://{SERVER_IP}:{SERVER_PORT}/ws/{CLIENT_ID}"
    ser_stm = None
    try:
        ser_stm = serial.Serial(SERIAL_PORT_STM, BAUD_RATE, timeout=0.05)
        print(f"✅ CONNECTED: STM32 on {SERIAL_PORT_STM}")
    except:
        print("⚠️ FAILED: STM32")

    async with websockets.connect(uri) as ws:
        asyncio.create_task(listen_to_gamepad(ws, ser_stm))
        
        while True:
            rssi = await asyncio.to_thread(get_real_rssi_from_snr)
            ping = await asyncio.to_thread(read_ping)
            
            packet = {
                "topic": "telemetry",
                "rssi": rssi,
                "temperature": read_cpu_temp(),
                "link_quality": f"{ping}ms"
            }
            await ws.send(json.dumps(packet))
            await asyncio.sleep(1.0)

if __name__ == "__main__":
    asyncio.run(send_telemetry())
