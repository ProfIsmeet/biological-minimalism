"""Fail-closed ingestion contract for a future Ismet science-completion manifest
(Phase 2, Stage 2-4 integration prep, governing prompt §23-34).

No manifest satisfying this contract exists in `results/` yet — Ismet's
science-completion sprint is still in progress on a separate branch. This
module exists so that, when the real manifest arrives, ingesting it is a
mechanical validate-then-project operation rather than a hand-hardcoding
exercise. Until then, `future_science_manifest.status()` reports
`PENDING_SCIENCE_HANDOFF` — never a fabricated result.

Every failure mode fails closed: a missing, malformed, wrong-version,
direction-conflicting, or under-specified manifest is reported as a typed
error, never silently ignored or replaced with stale/cached science.
"""

from __future__ import annotations

import json
from enum import StrEnum
from pathlib import Path

from pydantic import ValidationError

from app.research.catalog import REPOSITORY_ROOT
from app.schemas.experiment_manifest import (
    SUPPORTED_MANIFEST_SCHEMA_VERSIONS,
    ExperimentCompletionState,
    ExperimentManifestEntry,
    ExperimentManifestFile,
    FutureScienceManifestEnvelope,
    ManifestEntryDisplayProjection,
    ManifestMetric,
    ManifestResultValue,
    ReplicationClass,
)
from app.schemas.research import MetricDirectionality, ResearchAvailability

FUTURE_SCIENCE_MANIFEST_RELATIVE_PATH = "results/stage2_4_science_completion_manifest.json"

# Metrics already established elsewhere in this repo. An incoming manifest
# entry naming one of these MUST declare the matching directionality — a
# mismatch is a real defect (reversed sign), not a new metric definition.
# A metric name not in this registry is accepted as-is (first sighting).
KNOWN_METRIC_DIRECTIONS: dict[str, MetricDirectionality] = {
    "hr_mae_bpm": MetricDirectionality.LOWER_IS_BETTER,
    "ptt_mae_ms": MetricDirectionality.LOWER_IS_BETTER,
    "sleep_macro_f1": MetricDirectionality.HIGHER_IS_BETTER,
    "cognitive_macro_f1": MetricDirectionality.HIGHER_IS_BETTER,
    "qde_mass_mae_kg": MetricDirectionality.LOWER_IS_BETTER,
}

# An entry may only be promoted to a "headline"-style display when its
# evidence is actually complete (governing prompt §51: "diagnostic -> canonical
# promotion" and "blocked -> complete promotion" are explicit attack targets).
_PROMOTABLE_TO_HEADLINE = frozenset({ExperimentCompletionState.COMPLETE})

# Human labels a consumer displays VERBATIM — never re-derived or abbreviated
# in a way that could blur two distinct states together (Phase-3 consumer-
# guard requirement: BOUNDED_DIAGNOSTIC vs COMPLETE, HISTORICAL vs SUPERSEDED
# must always read as visibly different states).
_COMPLETION_STATE_LABELS: dict[ExperimentCompletionState, str] = {
    ExperimentCompletionState.COMPLETE: "Complete (canonical)",
    ExperimentCompletionState.BOUNDED_DIAGNOSTIC: "Bounded diagnostic (not full protocol)",
    ExperimentCompletionState.BLOCKED_BY_DATA_ACCESS: "Blocked (data access unavailable)",
    ExperimentCompletionState.PENDING: "Pending (not yet run)",
    ExperimentCompletionState.HISTORICAL: "Historical (superseded protocol, preserved for continuity)",
    ExperimentCompletionState.SUPERSEDED: "Superseded (do not cite as current)",
}

# A result must never be auto-labeled EXTERNAL_REPLICATION merely for being a
# second run (governing prompt §38); this map only ever echoes what the
# manifest itself declared.
_REPLICATION_CLASS_LABELS: dict[ReplicationClass, str] = {
    ReplicationClass.EXTERNAL_REPLICATION: "Independent external replication",
    ReplicationClass.SAME_DATASET_HOLDOUT: "Same-dataset holdout (not independent replication)",
    ReplicationClass.SINGLE_RUN: "Single run (no replication claim)",
    ReplicationClass.NOT_APPLICABLE: "Not applicable",
}

# Completion states whose evidence is NOT a full canonical protocol run, even
# though they may contain real (bounded/diagnostic) numbers (governing prompt
# §44: "bounded diagnostic where full evidence is required" must invalidate a
# claim demanding full evidence).
_INCOMPLETE_EVIDENCE_STATES = frozenset({
    ExperimentCompletionState.BLOCKED_BY_DATA_ACCESS,
    ExperimentCompletionState.PENDING,
    ExperimentCompletionState.SUPERSEDED,
})


