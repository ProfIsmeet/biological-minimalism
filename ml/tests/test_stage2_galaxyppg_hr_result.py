"""Contract tests for the real GalaxyPPG HR external-replication result.
No performance thresholds - the result is genuinely mixed and must not be
silently reversed or hidden by a future edit."""

from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
RESULT = json.loads((REPO_ROOT / "results" / "galaxyppg_hr_external_replication_stage2.json").read_text())
PER_SUBJECT = json.loads((REPO_ROOT / "results" / "galaxyppg_hr_per_subject_stage2.json").read_text())
ELIGIBILITY = json.loads((REPO_ROOT / "results" / "galaxyppg_eligibility_stage2.json").read_text())


def test_all_24_participants_eligible():
    assert ELIGIBILITY["n_eligible"] == 24


def test_scope_disclosure_present():
    assert "BOUNDED_TO_SINGLE_FOLD" in RESULT["scope_disclosure"]


def test_capacity_a_cap_close_to_b_c():
    pc = RESULT["parameter_counts"]
    residual_fraction = (pc["B_and_C"] - pc["A_cap"]) / pc["B_and_C"]
    assert residual_fraction < 0.02  # matches PPG-DaLiA capacity-control precedent (~0.77%)


def test_reference_is_ecg_r_peaks_not_device_hr():
    assert "R-peak" in RESULT["reference"]
    assert "device-derived" not in RESULT["reference"] or "never" in RESULT["reference"]


def test_hr_normalization_fit_on_train_only():
    assert RESULT["hr_normalization"]["fit_on"] == "train split only"


def test_five_seeds_present():
    assert set(RESULT["runs"]["A_cap"].keys()) == {f"seed{s}" for s in (42, 43, 44, 45, 46)}


def test_subject_level_sign_reversal_disclosed_not_hidden():
    summary = PER_SUBJECT["per_subject_summary"]
    a_to_b = [v["A_to_B_mean"] for v in summary.values()]
    assert any(v > 0 for v in a_to_b) and any(v < 0 for v in a_to_b)


def test_all_four_test_subjects_present_in_per_subject_result():
    split = json.loads((REPO_ROOT / "results" / "galaxyppg_split_stage2_single_fold.json").read_text())
    assert set(PER_SUBJECT["per_subject_summary"].keys()) == set(split["test"])


def test_no_subject_excluded_post_hoc():
    # all 4 test subjects from the frozen split must appear, even the outlier (P01)
    split = json.loads((REPO_ROOT / "results" / "galaxyppg_split_stage2_single_fold.json").read_text())
    for pid in split["test"]:
        assert pid in PER_SUBJECT["per_subject_summary"]
