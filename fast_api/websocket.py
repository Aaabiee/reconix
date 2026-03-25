from __future__ import annotations

import json
import logging
from typing import Any
from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)


class ConnectionManager:

    MAX_CONNECTIONS_PER_USER = 5

    def __init__(self) -> None:
        self._connections: dict[str, list[WebSocket]] = {}
        self._user_connections: dict[int, list[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, channel: str, user_id: int | None = None) -> bool:
        if user_id is not None:
            current = len(self._user_connections.get(user_id, []))
            if current >= self.MAX_CONNECTIONS_PER_USER:
                await websocket.close(code=4029, reason="Too many connections")
                return False

        await websocket.accept()

        if channel not in self._connections:
            self._connections[channel] = []
        self._connections[channel].append(websocket)

        if user_id is not None:
            if user_id not in self._user_connections:
                self._user_connections[user_id] = []
            self._user_connections[user_id].append(websocket)

        logger.info(
            "websocket_connected",
            extra={
                "extra_data": {
                    "channel": channel,
                    "user_id": user_id,
                    "total_connections": self.connection_count,
                }
            },
        )

        return True

    def disconnect(self, websocket: WebSocket, channel: str, user_id: int | None = None) -> None:
        if channel in self._connections:
            self._connections[channel] = [
                ws for ws in self._connections[channel] if ws != websocket
            ]
            if not self._connections[channel]:
                del self._connections[channel]

        if user_id is not None and user_id in self._user_connections:
            self._user_connections[user_id] = [
                ws for ws in self._user_connections[user_id] if ws != websocket
            ]
            if not self._user_connections[user_id]:
                del self._user_connections[user_id]

    async def broadcast(self, channel: str, message: dict[str, Any]) -> int:
        if channel not in self._connections:
            return 0

        payload = json.dumps(message, default=str)
        sent = 0
        dead: list[WebSocket] = []

        for ws in self._connections[channel]:
            try:
                await ws.send_text(payload)
                sent += 1
            except Exception:
                dead.append(ws)

        for ws in dead:
            self._connections[channel].remove(ws)

        return sent

    async def send_to_user(self, user_id: int, message: dict[str, Any]) -> int:
        if user_id not in self._user_connections:
            return 0

        payload = json.dumps(message, default=str)
        sent = 0
        dead: list[WebSocket] = []

        for ws in self._user_connections[user_id]:
            try:
                await ws.send_text(payload)
                sent += 1
            except Exception:
                dead.append(ws)

        for ws in dead:
            self._user_connections[user_id].remove(ws)

        return sent

    @property
    def connection_count(self) -> int:
        return sum(len(conns) for conns in self._connections.values())

    @property
    def channel_count(self) -> int:
        return len(self._connections)


ws_manager = ConnectionManager()
