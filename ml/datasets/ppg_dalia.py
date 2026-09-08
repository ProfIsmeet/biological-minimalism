"""Loader for PPG-DaLiA (Reiss, Indlekofer, Schmidt & Van Laerhoven, 2019,
"Deep PPG: Large-scale Heart Rate Estimation with Convolutional Neural
Networks," MDPI Sensors, 19(14)).

Source: original per-subject distribution, UCI Machine Learning Repository
https://doi.org/10.24432/C53890 (CC BY 4.0). NOT the Zenodo `.ts`
time-series-regression repackaging (zenodo.org/records/3902728) - that
version strips subject identity entirely (verified by inspecting its header:
no subject/group field exists in the `.ts` format), which makes it
impossible to guarantee a subject-disjoint split and is therefore unsuitable
for this project's ablation experiment (see
`datasets/DATASET_MATRIX.md` and `docs/TECHNICAL_HANDOFF_V2.md` §8's rule
against unverifiable data provenance).

Real, verified structure (inspected directly from the downloaded archive,
subject S1, before writing this loader - not assumed from the paper alone):

    ppg_dalia_uci.zip
      data.zip
        PPG_FieldStudy/S<N>/S<N>.pkl   - one per subject, S1..S15
          data['subject']              - str, e.g. "S1"
          data['signal']['wrist']['BVP']   (n_bvp, 1) float64 @ 64 Hz   - PPG
          data['signal']['wrist']['ACC']   (n_acc, 3) float64 @ 32 Hz  - wrist IMU
          data['label']                (n_windows,) float64            - real
              ECG-derived heart rate (bpm), one value per 8s window,
              2s step (verified: (duration_s - 8) / 2 + 1 == n_windows exactly)
          data['activity']             (n_act, 1) float64 @ 4 Hz       - real
              activity-ID label (0-8), used here for motion-severity
              stratification alongside a continuous accelerometer-energy
              measure

This module never fabricates a value: any subject file that fails to parse
into this exact shape is skipped with a warning, not padded or guessed.
"""

from __future__ import annotations

import json
import warnings
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from backend.app.data.ppg_dalia import (
    ALL_SUBJECTS,
    load_subject_payload,
    list_available_subjects,
)

CACHE_SCHEMA_VERSION = "ppg_dalia_cache.v1"  # audit M7/§35 cache provenance

PPG_FS = 64.0
ACC_FS = 32.0
ACTIVITY_FS = 4.0
WINDOW_SECONDS = 8.0
STEP_SECONDS = 2.0
PPG_WINDOW_SAMPLES = int(WINDOW_SECONDS * PPG_FS)  # 512
ACC_WINDOW_SAMPLES = int(WINDOW_SECONDS * ACC_FS)  # 256

FLAT_STD_THRESHOLD = 1e-8


class FlatSignalError(ValueError):
    """Raised when a window's signal is flat/dead (std below FLAT_STD_THRESHOLD)
    and cannot be meaningfully z-scored. Both the offline preprocessing path
    (_windowize, below) and any live/replay inference path must treat this
    the same way: refuse the window rather than normalizing noise - see
    ml/inference/ppg_dalia_hr.py, which reuses these exact functions so the
    two paths can never silently diverge."""


def zscore_ppg_window(window: np.ndarray) -> np.ndarray:
    """Per-window z-score for one raw PPG segment.

    `window`: 1D array, shape (PPG_WINDOW_SAMPLES,). This is the exact
    normalization applied during training/preprocessing - reused as-is by
    the inference adapter so the two paths cannot drift apart.
    """

    window = np.asarray(window)
    if window.shape != (PPG_WINDOW_SAMPLES,):
        raise ValueError(f"expected PPG window shape ({PPG_WINDOW_SAMPLES},), got {window.shape}")
    std = float(window.std())
    if std < FLAT_STD_THRESHOLD:
        raise FlatSignalError("PPG window is flat/dead (std < 1e-8) - refusing to normalize noise as signal")
    return ((window - window.mean()) / std).astype(np.float32)


