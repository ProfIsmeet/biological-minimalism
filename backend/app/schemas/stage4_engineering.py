"""Typed contract for the Stage 4 engineering-readiness summary.

Read-only projection of results/stage4_engineering_readiness.json (see
scripts/build_stage4_engineering_readiness.py). Follows the exact
Quantity/StrictModel idiom already established in
app.schemas.engineering_readiness: an unquantified value is UNKNOWN with
value=None, never a fabricated 0. This module additionally carries an
`evidence_class` on every quantity so a consumer can distinguish a frozen
Day-11 datasheet value from a new Stage-4 engineering assumption — the two
must never be visually or semantically merged.
"""

from __future__ import annotations

from enum import StrEnum

from app.schemas.engineering_readiness import Quantity, QuantityStatus, ReadinessLevel, StrictModel
from app.schemas.research import ResearchAvailability

__all__ = [
    "EvidenceClass",
    "EvidenceQuantity",
    "Stage4DutyScheduleEntry",
    "Stage4SystemPower",
    "Stage4SystemDataRate",
    "Stage4SystemMass",
    "Stage4BomAdvancement",
    "Stage4EngineeringReadiness",
    "Stage4EngineeringReadinessEnvelope",
]


class EvidenceClass(StrEnum):
    """How a value is known. Distinct from `QuantityStatus` (whether it is
    known at all): this says HOW confidently it is known when it is."""

    DATASHEET_DIRECT = "DATASHEET_DIRECT"
    DATASHEET_CALCULATED = "DATASHEET_CALCULATED"
    ENGINEERING_ASSUMPTION = "ENGINEERING_ASSUMPTION"
    ENGINEERING_ALLOWANCE_MECHANICAL_ESTIMATE = "ENGINEERING_ALLOWANCE_MECHANICAL_ESTIMATE"
    ASSUMED_USE_SCHEDULE = "ASSUMED_USE_SCHEDULE"


class EvidenceQuantity(Quantity):
    """`Quantity` plus the evidence-class tag. A field with
    `evidence_class in {ENGINEERING_ASSUMPTION, ENGINEERING_ALLOWANCE_MECHANICAL_ESTIMATE,
    ASSUMED_USE_SCHEDULE}` must never be displayed as if it were
    DATASHEET_DIRECT/DATASHEET_CALCULATED (governing prompt §34/§35)."""

    evidence_class: EvidenceClass


class Stage4DutyScheduleEntry(StrictModel):
    module: str
    state: str
    duty_fraction: float
    note: str


class Stage4SystemPower(StrictModel):
    status: str  # "PARTIAL_READY" (never "READY" while every contributor is an assumption)
    reason: str
    base_topology_load_side_mw: EvidenceQuantity
    base_topology_battery_side_mw: EvidenceQuantity
    contributors_mw: dict[str, float]
    excluded_from_base_total_mw: dict[str, float]
    duty_schedule: list[Stage4DutyScheduleEntry]


class Stage4SystemDataRate(StrictModel):
    system_raw_total_bps: EvidenceQuantity
    system_transmitted_bps: EvidenceQuantity
    processed_data_rate_status: str  # "NOT_READY"
    excluded_from_base_total_bps: dict[str, float]


class Stage4SystemMass(StrictModel):
    status: str  # "PARTIAL"
    tier_achieved: str  # "Tier2"
    system_mass_base_topology_excl_leg_g: EvidenceQuantity
    eog_incremental_mass_g: EvidenceQuantity


class Stage4BomAdvancement(StrictModel):
    not_a_final_bom: bool
    final: bool
    items_advanced: list[dict[str, str]]
    still_missing: list[str]


class Stage4EngineeringReadiness(StrictModel):
    artifact_id: str
    sprint: str
    statement: str
    prohibited: list[str]

    system_average_power: Stage4SystemPower
    system_data_rate: Stage4SystemDataRate
    system_mass: Stage4SystemMass
    bom: Stage4BomAdvancement

    final_architecture_status: str  # "UNRESOLVED"
    formal_pareto_status: str  # "FORMAL_PARETO_NOT_READY"
    source_artifacts: list[str]


class Stage4EngineeringReadinessEnvelope(StrictModel):
    availability: ResearchAvailability
    readiness: Stage4EngineeringReadiness | None = None
    error: str | None = None
