import asyncio
import websockets
import json
import serial
import struct # <--- CRITICAL: Packs V/W into Binary for STM32

# ================= CONFIGURATION =================
SERVER_IP = "127.0.0.1" # Connects to the local Dashboard Server
SERVER_PORT = 8000
CLIENT_ID = "drive_bridge"

# ⚠️ CRITICAL: Check your Drive STM port! 
# It is usually /dev/ttyUSB0 or /dev/ttyS0. 
# It MUST match what 'radxa_uart' was using.
SERIAL_PORT_DRIVE = '/dev/ttyUSB0' 
BAUD_RATE = 115200

# ================= SETUP =================
print(f"🔌 [DRIVE] Opening Drive STM on {SERIAL_PORT_DRIVE}...")
try:
    ser = serial.Serial(SERIAL_PORT_DRIVE, BAUD_RATE, timeout=0)
    print("✅ [DRIVE] Drive STM Connected!")
except Exception as e:
    print(f"❌ [DRIVE] Failed to open Serial: {e}")
    print("⚠️  (STOP 'radxa_uart' first! The port is busy.)")
    exit()

# ================= LISTENER LOOP =================
async def drive_listener():
    uri = f"ws://{SERVER_IP}:{SERVER_PORT}/ws/{CLIENT_ID}"
    
    while True:
        try:
            print(f"📡 [DRIVE] Connecting to {uri}...")
            async with websockets.connect(uri) as ws:
                print("✅ [DRIVE] Bridge Active - Ready for Physics!")
                
                async for message in ws:
                    try:
                        data = json.loads(message)
                        
                        # FILTER: Only listen for 'drive_data' from Laptop
                        if data.get("topic") == "drive_data":
                            payload = data.get("payload", {})
                            
                            # 1. Extract V and W
                            v = float(payload.get("v", 0.0))
                            w = float(payload.get("w", 0.0))
                            
                            # 2. Pack into Binary for STM32
                            # Protocol: 0xAA (Start) + Float(v) + Float(w) + 0x0A (End)
                            # '<BffB' = Little Endian, UByte, Float, Float, UByte
                            packet = struct.pack('<BffB', 0xAA, v, w, 0x0A)
                            
                            # 3. Send to STM32
                            ser.write(packet)
                            
                            # debug print (optional)
                            # print(f"🏎️  V:{v:.2f} W:{w:.2f}") 

                    except: pass

        except Exception as e:
            print(f"❌ Connection Error: {e}")
            await asyncio.sleep(2)

if __name__ == "__main__":
    try:
        asyncio.run(drive_listener())
    except KeyboardInterrupt:
        if ser: ser.close()
        print("\n🛑 Stopped.")
