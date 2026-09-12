"""Typed contract for the Day-11 engineering-readiness summary (Part-3 integration).

Read-only projection of the frozen Part-2 engineering artifacts. It deliberately
carries system-level UNKNOWN/NOT_READY states as explicit strings so the frontend
never renders a fabricated zero for an unquantified quantity.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict

from app.schemas.research import ResearchAvailability


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ReadinessLevel(StrEnum):
    AVAILABLE = "AVAILABLE"
    PARTIAL = "PARTIAL"
    NOT_READY = "NOT_READY"
    MISSING = "MISSING"


class QuantityStatus(StrEnum):
    """Availability of a single quantitative engineering value (audit H4/§9).
    A quantity that is absent or non-numeric in the frozen artifact is UNKNOWN
    with value=None — it is NEVER silently coerced to 0."""

    AVAILABLE = "AVAILABLE"
    NOT_READY = "NOT_READY"
    UNKNOWN = "UNKNOWN"


class Quantity(StrictModel):
    """A typed quantitative value with explicit availability. `value` is null
    unless `status == AVAILABLE`; the frontend renders `display` and styles by
    `status`, so an unquantified quantity can never be shown as a fabricated 0."""

    value: float | None
    unit: str
    status: QuantityStatus
    display: str
    reason_if_unavailable: str | None = None
    provenance: str | None = None


class EngineeringPanelRow(StrictModel):
    """One dimension of the engineering readiness panel."""

    dimension: str
    value_display: str
    status: ReadinessLevel
    note: str


class RawDataRate(StrictModel):
    value: Quantity  # partial raw lower bound in bps, or UNKNOWN (no 48068 fallback)
    status: str  # e.g. "PARTIAL_LOWER_BOUND" or "UNKNOWN"
    radio_data_rate_status: str  # e.g. "NOT_READY"
    note: str


class EngineeringCandidate(StrictModel):
    candidate: str
    label: str
    scientific_target: str
    scientific_direction: str  # human phrase (modest positive / aggregate negative / positive-with-control)
    gate_status: str  # CONDITIONAL_FOR_TARGET / DEPRIORITIZE_FOR_TARGET
    incremental_body_region: str  # display string ("0", "1", "0 or 1")
    incremental_module: str  # display string ("0", "1", "OPEN")
    incremental_sensing_contacts: Quantity  # count, or UNKNOWN if absent (never 0-by-default)
    reference_component_power_display: str  # "~0.018 mW (band 0.018–0.378)" or "Not ready"
    reference_component_power_status: ReadinessLevel
    raw_data_rate_increment: Quantity  # bps, or UNKNOWN if absent (never 0-by-default)
    mass_tier: str
    bom_readiness: str
    engineering_summary: str
    caveat: str


class EngineeringReadiness(StrictModel):
    artifact_id: str
    part: str
    source_head_commit: str
    statement: str

    system_average_power_status: str  # SYSTEM_AVERAGE_POWER_NOT_READY
    system_mass_status: str  # SYSTEM_MASS_NOT_READY
    bom_status: str  # PARTIAL
    formal_pareto_status: str  # FORMAL_PARETO_NOT_READY
    final_architecture_status: str  # UNRESOLVED

    raw_data_rate: RawDataRate
    panel: list[EngineeringPanelRow]
    candidates: list[EngineeringCandidate]
    boundaries: list[str]
    source_artifacts: list[str]


class EngineeringReadinessEnvelope(StrictModel):
    availability: ResearchAvailability
    readiness: EngineeringReadiness | None = None
    error: str | None = None
