import asyncio
import websockets
import serial
import struct

# ===============================
# Configuration
# ===============================
# Replace with your Laptop's actual IP address
SERVER_IP = "192.168.1.10" 
WS_URL = f"ws://{SERVER_IP}:8000/ws/radxa_rover"

# Radxa Serial Port (Usually /dev/ttyS0 or /dev/ttyUSB0 for STM32)
SERIAL_PORT = "/dev/ttyUSB1" 
BAUD_RATE = 115200

# ===============================
# Bridge Logic
# ===============================
async def bridge():
    try:
        # Initialize Serial connection to STM32
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=0.1)
        print(f"✅ Connected to STM32 on {SERIAL_PORT}")
    except Exception as e:
        print(f"❌ Serial Error: {e}")
        return

    print(f"📡 Connecting to Server at {WS_URL}...")
    
    while True:
        try:
            async with websockets.connect(WS_URL) as websocket:
                print("✅ WebSocket Connected: Pushing binary data to STM32")
                
                while True:
                    # Receive the binary packet (9 bytes: 0xAA + 2 floats)
                    packet = await websocket.recv()
                    
                    if isinstance(packet, bytes) and len(packet) == 9:
                        # Verify the header 0xAA
                        if packet[0] == 0xAA:
                            ser.write(packet)
                            # Optional: Print hex for debugging
                            print(f"Piped: {packet.hex()}") 
                    else:
                        # Handle JSON messages if any (like arm commands)
                        pass
                        
        except Exception as e:
            print(f"❌ Connection lost: {e}. Retrying in 2s...")
            await asyncio.sleep(2)

if __name__ == "__main__":
    asyncio.run(bridge())
