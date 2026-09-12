"""Adversarial tests for the Codex parent-science-audit delta-hardening
guards added to the future-science manifest ingestion pipeline: H-02
(capacity-confounded PPG headline), HMC split provenance consistency, raw
data provenance overstatement (GalaxyPPG/LBNP), and the closed
status-vocabulary allowlist (no self-promotion to an arbitrary CANONICAL
label).

All fixtures are synthetic and TEST-ONLY (governing prompt §49) — never
written into results/.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.research.future_science_ingestion import (
    ManifestErrorCode,
    ManifestValidationError,
    assert_not_governing_marginal_evidence,
    assert_raw_provenance_not_overstated,
    assert_split_provenance_consistent,
    build_two_arm_comparison_narrative,
    project_for_display,
    validate_claim_against_entry,
    validate_manifest_dict,
)
from app.schemas.experiment_manifest import ExperimentManifestEntry


def _valid_entry(**overrides) -> dict:
    entry = {
        "experiment_id": "test-experiment-alpha",
        "experiment_version": "V1",
        "dataset": "test-dataset",
        "dataset_version": "v1",
        "target": "test_target_mae",
        "baseline_config": "A",
        "candidate_config": "B",
        "control_config": "control",
        "metric": {
            "name": "test_metric_mae",
            "kind": "regression",
            "directionality": "lower_is_better",
            "unit": "unit",
        },
        "biological_subject_n": 5,
        "optimization_seed_n": 5,
        "primary_result": {"mean": 1.23, "sd": 0.1, "n": 5, "display": "1.23 unit"},
        "control_result": {"mean": 1.5, "sd": 0.1, "n": 5, "display": "1.50 unit"},
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
            "declared_split_source": None,
            "raw_data_provenance_level": None,
            "environment_provenance_status": "INCOMPLETE",
            "provenance_warnings": [],
        },
        "checkpoint_manifest": None,
        "safe_claims": [],
        "unsafe_claims": [],
        "limitations": [],
    }
    entry.update(overrides)
    return entry


def _valid_manifest(*entries: dict) -> dict:
    return {
        "schema_version": "1.0.0",
        "manifest_id": "test-manifest",
        "generated_by": "test-fixture",
        "generated_at": None,
        "entries": list(entries),
    }


# --- H-02: PPG capacity-confounded headline guard ---------------------------


def test_historical_capacity_confounded_entry_is_never_headline_eligible() -> None:
    manifest = validate_manifest_dict(_valid_manifest(_valid_entry(completion_state="HISTORICAL_CAPACITY_CONFOUNDED")))
    projection = project_for_display(manifest.entries[0])
    assert projection.is_headline_eligible is False
    assert projection.benefit_value is None
    assert "Historical" in projection.completion_state_label


def test_assert_not_governing_marginal_evidence_rejects_confounded_entry() -> None:
    manifest = validate_manifest_dict(_valid_manifest(_valid_entry(completion_state="HISTORICAL_CAPACITY_CONFOUNDED")))
    with pytest.raises(ManifestValidationError) as exc_info:
        assert_not_governing_marginal_evidence(manifest.entries[0])
    assert exc_info.value.code == ManifestErrorCode.CAPACITY_CONFOUNDED_CANNOT_GOVERN


def test_assert_not_governing_marginal_evidence_allows_complete_entry() -> None:
    manifest = validate_manifest_dict(_valid_manifest(_valid_entry(completion_state="COMPLETE")))
    assert_not_governing_marginal_evidence(manifest.entries[0])  # must not raise


def test_two_arm_narrative_refuses_confounded_entry_as_either_arm() -> None:
    confounded = _valid_entry(experiment_id="old-confounded", completion_state="HISTORICAL_CAPACITY_CONFOUNDED")
    current = _valid_entry(experiment_id="capacity-controlled")
    manifest = validate_manifest_dict(_valid_manifest(confounded, current))
    with pytest.raises(ManifestValidationError) as exc_info:
        build_two_arm_comparison_narrative(manifest.entries[0], manifest.entries[1])
    assert exc_info.value.code == ManifestErrorCode.CAPACITY_CONFOUNDED_CANNOT_GOVERN


def test_claim_validator_rejects_confounded_and_noncanonical_states() -> None:
    for state in ("HISTORICAL_CAPACITY_CONFOUNDED", "NONCANONICAL"):
        manifest = validate_manifest_dict(_valid_manifest(_valid_entry(completion_state=state)))
        with pytest.raises(ManifestValidationError) as exc_info:
            validate_claim_against_entry(manifest.entries[0])
        assert exc_info.value.code == ManifestErrorCode.CLAIM_EVIDENCE_INSUFFICIENT


# --- HMC split provenance consistency ---------------------------------------


def test_mismatched_declared_and_embedded_split_source_fails_closed() -> None:
    entry_dict = _valid_entry(
        provenance={
            **_valid_entry()["provenance"],
            "declared_split_source": "results/hmc_split_stage2_pilot.json",
            "subject_split_manifest_path": "results/hmc_split_stage3_bounded_n7.json",
        }
    )
    manifest = validate_manifest_dict(_valid_manifest(entry_dict))
    with pytest.raises(ManifestValidationError) as exc_info:
        assert_split_provenance_consistent(manifest.entries[0])
    assert exc_info.value.code == ManifestErrorCode.PROVENANCE_MISMATCH


def test_matching_declared_and_embedded_split_source_passes() -> None:
    entry_dict = _valid_entry(
        provenance={
            **_valid_entry()["provenance"],
            "declared_split_source": "results/hmc_split_stage3_bounded_n7.json",
            "subject_split_manifest_path": "results/hmc_split_stage3_bounded_n7.json",
        }
    )
    manifest = validate_manifest_dict(_valid_manifest(entry_dict))
    assert_split_provenance_consistent(manifest.entries[0])  # must not raise


def test_one_sided_declared_split_source_is_not_flagged_as_mismatch() -> None:
    """No claim was made about the embedded path, so there is nothing to
    disagree with — this is a missing-provenance concern, not a mismatch."""
    entry_dict = _valid_entry(
        provenance={
            **_valid_entry()["provenance"],
            "declared_split_source": "results/hmc_split_stage3_bounded_n7.json",
            "subject_split_manifest_path": None,
        }
    )
    manifest = validate_manifest_dict(_valid_manifest(entry_dict))
    assert_split_provenance_consistent(manifest.entries[0])  # must not raise


# --- Raw data provenance level (GalaxyPPG/LBNP) -----------------------------


@pytest.mark.parametrize(
    "level", ["OFFICIAL_METADATA_VERIFIED", "LOCAL_RAW_REPORTED_ONLY", "TRAINING_PENDING"]
)
def test_non_file_verified_levels_cannot_be_claimed_as_file_verified(level: str) -> None:
    entry_dict = _valid_entry(provenance={**_valid_entry()["provenance"], "raw_data_provenance_level": level})
    manifest = validate_manifest_dict(_valid_manifest(entry_dict))
    with pytest.raises(ManifestValidationError) as exc_info:
        assert_raw_provenance_not_overstated(manifest.entries[0], claimed_as_file_verified=True)
    assert exc_info.value.code == ManifestErrorCode.RAW_PROVENANCE_OVERSTATED


def test_actual_file_verified_level_can_be_claimed_as_file_verified() -> None:
    entry_dict = _valid_entry(provenance={**_valid_entry()["provenance"], "raw_data_provenance_level": "ACTUAL_FILE_VERIFIED"})
    manifest = validate_manifest_dict(_valid_manifest(entry_dict))
    assert_raw_provenance_not_overstated(manifest.entries[0], claimed_as_file_verified=True)  # must not raise


def test_reported_only_level_survives_into_display_projection() -> None:
    """The REPORTED_ONLY status must reach the display layer intact, not be
    silently upgraded or dropped."""
    entry_dict = _valid_entry(provenance={**_valid_entry()["provenance"], "raw_data_provenance_level": "LOCAL_RAW_REPORTED_ONLY"})
    manifest = validate_manifest_dict(_valid_manifest(entry_dict))
    projection = project_for_display(manifest.entries[0])
    assert projection.raw_data_provenance_level == "LOCAL_RAW_REPORTED_ONLY"


# --- Environment / cache provenance -----------------------------------------


def test_missing_environment_provenance_defaults_to_incomplete_not_silently_complete() -> None:
    entry_dict = _valid_entry()  # fixture's provenance already omits an explicit override
    manifest = validate_manifest_dict(_valid_manifest(entry_dict))
    assert manifest.entries[0].provenance.environment_provenance_status == "INCOMPLETE"


def test_provenance_warnings_are_never_hidden_in_display_projection() -> None:
    entry_dict = _valid_entry(
        provenance={
            **_valid_entry()["provenance"],
            "provenance_warnings": ["relies on weak filename-only cache binding"],
        }
    )
    manifest = validate_manifest_dict(_valid_manifest(entry_dict))
    projection = project_for_display(manifest.entries[0])
    assert "relies on weak filename-only cache binding" in projection.provenance_warnings


# --- Status vocabulary: no self-promotion to an arbitrary CANONICAL label ---


def test_source_artifact_cannot_self_promote_to_arbitrary_canonical_label() -> None:
    """CANONICAL_UNCHANGED is not in ExperimentCompletionState — a manifest
    declaring it must fail schema validation (UNKNOWN_STATUS), never be
    silently accepted as a stronger-than-declared state."""
    bad = _valid_entry(completion_state="CANONICAL_UNCHANGED")
    with pytest.raises(ManifestValidationError) as exc_info:
        validate_manifest_dict(_valid_manifest(bad))
    assert exc_info.value.code == ManifestErrorCode.UNKNOWN_STATUS


def test_source_artifact_cannot_self_promote_to_science_complete() -> None:
    bad = _valid_entry(completion_state="SCIENCE_COMPLETE")
    with pytest.raises(ManifestValidationError) as exc_info:
        validate_manifest_dict(_valid_manifest(bad))
    assert exc_info.value.code == ManifestErrorCode.UNKNOWN_STATUS


@pytest.mark.parametrize(
    "state",
    ["NONCANONICAL", "REPORTED_COMPLETE", "VERIFIED_COMPLETE", "ACCEPTED_FOR_SCOPE", "HISTORICAL_CAPACITY_CONFOUNDED"],
)
def test_new_allowlisted_states_validate_successfully(state: str) -> None:
    """The new vocabulary members ARE legitimate — only undeclared strings
    are rejected."""
    entry = _valid_entry(completion_state=state)
    manifest = validate_manifest_dict(_valid_manifest(entry))
    assert manifest.entries[0].completion_state == state


def test_pydantic_direct_construction_also_rejects_unknown_status() -> None:
    entry_dict = _valid_entry()
    entry_dict["completion_state"] = "CANONICAL_UNCHANGED"
    with pytest.raises(ValidationError):
        ExperimentManifestEntry.model_validate(entry_dict)
