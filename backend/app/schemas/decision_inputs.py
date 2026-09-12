"""Typed contract for the reviewed Day 5 scientific/operational join."""

from __future__ import annotations

from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict

from app.schemas.operational_cost import (
    CostEvidenceRecord,
    HardwareCharacterization,
    OperationalQuantity,
    SharedHardwareContext,
)
from app.schemas.research import ResearchAvailability


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ScientificDirection(StrEnum):
    POSITIVE = "POSITIVE"
    NEGATIVE = "NEGATIVE"


class ReadinessAvailability(StrEnum):
    AVAILABLE = "AVAILABLE"
    PARTIAL = "PARTIAL"
    MISSING = "MISSING"


class ParetoStatus(StrEnum):
    NOT_READY = "NOT_READY"


class SourceArtifactReference(StrictModel):
    path: str
    sha256: str
    role: str


class ComponentJoinMapping(StrictModel):
    component_id: str
    scientific_component_id: str
    scientific_experiment_id: str
    operational_experiment_id: str


class DecisionConfiguration(StrictModel):
    description: str
    channels: list[str]


class MetricEstimate(StrictModel):
    mean: float
    sd: float | None = None
    unit: str


class AccuracyMetrics(StrictModel):
    mae: MetricEstimate
    rmse: MetricEstimate
    n_windows: int | None = None


class ScientificProvenance(StrictModel):
    source_artifact: str
    source_reproducibility_artifact: str | None = None
    methodology_path: str
    contract_path: str


class ClaimBoundaries(StrictModel):
    supported: list[str]
    unsupported: list[str]
    limitations: list[str]


class ScientificMarginalValue(StrictModel):
    scientific_component_id: str
    target_id: str
    experiment_id: str
    dataset_id: str
    baseline_configuration: DecisionConfiguration
    candidate_configuration: DecisionConfiguration
    primary_metric: Literal["mae"]
    baseline_metrics: AccuracyMetrics
    candidate_metrics: AccuracyMetrics
    absolute_benefit: dict[str, float]
    relative_improvement: dict[str, float]
    direction: ScientificDirection
    variability: dict[str, Any]
    heterogeneity: dict[str, str]
    evidence_strength: str
    evidence_scope: dict[str, Any]
    # Audit H5/§12: when the raw absolute_benefit is capacity-confounded (e.g. PPG A->B),
    # carry the contract's capacity_confound_status so the UI never shows the raw MAE
    # benefit as the current pure marginal sensor value without the caveat.
    capacity_confound: dict[str, Any] | None = None
    provenance: ScientificProvenance
    claim_boundaries: ClaimBoundaries


class OperationalCostInput(StrictModel):
    source_component_id: str
    candidate_hardware_identity: str | None
    duty_cycle: OperationalQuantity
    dimensions: dict[str, OperationalQuantity]
    shared_hardware: SharedHardwareContext
    known_dimensions: list[str]
    unknown_dimensions: list[str]
    unknowns: list[str]
    evidence: list[CostEvidenceRecord]
    hardware_characterization: HardwareCharacterization | None = None


class RobustnessEvidence(StrictModel):
    status: Literal["RESOLVED_FROM_INTEGRATION_SOURCE"]
    experiment_id: str
    source_artifact: str
    audit_addendum: str
    subject_id: str
    scope: str
    condition_count: int
    eligible_windows_per_condition: int
    total_condition_windows: int
    clean_mae_bpm: float
    clean_rmse_bpm: float
    clean_prediction_availability: float
    imu_calibration_caveat: str
    packet_loss_interpretation: str
    supported_claim: str
    unsupported_claims: list[str]


class DecisionInputComponent(StrictModel):
    component_id: str
    label: str
    target: str
    experiment_id: str
    scientific_marginal_value: ScientificMarginalValue
    operational_cost: OperationalCostInput
    robustness_evidence: RobustnessEvidence | None = None


class ComponentReadiness(StrictModel):
    component_id: str
    scientific_benefit: ReadinessAvailability
    power: ReadinessAvailability
    mass: ReadinessAvailability
    contact_burden: ReadinessAvailability
    module_burden: ReadinessAvailability
    compute_data_burden: ReadinessAvailability
    robustness_evidence: ReadinessAvailability
    evidence_provenance: ReadinessAvailability


class ParetoReadiness(StrictModel):
    pareto_status: ParetoStatus
    formal_pareto_calculated: Literal[False]
    missing_requirements: list[str]
    cross_dataset_restriction: str
    limited_structural_observation: str
    component_matrix: list[ComponentReadiness]


class ParetoDecisionInputs(StrictModel):
    schema_version: str
    artifact_id: str
    source_artifacts: list[SourceArtifactReference]
    join_mappings: list[ComponentJoinMapping]
    components: list[DecisionInputComponent]
    readiness: ParetoReadiness


class ParetoDecisionInputsEnvelope(StrictModel):
    availability: ResearchAvailability
    decision_inputs: ParetoDecisionInputs | None = None
    error: str | None = None
