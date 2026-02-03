from fastapi import Request, WebSocket

from controllers.DiscordController.discord_controller import DiscordAppController
from utils.broadcaster import Broadcaster


def get_broadcaster(websocket: WebSocket) -> Broadcaster:
    return websocket.app.state.broadcaster


def get_discord_controller(request: Request) -> DiscordAppController:
    return request.app.state.discord_controller
