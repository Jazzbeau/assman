import asyncio
import time

from fastapi import FastAPI, WebSocket, WebSocketDisconnect

from dev.test import test_app, test_discord, test_routine
from dev.test_controller import test_controller
from utils.broadcaster import Broadcaster

app = FastAPI()
broadcaster = Broadcaster()


@app.get("/testwindows")
async def test_windows():
    await test_routine()


@app.get("/testcontroller")
async def test_controller_route():
    return await test_controller()


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
