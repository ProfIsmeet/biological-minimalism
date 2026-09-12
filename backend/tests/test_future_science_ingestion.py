"""Adversarial contract tests for the Phase-2 future-science ingestion pipeline
(governing prompt §33). The failure mode under test throughout: a missing,
malformed, under-specified, or mis-declared future manifest must fail closed
— never silently accepted, never masked as success, never allowed to promote
partial/blocked evidence to a canonical headline, and never combined across
incompatible protocol versions or targets.

All fixtures in this file are synthetic and TEST-ONLY; no fixture is written
into `results/` as real project evidence (governing prompt §49)."""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.research.future_science_ingestion import (
    FutureScienceManifestReader,
    ManifestErrorCode,
    ManifestValidationError,
    assert_promotable_to_headline,
    compute_benefit,
    forbid_cross_target_comparison,
    forbid_mixed_protocol_derivation,
    load_and_validate_manifest,
    validate_manifest_dict,
)
from app.schemas.experiment_manifest import (
    ExperimentCompletionState,
    ExperimentManifestEntry,
    ManifestMetric,
    ManifestResultValue,
)
from app.schemas.research import MetricDirectionality, MetricKind

client = TestClient(app)


def _valid_entry(**overrides) -> dict:
    entry = {
        "experiment_id": "test-experiment-alpha",
        "experiment_version": "V1",
        "dataset": "test-dataset",
        "dataset_version": "v1",
        "target": "test_target_mae",
        "baseline_config": "A",
        "candidate_config": "B",
        "control_config": None,
        "metric": {
            "name": "test_metric_mae",
            "kind": "regression",
            "directionality": "lower_is_better",
            "unit": "unit",
        },
        "biological_subject_n": 5,
        "optimization_seed_n": 5,
        "primary_result": {"mean": 1.23, "sd": 0.1, "n": 5, "display": "1.23 unit"},
        "control_result": None,
        "subject_sensitivity": {"status": "available", "entries": [], "dominant_key": None, "note": None},
        "class_sensitivity": None,
        "replication_class": "SINGLE_RUN",
        "completion_state": "COMPLETE",
        "access_blocker": None,
        "provenance": {
            "source_artifact_path": "results/test_fixture_only.json",
            "source_sha256": None,
            "experiment_commit": None,
            "dataset_version": "v1",
            "protocol_version": "protocol_v1",
            "checkpoint_manifest_path": None,
            "subject_split_manifest_path": None,
        },
        "checkpoint_manifest": None,
        "safe_claims": [],
        "unsafe_claims": [],
        "limitations": [],
    }
    entry.update(overrides)
    return entry


def _valid_manifest(entries: list[dict] | None = None) -> dict:
    return {
        "schema_version": "1.0.0",
        "manifest_id": "test-only-manifest",
        "generated_by": "pytest-fixture",
        "generated_at": None,
        "entries": entries if entries is not None else [_valid_entry()],
    }


# --- Positive path: a well-formed manifest ingests cleanly -----------------

def test_valid_manifest_ingests_successfully() -> None:
    manifest = validate_manifest_dict(_valid_manifest())
    assert manifest.entries[0].experiment_id == "test-experiment-alpha"
    assert manifest.entries[0].completion_state == ExperimentCompletionState.COMPLETE


# --- §33: missing final science manifest ------------------------------------

def test_missing_manifest_fails_closed(tmp_path: Path) -> None:
    reader = FutureScienceManifestReader(repository_root=tmp_path)
    envelope = reader.status()
    assert envelope.availability == "unavailable"
    assert envelope.status == "PENDING_SCIENCE_HANDOFF"
    assert envelope.manifest is None
    assert envelope.error is None  # missing is an expected state, not an error


def test_missing_manifest_raises_typed_error_from_loader(tmp_path: Path) -> None:
    with pytest.raises(ManifestValidationError) as excinfo:
        load_and_validate_manifest(tmp_path / "does_not_exist.json")
    assert excinfo.value.code == ManifestErrorCode.MISSING_MANIFEST


