"""Loader for the PhysioNet Pulse Transit Time PPG Dataset v1.1.0
(Mehrgardt et al., https://doi.org/10.13026/jpan-6n92).

Real, verified structure (Day 3 audit, see docs/PTT_DATASET_AUDIT_DAY3.md):
22 subjects (s1..s22), 3 activities each (sit/walk/run) = 66 WFDB records,
18 signal channels acquired on a single shared 500 Hz clock (ecg, pleth_1-6,
lc_1-2, temp_1-3, a_x/y/z, g_x/y/z), plus a separate .atr annotation file of
manually-verified ECG R-peaks (ANNOTATORS: "atr - manually verified beat
annotations").

This module follows the same conventions as `ml/datasets/ppg_dalia.py`:
never fabricate/interpolate data, raise explicitly on anything ambiguous
(flat signal, insufficient R-peaks, subject/activity mismatch), and keep
raw vs. cached-window responsibilities cleanly separated.

**Ground truth is ECG R-peak-derived heart rate ONLY.** ECG itself is never
returned as a model input channel by `windowize_record` - only its derived
scalar HR label and, for audit purposes, the raw R-peak sample indices.

**The sparse per-activity BP/HR-device/SpO2 metadata in each record's
header is NOT loaded by this module by design** (see docs audit §5-6): it is
two points per ~500s recording and cannot honestly serve as a continuous
window-level label. If a future experiment wants it, read it directly from
the .hea comment line - do not synthesize a continuous label from it here.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

# --- Frozen constants (Day 3 audit) -----------------------------------------

SIGNAL_FS = 500.0  # shared sample rate for ALL 18 .dat channels - verified
# directly from real .hea files (single `fs` field for the whole record) and
# cross-checked against the real CSV `time` column (2ms spacing). No
# resampling is required anywhere in this module.

ALL_SUBJECTS: tuple[str, ...] = tuple(f"s{i}" for i in range(1, 23))  # s1..s22
ACTIVITIES: tuple[str, ...] = ("sit", "walk", "run")  # exact official names

# Real channel names as they appear in the .hea `sig_name` list, verified
# against a downloaded header. Site 1 = distal phalanx, site 2 = proximal
# phalanx of the left index finger (README "Methods"/"Data Description").
SITE_1_CHANNELS: tuple[str, ...] = ("pleth_1", "pleth_2", "pleth_3")  # red, IR, green
SITE_2_CHANNELS: tuple[str, ...] = ("pleth_4", "pleth_5", "pleth_6")  # red, IR, green

# Model A / Model B channel contracts - frozen here, BEFORE any training run.
# See docs/MODEL_CONTRACT_PTT_HR.md for the full rationale.
MODEL_A_CHANNELS: tuple[str, ...] = SITE_1_CHANNELS
MODEL_B_CHANNELS: tuple[str, ...] = SITE_1_CHANNELS + SITE_2_CHANNELS

WINDOW_SECONDS = 8.0
STEP_SECONDS = 2.0
WINDOW_SAMPLES = int(round(WINDOW_SECONDS * SIGNAL_FS))  # 4000
STEP_SAMPLES = int(round(STEP_SECONDS * SIGNAL_FS))  # 1000

# A window's HR label requires at least this many R-peaks inside the window
# (i.e. at least MIN_RPEAKS_IN_WINDOW - 1 real RR intervals) to compute a
# mean instantaneous HR that isn't dominated by a single noisy interval.
# Real per-record beat counts audited Day 3 (s1: 613-767 beats / ~500s,
# i.e. ~1.2-1.5 beats/sec) make this comfortably satisfiable for an 8s
# window under every activity observed so far.
MIN_RPEAKS_IN_WINDOW = 3

FLAT_STD_THRESHOLD = 1e-8


class FlatSignalError(ValueError):
    """Raised when a window's signal has ~zero variance - refuse to
    fabricate a normalized value for a dead/disconnected channel."""


class InsufficientRPeaksError(ValueError):
    """Raised when a window does not contain enough R-peaks to compute an
    honest HR label - the window must be dropped, never fabricated."""


@dataclass(frozen=True)
class RawRecord:
    subject_id: str
    activity: str
    record_name: str
    fs: float
    sig_name: list[str]
    signals: np.ndarray  # (n_channels, n_samples), channel order == sig_name
    rpeak_samples: np.ndarray  # 1D int array, sample indices of annotated R-peaks


@dataclass(frozen=True)
class RecordWindows:
    subject_id: str
    activity: str
    record_name: str
    window_start_sample: np.ndarray  # (n_windows,) int
    ppg_a: np.ndarray  # (n_windows, len(MODEL_A_CHANNELS), WINDOW_SAMPLES) float32
    ppg_b: np.ndarray  # (n_windows, len(MODEL_B_CHANNELS), WINDOW_SAMPLES) float32
    hr: np.ndarray  # (n_windows,) float32, ECG-R-peak-derived mean HR (bpm)
    n_rpeaks_in_window: np.ndarray  # (n_windows,) int - provenance/audit only


def record_name(subject_id: str, activity: str) -> str:
    if activity not in ACTIVITIES:
        raise ValueError(f"Unknown activity {activity!r} - must be one of {ACTIVITIES}")
    return f"{subject_id}_{activity}"


def list_available_raw_records(raw_dir: str | Path) -> list[str]:
    """Real check of which (subject, activity) WFDB triplets are actually
    present locally (all three of .hea/.dat/.atr) - never assumes all
    66 records exist just because the dataset nominally has them."""

    raw_dir = Path(raw_dir)
    available = []
    for subject_id in ALL_SUBJECTS:
        for activity in ACTIVITIES:
            name = record_name(subject_id, activity)
            if all((raw_dir / f"{name}{ext}").exists() for ext in (".hea", ".dat", ".atr")):
                available.append(name)
    return available


def load_record_raw(raw_dir: str | Path, subject_id: str, activity: str) -> RawRecord:
    """Loads one real WFDB record (signals + manually-verified R-peak
    annotations) via the `wfdb` library - never hand-parses the binary
    format. Raises `FileNotFoundError` (via wfdb) if the record is absent;
    never fabricates a placeholder record."""

    import wfdb  # imported lazily so importing this module doesn't require wfdb installed

    raw_dir = Path(raw_dir)
    name = record_name(subject_id, activity)
    record_path = raw_dir / name

    rec = wfdb.rdrecord(str(record_path))
    ann = wfdb.rdann(str(record_path), "atr")

    if rec.fs != SIGNAL_FS:
        raise ValueError(
            f"{name}: real record fs={rec.fs} does not match the frozen SIGNAL_FS={SIGNAL_FS} "
            "- do not silently proceed with a mismatched sample rate."
        )

    return RawRecord(
        subject_id=subject_id,
        activity=activity,
        record_name=name,
        fs=float(rec.fs),
        sig_name=list(rec.sig_name),
        signals=np.asarray(rec.p_signal, dtype=np.float64).T,  # (n_channels, n_samples)
        rpeak_samples=np.asarray(ann.sample, dtype=np.int64),
    )


def zscore_channels_window(window: np.ndarray) -> np.ndarray:
    """Per-channel, per-window z-score - self-contained (no stored
    train-set statistics, matching `ml/datasets/ppg_dalia.py`'s
    `zscore_ppg_window`/`zscore_imu_window` convention). `window`:
    (n_channels, WINDOW_SAMPLES). Raises `FlatSignalError` if ANY channel
    in the window is flat (std below threshold) - a flat channel here means
    a disconnected/saturated sensor, not a real zero-variance physiological
    reading."""

    if window.ndim != 2 or window.shape[1] != WINDOW_SAMPLES:
        raise ValueError(f"expected shape (n_channels, {WINDOW_SAMPLES}), got {window.shape}")

    means = window.mean(axis=1, keepdims=True)
    stds = window.std(axis=1, keepdims=True)
    if np.any(stds < FLAT_STD_THRESHOLD):
        flat_channels = np.where(stds.reshape(-1) < FLAT_STD_THRESHOLD)[0]
        raise FlatSignalError(f"flat channel(s) at index {flat_channels.tolist()} (std < {FLAT_STD_THRESHOLD})")

    return ((window - means) / stds).astype(np.float32)


def compute_window_hr(
    rpeak_samples: np.ndarray,
    window_start_sample: int,
    window_end_sample: int,
    fs: float,
    min_rpeaks: int = MIN_RPEAKS_IN_WINDOW,
) -> tuple[float, int]:
    """Mean instantaneous HR (bpm) from real R-peaks falling inside
    [window_start_sample, window_end_sample), computed as
    60 / mean(RR intervals in seconds). Raises `InsufficientRPeaksError`
    if fewer than `min_rpeaks` peaks fall in the window - the window must
    be dropped, never assigned a fabricated/interpolated HR.

    Returns (hr_bpm, n_rpeaks_in_window)."""

    in_window = rpeak_samples[(rpeak_samples >= window_start_sample) & (rpeak_samples < window_end_sample)]
    if len(in_window) < min_rpeaks:
        raise InsufficientRPeaksError(
            f"only {len(in_window)} R-peak(s) in window [{window_start_sample}, {window_end_sample}) "
            f"- need at least {min_rpeaks}"
        )
    rr_seconds = np.diff(in_window) / fs
    mean_hr = 60.0 / float(rr_seconds.mean())
    return mean_hr, int(len(in_window))


def windowize_record(raw: RawRecord) -> RecordWindows:
    """Slides a WINDOW_SECONDS/STEP_SECONDS window over one real record,
    extracting Model A and Model B raw (not yet normalized) PPG channels
    plus a real ECG-R-peak-derived HR label per window. A window is
    dropped (not padded/fabricated) if it runs past the end of the
    recording or has too few R-peaks for an honest HR estimate."""

    channel_index = {name: i for i, name in enumerate(raw.sig_name)}
    missing = [c for c in MODEL_B_CHANNELS if c not in channel_index]
    if missing:
        raise ValueError(f"{raw.record_name}: missing expected channel(s) {missing} in sig_name={raw.sig_name}")

    a_idx = [channel_index[c] for c in MODEL_A_CHANNELS]
    b_idx = [channel_index[c] for c in MODEL_B_CHANNELS]

    n_samples = raw.signals.shape[1]
    n_windows_max = max(0, (n_samples - WINDOW_SAMPLES) // STEP_SAMPLES + 1)

    starts, ppg_a_list, ppg_b_list, hr_list, n_rpeaks_list = [], [], [], [], []

    for i in range(n_windows_max):
        start = i * STEP_SAMPLES
        end = start + WINDOW_SAMPLES

        try:
            hr, n_rpeaks = compute_window_hr(raw.rpeak_samples, start, end, raw.fs)
        except InsufficientRPeaksError:
            continue

        window_b_raw = raw.signals[b_idx, start:end]
        try:
            window_b_norm = zscore_channels_window(window_b_raw)
        except FlatSignalError:
            continue
        window_a_norm = window_b_norm[: len(MODEL_A_CHANNELS)]  # site-1 channels are a prefix of MODEL_B_CHANNELS

        starts.append(start)
        ppg_a_list.append(window_a_norm)
        ppg_b_list.append(window_b_norm)
        hr_list.append(hr)
        n_rpeaks_list.append(n_rpeaks)

    return RecordWindows(
        subject_id=raw.subject_id,
        activity=raw.activity,
        record_name=raw.record_name,
        window_start_sample=np.asarray(starts, dtype=np.int64),
        ppg_a=np.asarray(ppg_a_list, dtype=np.float32) if ppg_a_list else np.zeros((0, len(MODEL_A_CHANNELS), WINDOW_SAMPLES), dtype=np.float32),
        ppg_b=np.asarray(ppg_b_list, dtype=np.float32) if ppg_b_list else np.zeros((0, len(MODEL_B_CHANNELS), WINDOW_SAMPLES), dtype=np.float32),
        hr=np.asarray(hr_list, dtype=np.float32),
        n_rpeaks_in_window=np.asarray(n_rpeaks_list, dtype=np.int64),
    )


def preprocess_record(raw_dir: str | Path, cache_dir: str | Path, subject_id: str, activity: str) -> Path:
    """Loads, windows, and caches one real record to a small `.npz` file.
    Idempotent: skips real extraction if the cache already exists."""

    cache_dir = Path(cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)
    name = record_name(subject_id, activity)
    cache_path = cache_dir / f"{name}.npz"
    if cache_path.exists():
        return cache_path

    raw = load_record_raw(raw_dir, subject_id, activity)
    if raw.subject_id != subject_id:
        raise ValueError(f"loaded record's subject_id {raw.subject_id!r} does not match requested {subject_id!r}")

    windows = windowize_record(raw)
    np.savez_compressed(
        cache_path,
        window_start_sample=windows.window_start_sample,
        ppg_a=windows.ppg_a,
        ppg_b=windows.ppg_b,
        hr=windows.hr,
        n_rpeaks_in_window=windows.n_rpeaks_in_window,
    )
    return cache_path


def load_cached_record(cache_dir: str | Path, subject_id: str, activity: str) -> RecordWindows:
    name = record_name(subject_id, activity)
    cache_path = Path(cache_dir) / f"{name}.npz"
    if not cache_path.exists():
        raise FileNotFoundError(f"No cached windows for {name} at {cache_path}. Run preprocessing first.")
    with np.load(cache_path) as data:
        return RecordWindows(
            subject_id=subject_id,
            activity=activity,
            record_name=name,
            window_start_sample=data["window_start_sample"],
            ppg_a=data["ppg_a"],
            ppg_b=data["ppg_b"],
            hr=data["hr"],
            n_rpeaks_in_window=data["n_rpeaks_in_window"],
        )


def load_cached_subject_records(cache_dir: str | Path, subject_id: str, activities: tuple[str, ...] = ACTIVITIES) -> list[RecordWindows]:
    """Loads all cached activity records for one subject that are actually
    present - does not require all three activities to exist."""

    out = []
    for activity in activities:
        cache_path = Path(cache_dir) / f"{record_name(subject_id, activity)}.npz"
        if cache_path.exists():
            out.append(load_cached_record(cache_dir, subject_id, activity))
    return out


__all__ = [
    "SIGNAL_FS",
    "ALL_SUBJECTS",
    "ACTIVITIES",
    "SITE_1_CHANNELS",
    "SITE_2_CHANNELS",
    "MODEL_A_CHANNELS",
    "MODEL_B_CHANNELS",
    "WINDOW_SECONDS",
    "STEP_SECONDS",
    "WINDOW_SAMPLES",
    "STEP_SAMPLES",
    "MIN_RPEAKS_IN_WINDOW",
    "FlatSignalError",
    "InsufficientRPeaksError",
    "RawRecord",
    "RecordWindows",
    "record_name",
    "list_available_raw_records",
    "load_record_raw",
    "zscore_channels_window",
    "compute_window_hr",
    "windowize_record",
    "preprocess_record",
    "load_cached_record",
    "load_cached_subject_records",
]
