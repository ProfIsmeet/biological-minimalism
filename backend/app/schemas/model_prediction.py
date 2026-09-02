"""Scientifically explicit schemas for model-derived predictions."""

from __future__ import annotations

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.fault_injection import ReplayFaultState


class EvidenceLevel(StrEnum):
    AI_ESTIMATED = "AI_ESTIMATED"


class ModelInferenceStatus(StrEnum):
    WARMING_UP = "warming_up"
    AVAILABLE = "available"
    INPUT_UNAVAILABLE = "input_unavailable"
    MODEL_UNAVAILABLE = "model_unavailable"
    ERROR = "error"


class HeartRateInferenceState(BaseModel):
    status: ModelInferenceStatus
    message: str
    required_window_seconds: Literal[8.0] = 8.0
    required_channels: tuple[Literal["wrist_bvp"], Literal["wrist_acc"]] = (
        "wrist_bvp",
        "wrist_acc",
    )


class HeartRateModelProvenance(BaseModel):
    dataset_name: Literal["PPG-DaLiA"] = "PPG-DaLiA"
    subject_id: str
    window_index: int = Field(..., ge=0)
    window_start_seconds: float = Field(..., ge=0)
    window_duration_seconds: float = Field(..., gt=0)
    input_channels: tuple[Literal["wrist_bvp"], Literal["wrist_acc"]] = (
        "wrist_bvp",
        "wrist_acc",
    )
    model_id: str
    checkpoint_path: str
    checkpoint_sha256: str
    fault_injection: ReplayFaultState | None = None


class HeartRateModelPrediction(BaseModel):
    prediction_type: Literal["heart_rate"] = "heart_rate"
    value: float
    unit: Literal["bpm"] = "bpm"
    normalized_model_output: float
    evidence_level: EvidenceLevel = EvidenceLevel.AI_ESTIMATED
    uncertainty: None = None
    provenance: HeartRateModelProvenance
