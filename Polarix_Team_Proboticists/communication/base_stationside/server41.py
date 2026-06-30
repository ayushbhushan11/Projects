from fastapi import FastAPI, WebSocket, UploadFile, File
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import uvicorn, json, os, shutil, csv, asyncio
from datetime import datetime

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

# --- CONFIGURATION ---
MEDIA_FOLDER = os.path.expanduser("~/proboticists/rover/webrtcimplemenation/dashboard/mission_gallery")
LOG_FOLDER = os.path.expanduser("~/proboticists/rover/webrtcimplemenation/dashboard/mission_data")

for folder in [MEDIA_FOLDER, LOG_FOLDER]:
    if not os.path.exists(folder):
        os.makedirs(folder)

# --- CONNECTION MANAGER (NON-BLOCKING) ---
class ConnectionManager:
    def __init__(self): 
        self.active_connections = []
    
    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.active_connections.append(ws)

    def disconnect(self, ws: WebSocket):
        if ws in self.active_connections: 
            self.active_connections.remove(ws)

    async def broadcast(self, message: str, sender: WebSocket = None):
        # Loop through a copy of connections
        for connection in self.active_connections[:]:
            if connection != sender:
                try:
                    # --- THE FIX: TIMEOUT ---
                    # If a client (Rover) is slow, don't wait forever.
                    # Give it 20ms. If it fails, skip it and keep the Server alive.
                    await asyncio.wait_for(connection.send_text(message), timeout=0.02)
                except asyncio.TimeoutError:
                    # Client is too slow (Network lag), skip this frame
                    pass
                except Exception:
                    # Client is dead, remove it
                    self.disconnect(connection)

manager = ConnectionManager()

# --- ROUTES ---
@app.get("/")
async def get(): return FileResponse('index7.html')

@app.get("/science")
async def get_sci(): return FileResponse('science3.html')

@app.post("/log_data")
async def log(data: dict):
    file_path = os.path.join(LOG_FOLDER, "mission_log.csv")
    with open(file_path, "a", newline='') as f:
        w = csv.DictWriter(f, fieldnames=data.keys())
        if f.tell()==0: w.writeheader()
        w.writerow(data)
    return {"status":"ok"}

@app.post("/upload_media")
async def upload_media(file: UploadFile = File(...)):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    clean_name = f"{timestamp}_{file.filename}"
    save_path = os.path.join(MEDIA_FOLDER, clean_name)
    with open(save_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    return {"filename": clean_name}

# --- WEBSOCKET ENDPOINT ---
@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await manager.broadcast(data, sender=websocket)
    except:
        manager.disconnect(websocket)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
