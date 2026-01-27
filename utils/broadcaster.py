import asyncio
from typing import Set

from fastapi import WebSocket


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

    async def broadcast(self, message: dict):
        async with self._lock:
            connections = self._connections

        await asyncio.gather(
            # Broadcast to all connected sockets
            *[websocket.send_json(message) for websocket in connections],
            return_exceptions=True,
        )
