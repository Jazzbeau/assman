from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, WebSocket, WebSocketDisconnect

from controllers.DiscordController.discord_controller import DiscordAppController
from dependencies import get_broadcaster
from routers.discord_router import router as discord_router
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
app.include_router(discord_router, prefix="/discord")


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
