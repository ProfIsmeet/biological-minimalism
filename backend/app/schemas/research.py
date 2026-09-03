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
    ROBUSTNESS_CHARACTERIZATION = "robustness_characterization"


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


class ResearchProjectSummary(BaseModel):
    experiment_count: int = Field(..., ge=0)
    available_count: int = Field(..., ge=0)
    unavailable_count: int = Field(..., ge=0)
    experiments: list[ResearchExperimentSummaryEnvelope]
    statement: str
