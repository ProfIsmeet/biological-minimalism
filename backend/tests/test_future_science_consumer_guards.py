"""Phase-3 consumer-guard verification (explicit user requirement): proves
that a downstream consumer — frontend, Research Mode, claim checker, or a
paper/jury narrative — cannot bypass the Phase-2 guards while reading the
Phase-3 presentation layer (`project_for_display`, `build_two_arm_comparison_narrative`,
`validate_claim_against_entry`). Each test below is named after, and maps
directly to, one of the 8 guard categories called out in that requirement.

All fixtures are synthetic and TEST-ONLY (governing prompt §49); none are
written into `results/` as real project evidence."""

from __future__ import annotations

import pytest

from app.research.future_science_ingestion import (
    ManifestErrorCode,
    ManifestValidationError,
    build_two_arm_comparison_narrative,
    project_for_display,
    validate_claim_against_entry,
)
from app.schemas.experiment_manifest import ExperimentCompletionState, ExperimentManifestEntry, ReplicationClass


def _entry(**overrides) -> ExperimentManifestEntry:
    raw = {
        "experiment_id": "consumer-guard-experiment",
        "experiment_version": "V1",
        "dataset": "test-dataset",
        "dataset_version": "v1",
        "target": "test_target_mae",
        "baseline_config": "A",
        "candidate_config": "B",
        "control_config": "C",
        "metric": {"name": "unregistered_test_mae", "kind": "regression", "directionality": "lower_is_better", "unit": "unit"},
        "biological_subject_n": 5,
        "optimization_seed_n": 5,
        "primary_result": {"mean": 0.60, "sd": 0.05, "n": 5, "display": "0.60 unit"},
        "control_result": {"mean": 1.00, "sd": 0.05, "n": 5, "display": "1.00 unit"},
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
    raw.update(overrides)
    return ExperimentManifestEntry.model_validate(raw)


def _provenance(dataset_version: str, protocol_version: str) -> dict:
    return {
        "source_artifact_path": "results/test_fixture_only.json", "source_sha256": None,
        "experiment_commit": None, "dataset_version": dataset_version, "protocol_version": protocol_version,
        "checkpoint_manifest_path": None, "subject_split_manifest_path": None,
    }


# --- 1. assert_promotable_to_headline / the promotion gate ------------------

def test_guard_1_non_complete_entry_never_yields_a_numeric_benefit_via_projection() -> None:
    """A consumer reading only `project_for_display`'s output — never the raw
    entry, never `assert_promotable_to_headline` directly — must still be
    unable to obtain a fabricated benefit for a non-COMPLETE entry."""
    for state in (
        ExperimentCompletionState.BOUNDED_DIAGNOSTIC,
        ExperimentCompletionState.BLOCKED_BY_DATA_ACCESS,
        ExperimentCompletionState.PENDING,
        ExperimentCompletionState.HISTORICAL,
        ExperimentCompletionState.SUPERSEDED,
    ):
        projection = project_for_display(_entry(completion_state=state.value))
        assert projection.is_headline_eligible is False
        assert projection.benefit_value is None
        assert projection.benefit_display.startswith("N/A —")


def test_guard_1_complete_entry_is_headline_eligible_with_a_real_benefit() -> None:
    projection = project_for_display(_entry(completion_state="COMPLETE"))
    assert projection.is_headline_eligible is True
    assert projection.benefit_value == pytest.approx(0.40)  # control 1.00 -> primary 0.60, lower_is_better
    assert "N/A" not in projection.benefit_display


# --- 2. BOUNDED_DIAGNOSTIC vs COMPLETE separation ----------------------------

def test_guard_2_bounded_diagnostic_label_is_never_the_same_string_as_complete() -> None:
    complete = project_for_display(_entry(completion_state="COMPLETE"))
    diagnostic = project_for_display(_entry(completion_state="BOUNDED_DIAGNOSTIC"))
    assert complete.completion_state_label != diagnostic.completion_state_label
    assert "diagnostic" in diagnostic.completion_state_label.lower()
    assert "canonical" in complete.completion_state_label.lower()
    assert diagnostic.is_headline_eligible is False
    assert complete.is_headline_eligible is True


# --- 3. HISTORICAL / SUPERSEDED separation -----------------------------------

def test_guard_3_historical_and_superseded_have_distinct_non_bypassable_labels() -> None:
    historical = project_for_display(_entry(completion_state="HISTORICAL"))
    superseded = project_for_display(_entry(completion_state="SUPERSEDED"))
    assert historical.completion_state_label != superseded.completion_state_label
    assert "preserved" in historical.completion_state_label.lower()
    assert "do not cite" in superseded.completion_state_label.lower()
    assert historical.is_headline_eligible is False
    assert superseded.is_headline_eligible is False
    # A claim consumer must reject SUPERSEDED outright...
    with pytest.raises(ManifestValidationError) as excinfo:
        validate_claim_against_entry(_entry(completion_state="SUPERSEDED"))
    assert excinfo.value.code == ManifestErrorCode.CLAIM_EVIDENCE_INSUFFICIENT
    # ...but HISTORICAL alone (not blocked/pending/superseded) is still
    # claimable as "the historical result", never silently promoted further.
    validate_claim_against_entry(_entry(completion_state="HISTORICAL"))  # must not raise


# --- 4. EXTERNAL_REPLICATION vs SAME_DATASET_HOLDOUT distinction ------------

def test_guard_4_replication_class_is_never_inferred_only_echoed() -> None:
    external = project_for_display(_entry(replication_class="EXTERNAL_REPLICATION"))
    holdout = project_for_display(_entry(replication_class="SAME_DATASET_HOLDOUT"))
    assert external.replication_class_label != holdout.replication_class_label
    assert "independent" in external.replication_class_label.lower()
    assert "not independent" in holdout.replication_class_label.lower()
    # replication_class is a required field on the schema itself (no default
    # exists for a consumer to silently fall back to) — proven in Phase 2's
    # test_subject_n_and_seed_n_are_both_required_independently-style tests;
    # here we additionally confirm the two labels a consumer would render
    # never collapse to the same string for any of the 4 declared classes.
    labels = {
        rc.value: project_for_display(_entry(replication_class=rc.value)).replication_class_label
        for rc in ReplicationClass
    }
    assert len(set(labels.values())) == len(labels)  # all 4 labels distinct


# --- 5. Mixed-protocol / V1-V2 protection ------------------------------------

def test_guard_5_two_arm_narrative_refuses_mixed_protocol_version() -> None:
    v1_leg = _entry(experiment_id="leg-v1", provenance=_provenance("v1", "protocol_v1"))
    v2_leg = _entry(experiment_id="leg-v2", dataset_version="v2", provenance=_provenance("v2", "protocol_v2_seedfix"))
    with pytest.raises(ManifestValidationError) as excinfo:
        build_two_arm_comparison_narrative(v1_leg, v2_leg)
    assert excinfo.value.code == ManifestErrorCode.MIXED_PROTOCOL_VERSION


def test_guard_5_two_arm_narrative_succeeds_for_matched_protocol_version() -> None:
    leg_a = _entry(experiment_id="leg-a")
    leg_b = _entry(experiment_id="leg-b")
    narrative = build_two_arm_comparison_narrative(leg_a, leg_b)
    assert "leg-a" in narrative and "leg-b" in narrative
    assert "Complete (canonical)" in narrative


# --- 6. Metric directionality ------------------------------------------------

def test_guard_6_benefit_sign_is_correct_for_both_directions_via_projection() -> None:
    lower_is_better = project_for_display(_entry(
        metric={"name": "x_mae", "kind": "regression", "directionality": "lower_is_better", "unit": "u"},
        primary_result={"mean": 0.6, "sd": None, "n": None, "display": "0.6"},
        control_result={"mean": 1.0, "sd": None, "n": None, "display": "1.0"},
    ))
    higher_is_better = project_for_display(_entry(
        metric={"name": "x_f1", "kind": "classification", "directionality": "higher_is_better", "unit": "u"},
        primary_result={"mean": 0.8, "sd": None, "n": None, "display": "0.8"},
        control_result={"mean": 0.6, "sd": None, "n": None, "display": "0.6"},
    ))
    # Both cases: candidate is genuinely better than control by 0.2, regardless
    # of raw arithmetic sign of (primary - control) — a consumer must see a
    # POSITIVE benefit in both cases, never a sign flip from misapplied direction.
    assert lower_is_better.benefit_value == pytest.approx(0.4)
    assert higher_is_better.benefit_value == pytest.approx(0.2)
    assert lower_is_better.benefit_value > 0
    assert higher_is_better.benefit_value > 0


# --- 7. Cross-target comparison prohibition ----------------------------------

def test_guard_7_two_arm_narrative_refuses_cross_target_comparison() -> None:
    hr_entry = _entry(experiment_id="hr-exp", target="heart_rate_mae")
    sleep_entry = _entry(experiment_id="sleep-exp", target="sleep_stage_macro_f1")
    with pytest.raises(ManifestValidationError) as excinfo:
        build_two_arm_comparison_narrative(hr_entry, sleep_entry)
    assert excinfo.value.code == ManifestErrorCode.CROSS_TARGET_COMPARISON_PROHIBITED


# --- 8. Missing/malformed manifest fail-closed (at the consumer boundary) ---

def test_guard_8_consumer_never_sees_partial_display_projections_on_failure(tmp_path) -> None:
    """A frontend/paper consumer that blindly iterates `envelope.display_projections`
    must get an EMPTY list on any ingestion failure — never a partially-built,
    possibly-corrupt projection list."""
    from app.research.future_science_ingestion import FutureScienceManifestReader

    reader_missing = FutureScienceManifestReader(repository_root=tmp_path)
    envelope_missing = reader_missing.status()
    assert envelope_missing.display_projections == []
    assert envelope_missing.manifest is None

    manifest_dir = tmp_path / "results"
    manifest_dir.mkdir()
    (manifest_dir / "stage2_4_science_completion_manifest.json").write_text("{broken", encoding="utf-8")
    reader_broken = FutureScienceManifestReader(repository_root=tmp_path)
    envelope_broken = reader_broken.status()
    assert envelope_broken.display_projections == []
    assert envelope_broken.manifest is None


def test_guard_8_required_full_evidence_claim_rejects_bounded_diagnostic() -> None:
    with pytest.raises(ManifestValidationError) as excinfo:
        validate_claim_against_entry(_entry(completion_state="BOUNDED_DIAGNOSTIC"), required_full_evidence=True)
    assert excinfo.value.code == ManifestErrorCode.CLAIM_EVIDENCE_INSUFFICIENT
    # Same entry is fine for a claim that does NOT demand full-protocol evidence.
    validate_claim_against_entry(_entry(completion_state="BOUNDED_DIAGNOSTIC"), required_full_evidence=False)


@pytest.mark.parametrize(
    "state",
    [
        ExperimentCompletionState.BLOCKED_BY_DATA_ACCESS,
        ExperimentCompletionState.PENDING,
        ExperimentCompletionState.SUPERSEDED,
    ],
)
def test_guard_8_claim_validator_always_rejects_incomplete_evidence_states(state: ExperimentCompletionState) -> None:
    with pytest.raises(ManifestValidationError) as excinfo:
        validate_claim_against_entry(_entry(completion_state=state.value))
    assert excinfo.value.code == ManifestErrorCode.CLAIM_EVIDENCE_INSUFFICIENT
