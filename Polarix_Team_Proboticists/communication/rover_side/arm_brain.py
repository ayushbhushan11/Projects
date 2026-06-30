import asyncio
import websockets
import json
import serial

# ================= CONFIGURATION =================
SERVER_IP = "127.0.0.1" # Connects to local Dashboard Server
SERVER_PORT = 8000
CLIENT_ID = "arm_bridge"

# ⚠️ CHANGE THIS to your Arm Arduino Port
# Try /dev/ttyACM0, /dev/ttyACM1, or /dev/ttyUSB1
SERIAL_PORT_ARM = '/dev/ttyACM0' 
BAUD_RATE = 115200

# ================= SETUP =================
print(f"🔌 [ARM] Opening Serial Port {SERIAL_PORT_ARM}...")
try:
    ser = serial.Serial(SERIAL_PORT_ARM, BAUD_RATE, timeout=0)
    print("✅ [ARM] Arm Arduino Connected!")
except Exception as e:
    print(f"❌ [ARM] Failed to open Serial: {e}")
    print("⚠️  (Check if another script is using this port!)")
    exit()

# ================= LISTENER LOOP =================
async def arm_listener():
    uri = f"ws://{SERVER_IP}:{SERVER_PORT}/ws/{CLIENT_ID}"
    
    while True:
        try:
            print(f"🦾 [ARM] Connecting to {uri}...")
            async with websockets.connect(uri) as ws:
                print("✅ [ARM] Bridge Active - Waiting for Commands...")
                
                async for message in ws:
                    try:
                        data = json.loads(message)
                        
                        # FILTER: Only listen for 'arm_data'
                        if data.get("topic") == "arm_data":
                            # Payload is the string "<1,100|...>"
                            packet = data.get("payload", "")
                            
                            if packet and packet.startswith("<"):
                                # ⚠️ CRITICAL: Arduino uses readStringUntil('\n')
                                # We MUST add the newline character here!
                                final_cmd = packet + "\n"
                                ser.write(final_cmd.encode('utf-8'))
                                
                                # print(f"Sent: {packet}") # Uncomment to debug

                    except: pass

        except Exception as e:
            print(f"❌ Connection Error: {e}")
            await asyncio.sleep(2)

if __name__ == "__main__":
    try:
        asyncio.run(arm_listener())
    except KeyboardInterrupt:
        if ser: ser.close()
        print("\n🛑 Stopped.")
