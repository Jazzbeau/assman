import asyncio
import time

from fastapi import FastAPI, WebSocket, WebSocketDisconnect

from controllers.DiscordController.discord_controller import DiscordAppController
from dev.test import test_routine
from utils.broadcaster import Broadcaster

app = FastAPI()
broadcaster = Broadcaster()
discord_controller = DiscordAppController(broadcaster)


@app.get("/testwindows")
async def test_windows():
    await test_routine()


@app.websocket("/ws")
async def websocket_test(websocket: WebSocket):
    await websocket.accept()
    await broadcaster.connect(websocket)
    print("Client connected")
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        print("Client disconnected")
    finally:
        await broadcaster.disconnect(websocket)


@app.get("/testcontroller")
async def test_controller():
    print("STARTING CONTROLLER FROM ROUTE")
    await broadcaster.broadcast({"message": "Hello?"})
    await discord_controller.start()
    return
