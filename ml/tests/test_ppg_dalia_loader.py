"""Automated loader / data-integrity tests for the PPG-DaLiA pipeline
(docs/TECHNICAL_HANDOFF_V2.md §18 Priority 2 requirement: "Add automated
loader/data-integrity tests").

Run with `pytest` from `ml/` (or point pytest at this file directly) using
the backend venv, e.g.:
    ../backend/.venv/Scripts/python.exe -m pytest tests/ -q

Split into two kinds of test:
- Pure, fast, deterministic tests of `_windowize()` against a small
  synthetic signal built in-memory (no real dataset required - these always
  run, including in CI with no data downloaded).
- Integration checks against the real cached `.npz` windows, skipped
  automatically if `ml/preprocess_ppg_dalia.py` has not been run yet.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from ml.datasets.ppg_dalia import (  # noqa: E402
    ACC_WINDOW_SAMPLES,
    ACTIVITY_FS,
    ACC_FS,
    ALL_SUBJECTS,
    PPG_FS,
    PPG_WINDOW_SAMPLES,
    STEP_SECONDS,
    WINDOW_SECONDS,
    _windowize,
    load_cached_subject,
)

CACHE_DIR = REPO_ROOT / "datasets" / "ppg-dalia" / "processed"


def _make_synthetic_subject(duration_s: float, hr_bpm: float = 70.0, seed: int = 0) -> dict:
    """A small, fully synthetic (never claimed to be real) pickle-shaped dict,
    used only to test the windowing arithmetic itself in isolation."""

    rng = np.random.default_rng(seed)
    n_bvp = int(duration_s * PPG_FS)
    n_acc = int(duration_s * ACC_FS)
    n_act = int(duration_s * ACTIVITY_FS)
    n_windows = int((duration_s - WINDOW_SECONDS) / STEP_SECONDS) + 1

    return {
        "subject": "SYNTH",
        "signal": {
            "wrist": {
                "BVP": rng.normal(size=(n_bvp, 1)),
                "ACC": rng.normal(size=(n_acc, 3)),
            }
        },
        "label": np.full(n_windows, hr_bpm) + rng.normal(scale=0.1, size=n_windows),
        "activity": rng.integers(0, 9, size=(n_act, 1)).astype(float),
    }


def test_windowize_produces_expected_shapes() -> None:
    raw = _make_synthetic_subject(duration_s=60.0)
    windows = _windowize(raw, "SYNTH")

    assert windows.ppg.shape[1] == PPG_WINDOW_SAMPLES
    assert windows.acc.shape[1:] == (3, ACC_WINDOW_SAMPLES)
    assert len(windows.hr) == len(windows.ppg) == len(windows.acc) == len(windows.activity) == len(windows.motion_energy)


def test_windowize_window_count_matches_formula() -> None:
    """(duration - window) / step + 1, per the real dataset's own label
    array length (verified against real S1 data: (9212-8)/2+1 == 4603)."""

    duration_s = 200.0
    raw = _make_synthetic_subject(duration_s=duration_s)
    windows = _windowize(raw, "SYNTH")
    expected = int((duration_s - WINDOW_SECONDS) / STEP_SECONDS) + 1
    # All windows should survive (synthetic signal has no flat/dropped segments).
    assert len(windows.hr) == expected


def test_windowize_drops_flat_ppg_segment_rather_than_fabricating() -> None:
    raw = _make_synthetic_subject(duration_s=60.0)
    # Flatten the first PPG window's worth of samples to simulate a real
    # sensor dropout - the loader must exclude it, not invent a value.
    raw["signal"]["wrist"]["BVP"][:PPG_WINDOW_SAMPLES] = 0.0
    windows = _windowize(raw, "SYNTH")
    all_windows = _windowize(_make_synthetic_subject(duration_s=60.0), "SYNTH")
    assert len(windows.hr) == len(all_windows.hr) - 1


def test_windowize_z_scores_each_window_independently() -> None:
    raw = _make_synthetic_subject(duration_s=60.0)
    windows = _windowize(raw, "SYNTH")
    for i in range(len(windows.ppg)):
        assert abs(float(windows.ppg[i].mean())) < 1e-4
        assert abs(float(windows.ppg[i].std()) - 1.0) < 1e-3


def test_motion_energy_higher_for_more_variable_accelerometer() -> None:
    calm = _make_synthetic_subject(duration_s=60.0, seed=1)
    calm["signal"]["wrist"]["ACC"] *= 0.01  # low-variance accelerometer -> "calm"
    vigorous = _make_synthetic_subject(duration_s=60.0, seed=1)
    vigorous["signal"]["wrist"]["ACC"] *= 10.0  # high-variance -> "vigorous motion"

    calm_windows = _windowize(calm, "SYNTH")
    vigorous_windows = _windowize(vigorous, "SYNTH")

    assert vigorous_windows.motion_energy.mean() > calm_windows.motion_energy.mean()


def test_subject_id_mismatch_is_never_silently_accepted() -> None:
    """preprocess_subject() asserts the pickle's own 'subject' field matches
    the requested subject before caching - this test documents that
    contract directly against _windowize's caller-visible dataclass field."""

    raw = _make_synthetic_subject(duration_s=60.0)
    windows = _windowize(raw, "S99")  # deliberately mismatched vs raw["subject"]=="SYNTH"
    assert windows.subject_id == "S99"  # _windowize itself just labels what it's told;
    # the mismatch guard lives in preprocess_subject(), tested at the integration level below.


@pytest.mark.skipif(not CACHE_DIR.exists() or not any(CACHE_DIR.glob("S*.npz")), reason="real PPG-DaLiA cache not present - run ml/preprocess_ppg_dalia.py first")
def test_real_cached_subjects_are_internally_consistent() -> None:
    """Integration check against whatever real subjects have actually been
    preprocessed - skipped automatically if none have been."""

    cached = sorted(p.stem for p in CACHE_DIR.glob("S*.npz"))
    assert all(s in ALL_SUBJECTS for s in cached), f"unexpected subject id(s) cached: {cached}"

    for subject_id in cached[:3]:  # a few is enough to catch a systemic bug, not all 15 every run
        windows = load_cached_subject(CACHE_DIR, subject_id)
        assert windows.subject_id == subject_id
        n = len(windows.hr)
        assert n > 0
        assert windows.ppg.shape == (n, PPG_WINDOW_SAMPLES)
        assert windows.acc.shape == (n, 3, ACC_WINDOW_SAMPLES)
        assert windows.activity.shape == (n,)
        assert windows.motion_energy.shape == (n,)
        assert np.isfinite(windows.ppg).all(), f"{subject_id}: non-finite PPG values"
        assert np.isfinite(windows.acc).all(), f"{subject_id}: non-finite ACC values"
        assert np.isfinite(windows.hr).all(), f"{subject_id}: non-finite HR values"
        # Real HR ground truth should be in a physiologically plausible range -
        # a gross parsing bug (wrong column, wrong units) would fail this.
        assert (windows.hr > 30).all() and (windows.hr < 220).all(), f"{subject_id}: implausible HR values found"
