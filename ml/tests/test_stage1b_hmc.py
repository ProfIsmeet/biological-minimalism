"""Stage-1B contract tests for the HMC protocol freeze. Contract-only, no
dataset download, no performance thresholds (Section 38)."""

from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
PROTOCOL = json.loads((REPO_ROOT / "results" / "hmc_protocol_stage1b.json").read_text())
AUDIT = json.loads((REPO_ROOT / "results" / "hmc_actual_file_audit_stage1b.json").read_text())


def test_one_recording_per_subject_confirmed():
    assert "CONFIRMED one recording per unique subject" in AUDIT["actual_file_facts"]["unique_subject_grouping"]


def test_uniform_sample_rate_confirmed_not_assumed():
    assert "CONFIRMED" in AUDIT["actual_file_facts"]["sample_rate_uniformity"]
    assert "256" in AUDIT["actual_file_facts"]["sample_rate_uniformity"]


def test_eeg_derivation_frozen_and_not_reconsidered():
    sel = PROTOCOL["eeg_channel_selection"]
    assert sel["frozen_choice"] == "C4/M1"
    assert sel["not_reconsidered_after_results"] is True
    assert len(sel["candidates_considered"]) >= 3


def test_eog_polarity_fixed():
    eog = PROTOCOL["eog_derivation"]
    assert eog["polarity"] == "E1 minus E2, fixed (not sign-flipped per subject)"


def test_control_c_preserves_subject_identity_and_partition():
    c = PROTOCOL["control_C"]
    assert "subject identity" in c["preserves"]
    assert "partition assignment" in c["preserves"]
    assert c["labels_shuffled"] is False
    assert c["cross_subject_mixing"] is False


def test_stage_mapping_frozen_five_classes():
    assert PROTOCOL["stage_mapping"]["frozen_classes"] == ["W", "N1", "N2", "N3", "REM"]


def test_split_uses_recording_as_subject_unit():
    assert PROTOCOL["split_strategy"]["unit"] == "recording_id (== subject, confirmed 1:1 this sprint)"


def test_leakage_channels_excluded():
    excl = PROTOCOL["leakage_exclusions"]
    assert "chin EMG" in excl
    assert "ECG lead II" in excl


def test_classification_go_with_dependency():
    assert PROTOCOL["classification"] == "GO_WITH_DEPENDENCY"
    assert "dependency" in PROTOCOL["workflow_dependency"].lower()


def test_no_performance_thresholds_in_protocol():
    text = json.dumps(PROTOCOL).lower()
    for banned in ["f1 >", "eog helps", "beats baseline"]:
        assert banned not in text
