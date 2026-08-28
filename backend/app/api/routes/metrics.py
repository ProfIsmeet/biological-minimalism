"""`/metrics/*` — live and historical telemetry."""

from __future__ import annotations

from fastapi import APIRouter, Query

from app.core.config import settings
from app.engine.mock_data_engine import engine
from app.schemas.telemetry import LiveMetricsSnapshot

router = APIRouter()


@router.get("/live", response_model=LiveMetricsSnapshot, summary="Latest telemetry snapshot")
def get_live_metrics() -> LiveMetricsSnapshot:
    return engine.last_snapshot or engine.tick(settings.tick_interval_seconds)


@router.get("/history", response_model=list[LiveMetricsSnapshot], summary="Recent telemetry history for trend charts")
def get_metrics_history(
    limit: int = Query(100, ge=1, le=settings.rolling_history_length),
) -> list[LiveMetricsSnapshot]:
    return list(engine.history)[-limit:]
