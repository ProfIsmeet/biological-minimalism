"""`/simulation/*` — the control surface for Demo 1 (sensor failure) and
Demo 2 (mission mode / Solar Storm). Kept on REST rather than the
WebSocket so each control action is a single, idempotent, curl-testable
request; the effect is observed on the next `/ws/live-feed` frame."""

from __future__ import annotations

from fastapi import APIRouter

from app.engine.mock_data_engine import engine
from app.schemas.simulation import SetFailureRequest, SetModeRequest, SimulationStateResponse

router = APIRouter()


def _state() -> SimulationStateResponse:
    return SimulationStateResponse(
        mission_mode=engine.mission_mode,
        sensor_status={sensor.value: status for sensor, status in engine.sensor_status.items()},
    )


@router.get("/state", response_model=SimulationStateResponse, summary="Current mission mode and sensor status")
def get_simulation_state() -> SimulationStateResponse:
    return _state()


@router.post("/mode", response_model=SimulationStateResponse, summary="Set the mission mode (Demo 2 — Solar Storm Mode)")
def set_mission_mode(request: SetModeRequest) -> SimulationStateResponse:
    engine.set_mode(request.mode)
    return _state()


@router.post("/failure", response_model=SimulationStateResponse, summary="Set a sensor's status (Demo 1 — Sensor Failure Simulation)")
def set_sensor_failure(request: SetFailureRequest) -> SimulationStateResponse:
    engine.set_sensor_status(request.sensor, request.status)
    return _state()
