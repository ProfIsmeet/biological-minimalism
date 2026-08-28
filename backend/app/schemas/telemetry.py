"""Live telemetry snapshot schemas.

`LiveMetricsSnapshot` is the payload broadcast over the `/ws/live-feed`
WebSocket and returned by `GET /metrics/live`.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.schemas.mission import MissionMode, SensorName, SensorStatus


class VitalsSnapshot(BaseModel):
    heart_rate_bpm: float = Field(..., description="Estimated heart rate, beats per minute")
    hrv_rmssd_ms: float = Field(..., description="Heart rate variability (RMSSD), milliseconds")
    respiration_rate_bpm: float = Field(..., description="Estimated respiration rate, breaths per minute")
    blood_pressure_systolic_mmhg: float
    blood_pressure_diastolic_mmhg: float
    ppg_waveform: list[float] = Field(default_factory=list, description="Recent PPG waveform samples for charting")
    ecg_like_waveform: list[float] = Field(default_factory=list, description="Derived ECG-like waveform samples for charting")


class CognitiveSnapshot(BaseModel):
    cognitive_load: float = Field(..., ge=0, le=100)
    fatigue: float = Field(..., ge=0, le=100)
    circadian_stability: float = Field(..., ge=0, le=100)
    eeg_attention: float = Field(..., ge=0, le=100)
    eeg_band_powers: dict[str, float] = Field(default_factory=dict, description="alpha/beta/theta/delta relative power")


class SpaceAdaptationSnapshot(BaseModel):
    fluid_shift_risk: float = Field(..., ge=0, le=100)
    autonomic_balance: float = Field(..., ge=0, le=100)
    thermal_stability: float = Field(..., ge=0, le=100)


class SensorReading(BaseModel):
    sensor: SensorName
    status: SensorStatus
    signal_quality: float = Field(..., ge=0, le=1)


class SensorHealthSnapshot(BaseModel):
    sensors: list[SensorReading]


class AIConfidenceSnapshot(BaseModel):
    overall_confidence: float = Field(..., ge=0, le=100)
    sensor_contribution: dict[str, float] = Field(
        default_factory=dict, description="Relative contribution of each active sensor to the fused estimate (%)"
    )


class LiveMetricsSnapshot(BaseModel):
    timestamp: float = Field(..., description="Unix epoch seconds")
    mission_mode: MissionMode
    mission_day: float = Field(..., ge=0, description="Simulated elapsed mission day, used by the Digital Twin")
    vitals: VitalsSnapshot
    cognitive: CognitiveSnapshot
    space_adaptation: SpaceAdaptationSnapshot
    sensor_health: SensorHealthSnapshot
    ai_confidence: AIConfidenceSnapshot
