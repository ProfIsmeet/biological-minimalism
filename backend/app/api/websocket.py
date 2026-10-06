"""`/ws/live-feed` — the telemetry-only push stream.

Simulation controls (mode / sensor failure) stay on REST (`api/routes/simulation.py`);
this socket exists purely to broadcast `LiveMetricsSnapshot` frames as the
active synthetic or dataset-replay source ticks, so the frontend charts
update smoothly without polling.
"""

from __future__ import annotations

import asyncio
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()


class ConnectionManager:
    def __init__(self) -> None:
        self.active: set[WebSocket] = set()

    async def connect(self, websocket: WebSocket) -> None:
        if settings.public_presentation_mode and len(self.active) >= settings.public_max_websocket_clients:
            await websocket.close(code=1013, reason="Live feed is at capacity")
            raise WebSocketDisconnect(code=1013)
        await websocket.accept()
        self.active.add(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        self.active.discard(websocket)

    async def broadcast(self, payload: dict) -> None:
        stale: list[WebSocket] = []
        for ws in list(self.active):
            try:
                await asyncio.wait_for(ws.send_json(payload), timeout=2.0)
            except Exception:  # noqa: BLE001 - a broken socket shouldn't kill the tick loop
                stale.append(ws)
        for ws in stale:
            self.disconnect(ws)


manager = ConnectionManager()


@router.websocket("/ws/live-feed")
async def live_feed(websocket: WebSocket) -> None:
    if settings.public_presentation_mode:
        origin = websocket.headers.get("origin")
        if origin not in settings.allowed_origins:
            logger.warning("Rejected live-feed WebSocket from an unapproved origin")
            await websocket.close(code=1008, reason="Origin not allowed")
            return
    await manager.connect(websocket)
    try:
        while True:
            # This stream is telemetry-only; we don't act on client
            # messages, but awaiting receive keeps the connection open and
            # lets us detect a disconnect promptly.
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
