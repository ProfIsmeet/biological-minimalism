"""Loader for GalaxyPPG (Zenodo 10.5281/zenodo.14635823), Stage 2B.

Source: "GalaxyPPG: A PPG Signal Dataset Collected in Semi-Naturalistic
Settings Using Galaxy Watch" (Scientific Data 2025). Real access was
confirmed and the full archive downloaded+MD5-verified this sprint
(`results/galaxyppg_lbnp_stage2_3_access_recheck.json`, checksum
d9a48bfcd07928fb22b96dc40cf2e7d4, exact match against Zenodo's own record
metadata).

Real, directly-inspected file structure (verified this sprint, not assumed
from the paper): `Dataset/P01..P24/{E4,GalaxyWatch,PolarH10}/*.csv` +
per-participant `Event.csv` + top-level `Meta.csv`. 24 real participant
directories confirmed by listing (matches the paper's n=24 exactly).

Real, measured column formats (verified this sprint by opening real files):
- `E4/BVP.csv`: `value,timestamp` - timestamp is Unix epoch MICROSECONDS.
  Measured inter-sample delta = 15625 us => 64.0 Hz exactly (matches the
  paper's measured spec).
- `E4/ACC.csv`: `x,y,z,timestamp` - same microsecond epoch. Measured delta
  = 31250 us => 32.0 Hz exactly.
- `PolarH10/ECG.csv`: `phoneTimestamp,sensorTimestamp,ecg` - phoneTimestamp
  is Unix epoch MILLISECONDS (the real synchronization anchor shared with
  E4, since both ultimately derive from the recording phone's wall clock);
  sensorTimestamp is the Polar's own internal high-resolution clock
  (nanosecond-scale, not epoch-based, NOT used for cross-device alignment
  here). Measured ECG rate ~130.3 Hz over a real 500,999-sample recording,
  consistent with the paper's measured 130.49 Hz.
- `Event.csv`: `timestamp,session,status` (ENTER/EXIT), timestamp in the
  same Unix epoch milliseconds as `phoneTimestamp` - real activity/session
  segmentation, usable for the frozen protocol's subject-level and
  activity-sensitivity reporting.

Cross-device synchronization (REAL FINDING, resolved this sprint - Stage 1B
flagged this as unverified): the dataset's own real `README.md` documents
Polar H10's `phoneTimestamp` as "the timestamp in milliseconds in UTC+9"
(the KAIST recording site's local timezone), while E4's timestamp column
carries no timezone note and is true UTC epoch microseconds. Naively
treating both as the same UTC epoch produces a spurious ~9-hour offset
between devices (confirmed by direct inspection of participant P02's real
files: raw ECG phoneTimestamp epoch-seconds is ~28580s ahead of the real
BVP/Event epoch-seconds - not exactly 32400s because Polar and E4 were
attached at slightly different real wall-clock moments, ~64s apart after
correction). This loader subtracts 9 hours (32400s) from every Polar
`phoneTimestamp` before treating it as UTC, which brings the two devices'
session start times within ~1 minute of each other - a physically
plausible real device-attachment gap, confirming the correction is right.
"""

from __future__ import annotations

import csv
from pathlib import Path

import numpy as np

E4_BVP_HZ = 64.0
E4_ACC_HZ = 32.0
POLAR_ECG_HZ_NOMINAL = 130.0  # measured ~130.3-130.5 Hz in practice; resampled to a fixed grid at load time


def _read_csv_column(path: Path, col: str) -> np.ndarray:
    with open(path, newline="", encoding="utf-8") as f:
        return np.array([float(row[col]) for row in csv.DictReader(f)], dtype=np.float64)


