"""Integration tests for the canonical inference adapter
(`ml/inference/ppg_dalia_hr.py`) — docs/TECHNICAL_HANDOFF_V2.md-style
Day 2 requirement: the backend integration boundary must be numerically
checkable, not just documented.

Tests that need the real trained checkpoint and/or the real raw PPG-DaLiA
archive are skipped automatically (with a clear reason) if those files are
not present locally — same convention as `test_ppg_dalia_loader.py`.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "backend"))

from ml.datasets.ppg_dalia import (  # noqa: E402
    ACC_FS,
    ACC_WINDOW_SAMPLES,
    PPG_FS,
    PPG_WINDOW_SAMPLES,
    STEP_SECONDS,
    FlatSignalError,
    _extract_subject_pickle,
)
from ml.inference.ppg_dalia_hr import (  # noqa: E402
    DEFAULT_CHECKPOINT_PATH,
    HRPrediction,
    PPGDaliaHRPredictor,
)

CHECKPOINT_PATH = DEFAULT_CHECKPOINT_PATH
RAW_ARCHIVE_PATH = REPO_ROOT / "datasets" / "ppg-dalia" / "raw_uci" / "ppg_dalia_uci.zip"

_checkpoint_available = CHECKPOINT_PATH.exists()
_raw_archive_available = RAW_ARCHIVE_PATH.exists()

requires_checkpoint = pytest.mark.skipif(not _checkpoint_available, reason=f"checkpoint not present at {CHECKPOINT_PATH} - see docs/MODEL_CONTRACT_PPG_DALIA_HR.md for transfer instructions")
requires_raw_archive = pytest.mark.skipif(not _raw_archive_available, reason=f"raw PPG-DaLiA archive not present at {RAW_ARCHIVE_PATH}")


def _extract_raw_window(subject_id: str, window_index: int) -> tuple[np.ndarray, np.ndarray]:
    """Pull one REAL, RAW (not normalized) PPG+IMU window directly out of the
    original archive for a given subject/window index - not stored anywhere
    in the repo, computed fresh each time this is called."""

    raw = _extract_subject_pickle(RAW_ARCHIVE_PATH, subject_id)
    bvp = np.asarray(raw["signal"]["wrist"]["BVP"], dtype=np.float64).reshape(-1)
    acc = np.asarray(raw["signal"]["wrist"]["ACC"], dtype=np.float64)

    t0 = window_index * STEP_SECONDS
    ppg_start = int(round(t0 * PPG_FS))
    ppg_end = ppg_start + PPG_WINDOW_SAMPLES
    acc_start = int(round(t0 * ACC_FS))
    acc_end = acc_start + ACC_WINDOW_SAMPLES

    ppg_window = bvp[ppg_start:ppg_end]
    imu_window = acc[acc_start:acc_end].T  # (3, ACC_WINDOW_SAMPLES)
    return ppg_window, imu_window


# --- Test A: shape validation -----------------------------------------------


@requires_checkpoint
def test_invalid_ppg_shape_fails_cleanly() -> None:
    predictor = PPGDaliaHRPredictor(CHECKPOINT_PATH)
    bad_ppg = np.random.randn(500)  # wrong length
    good_imu = np.random.randn(3, ACC_WINDOW_SAMPLES) + 1.0  # non-flat
    with pytest.raises(ValueError):
        predictor.predict(bad_ppg, good_imu)


@requires_checkpoint
def test_invalid_imu_shape_fails_cleanly() -> None:
    predictor = PPGDaliaHRPredictor(CHECKPOINT_PATH)
    good_ppg = np.random.randn(PPG_WINDOW_SAMPLES) + 1.0
    bad_imu = np.random.randn(2, ACC_WINDOW_SAMPLES)  # wrong axis count
    with pytest.raises(ValueError):
        predictor.predict(good_ppg, bad_imu)


@requires_checkpoint
def test_flat_ppg_window_fails_cleanly_not_silently() -> None:
    predictor = PPGDaliaHRPredictor(CHECKPOINT_PATH)
    flat_ppg = np.full(PPG_WINDOW_SAMPLES, 1.234)  # zero variance
    good_imu = np.random.randn(3, ACC_WINDOW_SAMPLES) + 1.0
    with pytest.raises(FlatSignalError):
        predictor.predict(flat_ppg, good_imu)


@requires_checkpoint
def test_missing_input_fails_cleanly() -> None:
    predictor = PPGDaliaHRPredictor(CHECKPOINT_PATH)
    good_imu = np.random.randn(3, ACC_WINDOW_SAMPLES) + 1.0
    with pytest.raises(ValueError):
        predictor.predict(None, good_imu)  # type: ignore[arg-type]


def test_missing_checkpoint_raises_file_not_found() -> None:
    with pytest.raises(FileNotFoundError):
        PPGDaliaHRPredictor(checkpoint_path=REPO_ROOT / "ml" / "checkpoints" / "does_not_exist.pt")


# --- Test B: deterministic inference ----------------------------------------


@requires_checkpoint
def test_same_window_gives_same_prediction() -> None:
    predictor = PPGDaliaHRPredictor(CHECKPOINT_PATH)
    rng = np.random.default_rng(0)
    ppg = rng.normal(size=PPG_WINDOW_SAMPLES) + 2.0
    imu = rng.normal(size=(3, ACC_WINDOW_SAMPLES)) + 1.0

    pred1 = predictor.predict(ppg, imu)
    pred2 = predictor.predict(ppg, imu)

    assert pred1.heart_rate_bpm == pred2.heart_rate_bpm
    assert pred1.normalized_model_output == pred2.normalized_model_output


# --- Test C: training/evaluation parity -------------------------------------


@requires_checkpoint
@requires_raw_archive
def test_adapter_matches_official_evaluation_path_on_real_window() -> None:
    """The strongest test in this file: pulls a REAL raw window directly out
    of the archive (never cached/committed), runs it through the new
    canonical adapter, and independently runs the exact same real raw
    window through the official training/evaluation code path
    (`Conv1DEncoder`+`ModalityFusionTransformer`+head via `PPGPlusIMUHRModel`,
    the same class `ml/train_ppg_dalia_imu_ablation.py`'s own `evaluate()`
    uses) - the two must agree to floating-point precision."""

    from ml.datasets.ppg_dalia import zscore_imu_window, zscore_ppg_window
    from ml.train_ppg_dalia_imu_ablation import PPGPlusIMUHRModel
    import torch
    from app.ml._torch_bootstrap import ensure_torch_dll_path

    ensure_torch_dll_path()

    subject_id, window_index = "S14", 100  # S14 is a real held-out TEST subject (never trained on)
    raw_ppg, raw_imu = _extract_raw_window(subject_id, window_index)

    # Path 1: the canonical adapter (what Emir's integration should call)
    predictor = PPGDaliaHRPredictor(CHECKPOINT_PATH)
    adapter_pred = predictor.predict(raw_ppg, raw_imu)

    # Path 2: the "official" evaluation-style path, built independently here
    # from the same real raw window, using the exact same real checkpoint.
    ppg_norm = zscore_ppg_window(raw_ppg)
    imu_norm = zscore_imu_window(raw_imu)
    model = PPGPlusIMUHRModel(embedding_dim=32)
    model.load_state_dict(torch.load(CHECKPOINT_PATH, map_location="cpu"))
    model.eval()
    with torch.no_grad():
        raw_output = model(
            torch.from_numpy(ppg_norm).view(1, 1, PPG_WINDOW_SAMPLES),
            torch.from_numpy(imu_norm).view(1, 3, ACC_WINDOW_SAMPLES),
        )
    from ml.inference.ppg_dalia_hr import HR_MEAN, HR_STD

    official_hr_bpm = float(raw_output.item()) * HR_STD + HR_MEAN

    assert adapter_pred.heart_rate_bpm == pytest.approx(official_hr_bpm, abs=1e-4), (
        f"adapter={adapter_pred.heart_rate_bpm} vs official={official_hr_bpm} - "
        "these must match to floating-point precision on a real window"
    )


# --- Test D: preprocessing parity -------------------------------------------


@requires_raw_archive
def test_preprocessing_parity_between_offline_and_inference_paths() -> None:
    """Both the offline preprocessing path (ml/preprocess_ppg_dalia.py's
    `_windowize`) and the live-inference path (this module) call the exact
    same `zscore_ppg_window`/`zscore_imu_window` functions - this test
    confirms a real raw window, normalized independently through each
    call site's own import path, produces bit-identical tensors."""

    from ml.datasets.ppg_dalia import zscore_imu_window as offline_zscore_imu
    from ml.datasets.ppg_dalia import zscore_ppg_window as offline_zscore_ppg
    from ml.inference.ppg_dalia_hr import zscore_imu_window as inference_zscore_imu  # noqa: F401 (import-path check)
    from ml.inference.ppg_dalia_hr import zscore_ppg_window as inference_zscore_ppg  # noqa: F401

    raw_ppg, raw_imu = _extract_raw_window("S14", 50)

    assert offline_zscore_ppg is inference_zscore_ppg, "inference module must import the SAME function object, not a copy"
    assert offline_zscore_imu is inference_zscore_imu, "inference module must import the SAME function object, not a copy"

    a = offline_zscore_ppg(raw_ppg)
    b = inference_zscore_ppg(raw_ppg)
    assert np.array_equal(a, b)


# --- Test E: no fake uncertainty --------------------------------------------


@requires_checkpoint
def test_prediction_never_includes_fabricated_uncertainty() -> None:
    predictor = PPGDaliaHRPredictor(CHECKPOINT_PATH)
    rng = np.random.default_rng(1)
    ppg = rng.normal(size=PPG_WINDOW_SAMPLES) + 1.0
    imu = rng.normal(size=(3, ACC_WINDOW_SAMPLES)) + 1.0

    pred = predictor.predict(ppg, imu)

    assert isinstance(pred, HRPrediction)
    assert pred.uncertainty is None, "no validated predictive uncertainty exists - this field must stay None"
