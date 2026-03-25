import pytest
import json
from unittest.mock import AsyncMock, MagicMock
from fast_api.websocket import ConnectionManager


@pytest.fixture
def manager():
    return ConnectionManager()


def make_websocket():
    ws = AsyncMock()
    ws.send_text = AsyncMock()
    return ws


class TestConnectionManager:

    @pytest.mark.asyncio
    async def test_connect_increments_count(self, manager):
        ws = make_websocket()
        await manager.connect(ws, "notifications", user_id=1)
        assert manager.connection_count == 1

    @pytest.mark.asyncio
    async def test_disconnect_decrements_count(self, manager):
        ws = make_websocket()
        await manager.connect(ws, "notifications", user_id=1)
        assert manager.connection_count == 1
        manager.disconnect(ws, "notifications", user_id=1)
        assert manager.connection_count == 0

    @pytest.mark.asyncio
    async def test_broadcast_sends_to_channel(self, manager):
        ws1 = make_websocket()
        ws2 = make_websocket()
        await manager.connect(ws1, "notifications", user_id=1)
        await manager.connect(ws2, "notifications", user_id=2)

        sent = await manager.broadcast("notifications", {"type": "alert", "data": "test"})
        assert sent == 2
        ws1.send_text.assert_called_once()
        ws2.send_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_broadcast_to_empty_channel(self, manager):
        sent = await manager.broadcast("empty_channel", {"type": "test"})
        assert sent == 0

    @pytest.mark.asyncio
    async def test_send_to_user(self, manager):
        ws = make_websocket()
        await manager.connect(ws, "notifications", user_id=42)

        sent = await manager.send_to_user(42, {"type": "personal", "data": "hello"})
        assert sent == 1
        ws.send_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_to_nonexistent_user(self, manager):
        sent = await manager.send_to_user(999, {"type": "test"})
        assert sent == 0

    @pytest.mark.asyncio
    async def test_multiple_channels(self, manager):
        ws1 = make_websocket()
        ws2 = make_websocket()
        await manager.connect(ws1, "notifications", user_id=1)
        await manager.connect(ws2, "delink_updates", user_id=2)

        assert manager.channel_count == 2
        assert manager.connection_count == 2

    @pytest.mark.asyncio
    async def test_broadcast_removes_dead_connections(self, manager):
        ws_alive = make_websocket()
        ws_dead = make_websocket()
        ws_dead.send_text.side_effect = RuntimeError("connection closed")

        await manager.connect(ws_alive, "notifications", user_id=1)
        await manager.connect(ws_dead, "notifications", user_id=2)

        sent = await manager.broadcast("notifications", {"type": "test"})
        assert sent == 1
        assert manager.connection_count == 1

    @pytest.mark.asyncio
    async def test_disconnect_nonexistent_channel(self, manager):
        ws = make_websocket()
        manager.disconnect(ws, "nonexistent", user_id=1)
        assert manager.connection_count == 0

    @pytest.mark.asyncio
    async def test_user_multiple_connections(self, manager):
        ws1 = make_websocket()
        ws2 = make_websocket()
        await manager.connect(ws1, "notifications", user_id=1)
        await manager.connect(ws2, "delink_updates", user_id=1)

        sent = await manager.send_to_user(1, {"type": "broadcast"})
        assert sent == 2
