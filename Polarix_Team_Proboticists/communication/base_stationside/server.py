import uvicorn
import json
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from connection_manager import ConnectionManager

server = FastAPI()
manager = ConnectionManager()

server.mount("/static", StaticFiles(directory="static"), name="static")

@server.get("/")
async def get_index():
    return FileResponse('index3.html')


# --- WebSocket Endpoint ---
# --- ADD THIS NEW ROUTE ---
@server.get("/science")
async def get_science():
    return FileResponse('science.html')

@server.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """
    The main WebSocket endpoint. It registers a client by its ID
    and then listens for messages to route to other clients.
    """
    await manager.connect(websocket, client_id)
    try:
        while True:
            # Wait for a message from the client
            data = await websocket.receive_text()
            
            # --- Message Routing Logic ---
            try:
                message_data = json.loads(data)
                recipient = message_data.get("to")
                
                if recipient:
                    # Inject the sender's ID into the message
                    message_data["from"] = client_id
                    # Forward the message to the intended recipient
                    await manager.send_personal_message(json.dumps(message_data), recipient)
                else:
                    print(f"Message from '{client_id}' is missing 'to' field: {data}")

            except json.JSONDecodeError:
                print(f"Received invalid JSON from '{client_id}': {data}")

    except WebSocketDisconnect:
        manager.disconnect(client_id)
    except Exception as e:
        print(f"An error occurred with client '{client_id}': {e}")
        manager.disconnect(client_id)


if __name__ == "__main__":
    uvicorn.run(server, host="0.0.0.0", port=8000)

# --- How to Run ---
# uvicorn main:app --host 0.0.0.0 --reload
