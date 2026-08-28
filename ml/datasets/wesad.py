"""Loader for WESAD (Wearable Stress and Affect Detection).

Source: Schmidt, P., Reiss, A., Duerichen, R., Marberger, C., & Van Laerhoven,
K. (2018). Introducing WESAD, a multimodal dataset for wearable stress and
affect detection. Proceedings of the 20th ACM International Conference on
Multimodal Interaction (ICMI 2018). https://doi.org/10.1145/3242969.3242985

Distribution: https://archive.ics.uci.edu/dataset/465/wesad+wearable+stress+affect+detection
(also mirrored via the Ubicomp Uni-Siegen group's own release).

Not bundled with this repository (multi-GB, subject-recorded physiological
data). This module intentionally raises `NotImplementedError` until pointed
at a real local copy — see `datasets/README.md` at the repo root for the
download procedure.
"""

from __future__ import annotations

from pathlib import Path


def load_wesad_windows(dataset_dir: str | Path, window_seconds: float = 10.0):
    """Yield (modality_windows, label) pairs from a local WESAD checkout.

    `dataset_dir` should point at the directory containing one subfolder
    per subject (`S2/`, `S3/`, ...), each with a `SX.pkl` pickle as
    distributed by the WESAD authors.
    """

    dataset_dir = Path(dataset_dir)
    if not dataset_dir.exists():
        raise NotImplementedError(
            f"WESAD not found at {dataset_dir}. Download it per "
            "datasets/README.md, then re-run with --wesad-dir pointing at "
            "the extracted folder. This project does not ship or fabricate "
            "WESAD data."
        )
    # TODO(research phase): parse the WESAD .pkl per-subject files,
    # windowing chest/wrist BVP (-> PPG), EDA, TEMP and resampling to the
    # feature contract in backend/app/ml/models.py's MODALITIES.
    raise NotImplementedError("WESAD parsing is not implemented in this task's scope.")
