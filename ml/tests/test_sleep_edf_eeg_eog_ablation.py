"""Tests for the Sleep-EDF EEG vs EEG+EOG marginal-value ablation (Day 7
primary progression)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "backend"))

RESULTS_PATH = REPO_ROOT / "results" / "sleep_edf_eeg_eog_ablation.json"
REPRO_PATH = REPO_ROOT / "results" / "sleep_edf_eeg_eog_ablation_reproducibility.json"
SPLIT_PATH = REPO_ROOT / "ml" / "experiments" / "sleep_edf_eeg_eog_ablation" / "subject_split.json"
RAW_DIR = REPO_ROOT / "datasets" / "sleep-edfx" / "raw"

requires_results = pytest.mark.skipif(not RESULTS_PATH.exists(), reason="Sleep-EDF ablation not run yet")
requires_raw = pytest.mark.skipif(not RAW_DIR.exists(), reason="Sleep-EDF raw data not present")


# --- Structural (no training needed) ----------------------------------------


def test_frozen_split_disjoint_and_18_subjects():
    split = json.loads(SPLIT_PATH.read_text())
    train, val, test = set(split["train"]), set(split["val"]), set(split["test"])
    assert not (train & val) and not (train & test) and not (val & test)
    assert len(train) + len(val) + len(test) == 18


def test_eog_channel_is_not_eeg_channel():
    from ml.datasets.sleep_edf import EEG_CHANNEL, EOG_CHANNEL
    assert EEG_CHANNEL != EOG_CHANNEL
    assert "EOG" in EOG_CHANNEL and "EEG" not in EOG_CHANNEL


def test_baseline_and_candidate_share_architecture_class():
    from ml.train_sleep_edf_eeg_eog_ablation import SleepStageClassifier

    m1 = SleepStageClassifier(in_channels=1)
    m2 = SleepStageClassifier(in_channels=2)
    assert type(m1.encoder) is type(m2.encoder)
    assert type(m1.head) is type(m2.head)


def test_capacity_difference_is_small_and_disclosed():
    from ml.train_sleep_edf_eeg_eog_ablation import SleepStageClassifier

    n1 = sum(p.numel() for p in SleepStageClassifier(1).parameters())
    n2 = sum(p.numel() for p in SleepStageClassifier(2).parameters())
    relative_diff = (n2 - n1) / n2
    assert relative_diff < 0.05, f"capacity difference should be small (< 5%), got {relative_diff:.4f} - avoid repeating the PPG-DaLiA confound"


def test_original_single_channel_loader_unmodified():
    """Guards against the Day 7 additive loader functions breaking the
    original single-channel training path."""
    from ml.datasets.sleep_edf import EPOCH_SECONDS, STAGE_NAMES, _STAGE_MAP

    assert EPOCH_SECONDS == 30.0
    assert STAGE_NAMES == ("Wake", "N1", "N2", "N3", "REM")
    assert _STAGE_MAP["Sleep stage W"] == 0


@requires_raw
def test_multi_channel_loader_real_data_smoke():
    from ml.datasets.sleep_edf import EEG_CHANNEL, EOG_CHANNEL, load_dataset_windows_multi

    x, y, subj_idx, prefixes = load_dataset_windows_multi(RAW_DIR, channels=(EEG_CHANNEL, EOG_CHANNEL), subject_ids=["SC4001"])
    assert x.shape[1] == 2
    assert x.shape[2] == 3000  # 30s * 100Hz
    assert len(y) > 0
    assert set(y.tolist()).issubset({0, 1, 2, 3, 4})


@requires_raw
def test_loader_rejects_missing_subject():
    from ml.datasets.sleep_edf import EEG_CHANNEL, load_dataset_windows_multi

    with pytest.raises(FileNotFoundError):
        load_dataset_windows_multi(RAW_DIR, channels=(EEG_CHANNEL,), subject_ids=["SC9999"])


# --- Result-dependent --------------------------------------------------------


@requires_results
def test_results_use_frozen_split():
    results = json.loads(RESULTS_PATH.read_text())
    assert results["frozen_protocol"]["subject_split"] == json.loads(SPLIT_PATH.read_text())


@requires_results
def test_results_all_seeds_present():
    results = json.loads(RESULTS_PATH.read_text())
    for config in ("baseline_eeg_only", "candidate_eeg_plus_eog"):
        for seed in (42, 43, 44, 45, 46):
            assert f"seed{seed}" in results["runs"][config]


@requires_results
def test_results_macro_f1_in_valid_range():
    results = json.loads(RESULTS_PATH.read_text())
    for config in ("baseline_eeg_only", "candidate_eeg_plus_eog"):
        for seed_key, report in results["runs"][config].items():
            assert 0.0 <= report["macro_f1"] <= 1.0


@requires_results
def test_results_class_weights_computed_from_train_only():
    """Structural check: class weighting code path uses train_y, never test_y."""
    import inspect
    from ml.train_sleep_edf_eeg_eog_ablation import main

    source = inspect.getsource(main)
    assert "compute_class_weight(\"balanced\", classes=np.arange(len(STAGE_NAMES)), y=train_y)" in source


@requires_results
def test_results_checkpoint_manifest_complete():
    results = json.loads(RESULTS_PATH.read_text())
    assert len(results["checkpoint_manifest"]) == 10  # 2 configs x 5 seeds


@requires_results
def test_results_aggregate_matches_seed_values():
    results = json.loads(RESULTS_PATH.read_text())
    seeds = results["frozen_protocol"]["seeds"]
    baseline_f1 = [results["runs"]["baseline_eeg_only"][f"seed{s}"]["macro_f1"] for s in seeds]
    recomputed_mean = sum(baseline_f1) / len(baseline_f1)
    assert results["aggregate"]["baseline_macro_f1"]["mean"] == pytest.approx(recomputed_mean, abs=1e-9)


@requires_results
def test_results_reports_sample_sd_ddof1():
    results = json.loads(RESULTS_PATH.read_text())
    assert "sd_sample_ddof1" in results["aggregate"]["baseline_macro_f1"]


@requires_results
def test_no_class_collapsing_five_classes_preserved():
    results = json.loads(RESULTS_PATH.read_text())
    for config in ("baseline_eeg_only", "candidate_eeg_plus_eog"):
        report = results["runs"][config]["seed42"]
        assert len(report["per_class_f1"]) == 5


@pytest.mark.skipif(not REPRO_PATH.exists(), reason="reproducibility check not run yet")
def test_reproducibility_all_ok():
    report = json.loads(REPRO_PATH.read_text())
    assert report["all_ok"] is True
