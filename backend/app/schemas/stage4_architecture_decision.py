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
    note: str | None = None


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
    # v2.0.0 Gate-D Burden Closure fields (absent on a v1.0.0 record read
    # before this sprint - always optional so older history entries below
    # still validate as the same model).
    assessment_history: list[dict[str, Any]] = []
    chest_module_decomposition: dict[str, Any] | None = None
    eeg_eog_shared_afe_confirmation: dict[str, Any] | None = None
    new_artifacts_this_sprint: list[str] = []
    # v3.0.0 Stage-4 Final Architecture Closure field (absent on v1.0.0/v2.0.0
    # records preserved verbatim under assessment_history above).
    coordinator_acceptance: dict[str, Any] | None = None


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
    contact_electrode_burden: dict[str, Any] | None = None
    battery_topology_scenarios: dict[str, Any] | None = None
    candidate_burden_matrix: list[dict[str, Any]] = []
    robustness_analysis: dict[str, Any] | None = None
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


class Stage4ContactModality(BaseModel):
    modality: str
    anatomical_region: str
    module_id: str
    components: list[str]
    sensing_contacts: dict[str, Any]
    reference_electrodes: dict[str, Any]
    ground_bias_electrodes: dict[str, Any]
    shared_with: list[str]
    total_contacts: dict[str, Any]
    incremental_contacts_if_added: dict[str, Any]
    electrode_type: str
    disposable_or_reusable: str
    attachment_type: str
    external_cable_required: Any = None
    source: str
    confidence: str
    unresolved_topology_question: dict[str, Any] | None = None


class Stage4ContactElectrodeBurden(BaseModel):
    artifact_id: str
    schema_version: str
    sprint: str
    generated_role: str
    purpose: str
    method: str
    source_artifacts: list[str]
    modalities: list[Stage4ContactModality]
    new_findings_not_previously_disclosed: list[dict[str, Any]]
    final_architecture_status: str
    formal_pareto_status: str


class Stage4ContactElectrodeBurdenEnvelope(BaseModel):
    availability: ResearchAvailability
    burden: Stage4ContactElectrodeBurden | None = None
    error: str | None = None


class Stage4BatteryTopologyScenarios(BaseModel):
    artifact_id: str
    schema_version: str
    sprint: str
    generated_role: str
    purpose: str
    operating_duration_requirement_status: dict[str, Any]
    per_module_battery_reference: dict[str, Any]
    scenarios: dict[str, Any]
    candidate_class_comparison: list[dict[str, Any]]
    does_ranking_depend_on_topology: dict[str, Any]
    not_a_final_battery_selection: bool
    final_architecture_status: str
    formal_pareto_status: str


class Stage4BatteryTopologyScenariosEnvelope(BaseModel):
    availability: ResearchAvailability
    scenarios: Stage4BatteryTopologyScenarios | None = None
    error: str | None = None


class Stage4CandidateBurdenMatrix(BaseModel):
    artifact_id: str
    schema_version: str
    sprint: str
    generated_role: str
    purpose: str
    source_artifacts: list[str]
    classes: list[dict[str, Any]]
    robustness_analysis: dict[str, Any]
    final_architecture_status: str
    formal_pareto_status: str


class Stage4CandidateBurdenMatrixEnvelope(BaseModel):
    availability: ResearchAvailability
    matrix: Stage4CandidateBurdenMatrix | None = None
    error: str | None = None
