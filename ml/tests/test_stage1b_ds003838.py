"""Stage-1B contract tests for the ds003838 protocol freeze. Contract-only."""

from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
PROTOCOL = json.loads((REPO_ROOT / "results" / "ds003838_protocol_stage1b.json").read_text())
AUDIT = json.loads((REPO_ROOT / "results" / "ds003838_metadata_audit_stage1b.json").read_text())

VERIFIED_CHANNELS = AUDIT["eeg_metadata"]["channel_names_verified"]
MUSE_SET = ["AF7", "AF8", "TP9", "TP10"]


def test_frozen_sparse_channels_present_in_verified_montage():
    for ch in MUSE_SET:
        assert ch in VERIFIED_CHANNELS


def test_frozen_channel_set_matches_protocol():
    assert PROTOCOL["sparse_channel_selection"]["frozen_set"] == MUSE_SET
    assert PROTOCOL["sparse_channel_selection"]["not_reconsidered_after_results"] is True


def test_cohort_uses_65_not_86():
    assert PROTOCOL["cohort"]["eligible_subjects"] == 65
    assert AUDIT["cohort_reconciliation"]["recruited_participants"] == 86
    assert AUDIT["cohort_reconciliation"]["eeg_usable_count_confirmed"] == 65


def test_two_independent_sources_agree_on_65():
    text = AUDIT["cohort_reconciliation"]["eeg_bearing_participants_per_readme"]
    assert "AGREE exactly" in text


def test_load_labels_5_9_13_correctly_encoded_and_ordinal_note_present():
    assert "5" in PROTOCOL["target"] and "9" in PROTOCOL["target"] and "13" in PROTOCOL["target"]
    assert "ordinal error" in PROTOCOL["secondary_metrics"][-1]


def test_no_outcome_based_channel_selection():
    rationale = PROTOCOL["sparse_channel_selection"]["rationale"]
    assert "not by testing which channels perform best" in rationale


def test_control_shuffles_only_extra_channels_not_sparse_baseline():
    c = PROTOCOL["feature_sets"]["C"]
    assert "never across subjects" in c
    assert "A's 4 channels remain real/aligned in C" in c


def test_model_fairness_shared_encoder_near_identical_params():
    design = PROTOCOL["model_fairness"]["design"]
    assert "nearly IDENTICAL" in design or "identical" in design.lower()


def test_raw_trigger_code_excluded_from_features():
    assert "raw trigger-code string as a feature" in PROTOCOL["leakage_exclusions"]


def test_notch_frequency_verified_50hz_not_assumed_60():
    assert PROTOCOL["preprocessing"]["notch_hz"] == "50 Hz (PowerLineFrequency confirmed as 50 in the real eeg.json sidecar this sprint - NOT 60 Hz, verified not assumed)"


def test_classification_go_with_limitations():
    assert PROTOCOL["classification"] == "GO_WITH_LIMITATIONS"
