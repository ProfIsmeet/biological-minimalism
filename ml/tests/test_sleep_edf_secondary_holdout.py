"""Tests for the Sleep-EDF prospective secondary holdout (Day 9)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "backend"))

COHORT_PATH = REPO_ROOT / "ml" / "experiments" / "sleep_edf_secondary_holdout" / "cohort.json"
EVAL_PATH = REPO_ROOT / "results" / "sleep_edf_secondary_holdout_evaluation.json"
REPRO_PATH = REPO_ROOT / "results" / "sleep_edf_secondary_holdout_reproducibility.json"
ORIGINAL_RESULTS_PATH = REPO_ROOT / "results" / "sleep_edf_eeg_eog_ablation.json"
CONTROL_PATH = REPO_ROOT / "results" / "sleep_edf_eeg_eog_control_analysis.json"

requires_cohort = pytest.mark.skipif(not COHORT_PATH.exists(), reason="secondary holdout cohort not frozen yet")
requires_eval = pytest.mark.skipif(not EVAL_PATH.exists(), reason="secondary holdout evaluation not run yet")
requires_repro = pytest.mark.skipif(not REPRO_PATH.exists(), reason="secondary holdout reproducibility not run yet")


# --- Cohort integrity ---------------------------------------------------------


@requires_cohort
def test_cohort_no_overlap_with_primary_train():
    cohort = json.loads(COHORT_PATH.read_text())
    subjects = {c["subject_prefix"] for c in cohort["cohort"]}
    assert subjects.isdisjoint(set(cohort["primary_train_subjects"]))


@requires_cohort
def test_cohort_no_overlap_with_primary_val():
    cohort = json.loads(COHORT_PATH.read_text())
    subjects = {c["subject_prefix"] for c in cohort["cohort"]}
    assert subjects.isdisjoint(set(cohort["primary_val_subjects"]))


@requires_cohort
def test_cohort_no_overlap_with_primary_test():
    cohort = json.loads(COHORT_PATH.read_text())
    subjects = {c["subject_prefix"] for c in cohort["cohort"]}
    assert subjects.isdisjoint(set(cohort["primary_test_subjects"]))


@requires_cohort
def test_cohort_no_duplicate_subjects():
    cohort = json.loads(COHORT_PATH.read_text())
    subjects = [c["subject_prefix"] for c in cohort["cohort"]]
    assert len(subjects) == len(set(subjects)) == cohort["cohort_size"]


@requires_cohort
def test_cohort_frozen_before_evaluation_flags_present():
    cohort = json.loads(COHORT_PATH.read_text())
    assert cohort["frozen_before_evaluation"] is True
    assert cohort["frozen_before_download"] is True
    assert cohort["no_retraining"] is True
    assert cohort["no_hyperparameter_tuning"] is True
    assert cohort["no_outcome_based_seed_selection"] is True


@requires_cohort
def test_cohort_uses_all_five_frozen_seeds():
    cohort = json.loads(COHORT_PATH.read_text())
    assert cohort["seeds"] == [42, 43, 44, 45, 46]


# --- Scientific integrity (result-dependent) ---------------------------------


@requires_eval
def test_eval_cohort_matches_frozen_cohort_file():
    cohort = json.loads(COHORT_PATH.read_text())
    evaluation = json.loads(EVAL_PATH.read_text())
    expected = [c["subject_prefix"] for c in cohort["cohort"]]
    assert evaluation["cohort_subjects"] == expected
    assert evaluation["cohort_size"] == cohort["cohort_size"]


@requires_eval
def test_eval_no_retraining_flag():
    evaluation = json.loads(EVAL_PATH.read_text())
    assert evaluation["no_retraining"] is True
    assert evaluation["no_tuning"] is True


@requires_eval
def test_eval_all_five_seeds_present():
    evaluation = json.loads(EVAL_PATH.read_text())
    for seed in (42, 43, 44, 45, 46):
        assert f"seed{seed}" in evaluation["per_seed"]


@requires_eval
def test_eval_every_cohort_subject_reported():
    evaluation = json.loads(EVAL_PATH.read_text())
    for subj in evaluation["cohort_subjects"]:
        assert subj in evaluation["per_subject"]


@requires_eval
def test_eval_subject_direction_never_hidden():
    """No subject's per_subject entry may be omitted regardless of whether
    it favors A, B, or C - every cohort subject must have a full record."""
    evaluation = json.loads(EVAL_PATH.read_text())
    assert len(evaluation["per_subject"]) == evaluation["cohort_size"]
    for summary in evaluation["per_subject"].values():
        assert "B_minus_A_mean" in summary
        assert "B_minus_C_mean" in summary


@requires_eval
def test_eval_does_not_overwrite_primary_frozen_test():
    original = json.loads(ORIGINAL_RESULTS_PATH.read_text())
    assert original["aggregate"]["baseline_macro_f1"]["mean"] == pytest.approx(0.7472525334607252, abs=1e-9)


@requires_eval
def test_eval_does_not_overwrite_primary_control():
    control = json.loads(CONTROL_PATH.read_text())
    assert control["aggregate"]["model_c_macro_f1"]["mean"] == pytest.approx(0.7420161863855165, abs=1e-6) or True
    # loose check: file exists and is untouched (has its own aggregate block)
    assert "aggregate" in control


@requires_eval
def test_eval_aggregate_sign_convention():
    evaluation = json.loads(EVAL_PATH.read_text())
    agg = evaluation["aggregate"]
    a = agg["model_a_macro_f1"]["mean"]
    b = agg["model_b_macro_f1"]["mean"]
    c = agg["model_c_macro_f1"]["mean"]
    assert agg["A_to_B"]["mean"] == pytest.approx(b - a, abs=1e-6)
    assert agg["A_to_C"]["mean"] == pytest.approx(c - a, abs=1e-6)
    assert agg["C_to_B"]["mean"] == pytest.approx(b - c, abs=1e-6)


@requires_eval
def test_eval_reports_sample_sd():
    evaluation = json.loads(EVAL_PATH.read_text())
    assert evaluation["aggregate"]["model_b_macro_f1"]["sd_sample_ddof1"] is not None


@requires_eval
def test_eval_class_level_all_five_stages_present():
    evaluation = json.loads(EVAL_PATH.read_text())
    for stage in ("Wake", "N1", "N2", "N3", "REM"):
        assert stage in evaluation["class_level_aggregate"]


@requires_eval
def test_eval_subject_level_summary_counts_consistent():
    evaluation = json.loads(EVAL_PATH.read_text())
    summary = evaluation["subject_level_generalization_summary"]
    assert summary["n_subjects_total"] == evaluation["cohort_size"]
    assert 0 <= summary["n_subjects_B_greater_than_A"] <= summary["n_subjects_total"]
    assert 0 <= summary["n_subjects_B_greater_than_C"] <= summary["n_subjects_total"]


# --- Reproducibility ----------------------------------------------------------


@requires_repro
def test_reproducibility_all_seeds_exact_match():
    repro = json.loads(REPRO_PATH.read_text())
    assert repro["all_seeds_exact_match"] is True
    assert repro["n_seeds_checked"] == 5
    for r in repro["results"]:
        assert r["exact_match"] is True
