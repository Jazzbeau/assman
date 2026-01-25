import asyncio
import time

from fastapi import FastAPI, WebSocket, WebSocketDisconnect

from models.broadcaster import Broadcaster
from models.managed_app import test_app

app = FastAPI()
broadcaster = Broadcaster()


@app.get("/testwindows")
async def test_windows():
    await test_app()


@app.websocket("/ws")
async def websocket_test(websocket: WebSocket):
    await websocket.accept()
    await broadcaster.connect(websocket)
    print("Client connected")
    try:
        while True:
            await asyncio.sleep(1)
            await broadcaster.broadcast(
                {"message": f"{time.strftime("%I:%M:%S%p on %B %d, %Y")}!!!!"}
            )
            # await websocket.receive_text()
    except WebSocketDisconnect:
        print("Client disconnected")
    finally:
        await broadcaster.disconnect(websocket)
