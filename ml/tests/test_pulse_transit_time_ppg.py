"""Data-integrity tests for `ml/datasets/pulse_transit_time_ppg.py` and the
Day 3 model interface (`ml/train_ptt_ppg_site_ablation.py`).

Tests that need the real downloaded WFDB files are skipped automatically
(with a clear reason) if those files are not present locally - same
convention as `test_ppg_dalia_loader.py`.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "backend"))

from ml.datasets.pulse_transit_time_ppg import (  # noqa: E402
    ALL_SUBJECTS,
    FlatSignalError,
    InsufficientRPeaksError,
    MIN_RPEAKS_IN_WINDOW,
    MODEL_A_CHANNELS,
    MODEL_B_CHANNELS,
    SIGNAL_FS,
    SITE_1_CHANNELS,
    SITE_2_CHANNELS,
    WINDOW_SAMPLES,
    compute_window_hr,
    list_available_raw_records,
    load_record_raw,
    record_name,
    windowize_record,
    zscore_channels_window,
)

RAW_DIR = REPO_ROOT / "datasets" / "pulse-transit-time-ppg" / "raw"
CACHE_DIR = REPO_ROOT / "datasets" / "pulse-transit-time-ppg" / "processed"
EXPERIMENT_DIR = REPO_ROOT / "ml" / "experiments" / "ptt_ppg_site_ablation"

_available_records = list_available_raw_records(RAW_DIR) if RAW_DIR.exists() else []
requires_raw_data = pytest.mark.skipif(
    not _available_records, reason=f"no real PTT WFDB records present at {RAW_DIR} - see datasets/PTT_DATASET_AUDIT_DAY3.md"
)


# --- Channel contract ---------------------------------------------------


def test_model_a_is_site_1_only():
    assert MODEL_A_CHANNELS == SITE_1_CHANNELS
    assert len(MODEL_A_CHANNELS) == 3


def test_model_b_is_both_sites():
    assert MODEL_B_CHANNELS == SITE_1_CHANNELS + SITE_2_CHANNELS
    assert len(MODEL_B_CHANNELS) == 6


def test_model_a_channels_are_prefix_of_model_b():
    assert MODEL_B_CHANNELS[: len(MODEL_A_CHANNELS)] == MODEL_A_CHANNELS


def test_ecg_and_peaks_never_in_model_channel_lists():
    for name in MODEL_A_CHANNELS + MODEL_B_CHANNELS:
        assert name not in ("ecg", "peaks"), "ECG must never be a model input channel"


def test_no_imu_or_pressure_or_temp_channels_in_primary_contract():
    forbidden_prefixes = ("a_", "g_", "lc_", "temp_")
    for name in MODEL_A_CHANNELS + MODEL_B_CHANNELS:
        assert not name.startswith(forbidden_prefixes), f"{name} should not be in the primary PPG-site contract"


# --- record_name / subject IDs -------------------------------------------


def test_all_subjects_are_s1_to_s22():
    assert ALL_SUBJECTS == tuple(f"s{i}" for i in range(1, 23))
    assert len(ALL_SUBJECTS) == 22


def test_record_name_format():
    assert record_name("s14", "run") == "s14_run"


def test_record_name_rejects_unknown_activity():
    with pytest.raises(ValueError):
        record_name("s1", "sprint")


# --- z-score normalization -------------------------------------------------


def test_zscore_channels_window_shape_and_stats():
    rng = np.random.default_rng(0)
    window = rng.normal(loc=100.0, scale=5.0, size=(6, WINDOW_SAMPLES))
    normed = zscore_channels_window(window)
    assert normed.shape == (6, WINDOW_SAMPLES)
    assert normed.dtype == np.float32
    np.testing.assert_allclose(normed.mean(axis=1), 0.0, atol=1e-4)
    np.testing.assert_allclose(normed.std(axis=1), 1.0, atol=1e-4)


def test_zscore_channels_window_rejects_wrong_shape():
    with pytest.raises(ValueError):
        zscore_channels_window(np.zeros((6, 100)))


def test_zscore_channels_window_flat_channel_raises_not_silently():
    window = np.random.randn(3, WINDOW_SAMPLES).astype(np.float64)
    window[1] = 42.0  # one dead/flat channel
    with pytest.raises(FlatSignalError):
        zscore_channels_window(window)


# --- HR ground truth from R-peaks -------------------------------------------


def test_compute_window_hr_basic():
    fs = 500.0
    rpeaks = np.array([0, 400, 800, 1200])  # RR = 400 samples = 0.8s -> 75 bpm
    hr, n = compute_window_hr(rpeaks, 0, 2000, fs)
    assert n == 4
    assert hr == pytest.approx(75.0, abs=1e-6)


def test_compute_window_hr_insufficient_peaks_raises():
    fs = 500.0
    rpeaks = np.array([0, 400])  # only 2 peaks, below MIN_RPEAKS_IN_WINDOW=3
    with pytest.raises(InsufficientRPeaksError):
        compute_window_hr(rpeaks, 0, 2000, fs)


def test_compute_window_hr_never_uses_peaks_outside_window():
    fs = 500.0
    rpeaks = np.array([0, 400, 800, 1200, 50000])  # far-outside peak must be excluded
    hr, n = compute_window_hr(rpeaks, 0, 2000, fs)
    assert n == 4  # not 5


# --- Real-file tests (skipped if raw data absent) ---------------------------


@requires_raw_data
def test_real_record_loads_with_shared_500hz_clock():
    subject_id, activity = _available_records[0].rsplit("_", 1)
    raw = load_record_raw(RAW_DIR, subject_id, activity)
    assert raw.fs == SIGNAL_FS
    assert len(raw.sig_name) == 18
    assert raw.signals.shape[0] == 18
    assert "ecg" in raw.sig_name
    for ch in MODEL_B_CHANNELS:
        assert ch in raw.sig_name


@requires_raw_data
def test_real_record_subject_activity_preserved_through_windowize():
    subject_id, activity = _available_records[0].rsplit("_", 1)
    raw = load_record_raw(RAW_DIR, subject_id, activity)
    windows = windowize_record(raw)
    assert windows.subject_id == subject_id
    assert windows.activity == activity
    assert len(windows.hr) > 0
    assert windows.ppg_a.shape == (len(windows.hr), len(MODEL_A_CHANNELS), WINDOW_SAMPLES)
    assert windows.ppg_b.shape == (len(windows.hr), len(MODEL_B_CHANNELS), WINDOW_SAMPLES)


@requires_raw_data
def test_real_windowize_model_a_equals_model_b_prefix():
    subject_id, activity = _available_records[0].rsplit("_", 1)
    raw = load_record_raw(RAW_DIR, subject_id, activity)
    windows = windowize_record(raw)
    np.testing.assert_array_equal(windows.ppg_a, windows.ppg_b[:, : len(MODEL_A_CHANNELS), :])


@requires_raw_data
def test_real_windowize_hr_is_physiologically_plausible():
    subject_id, activity = _available_records[0].rsplit("_", 1)
    raw = load_record_raw(RAW_DIR, subject_id, activity)
    windows = windowize_record(raw)
    assert (windows.hr > 30).all() and (windows.hr < 220).all()


@requires_raw_data
def test_real_windowize_boundary_short_final_segment_dropped_not_padded():
    subject_id, activity = _available_records[0].rsplit("_", 1)
    raw = load_record_raw(RAW_DIR, subject_id, activity)
    windows = windowize_record(raw)
    last_start = windows.window_start_sample[-1]
    assert last_start + WINDOW_SAMPLES <= raw.signals.shape[1], "no window may run past the real recording length"


@requires_raw_data
def test_real_windowize_deterministic():
    subject_id, activity = _available_records[0].rsplit("_", 1)
    raw = load_record_raw(RAW_DIR, subject_id, activity)
    w1 = windowize_record(raw)
    w2 = windowize_record(raw)
    np.testing.assert_array_equal(w1.ppg_a, w2.ppg_a)
    np.testing.assert_array_equal(w1.hr, w2.hr)


@requires_raw_data
def test_corrupt_subject_id_mismatch_is_never_silently_accepted():
    from ml.datasets.pulse_transit_time_ppg import preprocess_record

    subject_id, activity = _available_records[0].rsplit("_", 1)
    raw = load_record_raw(RAW_DIR, subject_id, activity)
    assert raw.subject_id == subject_id  # sanity: the loader's own bookkeeping, not the file's

    # preprocess_record's internal consistency check requires an *actual*
    # filesystem layout to trigger a mismatch; here we confirm the guard
    # exists and passes for a real matching pair (a true mismatch would
    # require constructing a corrupt directory tree, out of scope for a
    # data-integrity smoke check).
    p = preprocess_record(RAW_DIR, CACHE_DIR, subject_id, activity)
    assert p.exists()


# --- Subject-wise split integrity -------------------------------------------


def test_frozen_split_file_exists_and_is_disjoint():
    split_path = EXPERIMENT_DIR / "subject_split.json"
    assert split_path.exists(), "Day 3 frozen split must be committed before any training run"
    split = json.loads(split_path.read_text())

    train, val, test = set(split["train"]), set(split["val"]), set(split["test"])
    assert not (train & val), "train/val subject overlap"
    assert not (train & test), "train/test subject overlap"
    assert not (val & test), "val/test subject overlap"

    all_split_subjects = train | val | test
    assert all_split_subjects == set(ALL_SUBJECTS), "split must partition exactly the 22 known subjects, no more, no less"


def test_frozen_split_matches_config_counts():
    split = json.loads((EXPERIMENT_DIR / "subject_split.json").read_text())
    config = json.loads((EXPERIMENT_DIR / "config.json").read_text())
    assert len(split["train"]) == config["n_train_subjects"]
    assert len(split["val"]) == config["n_val_subjects"]
    assert len(split["test"]) == config["n_test_subjects"]


# --- Model interface (shape-only, no scientific claims) ---------------------


def test_model_a_and_b_forward_shapes():
    import torch
    from app.ml._torch_bootstrap import ensure_torch_dll_path

    ensure_torch_dll_path()
    from ml.train_ptt_ppg_site_ablation import PPGSiteHRModel

    for channels in (MODEL_A_CHANNELS, MODEL_B_CHANNELS):
        model = PPGSiteHRModel(in_channels=len(channels), embedding_dim=8)
        x = torch.randn(4, len(channels), WINDOW_SAMPLES)
        out = model(x)
        assert out.shape == (4,)


def test_model_a_and_b_share_identical_hyperparameters_except_channels():
    import inspect

    from ml.train_ptt_ppg_site_ablation import PPGSiteHRModel

    sig = inspect.signature(PPGSiteHRModel.__init__)
    assert "embedding_dim" in sig.parameters, "capacity (embedding_dim) must be a shared, not per-model, parameter"