def zscore_imu_window(window: np.ndarray) -> np.ndarray:
    """Per-axis, per-window z-score for one raw IMU (accelerometer) segment.

    `window`: 2D array, shape (3, ACC_WINDOW_SAMPLES). Each of the 3 axes is
    normalized independently within this window - the exact normalization
    applied during training/preprocessing, reused as-is by the inference
    adapter.
    """

    window = np.asarray(window)
    if window.shape != (3, ACC_WINDOW_SAMPLES):
        raise ValueError(f"expected IMU window shape (3, {ACC_WINDOW_SAMPLES}), got {window.shape}")
    mean = window.mean(axis=1, keepdims=True)
    std = window.std(axis=1, keepdims=True)
    std_safe = np.where(std < FLAT_STD_THRESHOLD, 1.0, std)
    return ((window - mean) / std_safe).astype(np.float32)


ACTIVITY_NAMES = {
    0: "transient/unlabeled",
    1: "sitting",
    2: "stairs",
    3: "table_soccer",
    4: "cycling",
    5: "driving",
    6: "lunch_break",
    7: "walking",
    8: "working",
}

@dataclass
class SubjectWindows:
    subject_id: str
    ppg: np.ndarray  # (n_windows, PPG_WINDOW_SAMPLES) float32, z-scored per window
    acc: np.ndarray  # (n_windows, 3, ACC_WINDOW_SAMPLES) float32, z-scored per window per axis
    hr: np.ndarray  # (n_windows,) float32, real ECG-derived HR (bpm)
    activity: np.ndarray  # (n_windows,) int64, majority real activity ID for the window
    motion_energy: np.ndarray  # (n_windows,) float32, real accelerometer-magnitude std within the window


def _extract_subject_pickle(zip_path: Path, subject_id: str) -> dict:
    """Stream-read one subject's real .pkl directly out of the nested zip
    (`ppg_dalia_uci.zip` -> `data.zip` -> `PPG_FieldStudy/<subject>/<subject>.pkl`)
    without ever writing the ~1.2-1.7 GB raw file to disk."""

    return load_subject_payload(zip_path, subject_id)


def _windowize(raw: dict, subject_id: str) -> SubjectWindows:
    bvp = np.asarray(raw["signal"]["wrist"]["BVP"], dtype=np.float64).reshape(-1)
    acc = np.asarray(raw["signal"]["wrist"]["ACC"], dtype=np.float64)  # (n, 3)
    hr = np.asarray(raw["label"], dtype=np.float64).reshape(-1)
    activity_raw = np.asarray(raw["activity"], dtype=np.float64).reshape(-1)

    n_windows = len(hr)
    ppg_out = np.zeros((n_windows, PPG_WINDOW_SAMPLES), dtype=np.float32)
    acc_out = np.zeros((n_windows, 3, ACC_WINDOW_SAMPLES), dtype=np.float32)
    activity_out = np.zeros(n_windows, dtype=np.int64)
    motion_energy = np.zeros(n_windows, dtype=np.float32)
    keep = np.ones(n_windows, dtype=bool)

    for i in range(n_windows):
        t0 = i * STEP_SECONDS

        ppg_start = int(round(t0 * PPG_FS))
        ppg_end = ppg_start + PPG_WINDOW_SAMPLES
        acc_start = int(round(t0 * ACC_FS))
        acc_end = acc_start + ACC_WINDOW_SAMPLES
        act_start = int(round(t0 * ACTIVITY_FS))
        act_end = act_start + int(round(WINDOW_SECONDS * ACTIVITY_FS))

        if ppg_end > len(bvp) or acc_end > len(acc) or act_end > len(activity_raw):
            keep[i] = False  # real recording ended short of a full final window - dropped, not padded
            continue

        ppg_seg = bvp[ppg_start:ppg_end]
        acc_seg = acc[acc_start:acc_end].T  # (3, ACC_WINDOW_SAMPLES)

        try:
            ppg_out[i] = zscore_ppg_window(ppg_seg)
        except FlatSignalError:
            keep[i] = False  # flat/dropped real sensor segment - excluded, not fabricated
            continue
        acc_out[i] = zscore_imu_window(acc_seg)

        act_window = activity_raw[act_start:act_end]
        values, counts = np.unique(act_window, return_counts=True)
        activity_out[i] = int(values[np.argmax(counts)])

        # Real motion-severity proxy: std of the raw (non-normalized) accelerometer
        # magnitude within the window - a continuous complement to the categorical
        # activity label, per the task's "stratify by motion/activity severity" requirement.
        raw_acc_seg = acc[acc_start:acc_end]
        magnitude = np.linalg.norm(raw_acc_seg, axis=1)
        motion_energy[i] = float(magnitude.std())

    return SubjectWindows(
        subject_id=subject_id,
        ppg=ppg_out[keep],
        acc=acc_out[keep],
        hr=hr[keep].astype(np.float32),
        activity=activity_out[keep],
        motion_energy=motion_energy[keep],
    )


