"""Loader for STEW (Simultaneous Task EEG Workload dataset).

Source: Lim, W. L., Sourina, O., & Wang, L. P. (2018). STEW: Simultaneous
Task EEG Workload Data Set. IEEE Transactions on Neural Systems and
Rehabilitation Engineering, 26(11), 2106-2114.
https://doi.org/10.1109/TNSRE.2018.2872924

Distribution: https://ieee-dataport.org/open-access/stew-simultaneous-task-eeg-workload-dataset

Not bundled with this repository. See `datasets/README.md` for the
download procedure. This module raises `NotImplementedError` until pointed
at a real local copy.
"""

from __future__ import annotations

from pathlib import Path


def load_stew_windows(dataset_dir: str | Path, window_seconds: float = 10.0):
    """Yield (eeg_window, workload_label) pairs from a local STEW checkout."""

    dataset_dir = Path(dataset_dir)
    if not dataset_dir.exists():
        raise NotImplementedError(
            f"STEW not found at {dataset_dir}. Download it per "
            "datasets/README.md, then re-run with --stew-dir pointing at "
            "the extracted folder."
        )
    # TODO(research phase): parse the STEW per-subject .txt EEG recordings
    # and the accompanying self-reported workload ratings.
    raise NotImplementedError("STEW parsing is not implemented in this task's scope.")
