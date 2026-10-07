"""Architecture-only Digital Twin reference schema.

The application has no trained, personalized, or validated longitudinal Digital
Twin.  This contract intentionally carries no physiological score, percentage,
or inferred adaptation state.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class DigitalTwinState(BaseModel):
    mission_day: float = Field(..., ge=0, le=30)
    milestone_label: str = Field(..., description="Conceptual architecture-review marker")
    narrative: str = Field(..., description="Architecture-only scope statement; never a physiological result")
    scientific_status: Literal["ARCHITECTURE_ONLY_UNTRAINED_UNVALIDATED"] = (
        "ARCHITECTURE_ONLY_UNTRAINED_UNVALIDATED"
    )
