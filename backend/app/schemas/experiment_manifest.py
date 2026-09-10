"""Generic future-science ingestion contract (Phase 2, Stage 2-4 integration prep).

This schema describes the shape a future Ismet science-completion manifest
must have to be ingested safely. It does NOT contain any real experiment
results — no manifest satisfying this schema exists in `results/` yet. See
`app.research.future_science_ingestion` for the fail-closed validator.

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
    Deliberately NOT a boolean complete/not-complete (governing prompt §25).

    This is the project's closed status-vocabulary allowlist (Codex parent-audit MEDIUM finding: a source artifact must never self-promote to an arbitrary strong label like "CANONICAL_UNCHANGED" or "SCIENCE_COMPLETE").
    Because this is a Pydantic StrEnum, any manifest value not listed here
    fails schema validation (UNKNOWN_STATUS) rather than being accepted —
    the allowlist is enforced structurally, not just by convention."""

    COMPLETE = "COMPLETE"
    BOUNDED_DIAGNOSTIC = "BOUNDED_DIAGNOSTIC"
    BLOCKED_BY_DATA_ACCESS = "BLOCKED_BY_DATA_ACCESS"
    PENDING = "PENDING"
    HISTORICAL = "HISTORICAL"
    SUPERSEDED = "SUPERSEDED"
    NONCANONICAL = "NONCANONICAL"
    REPORTED_COMPLETE = "REPORTED_COMPLETE"
    VERIFIED_COMPLETE = "VERIFIED_COMPLETE"
    ACCEPTED_FOR_SCOPE = "ACCEPTED_FOR_SCOPE"
    # Codex parent-audit finding H-02: an old comparison that used
    # unequal-capacity models (e.g. the historical ~23% PPG-only -> PPG+IMU
    # figure) is real evidence that once existed, but must never be
    # presented as governing marginal-value evidence for any target.
    HISTORICAL_CAPACITY_CONFOUNDED = "HISTORICAL_CAPACITY_CONFOUNDED"


class RawDataProvenanceLevel(StrEnum):
    """Codex parent-audit MEDIUM finding (GalaxyPPG/LBNP): official dataset
    access/metadata being verified is NOT the same claim as the local raw
    files having been hash/structure verified. A prose report asserting
    verification must never be rendered as ACTUAL_FILE_VERIFIED merely
    because the report said so."""

    OFFICIAL_METADATA_VERIFIED = "OFFICIAL_METADATA_VERIFIED"
    LOCAL_RAW_REPORTED_ONLY = "LOCAL_RAW_REPORTED_ONLY"
    ACTUAL_FILE_VERIFIED = "ACTUAL_FILE_VERIFIED"
    TRAINING_PENDING = "TRAINING_PENDING"


class EnvironmentProvenanceStatus(StrEnum):
    """Codex parent-audit MEDIUM finding: a later result must not silently
    inherit an old (e.g. Day-8) environment manifest's reproducibility
    claim. Defaults fail-closed to INCOMPLETE — a manifest entry must
    explicitly declare COMPLETE, it is never assumed."""

    COMPLETE = "COMPLETE"
    INCOMPLETE = "INCOMPLETE"


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
    # Codex parent-audit MEDIUM finding (HMC split provenance): the
    # manifest's OWN top-level claim about which split artifact was used.
    # Must be cross-checked against subject_split_manifest_path (the
    # embedded/actual pointer) — see
    # app.research.future_science_ingestion.assert_split_provenance_consistent.
    # A valid embedded split does not excuse a disagreeing declared source.
    declared_split_source: str | None = None
    raw_data_provenance_level: RawDataProvenanceLevel | None = None
    # Fail-closed default: environment reproducibility is INCOMPLETE unless
    # this entry's OWN provenance explicitly says otherwise. Never silently
    # inherits an older result's environment record (Codex MEDIUM finding).
    environment_provenance_status: EnvironmentProvenanceStatus = EnvironmentProvenanceStatus.INCOMPLETE
    # Known limitations that must survive into ingestion/display rather than
    # being silently dropped (Codex MEDIUM finding: cache provenance — e.g.
    # "relies on weak filename-only cache binding").
    provenance_warnings: list[str] = Field(default_factory=list)


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
    # Nullable: a manifest may not yet know either count (e.g. a BLOCKED/PENDING
    # entry with no execution yet). Missing must degrade to "unavailable" at
    # display time, never to a fabricated 0 (H4-style UNKNOWN handling,
    # Phase-4 close-out). When present, still must be a real positive count.
    biological_subject_n: int | None = Field(default=None, ge=1)
    optimization_seed_n: int | None = Field(default=None, ge=1)

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
    # Phase-4 close-out: named separately and labeled semantically so a
    # consumer can never merge them into one ambiguous "n" or imply seeds are
    # biological replication. `_display` is never a fabricated 0 for a
    # missing count (governing prompt Phase-4 close-out requirement).
    biological_subject_n: int | None
    biological_subject_n_display: str
    optimization_seed_n: int | None
    optimization_seed_n_display: str
    # Phase-4 hostile-review finding: an aggregate benefit_value must never be
    # the ONLY thing a consumer can see. Carrying these through means a
    # strongly-positive aggregate cannot visually hide severe per-subject/
    # per-class heterogeneity (governing prompt §52: "Can an aggregate result
    # hide heterogeneity?").
    subject_sensitivity: SensitivityBlock
    class_sensitivity: SensitivityBlock | None
    limitations: list[str]
    provenance_source: str
    # Codex parent-audit MEDIUM findings: never silently inherit an old
    # environment record, and never hide a known provenance limitation
    # (e.g. weak filename-only cache binding) from the consumer.
    environment_provenance_status: EnvironmentProvenanceStatus
    provenance_warnings: list[str]
    raw_data_provenance_level: RawDataProvenanceLevel | None


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
