"""Canonical, read-only representation of completed research experiments."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field


class ResearchAvailability(StrEnum):
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"


class ResearchStatus(StrEnum):
    COMPLETE = "complete"


class ResearchEvidenceLevel(StrEnum):
    EXPERIMENTAL_EVALUATION = "experimental_evaluation"


class ResearchEnvironmentScope(StrEnum):
    TERRESTRIAL_FREE_LIVING = "terrestrial_free_living"
    TERRESTRIAL_CONTROLLED = "terrestrial_controlled"
    ANALOG = "analog"
    SIMULATION = "simulation"
    SPACEFLIGHT = "spaceflight"


class MarginalDirection(StrEnum):
    IMPROVED = "improved"
    WORSENED = "worsened"
    MIXED = "mixed"
    NOT_APPLICABLE = "not_applicable"


class ResearchResultClass(StrEnum):
    POSITIVE_MARGINAL_VALUE = "positive_marginal_value"
    NEGATIVE_MARGINAL_RESULT = "negative_marginal_result"
    NEUTRAL_MARGINAL_RESULT = "neutral_marginal_result"
    HETEROGENEOUS_MARGINAL_RESULT = "heterogeneous_marginal_result"
    ROBUSTNESS_CHARACTERIZATION = "robustness_characterization"


class MetricKind(StrEnum):
    """Whether a target's primary metric is a regression or classification metric.
    Enables representing non-HR targets (e.g. sleep-stage classification) without
    assuming a regression/HR-only structure."""

    REGRESSION = "regression"
    CLASSIFICATION = "classification"


class MetricDirectionality(StrEnum):
    LOWER_IS_BETTER = "lower_is_better"
    HIGHER_IS_BETTER = "higher_is_better"
    NOT_APPLICABLE = "not_applicable"


class CapacityMatchStatus(StrEnum):
    """Whether a baseline/candidate comparison is confounded by model capacity."""

    MATCHED = "matched"
    CONFOUNDED = "confounded"
    UNKNOWN = "unknown"
    NOT_APPLICABLE = "not_applicable"


class EvidenceStrength(StrEnum):
    STRONGLY_REPLICATED = "strongly_replicated"
    REPLICATED_BUT_VARIABLE = "replicated_but_variable"
    MIXED = "mixed"
    SINGLE_SEED = "single_seed"
    INSUFFICIENT = "insufficient"


class SensitivityStatus(StrEnum):
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    PENDING = "pending"


class ResearchMetricEstimate(BaseModel):
    """One experimental metric; ``mean=None`` preserves undefined values."""

    mean: float | None
    sd: float | None = Field(default=None, ge=0)
    n: int | None = Field(default=None, ge=0)
    unit: str


class ResearchConfiguration(BaseModel):
    configuration_id: str
    label: str
    description: str
    sensing: list[str]
    metrics: dict[str, ResearchMetricEstimate]


class ResearchScope(BaseModel):
    subjects: list[str]
    held_out_subjects: list[str]
    evaluation_windows: int = Field(..., ge=0)
    activities: list[str] = Field(default_factory=list)
    evidence_level: ResearchEvidenceLevel = ResearchEvidenceLevel.EXPERIMENTAL_EVALUATION
    environment_scope: ResearchEnvironmentScope
    cohort_note: str


class ResearchMarginalResult(BaseModel):
    baseline_configuration_id: str
    candidate_configuration_id: str
    added_sensing: str
    metric: str
    delta: ResearchMetricEstimate
    direction: MarginalDirection
    paired_replicates: int | None = Field(default=None, ge=0)
    candidate_improved_count: int | None = Field(default=None, ge=0)
    candidate_worsened_count: int | None = Field(default=None, ge=0)
    # Multi-target / capacity / heterogeneity extensions (optional, backward-compatible).
    # Populated only where current frozen evidence supports them.
    metric_kind: MetricKind | None = None
    metric_directionality: MetricDirectionality | None = None
    capacity_match_status: CapacityMatchStatus | None = None
    evidence_strength: EvidenceStrength | None = None
    subject_heterogeneity: str | None = None
    class_heterogeneity: str | None = None
    sensitivity_status: SensitivityStatus | None = None
    notes: list[str] = Field(default_factory=list)


class ResearchBreakdownEntry(BaseModel):
    entry_id: str
    label: str
    dimensions: dict[str, str | float | int | bool | None] = Field(default_factory=dict)
    configuration_metrics: dict[str, dict[str, ResearchMetricEstimate]]
    delta: ResearchMetricEstimate | None = None


class ResearchBreakdown(BaseModel):
    breakdown_id: str
    kind: str
    title: str
    entries: list[ResearchBreakdownEntry]


class ResearchCheckpointIdentity(BaseModel):
    run_id: str
    model_id: str
    sha256: str
    size_bytes: int = Field(..., ge=0)


class ResearchProvenance(BaseModel):
    source_artifact: str
    supporting_artifacts: list[str] = Field(default_factory=list)
    dataset_version: str | None = None
    split_identity: str | None = None
    model_identity: list[str] = Field(default_factory=list)
    checkpoints: list[ResearchCheckpointIdentity] = Field(default_factory=list)
    experiment_version: str | None = None


class ResearchClaimBoundaries(BaseModel):
    supported: list[str]
    unsupported: list[str]
    limitations: list[str]


class OperationalCostPlaceholder(BaseModel):
    """Unscored future fields; Day 4 intentionally supplies no cost values."""

    sensor_contact_regions: int | None = Field(default=None, ge=0)
    additional_module_count: int | None = Field(default=None, ge=0)
    power_estimate: float | None = Field(default=None, ge=0)
    mass_estimate: float | None = Field(default=None, ge=0)
    compute_estimate: float | None = Field(default=None, ge=0)
    comfort_burden: float | None = Field(default=None, ge=0)


class ResearchExperiment(BaseModel):
    experiment_id: str
    title: str
    research_question: str
    dataset: str
    target: str
    status: ResearchStatus
    result_class: ResearchResultClass
    outcome_summary: str
    scope: ResearchScope
    configurations: list[ResearchConfiguration]
    marginal_result: ResearchMarginalResult | None = None
    breakdowns: list[ResearchBreakdown] = Field(default_factory=list)
    provenance: ResearchProvenance
    claim_boundaries: ResearchClaimBoundaries
    operational_costs: OperationalCostPlaceholder = Field(default_factory=OperationalCostPlaceholder)


class ResearchExperimentSummary(BaseModel):
    experiment_id: str
    title: str
    research_question: str
    dataset: str
    target: str
    status: ResearchStatus
    result_class: ResearchResultClass
    outcome_summary: str
    held_out_subject_count: int = Field(..., ge=0)
    source_artifact: str


class ResearchExperimentEnvelope(BaseModel):
    experiment_id: str
    availability: ResearchAvailability
    experiment: ResearchExperiment | None = None
    error: str | None = None


class ResearchExperimentSummaryEnvelope(BaseModel):
    experiment_id: str
    availability: ResearchAvailability
    summary: ResearchExperimentSummary | None = None
    error: str | None = None


class ReproducibilityInteraction(BaseModel):
    """Day-10 EEG x EOG x Resp interaction summary (conservative, bounded)."""

    tested: bool
    configs: str
    interaction_estimate: str
    uncertainty: str
    interpretation: str
    plain_language: str
    boundary: str


class ReproducibilitySummary(BaseModel):
    """Concise Day-10 reproducibility panel (§11). All fields are honest status
    strings; nothing here upgrades a scientific claim."""

    frozen_environment: str
    checkpoints: str
    datasets: str
    canonical_results: str
    robustness: str
    raw_data_committed: str
    n3_diagnostic: str
    independence_caveat: str
    overall_status: str
    interaction: ReproducibilityInteraction | None = None


class ResearchProjectSummary(BaseModel):
    experiment_count: int = Field(..., ge=0)
    available_count: int = Field(..., ge=0)
    unavailable_count: int = Field(..., ge=0)
    experiments: list[ResearchExperimentSummaryEnvelope]
    statement: str
    reproducibility: ReproducibilitySummary | None = None


class TargetEvidenceMatrixEntry(BaseModel):
    """One (target, dataset, candidate) evidence cell. Raw metric magnitudes across
    different targets/datasets are NOT comparable and must never be ranked against
    each other."""

    experiment_id: str
    target: str
    dataset: str
    candidate: str
    metric: str
    metric_kind: MetricKind
    metric_directionality: MetricDirectionality
    baseline_configuration_id: str
    candidate_configuration_id: str
    direction: MarginalDirection
    result_class: ResearchResultClass
    evidence_strength: EvidenceStrength
    capacity_match_status: CapacityMatchStatus
    subject_heterogeneity: str | None = None
    class_heterogeneity: str | None = None
    sensitivity_status: SensitivityStatus
    operational_cost_linkage_status: str
    supported_claim: str
    prohibited_claims: list[str] = Field(default_factory=list)


class TargetEvidenceMatrix(BaseModel):
    matrix_id: str
    statement: str
    cross_target_comparability: str
    entries: list[TargetEvidenceMatrixEntry]
    awaiting: list[str] = Field(default_factory=list)


class TargetEvidenceMatrixEnvelope(BaseModel):
    availability: ResearchAvailability
    matrix: TargetEvidenceMatrix | None = None
    error: str | None = None
