"""Contract tests for the corrected GalaxyPPG result (post reference-ECG-
quality BLOCKER fix). This is a genuinely positive result - tests verify
it is not silently weakened or the fix silently reverted, without
asserting a specific performance threshold."""

from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
RESULT = json.loads((REPO_ROOT / "results" / "galaxyppg_hr_corrected_eligibility_stage3.json").read_text())
PER_SUBJECT = json.loads((REPO_ROOT / "results" / "galaxyppg_hr_corrected_per_subject_stage3.json").read_text())
SPLIT = json.loads((REPO_ROOT / "results" / "galaxyppg_split_stage3_corrected_eligibility.json").read_text())


def test_split_uses_18_eligible_subjects():
    assert SPLIT["n_eligible"] == 18
    assert len(SPLIT["train"]) + len(SPLIT["val"]) + len(SPLIT["test"]) == 18


def test_corrupted_subjects_not_in_split():
    all_ids = set(SPLIT["train"] + SPLIT["val"] + SPLIT["test"])
    for pid in ("P01", "P03", "P07", "P15", "P19", "P22"):
        assert pid not in all_ids


def test_five_seeds_present():
    assert set(RESULT["runs"]["A_cap"].keys()) == {f"seed{s}" for s in (42, 43, 44, 45, 46)}


def test_per_subject_all_three_test_subjects_present():
    assert set(PER_SUBJECT["per_subject_summary"].keys()) == set(SPLIT["test"])


def test_scope_still_disclosed_as_bounded():
    assert "BOUNDED_TO_SINGLE_FOLD" in RESULT["scope_disclosure"]