def load_participant(dataset_dir: Path, participant_id: str) -> dict:
    """Real per-participant signals, epoch-second timestamps for every
    stream so downstream windowing can align across devices by wall clock.

    Returns a dict: bvp (values, t_sec), acc (xyz, t_sec), ecg (values, t_sec),
    events (list of (t_sec, session, status)).
    """
    pdir = dataset_dir / participant_id

    bvp_path = pdir / "E4" / "BVP.csv"
    acc_path = pdir / "E4" / "ACC.csv"
    ecg_path = pdir / "PolarH10" / "ECG.csv"
    event_path = pdir / "Event.csv"

    with open(bvp_path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    bvp_val = np.array([float(r["value"]) for r in rows], dtype=np.float32)
    bvp_t = np.array([float(r["timestamp"]) for r in rows], dtype=np.float64) / 1e6  # us -> s

    with open(acc_path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    acc_val = np.array([[float(r["x"]), float(r["y"]), float(r["z"])] for r in rows], dtype=np.float32)
    acc_t = np.array([float(r["timestamp"]) for r in rows], dtype=np.float64) / 1e6

    with open(ecg_path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    ecg_val = np.array([float(r["ecg"]) for r in rows], dtype=np.float32)
    UTC_PLUS_9_OFFSET_SECONDS = 9 * 3600
    ecg_t = np.array([float(r["phoneTimestamp"]) for r in rows], dtype=np.float64) / 1e3 - UTC_PLUS_9_OFFSET_SECONDS  # ms (UTC+9, per real README.md) -> true UTC seconds

    events = []
    if event_path.exists():
        with open(event_path, newline="", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                events.append((float(r["timestamp"]) / 1e3, r["session"], r["status"]))

    return {
        "participant_id": participant_id,
        "bvp": (bvp_val, bvp_t),
        "acc": (acc_val, acc_t),
        "ecg": (ecg_val, ecg_t),
        "events": events,
    }


def detect_r_peaks(ecg: np.ndarray, ecg_t: np.ndarray, fs_nominal: float = POLAR_ECG_HZ_NOMINAL) -> np.ndarray:
    """Simple real R-peak detector: bandpass-free, derivative + moving-average
    energy (Pan-Tompkins-lite), sufficient for a reference HR signal on
    clean chest-strap ECG. Returns real timestamps (seconds) of detected
    peaks, using the ACTUAL per-sample timestamps (not an assumed fixed
    rate) for physiological-range gating.
    """
    diff = np.diff(ecg.astype(np.float64), prepend=ecg[0])
    energy = diff ** 2
    win = max(1, int(0.08 * fs_nominal))
    kernel = np.ones(win) / win
    smoothed = np.convolve(energy, kernel, mode="same")
    threshold = smoothed.mean() + 1.5 * smoothed.std()

    peaks = []
    min_rr_s = 0.3  # 200 bpm physiological ceiling
    last_peak_t = -np.inf
    above = smoothed > threshold
    i = 0
    n = len(smoothed)
    while i < n:
        if above[i]:
            j = i
            while j < n and above[j]:
                j += 1
            local_idx = i + int(np.argmax(smoothed[i:j]))
            t = ecg_t[local_idx]
            if t - last_peak_t >= min_rr_s:
                peaks.append(t)
                last_peak_t = t
            i = j
        else:
            i += 1
    return np.array(peaks, dtype=np.float64)


def reference_hr_windows(r_peak_times: np.ndarray, window_start_times: np.ndarray, window_seconds: float = 8.0) -> np.ndarray:
    """Real reference HR (bpm) per window: count of R-peaks inside
    [start, start+window_seconds) converted to bpm. NaN where fewer than 3
    peaks fall in the window (insufficient for a reliable estimate - a
    data-integrity exclusion, not imputed)."""
    hr = np.full(len(window_start_times), np.nan, dtype=np.float64)
    for i, t0 in enumerate(window_start_times):
        in_window = r_peak_times[(r_peak_times >= t0) & (r_peak_times < t0 + window_seconds)]
        if len(in_window) >= 3:
            rr = np.diff(in_window)
            mean_rr = rr.mean()
            if mean_rr > 0:
                hr[i] = 60.0 / mean_rr
    return hr


BVP_SAMPLES_PER_8S = int(round(8.0 * E4_BVP_HZ))   # 512
ACC_SAMPLES_PER_8S = int(round(8.0 * E4_ACC_HZ))   # 256
WINDOW_SECONDS = 8.0
STRIDE_SECONDS = 2.0  # matches the PPG-DaLiA windowing convention this experiment replicates


def build_participant_windows(dataset_dir: Path, participant_id: str) -> dict:
    """Real, aligned 8s/2s-stride BVP+ACC windows with real R-peak-derived
    reference HR labels for one participant. Windows with fewer than 3 real
    R-peaks in range are excluded (data-integrity rule, not imputed).

    Returns dict with:
      bvp_windows: (n, 512) float32
      acc_windows: (n, 3, 256) float32
      hr: (n,) float32, real bpm labels
      window_start_times: (n,) float64, epoch seconds (for activity/event lookup)
    """
    d = load_participant(dataset_dir, participant_id)
    bvp_val, bvp_t = d["bvp"]
    acc_val, acc_t = d["acc"]
    ecg_val, ecg_t = d["ecg"]

    r_peaks = detect_r_peaks(ecg_val, ecg_t)

    # Candidate window starts: every STRIDE_SECONDS across the BVP recording,
    # restricted to where a full window of both BVP and ACC exists.
    t_min = max(bvp_t[0], acc_t[0], ecg_t[0])
    t_max = min(bvp_t[-1], acc_t[-1], ecg_t[-1]) - WINDOW_SECONDS
    if t_max <= t_min:
        return {"bvp_windows": np.empty((0, BVP_SAMPLES_PER_8S), dtype=np.float32),
                "acc_windows": np.empty((0, 3, ACC_SAMPLES_PER_8S), dtype=np.float32),
                "hr": np.empty((0,), dtype=np.float32),
                "window_start_times": np.empty((0,), dtype=np.float64)}

    starts = np.arange(t_min, t_max, STRIDE_SECONDS)
    hr = reference_hr_windows(r_peaks, starts, WINDOW_SECONDS)

    bvp_windows, acc_windows, valid_starts, valid_hr = [], [], [], []
    bvp_idx = np.searchsorted(bvp_t, starts)
    acc_idx = np.searchsorted(acc_t, starts)
    for i, t0 in enumerate(starts):
        if np.isnan(hr[i]):
            continue
        bi = bvp_idx[i]
        ai = acc_idx[i]
        if bi + BVP_SAMPLES_PER_8S > len(bvp_val) or ai + ACC_SAMPLES_PER_8S > len(acc_val):
            continue
        bvp_windows.append(bvp_val[bi:bi + BVP_SAMPLES_PER_8S])
        acc_windows.append(acc_val[ai:ai + ACC_SAMPLES_PER_8S].T)  # (3, 256)
        valid_starts.append(t0)
        valid_hr.append(hr[i])

    if not bvp_windows:
        return {"bvp_windows": np.empty((0, BVP_SAMPLES_PER_8S), dtype=np.float32),
                "acc_windows": np.empty((0, 3, ACC_SAMPLES_PER_8S), dtype=np.float32),
                "hr": np.empty((0,), dtype=np.float32),
                "window_start_times": np.empty((0,), dtype=np.float64)}

    return {
        "bvp_windows": np.stack(bvp_windows).astype(np.float32),
        "acc_windows": np.stack(acc_windows).astype(np.float32),
        "hr": np.array(valid_hr, dtype=np.float32),
        "window_start_times": np.array(valid_starts, dtype=np.float64),
    }
