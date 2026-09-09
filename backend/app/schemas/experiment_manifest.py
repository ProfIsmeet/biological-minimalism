"""Generic future-science ingestion contract (Phase 2, Stage 2-4 integration prep).

This schema describes the shape a future Ismet science-completion manifest
must have to be ingested safely. It does NOT contain any real experiment
results — no manifest satisfying this schema exists in `results/` yet. See
`app.research.future_science_ingestion` for the fail-closed validator and
`docs/CLAUDE_TO_ISMET_STAGE2_4_SCIENCE_TRANSFER_HANDOFF.md` / governing
prompt §23-34 for the design rationale.

Reuses existing project enums (`MetricKind`, `MetricDirectionality`,
`SensitivityStatus`) rather than inventing a parallel vocabulary.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.research import MetricDirectionality, MetricKind, ResearchAvailability, SensitivityStatus


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ExperimentCompletionState(StrEnum):
    """How much of a declared experiment actually exists as frozen evidence.
    Deliberately NOT a boolean complete/not-complete (governing prompt §25)."""

    COMPLETE = "COMPLETE"
    BOUNDED_DIAGNOSTIC = "BOUNDED_DIAGNOSTIC"
    BLOCKED_BY_DATA_ACCESS = "BLOCKED_BY_DATA_ACCESS"
    PENDING = "PENDING"
    HISTORICAL = "HISTORICAL"
    SUPERSEDED = "SUPERSEDED"


class ReplicationClass(StrEnum):
    """What kind of replication (if any) a result represents. A result must
    never be auto-labeled EXTERNAL_REPLICATION merely for being a second run;
    the manifest must say so explicitly (governing prompt §38)."""

    EXTERNAL_REPLICATION = "EXTERNAL_REPLICATION"
    SAME_DATASET_HOLDOUT = "SAME_DATASET_HOLDOUT"
    SINGLE_RUN = "SINGLE_RUN"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class ManifestMetric(StrictModel):
    name: str
    kind: MetricKind
    directionality: MetricDirectionality
    unit: str


class ManifestResultValue(StrictModel):
    mean: float
    sd: float | None = None
    n: int | None = None
    display: str


class SensitivityEntry(StrictModel):
    key: str
    value: float | None
    note: str | None = None


class SensitivityBlock(StrictModel):
    status: SensitivityStatus
    entries: list[SensitivityEntry] = Field(default_factory=list)
    dominant_key: str | None = None
    note: str | None = None


class ProvenanceRecord(StrictModel):
    """No result becomes canonical without this (governing prompt §30)."""

    source_artifact_path: str
    source_sha256: str | None = None
    experiment_commit: str | None = None
    dataset_version: str
    protocol_version: str
    checkpoint_manifest_path: str | None = None
    subject_split_manifest_path: str | None = None


class CheckpointManifestRef(StrictModel):
    path: str
    checkpoint_count: int | None = None
    note: str | None = None


class ExperimentManifestEntry(StrictModel):
    experiment_id: str
    experiment_version: str
    dataset: str
    dataset_version: str
    target: str
    baseline_config: str
    candidate_config: str
    control_config: str | None = None
    metric: ManifestMetric

    # Biological subjects and optimization seeds are always independently
    # required and never conflated (governing prompt §26/§33).
    biological_subject_n: int = Field(ge=1)
    optimization_seed_n: int = Field(ge=1)

    primary_result: ManifestResultValue
    control_result: ManifestResultValue | None = None
    subject_sensitivity: SensitivityBlock
    class_sensitivity: SensitivityBlock | None = None

    replication_class: ReplicationClass
    completion_state: ExperimentCompletionState
    access_blocker: str | None = None
    provenance: ProvenanceRecord
    checkpoint_manifest: CheckpointManifestRef | None = None

    safe_claims: list[str] = Field(default_factory=list)
    unsafe_claims: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)


SUPPORTED_MANIFEST_SCHEMA_VERSIONS = frozenset({"1.0.0"})


class ExperimentManifestFile(StrictModel):
    schema_version: str
    manifest_id: str
    generated_by: str
    generated_at: str | None = None
    entries: list[ExperimentManifestEntry]


class ManifestEntryDisplayProjection(StrictModel):
    """The ONLY shape any frontend/paper/jury consumer should read from.

    Produced exclusively by `app.research.future_science_ingestion.project_for_display`,
    which already applies the promotion gate, state-separation, and metric-
    directionality guards. A consumer that only ever reads this projection
    (never `ExperimentManifestEntry` directly) structurally cannot render a
    fabricated headline number for a non-COMPLETE entry, cannot blur
    HISTORICAL into SUPERSEDED, and cannot infer a replication class that
    the manifest did not explicitly declare (governing prompt Phase-3
    consumer-guard requirement)."""

    experiment_id: str
    completion_state: ExperimentCompletionState
    completion_state_label: str
    is_headline_eligible: bool
    replication_class: ReplicationClass
    replication_class_label: str
    metric_name: str
    metric_directionality: MetricDirectionality
    benefit_value: float | None
    benefit_display: str
    # Phase-4 hostile-review finding: an aggregate benefit_value must never be
    # the ONLY thing a consumer can see. Carrying these through means a
    # strongly-positive aggregate cannot visually hide severe per-subject/
    # per-class heterogeneity (governing prompt §52: "Can an aggregate result
    # hide heterogeneity?").
    subject_sensitivity: SensitivityBlock
    class_sensitivity: SensitivityBlock | None
    limitations: list[str]
    provenance_source: str


class FutureScienceManifestEnvelope(StrictModel):
    """API-facing envelope. `status` carries the rich typed state (governing
    prompt §2/§25); `availability` stays for consistency with every other
    research envelope in this codebase."""

    availability: ResearchAvailability
    status: str  # "PENDING_SCIENCE_HANDOFF" | "INGESTION_FAILED" | "INGESTED"
    manifest_path: str
    error_code: str | None = None
    error: str | None = None
    manifest: ExperimentManifestFile | None = None
    # Empty unless status == "INGESTED" — never partially populated from a
    # failed/malformed parse (governing prompt §33 "stale result fallback").
    display_projections: list[ManifestEntryDisplayProjection] = Field(default_factory=list)
