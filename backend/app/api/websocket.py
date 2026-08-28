"""`/ws/live-feed` — the telemetry-only push stream.

Simulation controls (mode / sensor failure) stay on REST (`api/routes/simulation.py`);
this socket exists purely to broadcast `LiveMetricsSnapshot` frames as the
mock engine ticks, so the frontend charts update smoothly without polling.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)
router = APIRouter()


class ConnectionManager:
    def __init__(self) -> None:
        self.active: set[WebSocket] = set()

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active.add(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        self.active.discard(websocket)

    async def broadcast(self, payload: dict) -> None:
        stale: list[WebSocket] = []
        for ws in list(self.active):
            try:
                await ws.send_json(payload)
            except Exception:  # noqa: BLE001 - a broken socket shouldn't kill the tick loop
                stale.append(ws)
        for ws in stale:
            self.disconnect(ws)


manager = ConnectionManager()


@router.websocket("/ws/live-feed")
async def live_feed(websocket: WebSocket) -> None:
    await manager.connect(websocket)
    try:
        while True:
            # This stream is telemetry-only; we don't act on client
            # messages, but awaiting receive keeps the connection open and
            # lets us detect a disconnect promptly.
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
