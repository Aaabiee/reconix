from __future__ import annotations

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from fast_api.websocket import ws_manager
from fast_api.auth.authlib.jwt_handler import JWTHandler

router = APIRouter(tags=["websocket"])

ALLOWED_CHANNELS = frozenset({
    "notifications", "delink_updates", "sim_alerts", "system",
})


@router.websocket("/ws/{channel}")
async def websocket_endpoint(
    websocket: WebSocket,
    channel: str,
    token: str = Query(...),
):
    if channel not in ALLOWED_CHANNELS:
        await websocket.close(code=4003, reason="Invalid channel")
        return

    try:
        payload = JWTHandler.verify_token(token, expected_type="access")
        user_id = int(payload.get("sub", 0))
    except Exception:
        await websocket.close(code=4001, reason="Authentication failed")
        return

    if not user_id:
        await websocket.close(code=4001, reason="Invalid token")
        return

    await ws_manager.connect(websocket, channel, user_id)

    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket, channel, user_id)
    except Exception:
        ws_manager.disconnect(websocket, channel, user_id)
