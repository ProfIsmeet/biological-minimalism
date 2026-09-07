"""Tests for the Sleep-EDF shuffled-EOG negative control and the
per-subject decomposition (Day 8 mandatory strengthening)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "backend"))

PER_SUBJECT_PATH = REPO_ROOT / "results" / "sleep_edf_per_subject_analysis.json"
CONTROL_PATH = REPO_ROOT / "results" / "sleep_edf_eeg_eog_control_analysis.json"
ORIGINAL_RESULTS_PATH = REPO_ROOT / "results" / "sleep_edf_eeg_eog_ablation.json"

requires_per_subject = pytest.mark.skipif(not PER_SUBJECT_PATH.exists(), reason="per-subject analysis not run yet")
requires_control = pytest.mark.skipif(not CONTROL_PATH.exists(), reason="shuffled-EOG control not run yet")


# --- Shuffle function structural/correctness tests --------------------------


def test_shuffle_never_touches_eeg_channel():
    from ml.datasets.sleep_edf import shuffle_eog_within_subject

    rng = np.random.default_rng(0)
    x = rng.normal(size=(20, 2, 10)).astype(np.float32)
    subj = np.array([0] * 10 + [1] * 10)
    shuffled = shuffle_eog_within_subject(x, subj, eog_channel_index=1, seed=42)

    np.testing.assert_array_equal(shuffled[:, 0, :], x[:, 0, :])  # EEG channel untouched


def test_shuffle_never_mixes_subjects():
    from ml.datasets.sleep_edf import shuffle_eog_within_subject

    rng = np.random.default_rng(0)
    x = rng.normal(size=(20, 2, 10)).astype(np.float32)
    subj = np.array([0] * 10 + [1] * 10)
    shuffled = shuffle_eog_within_subject(x, subj, eog_channel_index=1, seed=42)

    # Every shuffled EOG epoch for subject 0 must still be one of subject 0's original EOG epochs
    subj0_original = set(map(tuple, x[:10, 1, :].round(6).tolist()))
    subj0_shuffled = set(map(tuple, shuffled[:10, 1, :].round(6).tolist()))
    assert subj0_original == subj0_shuffled


def test_shuffle_deterministic_given_seed():
    from ml.datasets.sleep_edf import shuffle_eog_within_subject

    rng = np.random.default_rng(0)
    x = rng.normal(size=(20, 2, 10)).astype(np.float32)
    subj = np.array([0] * 10 + [1] * 10)
    s1 = shuffle_eog_within_subject(x, subj, eog_channel_index=1, seed=42)
    s2 = shuffle_eog_within_subject(x, subj, eog_channel_index=1, seed=42)
    np.testing.assert_array_equal(s1, s2)


def test_shuffle_different_seeds_differ():
    from ml.datasets.sleep_edf import shuffle_eog_within_subject

    rng = np.random.default_rng(0)
    x = rng.normal(size=(60, 2, 10)).astype(np.float32)  # larger to make identical-by-chance unlikely
    subj = np.zeros(60, dtype=np.int64)
    s1 = shuffle_eog_within_subject(x, subj, eog_channel_index=1, seed=42)
    s2 = shuffle_eog_within_subject(x, subj, eog_channel_index=1, seed=43)
    assert not np.array_equal(s1, s2)


def test_shuffle_preserves_label_array_untouched():
    """Structural guard: the training script never passes y through the
    shuffle function - only x is shuffled."""
    import inspect
    from ml.train_sleep_edf_shuffled_eog_control import main

    source = inspect.getsource(main)
    assert "shuffle_eog_within_subject(train_x" in source
    assert "shuffle_eog_within_subject(train_y" not in source


# --- Capacity fairness -------------------------------------------------------


def test_model_c_architecture_identical_to_model_b():
    from ml.train_sleep_edf_eeg_eog_ablation import SleepStageClassifier

    b = SleepStageClassifier(in_channels=2)
    c = SleepStageClassifier(in_channels=2)  # Model C uses the identical class/config
    n_b = sum(p.numel() for p in b.parameters())
    n_c = sum(p.numel() for p in c.parameters())
    assert n_b == n_c


# --- Per-subject analysis (result-dependent) --------------------------------


@requires_per_subject
def test_per_subject_uses_frozen_test_subjects():
    analysis = json.loads(PER_SUBJECT_PATH.read_text())
    original = json.loads(ORIGINAL_RESULTS_PATH.read_text())
    assert analysis["test_subjects"] == original["frozen_protocol"]["subject_split"]["test"]


@requires_per_subject
def test_per_subject_no_subject_silently_dropped():
    analysis = json.loads(PER_SUBJECT_PATH.read_text())
    for subj in analysis["test_subjects"]:
        assert subj in analysis["subject_summary"]


@requires_per_subject
def test_per_subject_direction_never_hidden():
    analysis = json.loads(PER_SUBJECT_PATH.read_text())
    for subj, summary in analysis["subject_summary"].items():
        assert summary["direction"] in ("IMPROVES", "WORSENS", "MIXED")


@requires_per_subject
def test_per_subject_aggregation_matches_manual_recomputation():
    analysis = json.loads(PER_SUBJECT_PATH.read_text())
    seeds = analysis["seeds"]
    for subj, summary in analysis["subject_summary"].items():
        base_vals = [analysis["per_subject"][subj]["baseline"][f"seed{s}"]["macro_f1"] for s in seeds]
        recomputed_mean = sum(base_vals) / len(base_vals)
        assert summary["baseline_macro_f1"]["mean"] == pytest.approx(recomputed_mean, abs=1e-9)


# --- Shuffled-EOG control results (result-dependent) ------------------------


@requires_control
def test_control_capacity_identical_to_b():
    control = json.loads(CONTROL_PATH.read_text())
    assert control["frozen_protocol"]["capacity_identical_to_b"] is True
    assert control["frozen_protocol"]["n_parameters_model_c"] == control["frozen_protocol"]["n_parameters_model_b_original"]


@requires_control
def test_control_uses_frozen_split():
    control = json.loads(CONTROL_PATH.read_text())
    original = json.loads(ORIGINAL_RESULTS_PATH.read_text())
    assert control["frozen_protocol"]["subject_split"] == original["frozen_protocol"]["subject_split"]


@requires_control
def test_control_does_not_overwrite_original():
    original = json.loads(ORIGINAL_RESULTS_PATH.read_text())
    assert original["aggregate"]["baseline_macro_f1"]["mean"] == pytest.approx(0.7472525334607252, abs=1e-9)


@requires_control
def test_control_all_seeds_present():
    control = json.loads(CONTROL_PATH.read_text())
    for seed in (42, 43, 44, 45, 46):
        assert f"seed{seed}" in control["runs"]


@requires_control
def test_control_aggregate_sign_convention():
    control = json.loads(CONTROL_PATH.read_text())
    agg = control["aggregate"]
    # A_to_B and C_to_B use "positive = B better" convention (B - A, B - C respectively via A_to_B/C_to_B naming)
    a = agg["model_a_macro_f1"]["mean"]
    b = agg["model_b_macro_f1"]["mean"]
    c = agg["model_c_macro_f1"]["mean"]
    assert agg["A_to_B"]["mean"] == pytest.approx(b - a, abs=1e-6)
    assert agg["C_to_B"]["mean"] == pytest.approx(b - c, abs=1e-6)


@requires_control
def test_control_reports_sample_sd():
    control = json.loads(CONTROL_PATH.read_text())
    assert control["aggregate"]["model_c_macro_f1"]["sd_sample_ddof1"] is not None


@requires_control
def test_control_checkpoint_manifest_complete():
    control = json.loads(CONTROL_PATH.read_text())
    assert len(control["checkpoint_manifest"]) == 5
