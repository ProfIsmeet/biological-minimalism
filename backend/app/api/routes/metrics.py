"""`/metrics/*` — live and historical telemetry."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from app.core.config import settings
from app.engine.data_sources import data_source_manager
from app.schemas.telemetry import LiveMetricsSnapshot

router = APIRouter()


@router.get("/live", response_model=LiveMetricsSnapshot, summary="Latest telemetry snapshot")
def get_live_metrics() -> LiveMetricsSnapshot:
    snapshot = data_source_manager.latest_snapshot
    if snapshot is None:
        snapshot = data_source_manager.tick(settings.tick_interval_seconds)
    if snapshot is None:
        raise HTTPException(
            status_code=409,
            detail="The active dataset replay is paused or has not emitted a frame yet.",
        )
    return snapshot


@router.get("/history", response_model=list[LiveMetricsSnapshot], summary="Recent telemetry history for trend charts")
def get_metrics_history(
    limit: int = Query(100, ge=1, le=settings.rolling_history_length),
) -> list[LiveMetricsSnapshot]:
    return data_source_manager.history(limit)
