"""Display schemas for this closure-prep sprint's own Integration-Owner-
authored artifacts (Gate D assessment, candidate burden comparison,
architecture decision projection, Gate E options, final decision packet).

Unlike `app.schemas.stage4_science_manifest` / `stage4_architecture_framework`
(which project third-party Science Owner content that must never be
reinterpreted), these schemas project Integration Owner's OWN generated
artifacts - still typed on their key status/verdict fields (so contract
tests can assert on them), with `dict[str, Any]`/`list[Any]` for the
narrative/heterogeneous sub-structures that vary in shape per item.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from app.schemas.research import ResearchAvailability


class Stage4GateDDimension(BaseModel):
    dimension: str
    status: str
    evidence: str
    gap: str | None = None


class Stage4GateDKnownUnknown(BaseModel):
    item: str
    why_it_matters: str
    bounded: bool
    could_be_decision_changing: bool


class Stage4GateDBurdenCompleteness(BaseModel):
    artifact_id: str
    schema_version: str
    sprint: str
    generated_role: str
    gate_reference: str
    primary_question: str
    source_artifacts: list[str]
    dimensions_audited: list[Stage4GateDDimension]
    shared_resource_accounting: dict[str, Any]
    known_unknowns: list[Stage4GateDKnownUnknown]
    bom_final: bool
    bom_still_missing: list[str]
    gate_d_burden_completeness: str
    rationale: str
    what_would_close_it: list[str]
    final_architecture_status: str
    formal_pareto_status: str


class Stage4GateDBurdenCompletenessEnvelope(BaseModel):
    availability: ResearchAvailability
    assessment: Stage4GateDBurdenCompleteness | None = None
    error: str | None = None


class Stage4CandidateClassBurden(BaseModel):
    class_id: str
    description: str
    sensors: list[str]
    evidence_confidence: str
    pending_science_exposure: str
    power: dict[str, Any]
    data_rate_raw_bps: dict[str, Any]
    mass: dict[str, Any]
    dominance_flag: str
    dominance_reason: str


class Stage4CandidateClassBurdenComparison(BaseModel):
    artifact_id: str
    schema_version: str
    sprint: str
    generated_role: str
    purpose: str
    explicit_non_goal: str
    derivation_note: str
    source_artifacts: list[str]
    classes: list[Stage4CandidateClassBurden]
    allowed_dominance_flags: list[str]
    note_on_dominance: str
    final_architecture_status: str
    formal_pareto_status: str


class Stage4CandidateClassBurdenComparisonEnvelope(BaseModel):
    availability: ResearchAvailability
    comparison: Stage4CandidateClassBurdenComparison | None = None
    error: str | None = None


class Stage4ArchitectureDecisionUnit(BaseModel):
    decision_unit: str
    related_sensor_value_matrix_modalities: list[dict[str, Any]]
    confidence_tier_decision_framework: str
    decision_sensitivity: str
    pending_evidence: str | None = None
    decision_flip_condition: Any = None
    burden_state: dict[str, Any] | None = None
    unresolved_science: str | None = None
    unresolved_engineering: str | None = None
    coordinator_decision_requirement: str


class Stage4ArchitectureDecisionProjection(BaseModel):
    artifact_id: str
    schema_version: str
    sprint: str
    generated_role: str
    purpose: str
    join_note: str
    source_artifacts: list[str]
    units: list[Stage4ArchitectureDecisionUnit]
    final_architecture_status: str
    formal_pareto_status: str


class Stage4ArchitectureDecisionProjectionEnvelope(BaseModel):
    availability: ResearchAvailability
    projection: Stage4ArchitectureDecisionProjection | None = None
    error: str | None = None


class Stage4GateEHighSensitivityItem(BaseModel):
    item: str
    current_science_state: str
    current_confidence_tier: str
    pending_evidence: str | None = None
    decision_flip_scenarios: dict[str, Any]
    options: dict[str, Any]


class Stage4GateECoordinatorOptions(BaseModel):
    artifact_id: str
    schema_version: str
    sprint: str
    generated_role: str
    purpose: str
    gate_reference: str
    source_artifacts: list[str]
    high_sensitivity_items: list[Stage4GateEHighSensitivityItem]
    no_option_selected: bool
    coordinator_action_required: str
    final_architecture_status: str
    formal_pareto_status: str


class Stage4GateECoordinatorOptionsEnvelope(BaseModel):
    availability: ResearchAvailability
    options: Stage4GateECoordinatorOptions | None = None
    error: str | None = None


class Stage4FinalArchitectureDecisionPacket(BaseModel):
    artifact_id: str
    schema_version: str
    sprint: str
    generated_role: str
    purpose: str
    statement: str
    candidate_configurations: list[dict[str, Any]]
    scientific_evidence_summary: dict[str, Any]
    burden_evidence_summary: dict[str, Any]
    uncertainties: dict[str, Any]
    pending_science_sensitivity: list[dict[str, Any]]
    potential_dominance: list[dict[str, Any]]
    acceptance_gate_readiness: list[dict[str, Any]]
    decision_blockers: list[dict[str, Any]]
    coordinator_choices_required: list[str]
    final_architecture_status: str
    formal_pareto_status: str


class Stage4FinalArchitectureDecisionPacketEnvelope(BaseModel):
    availability: ResearchAvailability
    packet: Stage4FinalArchitectureDecisionPacket | None = None
    error: str | None = None