# --- §33: malformed manifest -------------------------------------------------

def test_malformed_json_fails_closed(tmp_path: Path) -> None:
    manifest_dir = tmp_path / "results"
    manifest_dir.mkdir()
    (manifest_dir / "stage2_4_science_completion_manifest.json").write_text("{not valid json", encoding="utf-8")
    reader = FutureScienceManifestReader(repository_root=tmp_path)
    envelope = reader.status()
    assert envelope.availability == "unavailable"
    assert envelope.status == "INGESTION_FAILED"
    assert envelope.error_code == ManifestErrorCode.MALFORMED_JSON.value


def test_unsupported_schema_version_fails_closed() -> None:
    raw = _valid_manifest()
    raw["schema_version"] = "99.0.0"
    with pytest.raises(ManifestValidationError) as excinfo:
        validate_manifest_dict(raw)
    assert excinfo.value.code == ManifestErrorCode.UNSUPPORTED_SCHEMA_VERSION


def test_unknown_completion_state_fails_closed() -> None:
    raw = _valid_manifest([_valid_entry(completion_state="TOTALLY_MADE_UP_STATUS")])
    with pytest.raises(ManifestValidationError) as excinfo:
        validate_manifest_dict(raw)
    assert excinfo.value.code == ManifestErrorCode.UNKNOWN_STATUS


# --- §33: no provenance -------------------------------------------------------

def test_missing_provenance_fails_closed() -> None:
    raw = _valid_manifest([_valid_entry(provenance={
        "source_artifact_path": "   ",
        "source_sha256": None,
        "experiment_commit": None,
        "dataset_version": "v1",
        "protocol_version": "protocol_v1",
        "checkpoint_manifest_path": None,
        "subject_split_manifest_path": None,
    })])
    with pytest.raises(ManifestValidationError) as excinfo:
        validate_manifest_dict(raw)
    assert excinfo.value.code == ManifestErrorCode.MISSING_PROVENANCE


# --- §33: subject/seed n conflated -------------------------------------------

def test_subject_n_and_seed_n_missing_becomes_unavailable_never_zero_or_conflated() -> None:
    """Phase-4 close-out revision: both fields are nullable (a manifest may
    not yet know either count, e.g. an unexecuted BLOCKED/PENDING entry), so
    omitting one no longer fails the whole manifest — it degrades to
    `None` ("unavailable" at display time) for that field only, and the
    OTHER field is never silently backfilled from it (no conflation). An
    explicitly invalid non-positive value is still a real malformed value,
    not an absence, and is still rejected."""
    raw = _valid_manifest()
    del raw["entries"][0]["optimization_seed_n"]
    manifest = validate_manifest_dict(raw)  # no longer raises
    entry = manifest.entries[0]
    assert entry.optimization_seed_n is None
    assert entry.biological_subject_n == 5  # untouched — not backfilled from the missing seed_n

    raw2 = _valid_manifest()
    raw2["entries"][0]["biological_subject_n"] = 0
    with pytest.raises(ManifestValidationError) as excinfo2:
        validate_manifest_dict(raw2)
    assert excinfo2.value.code == ManifestErrorCode.SCHEMA_VALIDATION_FAILED


# --- §33: MAE / F1 direction reversed ----------------------------------------

def test_mae_direction_reversed_is_rejected() -> None:
    raw = _valid_manifest([_valid_entry(
        metric={"name": "hr_mae_bpm", "kind": "regression", "directionality": "higher_is_better", "unit": "bpm"},
    )])
    with pytest.raises(ManifestValidationError) as excinfo:
        validate_manifest_dict(raw)
    assert excinfo.value.code == ManifestErrorCode.CONFLICTING_METRIC_DIRECTION


