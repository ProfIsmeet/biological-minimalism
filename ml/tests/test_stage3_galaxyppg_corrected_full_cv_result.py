"""Regression tests for the completed GalaxyPPG corrected full 6-fold CV
result: fold completeness, subject coverage, window-weighted vs
participant-level aggregate agreement, no sign reversal under
leave-one-out sensitivity, and the final classification."""

from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def _load():
    return json.loads((REPO_ROOT / "results" / "galaxyppg_corrected_full_cv_result.json").read_text())


def test_all_six_folds_present_with_no_duplicate_subjects():
    d = _load()
    assert len(d["folds"]) == 6
    all_test_subjects = []
    for fk, fd in d["folds"].items():
        subs = fd.get("test_subjects")
        assert subs is not None and len(subs) == 3
        all_test_subjects.extend(subs)
    assert len(all_test_subjects) == 18
    assert len(set(all_test_subjects)) == 18


def test_stale_aggregate_key_renamed_with_disclosure():
    d = _load()
    assert "aggregate_across_all_24_subjects" not in d
    assert "aggregate_across_all_18_eligible_subjects" in d
    assert d["aggregate_across_all_18_eligible_subjects"]["A_cap_mae"]["n"] == 18
    assert "aggregate_key_name_correction_note" in d


def test_window_weighted_and_participant_level_agree_in_sign_and_magnitude():
    d = _load()
    ww = d["window_weighted_aggregate"]["pooled"]
    participant = d["aggregate_across_all_18_eligible_subjects"]
    assert ww["A_to_B"] > 0
    assert ww["C_to_B"] > 0
    assert participant["A_to_B"]["mean"] > 0
    assert participant["C_to_B"]["mean"] > 0
    # aggregation methods should not disagree by more than 0.1 bpm
    assert abs(ww["A_to_B"] - participant["A_to_B"]["mean"]) < 0.1
    assert abs(ww["C_to_B"] - participant["C_to_B"]["mean"]) < 0.1


def test_no_sign_reversal_under_leave_one_out():
    d = _load()
    hs = d["heterogeneity_and_sensitivity"]
    assert hs["leave_one_out_sensitivity_A_to_B"]["sign_reversal_on_exclusion"] is False
    assert hs["leave_one_out_sensitivity_C_to_B"]["sign_reversal_on_exclusion"] is False


def test_majority_subjects_favor_B_but_heterogeneity_disclosed():
    d = _load()
    hs = d["heterogeneity_and_sensitivity"]
    assert hs["n_subjects_favor_B_A_to_B"] > hs["n_subjects_total"] / 2
    assert hs["n_subjects_favor_B_C_to_B"] > hs["n_subjects_total"] / 2
    # heterogeneity must be honestly disclosed, not hidden
    assert hs["n_subjects_favor_B_A_to_B"] < hs["n_subjects_total"]


def test_final_classification_is_valid_enum_value():
    d = _load()
    assert d["final_classification"] in {
        "EXTERNAL_REPLICATION_SUPPORTIVE",
        "MIXED",
        "NEGATIVE",
        "UNRESOLVED",
        "CORRECTED_FULL_CV_BLOCKED",
    }