def preprocess_subject(zip_path: str | Path, subject_id: str, cache_dir: str | Path) -> Path:
    """Extract, window, and cache one subject to a small `.npz` file. Returns
    the cache file path. Idempotent: skips real extraction if the cache
    already exists."""

    zip_path = Path(zip_path)
    cache_dir = Path(cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_path = cache_dir / f"{subject_id}.npz"
    if cache_path.exists():
        return cache_path

    if not zip_path.exists():
        raise NotImplementedError(
            f"PPG-DaLiA raw archive not found at {zip_path}. See "
            "datasets/ppg-dalia/README.md for the download command. This "
            "project does not ship or fabricate this data."
        )

    raw = _extract_subject_pickle(zip_path, subject_id)
    assert raw.get("subject") == subject_id, (
        f"pickle's own 'subject' field ({raw.get('subject')!r}) does not match "
        f"the requested subject ({subject_id!r}) - refusing to cache a mislabeled file."
    )
    windows = _windowize(raw, subject_id)

    # Audit M7/§35: embed cache provenance metadata so a loader can reject a
    # mislabeled or stale cache instead of silently trusting it. Existing caches
    # without this key are tolerated as LEGACY_CACHE_UNVERIFIED (§36).
    meta = {
        "cache_schema_version": CACHE_SCHEMA_VERSION,
        "subject_id": subject_id,
        "modality_config": {
            "ppg_fs": PPG_FS, "acc_fs": ACC_FS,
            "window_seconds": WINDOW_SECONDS, "step_seconds": STEP_SECONDS,
        },
        "preprocessing": "ml/datasets/ppg_dalia.py::_windowize (deterministic)",
    }
    np.savez_compressed(
        cache_path,
        ppg=windows.ppg,
        acc=windows.acc,
        hr=windows.hr,
        activity=windows.activity,
        motion_energy=windows.motion_energy,
        _provenance=np.array(json.dumps(meta)),
    )
    return cache_path


def load_cached_subject(cache_dir: str | Path, subject_id: str) -> SubjectWindows:
    cache_path = Path(cache_dir) / f"{subject_id}.npz"
    if not cache_path.exists():
        raise NotImplementedError(
            f"No cached windows for {subject_id} at {cache_path}. Run "
            "ml/preprocess_ppg_dalia.py first."
        )
    with np.load(cache_path) as data:
        # Audit M7/§35-§36: verify embedded provenance; reject a cache whose
        # recorded subject/schema does not match, but tolerate legacy caches
        # (no provenance) as LEGACY_CACHE_UNVERIFIED rather than silently trusting.
        if "_provenance" in data:
            meta = json.loads(str(data["_provenance"]))
            if meta.get("subject_id") != subject_id:
                raise ValueError(
                    f"Cache provenance mismatch: {cache_path} records subject "
                    f"{meta.get('subject_id')!r} but {subject_id!r} was requested."
                )
            if meta.get("cache_schema_version") != CACHE_SCHEMA_VERSION:
                warnings.warn(
                    f"Cache {cache_path} schema {meta.get('cache_schema_version')!r} != "
                    f"{CACHE_SCHEMA_VERSION!r}; treating as LEGACY_CACHE_UNVERIFIED.",
                    stacklevel=2,
                )
        else:
            warnings.warn(
                f"Cache {cache_path} has no provenance metadata "
                "(LEGACY_CACHE_UNVERIFIED): re-run ml/preprocess_ppg_dalia.py to stamp it.",
                stacklevel=2,
            )
        return SubjectWindows(
            subject_id=subject_id,
            ppg=data["ppg"],
            acc=data["acc"],
            hr=data["hr"],
            activity=data["activity"],
            motion_energy=data["motion_energy"],
        )


def load_cached_subjects(cache_dir: str | Path, subject_ids: list[str]) -> list[SubjectWindows]:
    return [load_cached_subject(cache_dir, s) for s in subject_ids]


def list_available_raw_subjects(zip_path: str | Path) -> list[str]:
    """Real check of which subjects actually exist in the archive - used by
    the preprocessing script and tests instead of assuming all of S1-S15
    are present."""

    return list_available_subjects(zip_path)
