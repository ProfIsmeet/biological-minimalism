"""`/sensor-health` — current status of each of the four sensors."""

from __future__ import annotations

from fastapi import APIRouter

from app.engine.mock_data_engine import engine
from app.schemas.telemetry import SensorHealthSnapshot, SensorReading

router = APIRouter()


@router.get("/sensor-health", response_model=SensorHealthSnapshot, summary="Per-sensor status and signal quality")
def get_sensor_health() -> SensorHealthSnapshot:
    quality = engine.signal_quality()
    return SensorHealthSnapshot(
        sensors=[
            SensorReading(sensor=sensor, status=status, signal_quality=quality[sensor.value])
            for sensor, status in engine.sensor_status.items()
        ]
    )
