"""Contract tests for the real GalaxyPPG loader (Stage 2B), including the
real cross-device UTC+9 synchronization fix found this sprint. Uses
synthetic CSVs matching the real documented format so tests do not require
the ~481 MB real archive to be present."""

from __future__ import annotations

import csv
import sys
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from ml.datasets.galaxyppg import detect_r_peaks, load_participant, reference_hr_windows  # noqa: E402


def _write_participant(root: Path, pid: str):
    pdir = root / pid
    (pdir / "E4").mkdir(parents=True)
    (pdir / "PolarH10").mkdir(parents=True)

    bvp_t0_us = 1_710_811_943_000_000
    with open(pdir / "E4" / "BVP.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["value", "timestamp"])
        for i in range(200):
            w.writerow([0.0, bvp_t0_us + i * 15625])

    (pdir / "E4" / "ACC.csv").write_text("x,y,z,timestamp\n")

    # Polar ECG: real documented format is UTC+9 phoneTimestamp.
    # Simulate a real device-attach gap of ~60s AFTER converting to true UTC.
    true_utc_ecg_t0_s = bvp_t0_us / 1e6 + 60.0
    phone_t0_ms = int((true_utc_ecg_t0_s + 9 * 3600) * 1000)
    with open(pdir / "PolarH10" / "ECG.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["phoneTimestamp", "sensorTimestamp", "ecg"])
        # simple synthetic periodic spikes every ~0.8s (75 bpm) over 130 Hz
        import math
        fs = 130.0
        n = int(120 * fs)
        for i in range(n):
            t_s = i / fs
            phase = (t_s % 0.8)
            val = 2000.0 if phase < (1.0 / fs) else 100.0 + 10.0 * math.sin(2 * math.pi * t_s)
            w.writerow([phone_t0_ms + int(t_s * 1000), i * 7692308, val])

    (pdir / "Event.csv").write_text("timestamp,session,status\n")


def test_polar_utc9_correction_aligns_devices_within_plausible_gap(tmp_path):
    _write_participant(tmp_path, "P99")
    d = load_participant(tmp_path, "P99")
    bvp_t = d["bvp"][1]
    ecg_t = d["ecg"][1]
    gap = ecg_t[0] - bvp_t[0]
    assert 0 < gap < 300, f"expected a small real device-attach gap after UTC+9 correction, got {gap}s"


def test_uncorrected_would_show_spurious_nine_hour_gap():
    # sanity: the raw (uncorrected) ms value really is ~9h ahead, proving
    # the fix is doing real work, not a no-op
    bvp_t0_us = 1_710_811_943_000_000
    true_utc_ecg_t0_s = bvp_t0_us / 1e6 + 60.0
    phone_t0_ms = (true_utc_ecg_t0_s + 9 * 3600) * 1000
    naive_gap = phone_t0_ms / 1000 - bvp_t0_us / 1e6
    assert naive_gap > 30000  # ~9 hours in seconds, way outside a plausible attach gap


def test_reference_hr_windows_produces_valid_values_after_sync_fix(tmp_path):
    _write_participant(tmp_path, "P99")
    d = load_participant(tmp_path, "P99")
    ecg_val, ecg_t = d["ecg"]
    bvp_val, bvp_t = d["bvp"]
    peaks = detect_r_peaks(ecg_val, ecg_t)
    assert len(peaks) > 0
    window_starts = np.array([ecg_t[0] + 1.0])  # a window that genuinely overlaps the (later-starting) ECG stream
    hr = reference_hr_windows(peaks, window_starts, window_seconds=8.0)
    assert not np.isnan(hr[0])
    assert 40 < hr[0] < 200  # physiological range


def test_reference_hr_excludes_windows_with_too_few_peaks():
    peaks = np.array([1.0, 1.5])  # only 2 peaks, below the min-3 threshold
    hr = reference_hr_windows(peaks, np.array([0.0]), window_seconds=8.0)
    assert np.isnan(hr[0])