def test_f1_direction_reversed_is_rejected() -> None:
    raw = _valid_manifest([_valid_entry(
        metric={"name": "sleep_macro_f1", "kind": "classification", "directionality": "lower_is_better", "unit": "f1"},
        target="sleep_stage_classification",
    )])
    with pytest.raises(ManifestValidationError) as excinfo:
        validate_manifest_dict(raw)
    assert excinfo.value.code == ManifestErrorCode.CONFLICTING_METRIC_DIRECTION


def test_compute_benefit_respects_declared_direction_both_ways() -> None:
    lower_metric = ManifestMetric(name="x_mae", kind=MetricKind.REGRESSION, directionality=MetricDirectionality.LOWER_IS_BETTER, unit="u")
    higher_metric = ManifestMetric(name="x_f1", kind=MetricKind.CLASSIFICATION, directionality=MetricDirectionality.HIGHER_IS_BETTER, unit="u")
    baseline = ManifestResultValue(mean=1.0, display="1.0")
    candidate_better_lower = ManifestResultValue(mean=0.6, display="0.6")
    candidate_better_higher = ManifestResultValue(mean=1.4, display="1.4")

    assert compute_benefit(lower_metric, baseline, candidate_better_lower) == pytest.approx(0.4)
    assert compute_benefit(higher_metric, baseline, candidate_better_higher) == pytest.approx(0.4)

    not_applicable = ManifestMetric(name="x_unranked", kind=MetricKind.REGRESSION, directionality=MetricDirectionality.NOT_APPLICABLE, unit="u")
    with pytest.raises(ManifestValidationError) as excinfo:
        compute_benefit(not_applicable, baseline, candidate_better_lower)
    assert excinfo.value.code == ManifestErrorCode.CONFLICTING_METRIC_DIRECTION


# --- §33: BOUNDED diagnostic incorrectly promoted / blocked shown as complete -

@pytest.mark.parametrize(
    "state",
    [
        ExperimentCompletionState.BOUNDED_DIAGNOSTIC,
        ExperimentCompletionState.BLOCKED_BY_DATA_ACCESS,
        ExperimentCompletionState.PENDING,
        ExperimentCompletionState.HISTORICAL,
        ExperimentCompletionState.SUPERSEDED,
    ],
)
def test_non_complete_states_cannot_be_promoted_to_headline(state: ExperimentCompletionState) -> None:
    entry = ExperimentManifestEntry.model_validate(_valid_entry(completion_state=state.value))
    with pytest.raises(ManifestValidationError) as excinfo:
        assert_promotable_to_headline(entry)
    assert excinfo.value.code == ManifestErrorCode.NOT_PROMOTABLE_TO_HEADLINE


def test_complete_state_is_promotable_to_headline() -> None:
    entry = ExperimentManifestEntry.model_validate(_valid_entry(completion_state="COMPLETE"))
    assert_promotable_to_headline(entry)  # must not raise


# --- §33: V1/V2 (generalized: mixed-protocol) mixed source ------------------

def test_mixed_protocol_version_derivation_is_blocked() -> None:
    entry_v1 = ExperimentManifestEntry.model_validate(_valid_entry(
        experiment_id="exp-v1-leg",
        provenance={
            "source_artifact_path": "results/test_fixture_only.json", "source_sha256": None,
            "experiment_commit": None, "dataset_version": "v1", "protocol_version": "protocol_v1",
            "checkpoint_manifest_path": None, "subject_split_manifest_path": None,
        },
    ))
    entry_v2 = ExperimentManifestEntry.model_validate(_valid_entry(
        experiment_id="exp-v2-leg",
        dataset_version="v2",
        provenance={
            "source_artifact_path": "results/test_fixture_only.json", "source_sha256": None,
            "experiment_commit": None, "dataset_version": "v2", "protocol_version": "protocol_v2_seedfix",
            "checkpoint_manifest_path": None, "subject_split_manifest_path": None,
        },
    ))
    with pytest.raises(ManifestValidationError) as excinfo:
        forbid_mixed_protocol_derivation(entry_v1, entry_v2)
    assert excinfo.value.code == ManifestErrorCode.MIXED_PROTOCOL_VERSION

    # Same dataset/version/protocol on both legs -> allowed (no raise).
    entry_v1_again = ExperimentManifestEntry.model_validate(_valid_entry(experiment_id="exp-v1-leg-b"))
    forbid_mixed_protocol_derivation(entry_v1, entry_v1_again)


