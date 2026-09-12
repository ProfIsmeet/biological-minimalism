"""Display schemas for the Stage-4 Final Architecture Closure sprint's own
Integration-Owner-authored artifacts (Gate E coordinator decisions, formal
Pareto analysis, final wearable architecture). Same convention as
`app.schemas.stage4_architecture_decision`: typed on key status/verdict
fields (so contract tests can assert on them), `dict[str, Any]`/`list[Any]`
for the narrative/heterogeneous sub-structures that vary in shape per item.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from app.schemas.research import ResearchAvailability


class Stage4GateECoordinatorDecision(BaseModel):
    item: str
    decision: str
    architecture_disposition: str
    claim_limitations: str
    what_could_trigger_revision: str | None = None
    revision_trigger: dict[str, Any]
    decided_by: str
    near_zero_result_note: str | None = None
    condition_ds2: str | None = None
    condition_ds3: str | None = None


class Stage4GateECoordinatorDecisions(BaseModel):
    artifact_id: str
    schema_version: str
    sprint: str
    generated_role: str
    purpose: str
    gate_reference: str
    source_artifacts: list[str]
    decisions: list[Stage4GateECoordinatorDecision]
    no_option_selected: bool
    gate_e_pending_science_sensitivity: str
    pending_science_still_pending: str


class Stage4GateECoordinatorDecisionsEnvelope(BaseModel):
    availability: ResearchAvailability
    decisions: Stage4GateECoordinatorDecisions | None = None
    error: str | None = None


class Stage4FormalParetoAnalysis(BaseModel):
    artifact_id: str
    schema_version: str
    sprint: str
    generated_role: str
    purpose: str
    methodology: dict[str, Any]
    pairwise_dominance_analysis: list[dict[str, Any]]
    pareto_relevant_set: list[str]
    potentially_dominated_set: list[str]
    no_unique_pareto_winner: bool
    no_unique_pareto_winner_reason: str
    coordinator_selected_architecture: str
    coordinator_selection_rationale: str
    coordinator_selection_is_not_mathematical_dominance: str
    final_architecture_status: str
    formal_pareto_status: str


class Stage4FormalParetoAnalysisEnvelope(BaseModel):
    availability: ResearchAvailability
    analysis: Stage4FormalParetoAnalysis | None = None
    error: str | None = None


class FinalWearableArchitecture(BaseModel):
    artifact_id: str
    schema_version: str
    sprint: str
    generated_role: str
    purpose: str
    selected_class: str
    selected_modalities: list[str]
    selected_body_regions: list[str]
    module_topology: dict[str, Any]
    contact_model: dict[str, Any]
    burden_ranges: dict[str, Any]
    science_rationale: dict[str, Any]
    exclusion_rationale: dict[str, Any]
    gate_d_status: dict[str, Any]
    gate_e_decisions: dict[str, Any]
    revision_triggers: list[dict[str, Any]]
    provenance: dict[str, Any]
    coordinator_decision_status: dict[str, Any]
    final_architecture_status: str
    formal_pareto_status: str


class FinalWearableArchitectureEnvelope(BaseModel):
    availability: ResearchAvailability
    architecture: FinalWearableArchitecture | None = None
    error: str | None = None


class Stage4FinalClosureManifest(BaseModel):
    artifact_id: str
    schema_version: str
    sprint: str
    generated_role: str
    purpose: str
    authoritative_artifacts: list[dict[str, Any]]
    final_architecture: str
    formal_pareto_status: str
    acceptance_gates: list[dict[str, Any]]
    pending_science: dict[str, Any]
    coordinator_decisions: dict[str, Any]
    repository_sha_after_closure: str
    accepted_stage3_sha: str
    status: str


class Stage4FinalClosureManifestEnvelope(BaseModel):
    availability: ResearchAvailability
    manifest: Stage4FinalClosureManifest | None = None
    error: str | None = None
