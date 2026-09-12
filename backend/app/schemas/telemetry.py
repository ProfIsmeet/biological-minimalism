"""Live telemetry snapshot schemas.

`LiveMetricsSnapshot` is the payload broadcast over the `/ws/live-feed`
WebSocket and returned by `GET /metrics/live`.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.schemas.data_source import DataSourceType, RawChannelBatch, TelemetrySourceMetadata
from app.schemas.fault_injection import ReplayFaultState
from app.schemas.mission import MissionMode, SensorName, SensorStatus
from app.schemas.model_prediction import HeartRateInferenceState, HeartRateModelPrediction


class VitalsSnapshot(BaseModel):
    heart_rate_bpm: float | None = Field(default=None, description="Estimated heart rate, beats per minute")
    hrv_rmssd_ms: float | None = Field(default=None, description="Heart rate variability (RMSSD), milliseconds")
    respiration_rate_bpm: float | None = Field(default=None, description="Estimated respiration rate, breaths per minute")
    blood_pressure_systolic_mmhg: float | None = None
    blood_pressure_diastolic_mmhg: float | None = None
    ppg_waveform: list[float] = Field(default_factory=list, description="Recent PPG waveform samples for charting")
    ecg_like_waveform: list[float] = Field(default_factory=list, description="Derived ECG-like waveform samples for charting")
    ecg_waveform: list[float] = Field(default_factory=list, description="Recorded ECG samples when the source provides ECG")


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
    source: TelemetrySourceMetadata = Field(
        default_factory=lambda: TelemetrySourceMetadata(
            source_type=DataSourceType.SYNTHETIC,
            display_label="SYNTHETIC DEMO",
        )
    )
    channels: list[RawChannelBatch] = Field(default_factory=list)
    heart_rate_prediction: HeartRateModelPrediction | None = None
    heart_rate_inference: HeartRateInferenceState | None = None
    fault_injection: ReplayFaultState | None = None
    mission_mode: MissionMode | None = None
    mission_day: float | None = Field(default=None, ge=0, description="Simulated elapsed mission day, used by the Digital Twin")
    vitals: VitalsSnapshot | None = None
    cognitive: CognitiveSnapshot | None = None
    space_adaptation: SpaceAdaptationSnapshot | None = None
    sensor_health: SensorHealthSnapshot | None = None
    ai_confidence: AIConfidenceSnapshot | None = None
