"""Regression test for the real BLOCKER found this sprint: eligibility must
reject subjects whose reference ECG is too corrupted for R-peak detection,
not just check file presence/timestamp overlap."""

from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
ELIGIBILITY = json.loads((REPO_ROOT / "results" / "galaxyppg_eligibility_stage2.json").read_text())


def test_eligibility_includes_r_peaks_per_min_field():
    for e in ELIGIBILITY["table"]:
        if e["bvp_present"] and e["acc_present"] and e["ecg_present"]:
            assert "r_peaks_per_min" in e


def test_known_corrupted_subjects_excluded():
    excluded_ids = {e["participant_id"] for e in ELIGIBILITY["table"] if not e["eligible"]}
    # real subjects confirmed this sprint to have near-zero detectable R-peaks
    for pid in ("P03", "P07", "P15", "P19", "P22"):
        assert pid in excluded_ids, f"{pid} should be excluded (corrupted reference ECG)"


def test_eligible_count_is_18_not_24():
    assert ELIGIBILITY["n_eligible"] == 18


def test_healthy_reference_subjects_still_eligible():
    eligible_ids = {e["participant_id"] for e in ELIGIBILITY["table"] if e["eligible"]}
    for pid in ("P02", "P09"):
        assert pid in eligible_ids


def test_exclusion_reason_distinguishes_ecg_quality_from_missing_files():
    for e in ELIGIBILITY["table"]:
        if not e["eligible"] and e.get("r_peaks_per_min") is not None and e["r_peaks_per_min"] < 40.0:
            assert "R-peak detection" in e["exclusion_reason"]
            assert "not a low heart rate" in e["exclusion_reason"]
