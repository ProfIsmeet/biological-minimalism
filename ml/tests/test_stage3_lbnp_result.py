"""Contract tests for the real LBNP thoracic EIS result. No performance
thresholds - this is a real negative result and must not be silently
reversed or hidden."""

from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
RESULT = json.loads((REPO_ROOT / "results" / "lbnp_thoracic_eis_stage3.json").read_text())


def test_eligible_cohort_is_12_not_16():
    assert RESULT["n_subjects"] == 12
    assert "12/16" in RESULT["real_eligibility_finding"]


def test_negative_result_not_hidden():
    agg = RESULT["aggregate"]
    assert agg["A_minus_B_mean"] < 0
    assert agg["n_subjects_favoring_B_over_A"] < agg["n_subjects_total"] / 2


def test_all_12_subjects_present_in_deltas():
    assert len(RESULT["per_subject_deltas"]) == 12


def test_target_is_real_stage_not_synthesized():
    assert "step-function" in RESULT["target"]


def test_c_control_uses_within_subject_derangement():
    src = (REPO_ROOT / "ml" / "train_lbnp_thoracic_eis.py").read_text()
    assert "deranged_eis" in src
    assert "no fixed points" in src or "perm == np.arange" in src


def test_no_test_subject_normalization_leakage():
    src = (REPO_ROOT / "ml" / "train_lbnp_thoracic_eis.py").read_text()
    assert "X_tr.mean(axis=0)" in src
    assert "inner_train" in src
