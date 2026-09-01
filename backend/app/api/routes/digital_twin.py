"""`/digital-twin` — powers the Digital Twin page's mission-day slider (Demo 3)."""

from __future__ import annotations

from fastapi import APIRouter, Query

from app.api.routes._source_guard import require_synthetic_source
from app.engine.mock_data_engine import engine
from app.schemas.digital_twin import DigitalTwinState

router = APIRouter()


@router.get("/digital-twin", response_model=DigitalTwinState, summary="Digital Twin adaptation state at a given mission day")
def get_digital_twin(day: float = Query(1.0, ge=0, le=30, description="Mission day to inspect (0-30)")) -> DigitalTwinState:
    require_synthetic_source("Digital Twin")
    return engine.get_digital_twin_state(day)
