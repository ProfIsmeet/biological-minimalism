"""Scientifically explicit schemas for model-derived predictions."""

from __future__ import annotations

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field


class EvidenceLevel(StrEnum):
    AI_ESTIMATED = "AI_ESTIMATED"


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


class HeartRateModelPrediction(BaseModel):
    prediction_type: Literal["heart_rate"] = "heart_rate"
    value: float
    unit: Literal["bpm"] = "bpm"
    normalized_model_output: float
    evidence_level: EvidenceLevel = EvidenceLevel.AI_ESTIMATED
    uncertainty: None = None
    provenance: HeartRateModelProvenance
