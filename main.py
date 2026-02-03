from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, WebSocket, WebSocketDisconnect

from controllers.DiscordController.discord_controller import DiscordAppController
from dependencies import get_broadcaster, get_discord_controller
from dev.test import test_routine
from utils.broadcaster import Broadcaster


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting the A.S.S.M.A.N.")
    broadcaster = Broadcaster()
    discord_controller = DiscordAppController(broadcaster)

    app.state.broadcaster = broadcaster
    app.state.discord_controller = discord_controller

    yield

    if discord_controller.is_running():
        await discord_controller.stop()


app = FastAPI(lifespan=lifespan)


@app.get("/testwindows")
async def test_windows():
    await test_routine()


@app.websocket("/ws")
async def websocket_connect(websocket: WebSocket, broadcaster=Depends(get_broadcaster)):
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


@app.get("/start")
async def start_discord(
    discord_controller: DiscordAppController = Depends(get_discord_controller),
):
    await discord_controller.start()
    return
