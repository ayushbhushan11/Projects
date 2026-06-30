from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
import json

app = FastAPI()

# Mount static files (CSS, JS, Images)
app.mount("/static", StaticFiles(directory="static"), name="static")

# ==========================================
# 1. CONNECTION MANAGER (The Traffic Cop)
# ==========================================
class ConnectionManager:
    def __init__(self):
        # We hold lists of active connections
        self.dashboard_connections = []  # List of all open Dashboard tabs
        self.rover_connection = None     # Only one Rover allowed
        self.control_connections = []    # Gamepads

    async def connect_dashboard(self, websocket: WebSocket):
        await websocket.accept()
        self.dashboard_connections.append(websocket)
        print(f"🖥️  Dashboard connected. Total tabs: {len(self.dashboard_connections)}")

    async def connect_rover(self, websocket: WebSocket):
        await websocket.accept()
        self.rover_connection = websocket
        print("🚜 ROVER CONNECTED!")

    async def connect_control(self, websocket: WebSocket):
        await websocket.accept()
        self.control_connections.append(websocket)
        print("🎮 Controller connected")

    def disconnect(self, websocket: WebSocket, client_type: str):
        if client_type == "dashboard":
            if websocket in self.dashboard_connections:
                self.dashboard_connections.remove(websocket)
                print(f"🖥️  Dashboard tab closed. Remaining: {len(self.dashboard_connections)}")
        elif client_type == "rover":
            self.rover_connection = None
            print("⚠️ ROVER DISCONNECTED")
        elif client_type == "control":
            if websocket in self.control_connections:
                self.control_connections.remove(websocket)

    # --- BROADCASTING ---
    async def broadcast_to_dashboards(self, message: dict):
        # Send to EVERY open dashboard tab
        dead_connections = []
        for connection in self.dashboard_connections:
            try:
                await connection.send_text(json.dumps(message))
            except:
                dead_connections.append(connection)
        
        # Cleanup dead tabs
        for dead in dead_connections:
            self.dashboard_connections.remove(dead)

    async def send_to_rover(self, message: dict):
        # Send command to the Rover
        if self.rover_connection:
            try:
                await self.rover_connection.send_text(json.dumps(message))
            except:
                print("❌ Failed to send to Rover")

manager = ConnectionManager()

# ==========================================
# 2. ROUTES (HTML Pages)
# ==========================================
@app.get("/")
async def get_dashboard():
    return FileResponse('index3.html') 

@app.get("/science")
async def get_science():
    return FileResponse('science.html')

# ==========================================
# 3. WEBSOCKET ENDPOINTS
# ==========================================

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    # 1. DETERMINE WHO IS CONNECTING
    client_type = ""
    if "dashboard" in client_id:
        client_type = "dashboard"
        await manager.connect_dashboard(websocket)
    elif "rover" in client_id:
        client_type = "rover"
        await manager.connect_rover(websocket)
    elif "gamepad" in client_id:
        client_type = "control"
        await manager.connect_control(websocket)
    else:
        # Default fallback (treat as dashboard if unsure)
        client_type = "dashboard"
        await manager.connect_dashboard(websocket)

    # 2. MAIN LOOP
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # LOGIC: ROUTE THE MESSAGE
            
            # Case A: Message FROM Rover -> TO Dashboards
            if client_type == "rover":
                # Broadcast telemetry/science to ALL dashboard tabs
                await manager.broadcast_to_dashboards(message)

            # Case B: Message FROM Gamepad -> TO Rover
            elif client_type == "control":
                # Forward joystick commands to Rover
                await manager.send_to_rover(message)

            # Case C: Message FROM Dashboard -> TO Rover (Future proofing)
            elif client_type == "dashboard":
                await manager.send_to_rover(message)

    except WebSocketDisconnect:
        manager.disconnect(websocket, client_type)
    except Exception as e:
        print(f"Error: {e}")
        manager.disconnect(websocket, client_type)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