# --- §27/§52: cross-target comparison prohibited -----------------------------

def test_cross_target_comparison_is_prohibited() -> None:
    hr_entry = ExperimentManifestEntry.model_validate(_valid_entry(experiment_id="hr-exp", target="heart_rate_mae"))
    sleep_entry = ExperimentManifestEntry.model_validate(_valid_entry(experiment_id="sleep-exp", target="sleep_stage_macro_f1"))
    with pytest.raises(ManifestValidationError) as excinfo:
        forbid_cross_target_comparison(hr_entry, sleep_entry)
    assert excinfo.value.code == ManifestErrorCode.CROSS_TARGET_COMPARISON_PROHIBITED


# --- invalid checkpoint mapping ----------------------------------------------

def test_invalid_checkpoint_mapping_is_rejected() -> None:
    raw = _valid_manifest([_valid_entry(checkpoint_manifest={
        "path": "not-a-manifest.txt", "checkpoint_count": 5, "note": None,
    })])
    with pytest.raises(ManifestValidationError) as excinfo:
        validate_manifest_dict(raw)
    assert excinfo.value.code == ManifestErrorCode.INVALID_CHECKPOINT_MAPPING


# --- §33: stale result fallback — ingestion failure never serves old data ---

def test_ingestion_failure_never_falls_back_to_cached_or_canonical_science(tmp_path: Path) -> None:
    manifest_dir = tmp_path / "results"
    manifest_dir.mkdir()
    broken = _valid_manifest()
    broken["schema_version"] = "0.0.1-broken"
    (manifest_dir / "stage2_4_science_completion_manifest.json").write_text(json.dumps(broken), encoding="utf-8")

    reader = FutureScienceManifestReader(repository_root=tmp_path)
    envelope_1 = reader.status()
    envelope_2 = reader.status()

    for envelope in (envelope_1, envelope_2):
        assert envelope.status == "INGESTION_FAILED"
        assert envelope.manifest is None
        # Must never leak fields/values belonging to the existing canonical
        # research catalog (proves this failure path is fully isolated and
        # cannot be confused with, or fall back to, real PPG/Sleep science).
        dumped = envelope.model_dump_json().lower()
        for forbidden in ("ppg", "sleep", "0.605", "capacity_control"):
            assert forbidden not in dumped


def test_deep_copy_of_valid_manifest_is_unaffected_by_mutation_isolation() -> None:
    """Sanity check that the fixture helpers build independent dicts per call
    (protects every other test in this file from cross-test mutation bleed)."""
    a = _valid_manifest()
    b = _valid_manifest()
    a["entries"][0]["experiment_id"] = "mutated"
    assert b["entries"][0]["experiment_id"] == "test-experiment-alpha"
    assert copy.deepcopy(a) is not a  # trivial, just documents intent


# --- API-level: today's real repo has no manifest -> PENDING, not a 404/fake -

def test_live_api_reports_pending_science_handoff_today() -> None:
    response = client.get("/research/future-science-manifest")
    assert response.status_code == 200
    body = response.json()
    assert body["availability"] == "unavailable"
    assert body["status"] == "PENDING_SCIENCE_HANDOFF"
    assert body["manifest"] is None


def test_future_science_manifest_route_is_read_only() -> None:
    assert client.post("/research/future-science-manifest", json={}).status_code == 405
