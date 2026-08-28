"""Request/response schemas for the simulation control endpoints (Demos 1 & 2)."""

from __future__ import annotations

from pydantic import BaseModel

from app.schemas.mission import MissionMode, SensorName, SensorStatus


class SetModeRequest(BaseModel):
    mode: MissionMode


class SetFailureRequest(BaseModel):
    sensor: SensorName
    status: SensorStatus


class SimulationStateResponse(BaseModel):
    mission_mode: MissionMode
    sensor_status: dict[str, SensorStatus]
