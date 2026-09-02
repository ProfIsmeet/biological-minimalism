"""Typed configuration and provenance for replay-only signal corruption."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field, model_validator


class ReplayFaultType(StrEnum):
    MODALITY_DROPOUT = "modality_dropout"
    PACKET_LOSS = "packet_loss"
    FROZEN_SENSOR = "frozen_sensor"
    ADDITIVE_NOISE = "additive_noise"
    SATURATION = "saturation"


class ReplayFaultTarget(StrEnum):
    PPG = "ppg"
    IMU = "imu"
    BOTH = "both"


class ReplayFaultConfig(BaseModel):
    """One deterministic replay fault; faults are intentionally not composited.

    ``severity`` is a unit interval with type-specific semantics documented in
    ``docs/DATASET_REPLAY.md``. Dropout and frozen-sensor faults use the full
    corruption regardless of this value.
    """

    fault_type: ReplayFaultType
    target: ReplayFaultTarget
    severity: float = Field(default=1.0, ge=0.0, le=1.0)
    seed: int = Field(default=0, ge=0, le=2_147_483_647)

    @model_validator(mode="after")
    def force_full_severity_for_binary_faults(self) -> "ReplayFaultConfig":
        if self.fault_type in {
            ReplayFaultType.MODALITY_DROPOUT,
            ReplayFaultType.FROZEN_SENSOR,
        }:
            self.severity = 1.0
        return self


FaultParameter = float | int | str | list[float] | list[str]


class ReplayFaultState(BaseModel):
    """Configuration plus per-frame, auditable corruption details."""

    active: bool = False
    fault_type: ReplayFaultType | None = None
    target: ReplayFaultTarget | None = None
    target_channels: list[str] = Field(default_factory=list)
    affected_channels: list[str] = Field(default_factory=list)
    severity: float | None = Field(default=None, ge=0.0, le=1.0)
    seed: int | None = None
    dropped_samples: dict[str, int] = Field(default_factory=dict)
    parameters: dict[str, FaultParameter] = Field(default_factory=dict)
