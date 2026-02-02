import asyncio
from typing import Set

from fastapi import WebSocket

from controllers.controller_types import AppBroadcastType, JSONType


class Broadcaster:
    def __init__(self):
        self._connections: Set[WebSocket] = set()
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket):
        async with self._lock:
            self._connections.add(websocket)

    async def disconnect(self, websocket: WebSocket):
        async with self._lock:
            self._connections.discard(websocket)

    async def broadcast(self, message: dict[str, JSONType], message_type: AppBroadcastType | None = None):
        async with self._lock:
            connections = self._connections

        broadcast = message

        if message_type:
            broadcast['message_type'] = message_type.value


        await asyncio.gather(
            # Broadcast to all connected sockets
            *[websocket.send_json(message) for websocket in connections],
            return_exceptions=True,
        )
