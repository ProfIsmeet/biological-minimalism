"""Display schemas for the second, parallel Science Owner Stage-4 package -
the architecture decision framework
(`docs/STAGE4_ARCHITECTURE_DECISION_FRAMEWORK_HANDOFF.md`,
`stage4-architecture-decision-framework @ fa71eec`).

Same discipline as `app.schemas.stage4_science_manifest`: every field is
read verbatim from the Science Owner's package. Integration Owner code must
never reinterpret a tier, sensitivity rating, gate severity, or candidate
class here. Free-form/heterogeneous narrative sub-structures (decision-flip
scenarios, confidence-dimension definitions) use `dict[str, Any]` rather
than forcing a rigid shape that could silently drop a field on the next
Science Owner revision.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class Stage4ConfidenceTier(BaseModel):
    mechanical_definition: str
    current_occupants: list[str]


class Stage4ArchitectureScienceDecisionFramework(BaseModel):
    purpose: str
    accepted_stage3_sha: str
    prior_stage4_package: dict[str, Any]
    confidence_dimensions: dict[str, Any]
    confidence_tiers: dict[str, Stage4ConfidenceTier]
    tier_assignment_rule: str
    pending_science_handling: dict[str, Any]
    final_architecture_status: str
    formal_pareto_status: str


class Stage4SensorDecisionSensitivityEntry(BaseModel):
    modality: str
    current_science_state: str
    current_confidence_tier: str
    pending_evidence: str | None = None
    decision_sensitivity: str
    decision_flip_condition: str | None = None
    decision_flip_scenarios: dict[str, Any] | None = None
    reason: str


class Stage4SensorDecisionSensitivity(BaseModel):
    purpose: str
    accepted_stage3_sha: str
    sensors: list[Stage4SensorDecisionSensitivityEntry]


class Stage4ParetoAxisModalityValues(BaseModel):
    modality: str
    incremental_value: str
    breadth: str
    evidence_maturity: str
    robustness: str
    uniqueness: str
    dependency: str
    decision_fragility: str
    mission_relevance: str


class Stage4ScientificParetoInputs(BaseModel):
    purpose: str
    accepted_stage3_sha: str
    explicit_non_goal: str
    scientific_pareto_axes: dict[str, Any]
    per_modality_axis_values: list[Stage4ParetoAxisModalityValues]
    shared_resource_analysis_reference: str
    final_architecture_status: str
    formal_pareto_status: str


class Stage4AcceptanceGate(BaseModel):
    gate_id: str
    requirement: str
    rationale: str
    severity: str
    evidence_needed: str
    owner: str
    current_readiness: str
    what_closes_it: str


class Stage4ArchitectureAcceptanceGates(BaseModel):
    purpose: str
    accepted_stage3_sha: str
    severity_enum: list[str]
    gates: list[Stage4AcceptanceGate]
    final_architecture_status: str
    formal_pareto_status: str


class Stage4ArchitectureCandidateClass(BaseModel):
    class_id: str
    description: str
    sensors: list[str]
    anatomical_regions: list[str]
    scientific_capabilities: list[str]
    evidence_confidence: str
    unresolved_dependencies: str
    pending_science_exposure: str


class Stage4ArchitectureCandidateClasses(BaseModel):
    purpose: str
    accepted_stage3_sha: str
    explicit_non_goal: str
    classes: list[Stage4ArchitectureCandidateClass]
    note_on_composability: str
    final_architecture_status: str
    formal_pareto_status: str