class ManifestErrorCode(StrEnum):
    MISSING_MANIFEST = "MISSING_MANIFEST"
    MALFORMED_JSON = "MALFORMED_JSON"
    SCHEMA_VALIDATION_FAILED = "SCHEMA_VALIDATION_FAILED"
    UNSUPPORTED_SCHEMA_VERSION = "UNSUPPORTED_SCHEMA_VERSION"
    UNKNOWN_STATUS = "UNKNOWN_STATUS"
    CONFLICTING_METRIC_DIRECTION = "CONFLICTING_METRIC_DIRECTION"
    MISSING_PROVENANCE = "MISSING_PROVENANCE"
    INVALID_CHECKPOINT_MAPPING = "INVALID_CHECKPOINT_MAPPING"
    MIXED_PROTOCOL_VERSION = "MIXED_PROTOCOL_VERSION"
    CROSS_TARGET_COMPARISON_PROHIBITED = "CROSS_TARGET_COMPARISON_PROHIBITED"
    NOT_PROMOTABLE_TO_HEADLINE = "NOT_PROMOTABLE_TO_HEADLINE"
    CLAIM_EVIDENCE_INSUFFICIENT = "CLAIM_EVIDENCE_INSUFFICIENT"


class ManifestValidationError(Exception):
    """Typed, fail-closed ingestion error. Callers must branch on `.code`,
    never treat any failure as "close enough, use it anyway"."""

    def __init__(self, code: ManifestErrorCode, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(f"{code.value}: {message}")


def _validate_entry_semantics(entry: ExperimentManifestEntry) -> None:
    expected = KNOWN_METRIC_DIRECTIONS.get(entry.metric.name.lower())
    if expected is not None and entry.metric.directionality != expected:
        raise ManifestValidationError(
            ManifestErrorCode.CONFLICTING_METRIC_DIRECTION,
            f"{entry.experiment_id}: metric {entry.metric.name!r} declared "
            f"{entry.metric.directionality.value}, but this repository already established "
            f"{expected.value} for that metric elsewhere.",
        )
    if not entry.provenance.source_artifact_path.strip():
        raise ManifestValidationError(
            ManifestErrorCode.MISSING_PROVENANCE,
            f"{entry.experiment_id}: provenance.source_artifact_path is empty.",
        )
    if entry.checkpoint_manifest is not None and not entry.checkpoint_manifest.path.strip().endswith(".json"):
        raise ManifestValidationError(
            ManifestErrorCode.INVALID_CHECKPOINT_MAPPING,
            f"{entry.experiment_id}: checkpoint_manifest.path must reference a .json manifest, "
            f"got {entry.checkpoint_manifest.path!r}.",
        )


def validate_manifest_dict(raw: dict) -> ExperimentManifestFile:
    """Fail-closed validation of an already-parsed manifest dict. Raises
    `ManifestValidationError` for every failure mode in governing prompt §29;
    never returns a partially-trusted object."""
    schema_version = raw.get("schema_version") if isinstance(raw, dict) else None
    if schema_version not in SUPPORTED_MANIFEST_SCHEMA_VERSIONS:
        raise ManifestValidationError(
            ManifestErrorCode.UNSUPPORTED_SCHEMA_VERSION,
            f"got {schema_version!r}, supported {sorted(SUPPORTED_MANIFEST_SCHEMA_VERSIONS)}.",
        )
    try:
        manifest = ExperimentManifestFile.model_validate(raw)
    except ValidationError as exc:
        status_field_failed = any(
            err.get("loc") and err["loc"][-1] in ("completion_state", "replication_class")
            for err in exc.errors()
        )
        code = ManifestErrorCode.UNKNOWN_STATUS if status_field_failed else ManifestErrorCode.SCHEMA_VALIDATION_FAILED
        raise ManifestValidationError(code, str(exc)) from exc

    for entry in manifest.entries:
        _validate_entry_semantics(entry)
    return manifest


def load_and_validate_manifest(path: Path) -> ExperimentManifestFile:
    if not path.is_file():
        raise ManifestValidationError(ManifestErrorCode.MISSING_MANIFEST, f"{path} does not exist.")
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ManifestValidationError(ManifestErrorCode.MALFORMED_JSON, f"{path}: {exc}") from exc
    return validate_manifest_dict(raw)


def compute_benefit(metric: ManifestMetric, baseline: ManifestResultValue, candidate: ManifestResultValue) -> float:
    """Positive return = candidate is better than baseline, per the metric's
    OWN declared directionality. Never assumes "lower is better" (governing
    prompt §26/§27) and refuses to compute anything for NOT_APPLICABLE."""
    if metric.directionality == MetricDirectionality.LOWER_IS_BETTER:
        return baseline.mean - candidate.mean
    if metric.directionality == MetricDirectionality.HIGHER_IS_BETTER:
        return candidate.mean - baseline.mean
    raise ManifestValidationError(
        ManifestErrorCode.CONFLICTING_METRIC_DIRECTION,
        f"cannot compute a directional benefit for metric {metric.name!r} "
        f"with directionality {MetricDirectionality.NOT_APPLICABLE.value}.",
    )


def assert_promotable_to_headline(entry: ExperimentManifestEntry) -> None:
    """Refuses to let a BOUNDED_DIAGNOSTIC/BLOCKED/PENDING/HISTORICAL/SUPERSEDED
    entry be treated as a canonical headline result (governing prompt §51:
    'diagnostic -> canonical promotion' / 'blocked -> complete promotion')."""
    if entry.completion_state not in _PROMOTABLE_TO_HEADLINE:
        raise ManifestValidationError(
            ManifestErrorCode.NOT_PROMOTABLE_TO_HEADLINE,
            f"{entry.experiment_id}: completion_state={entry.completion_state.value} "
            f"cannot be presented as a headline result.",
        )


def forbid_cross_target_comparison(entry_a: ExperimentManifestEntry, entry_b: ExperimentManifestEntry) -> None:
    """No generic normalized ranking may ever compare two different targets
    (governing prompt §27) — e.g. HR MAE vs sleep macro-F1."""
    if entry_a.target != entry_b.target:
        raise ManifestValidationError(
            ManifestErrorCode.CROSS_TARGET_COMPARISON_PROHIBITED,
            f"cannot compare {entry_a.experiment_id} (target={entry_a.target!r}) with "
            f"{entry_b.experiment_id} (target={entry_b.target!r}).",
        )


def forbid_mixed_protocol_derivation(entry_a: ExperimentManifestEntry, entry_b: ExperimentManifestEntry) -> None:
    """Generalizes `app.research.sleep_version_guard` to the generic contract:
    two operands may only be combined into one derived delta if they share the
    same dataset, dataset_version, AND protocol_version (governing prompt §14)."""
    if entry_a.dataset != entry_b.dataset:
        raise ManifestValidationError(
            ManifestErrorCode.CROSS_TARGET_COMPARISON_PROHIBITED,
            f"{entry_a.experiment_id} (dataset={entry_a.dataset!r}) vs "
            f"{entry_b.experiment_id} (dataset={entry_b.dataset!r}) are different datasets.",
        )
    if (
        entry_a.dataset_version != entry_b.dataset_version
        or entry_a.provenance.protocol_version != entry_b.provenance.protocol_version
    ):
        raise ManifestValidationError(
            ManifestErrorCode.MIXED_PROTOCOL_VERSION,
            f"{entry_a.experiment_id} ({entry_a.dataset_version}/{entry_a.provenance.protocol_version}) "
            f"vs {entry_b.experiment_id} ({entry_b.dataset_version}/{entry_b.provenance.protocol_version}) "
            f"do not share one dataset_version+protocol_version pair.",
        )


def project_for_display(entry: ExperimentManifestEntry) -> ManifestEntryDisplayProjection:
    """The single choke point any frontend/paper/jury consumer must go
    through (Phase-3 consumer-guard requirement). Never returns a bypassable
    raw pass-through of the entry: a non-COMPLETE entry can never carry a
    numeric `benefit_value`, and `completion_state_label`/`replication_class_label`
    are always the entry's OWN declared state — never inferred or blurred."""
    try:
        assert_promotable_to_headline(entry)
        headline_eligible = True
    except ManifestValidationError:
        headline_eligible = False

    benefit_value: float | None = None
    if headline_eligible and entry.control_result is not None:
        try:
            benefit_value = compute_benefit(entry.metric, baseline=entry.control_result, candidate=entry.primary_result)
        except ManifestValidationError:
            benefit_value = None

    if not headline_eligible:
        benefit_display = f"N/A — {_COMPLETION_STATE_LABELS[entry.completion_state]}"
    elif benefit_value is not None:
        sign = "+" if benefit_value >= 0 else ""
        benefit_display = (
            f"{entry.primary_result.display} (control-relative benefit {sign}{benefit_value:.4g} {entry.metric.unit})"
        )
    else:
        benefit_display = entry.primary_result.display

    return ManifestEntryDisplayProjection(
        experiment_id=entry.experiment_id,
        completion_state=entry.completion_state,
        completion_state_label=_COMPLETION_STATE_LABELS[entry.completion_state],
        is_headline_eligible=headline_eligible,
        replication_class=entry.replication_class,
        replication_class_label=_REPLICATION_CLASS_LABELS[entry.replication_class],
        metric_name=entry.metric.name,
        metric_directionality=entry.metric.directionality,
        benefit_value=benefit_value if headline_eligible else None,
        benefit_display=benefit_display,
        limitations=list(entry.limitations),
        provenance_source=entry.provenance.source_artifact_path,
    )


def build_two_arm_comparison_narrative(entry_a: ExperimentManifestEntry, entry_b: ExperimentManifestEntry) -> str:
    """The only sanctioned way to narrate two manifest entries together (e.g.
    for a paper's Results section or a jury answer). Refuses to combine
    mismatched targets or mismatched protocol versions rather than silently
    producing a narrative that implies a comparison that was never validated."""
    forbid_cross_target_comparison(entry_a, entry_b)
    forbid_mixed_protocol_derivation(entry_a, entry_b)
    proj_a = project_for_display(entry_a)
    proj_b = project_for_display(entry_b)
    return (
        f"{entry_a.experiment_id} ({proj_a.completion_state_label}) vs "
        f"{entry_b.experiment_id} ({proj_b.completion_state_label}): "
        f"{proj_a.benefit_display} / {proj_b.benefit_display}."
    )


def validate_claim_against_entry(entry: ExperimentManifestEntry, *, required_full_evidence: bool = False) -> None:
    """Governing prompt §44: "A claim should be invalid if its evidence is:
    blocked, pending, bounded diagnostic where full evidence is required,
    superseded, or mixed-version." (Mixed-version is enforced separately, at
    the two-entry boundary, by `forbid_mixed_protocol_derivation`.)"""
    if entry.completion_state in _INCOMPLETE_EVIDENCE_STATES:
        raise ManifestValidationError(
            ManifestErrorCode.CLAIM_EVIDENCE_INSUFFICIENT,
            f"{entry.experiment_id}: completion_state={entry.completion_state.value} "
            f"cannot support a paper/jury claim.",
        )
    if required_full_evidence and entry.completion_state == ExperimentCompletionState.BOUNDED_DIAGNOSTIC:
        raise ManifestValidationError(
            ManifestErrorCode.CLAIM_EVIDENCE_INSUFFICIENT,
            f"{entry.experiment_id}: completion_state=BOUNDED_DIAGNOSTIC is insufficient "
            f"for a claim that requires full-protocol evidence.",
        )


class FutureScienceManifestReader:
    """Loads the future manifest on demand; never caches a stale result and
    never falls back to any existing canonical science artifact on failure."""

    def __init__(self, repository_root: str | Path = REPOSITORY_ROOT) -> None:
        self.repository_root = Path(repository_root).resolve()
        self.manifest_path = self.repository_root / FUTURE_SCIENCE_MANIFEST_RELATIVE_PATH

    def status(self) -> FutureScienceManifestEnvelope:
        if not self.manifest_path.is_file():
            return FutureScienceManifestEnvelope(
                availability=ResearchAvailability.UNAVAILABLE,
                status="PENDING_SCIENCE_HANDOFF",
                manifest_path=FUTURE_SCIENCE_MANIFEST_RELATIVE_PATH,
            )
        try:
            manifest = load_and_validate_manifest(self.manifest_path)
        except ManifestValidationError as exc:
            return FutureScienceManifestEnvelope(
                availability=ResearchAvailability.UNAVAILABLE,
                status="INGESTION_FAILED",
                manifest_path=FUTURE_SCIENCE_MANIFEST_RELATIVE_PATH,
                error_code=exc.code.value,
                error=exc.message,
            )
        return FutureScienceManifestEnvelope(
            availability=ResearchAvailability.AVAILABLE,
            status="INGESTED",
            manifest_path=FUTURE_SCIENCE_MANIFEST_RELATIVE_PATH,
            manifest=manifest,
            display_projections=[project_for_display(entry) for entry in manifest.entries],
        )


future_science_manifest = FutureScienceManifestReader()
