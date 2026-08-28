"""FastAPI entrypoint.

Boots the mock telemetry engine's background tick loop, mounts the REST
routers and the `/ws/live-feed` WebSocket, and configures CORS for the
Next.js frontend.
"""

from __future__ import annotations

import asyncio
import contextlib
from collections.abc import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import ai_explanation, digital_twin, metrics, sensor_health, simulation
from app.api.websocket import manager
from app.api.websocket import router as ws_router
from app.core.config import settings
from app.engine.mock_data_engine import engine
from app.ml.inference import create_inference_engine

_tick_task: asyncio.Task | None = None

# Resolved once at import time: RuleBasedInferenceEngine unless
# BIOMIN_MODEL_CHECKPOINT_PATH points at a real trained checkpoint (see
# app/ml/inference.py). This never imports torch unless a checkpoint is
# actually configured, so the demo stays torch-free by default.
inference_engine = create_inference_engine()


async def _tick_loop() -> None:
    while True:
        snapshot = engine.tick(settings.tick_interval_seconds)
        await manager.broadcast(snapshot.model_dump(mode="json"))
        await asyncio.sleep(settings.tick_interval_seconds)


@contextlib.asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    global _tick_task
    _tick_task = asyncio.create_task(_tick_loop())
    try:
        yield
    finally:
        if _tick_task is not None:
            _tick_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await _tick_task


app = FastAPI(
    title=settings.app_name,
    version=settings.api_version,
    description="Mock-data-driven mission control API for the Biological Minimalism dashboard.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(metrics.router, prefix="/metrics", tags=["metrics"])
app.include_router(digital_twin.router, tags=["digital-twin"])
app.include_router(sensor_health.router, tags=["sensor-health"])
app.include_router(simulation.router, prefix="/simulation", tags=["simulation"])
app.include_router(ai_explanation.router, prefix="/ai", tags=["ai"])
app.include_router(ws_router, tags=["websocket"])


@app.get("/health", tags=["meta"], summary="Liveness check")
def health_check() -> dict[str, str]:
    return {
        "status": "ok",
        "service": settings.app_name,
        "version": settings.api_version,
        "inference_engine": inference_engine.name,
    }
