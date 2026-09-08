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


class ComparisonRole(StrEnum):
    """Role of a controlled comparison in the PPG headline (audit H5 §12-15)."""

    PRIMARY_CONTROLLED = "PRIMARY_CONTROLLED"
    MATCHED_SHUFFLED_CONTROL = "MATCHED_SHUFFLED_CONTROL"
    HISTORICAL_CAPACITY_CONFOUNDED_RESULT = "HISTORICAL_CAPACITY_CONFOUNDED_RESULT"


class ControlledComparison(BaseModel):
    """One self-contained comparison. Each carries its OWN operands and its OWN
    replication statistics (audit M15 §15): no blending of a single-run magnitude
    with a different comparison's five-seed consistency."""

    comparison_id: str
    label: str  # semantic label, e.g. "capacity-controlled IMU-information benefit (A_cap -> B)"
    role: ComparisonRole
    baseline_id: str
    candidate_id: str
    delta_definition: str  # e.g. "baseline_MAE - candidate_MAE (positive = candidate better)"
    delta: ResearchMetricEstimate  # mean + SD + n for THIS comparison
    n_seeds: int | None = Field(default=None, ge=0)
    n_seeds_favor_candidate: int | None = Field(default=None, ge=0)
    interpretation: str


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
    # Structured controlled comparisons (audit H5/M15). When populated, the
    # `delta` above is the capacity-controlled headline, and `headline_comparison_id`
    # names which entry it corresponds to. The historical capacity-confounded
    # A->B is present here only as HISTORICAL_CAPACITY_CONFOUNDED_RESULT.
    controlled_comparisons: list[ControlledComparison] = Field(default_factory=list)
    headline_comparison_id: str | None = None
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
    """Day-10 EEG x EOG x Resp interaction summary (conservative, bounded).

    Every numeric field is DERIVED from the reproduction artifact, never
    hardcoded (audit H3 / §6)."""

    tested: bool
    configs: str
    interaction_estimate: str
    uncertainty: str
    interpretation: str
    plain_language: str
    boundary: str


class ReproComponentStatus(StrEnum):
    """Per-subcomponent reproduction status (audit H3 §4). There is NO implicit
    success: a missing/empty/failed/malformed artifact can never yield PASS."""

    PASS = "PASS"
    PARTIAL = "PARTIAL"
    FAIL = "FAIL"
    UNAVAILABLE = "UNAVAILABLE"
    MALFORMED = "MALFORMED"


class ReproComponent(BaseModel):
    """One validated reproduction subcomponent. `status` drives UI styling
    (§7); `value_display` carries only artifact-derived numbers (§6)."""

    key: str
    label: str
    status: ReproComponentStatus
    detail: str
    value_display: str | None = None
    provenance: str | None = None
    reason_if_unavailable: str | None = None


class ReproducibilitySummary(BaseModel):
    """Concise reproducibility panel (§4-§7). Every visible field derives from
    validated artifact data; `overall_status` is COMPUTED from the component
    statuses (worst-of), never defaulted to PASS. `overall_declared` echoes the
    artifact's own self-declared verdict for cross-check, and
    `overall_matches_declared` flags any divergence."""

    overall_status: str
    overall_declared: str | None
    overall_matches_declared: bool
    environment_scope: str
    independence_caveat: str
    components: list[ReproComponent]
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
