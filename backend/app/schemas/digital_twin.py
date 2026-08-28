"""Digital Twin state schema — powers the Digital Twin page's day slider (Demo 3)."""

from __future__ import annotations

from pydantic import BaseModel, Field


class DigitalTwinSystemScore(BaseModel):
    """Adaptation score (0-100, 100 = fully adapted/stable) for one physiological system."""

    system: str
    baseline_score: float = Field(..., ge=0, le=100, description="Score on Day 1 (pre-adaptation)")
    current_score: float = Field(..., ge=0, le=100, description="Score at the requested mission day")
    delta: float = Field(..., description="current_score - baseline_score")


class DigitalTwinState(BaseModel):
    mission_day: float = Field(..., ge=0, le=30)
    milestone_label: str = Field(..., description="e.g. 'Day 1 — Acute Adaptation'")
    narrative: str = Field(..., description="Short natural-language summary of the twin's state at this day")
    systems: list[DigitalTwinSystemScore]
    overall_adaptation: float = Field(..., ge=0, le=100)
