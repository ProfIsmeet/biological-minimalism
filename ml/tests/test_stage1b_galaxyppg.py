"""Stage-1B contract tests for the GalaxyPPG protocol freeze.

These validate the FROZEN CONTRACT (results/galaxyppg_protocol_stage1b.json),
not any performance outcome - no dataset download or training occurs here,
per Section 38 (no performance tests at this stage).
"""

from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
PROTOCOL = json.loads((REPO_ROOT / "results" / "galaxyppg_protocol_stage1b.json").read_text())
AUDIT = json.loads((REPO_ROOT / "results" / "galaxyppg_actual_file_audit_stage1b.json").read_text())
LEAKAGE = json.loads((REPO_ROOT / "results" / "dataset_expansion_leakage_matrix_stage1b.json").read_text())


def test_reference_is_raw_ecg_not_device_hr():
    assert "raw ecg" in PROTOCOL["reference"].lower()
    assert LEAKAGE["GalaxyPPG_HR"]["polar_h10_device_hr"] == "EXCLUDE_LEAKAGE"
    assert LEAKAGE["GalaxyPPG_HR"]["galaxy_watch5_device_hr"] == "EXCLUDE_LEAKAGE"


def test_reference_signal_marked_reference_only_not_input():
    assert LEAKAGE["GalaxyPPG_HR"]["polar_h10_raw_ecg"] == "TARGET_REFERENCE_ONLY"


def test_split_is_subject_grouped_not_epoch_random():
    assert "grouped" in PROTOCOL["split_strategy"]["decision"].lower()
    assert "subject" in PROTOCOL["split_strategy"]["decision"].lower()


def test_control_c_never_crosses_subjects():
    control = PROTOCOL["control_C"]
    assert "within-subject" in control
    assert "never a different subject" in control


def test_capacity_control_is_architecture_matched_and_disclosed():
    cc = PROTOCOL["capacity_control"]
    assert cc["method"] == "Architecture-matched dual encoder"
    assert "disclosed" in cc["detail"]


def test_all_three_required_signals_reported_complete_for_all_24():
    completeness = AUDIT["actual_file_facts"]["per_device_completeness"]
    assert completeness["e4_bvp"] == "24/24 (complete)"
    assert completeness["e4_acc"] == "24/24 (complete, no completeness caveat reported)"
    assert completeness["polar_h10_ecg"] == "24/24 (complete) - the reference signal this project actually needs"


def test_eligible_cohort_is_all_24():
    assert AUDIT["usable_cohort_for_this_projects_experiment"]["n_eligible"] == 24


def test_primary_metric_frozen_before_training():
    assert PROTOCOL["primary_metric"] == "MAE (bpm)"
    assert "RMSE (bpm)" in PROTOCOL["secondary_metrics"]


def test_no_performance_thresholds_present_anywhere_in_protocol():
    text = json.dumps(PROTOCOL).lower()
    for banned in ["mae <", "f1 >", "candidate > baseline", "replication succeeds", "imu helps"]:
        assert banned not in text


def test_classification_is_go():
    assert PROTOCOL["classification"] == "GO"
