"""Loader for PulseDB (cuffless blood pressure, PPG/ECG derived from MIMIC-III/VitalDB).

Source: Wang, W., Mohseni, P., Kilgore, K. L., & Najafizadeh, L. (2023).
PulseDB: A large, cleaned dataset based on MIMIC-III and VitalDB for
benchmarking cuff-less blood pressure estimation methods. Frontiers in
Digital Health, 4, 1090854. https://doi.org/10.3389/fdgth.2022.1090854

Distribution: https://github.com/pulselabteam/PulseDB

Not bundled with this repository. See `datasets/README.md` for the
download procedure. This module raises `NotImplementedError` until pointed
at a real local copy.
"""

from __future__ import annotations

from pathlib import Path


def load_pulsedb_windows(dataset_dir: str | Path, window_seconds: float = 10.0):
    """Yield (ppg_window, (systolic, diastolic)) pairs from a local PulseDB checkout."""

    dataset_dir = Path(dataset_dir)
    if not dataset_dir.exists():
        raise NotImplementedError(
            f"PulseDB not found at {dataset_dir}. Download it per "
            "datasets/README.md, then re-run with --pulsedb-dir pointing "
            "at the extracted folder."
        )
    # TODO(research phase): parse PulseDB's .mat segment files (PPG + ABP
    # ground truth) into fixed-length windows matching the feature
    # contract in backend/app/ml/models.py.
    raise NotImplementedError("PulseDB parsing is not implemented in this task's scope.")
