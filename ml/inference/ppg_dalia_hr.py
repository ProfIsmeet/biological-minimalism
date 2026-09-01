"""Canonical reference inference adapter for the Priority 2 PPG+IMU
heart-rate model (Model B).

**This is the authoritative implementation** of "given a real PPG window and
a real synchronized IMU window, produce a heart-rate prediction." Backend
integration (Emir/Codex) should call this directly, or numerically match it
exactly (see `results/ppg_dalia_integration_reference.json` for a golden
parity check) — never re-derive the preprocessing or normalization logic
from `ml/train_ppg_dalia_imu_ablation.py`.

Full human-readable contract, including the exact synchronization rule this
adapter assumes its caller already applied: `docs/MODEL_CONTRACT_PPG_DALIA_HR.md`.

This module does not fabricate anything it cannot validate:
- Wrong input shape -> `ValueError`, immediately, before any computation.
- A flat/dead PPG window -> `FlatSignalError`, immediately.
- Missing checkpoint file -> `FileNotFoundError` with the exact expected path.
- No uncertainty is invented — `HRPrediction.uncertainty` is always `None`,
  by design (see docs/MODEL_CONTRACT_PPG_DALIA_HR.md §7).
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "backend"))
sys.path.insert(0, str(REPO_ROOT))

from app.ml._torch_bootstrap import ensure_torch_dll_path  # noqa: E402

ensure_torch_dll_path()

import torch  # noqa: E402

from ml.datasets.ppg_dalia import (  # noqa: E402
    ACC_WINDOW_SAMPLES,
    PPG_WINDOW_SAMPLES,
    FlatSignalError,
    zscore_imu_window,
    zscore_ppg_window,
)

# These three constants are the exact values recorded in
# ml/experiments/ppg_dalia_imu_ablation/results.json's "hr_normalization"
# block, computed from TRAINING subjects only. Do not change them without
# re-deriving from that file - they are not free parameters.
DEFAULT_CHECKPOINT_PATH = REPO_ROOT / "ml" / "checkpoints" / "model_b_ppg_plus_imu_ppg_dalia.pt"
DEFAULT_EMBEDDING_DIM = 32
HR_MEAN = 86.34466552734375
HR_STD = 21.048254013061523


@dataclass(frozen=True)
class HRPrediction:
    heart_rate_bpm: float
    normalized_model_output: float
    uncertainty: None = None
    """Always None. No validated predictive uncertainty exists for this
    model (docs/MODEL_CONTRACT_PPG_DALIA_HR.md §7) - this field exists so a
    caller cannot forget to handle the "no uncertainty" case, not to imply
    one is coming later without further work."""


class PPGDaliaHRPredictor:
    """Loads the trained Model B checkpoint once; call `.predict()` per window.

    Construct one instance and reuse it across many windows/a live stream —
    each `.predict()` call is a single forward pass with no hidden state
    carried between windows (the model itself is stateless across windows;
    each window is normalized independently, matching training exactly).
    """

    def __init__(
        self,
        checkpoint_path: str | Path = DEFAULT_CHECKPOINT_PATH,
        embedding_dim: int = DEFAULT_EMBEDDING_DIM,
        hr_mean: float = HR_MEAN,
        hr_std: float = HR_STD,
        device: str = "cpu",
    ) -> None:
        checkpoint_path = Path(checkpoint_path)
        if not checkpoint_path.exists():
            raise FileNotFoundError(
                f"Checkpoint not found at {checkpoint_path}. This file is intentionally not "
                "committed to git (see .gitignore) - it must be transferred separately. See "
                "docs/MODEL_CONTRACT_PPG_DALIA_HR.md for the checkpoint's expected size/SHA256 "
                "and results/ppg_dalia_integration_reference.json for the transfer record."
            )

        # Imported lazily (not at module top level) to avoid importing torch's
        # training-script module (with its argparse CLI) as a side effect of
        # simply importing this inference module.
        from ml.train_ppg_dalia_imu_ablation import PPGPlusIMUHRModel

        self.model = PPGPlusIMUHRModel(embedding_dim)
        state_dict = torch.load(checkpoint_path, map_location=device)
        self.model.load_state_dict(state_dict)
        self.model.eval()
        self.model.to(device)

        self.hr_mean = hr_mean
        self.hr_std = hr_std
        self.device = device
        self.checkpoint_path = checkpoint_path

    def predict(self, ppg_window: np.ndarray, imu_window: np.ndarray) -> HRPrediction:
        """`ppg_window`: RAW (not pre-normalized) real PPG samples, shape
        `(512,)`, 64 Hz, starting at some absolute time `t0`.
        `imu_window`: RAW real accelerometer samples, shape `(3, 256)`,
        32 Hz, starting at the SAME `t0` as `ppg_window` (see
        docs/MODEL_CONTRACT_PPG_DALIA_HR.md §4 for the exact synchronization
        rule — this function does not itself verify the two windows are
        correctly time-aligned; that is the caller's responsibility).

        Raises `ValueError` for a wrong shape, `FlatSignalError` for a
        flat/dead PPG window. Never reshapes, pads, or fabricates input to
        make it fit.
        """

        if ppg_window is None or imu_window is None:
            raise ValueError("ppg_window and imu_window are both required - no default/fallback input is used")

        ppg_norm = zscore_ppg_window(np.asarray(ppg_window, dtype=np.float64))
        imu_norm = zscore_imu_window(np.asarray(imu_window, dtype=np.float64))

        ppg_t = torch.from_numpy(ppg_norm).to(self.device).view(1, 1, PPG_WINDOW_SAMPLES)
        imu_t = torch.from_numpy(imu_norm).to(self.device).view(1, 3, ACC_WINDOW_SAMPLES)

        self.model.eval()
        with torch.no_grad():
            raw_output = self.model(ppg_t, imu_t)

        normalized = float(raw_output.item())
        if not np.isfinite(normalized):
            raise RuntimeError(f"Model produced a non-finite output ({normalized}) - refusing to convert to bpm")

        hr_bpm = normalized * self.hr_std + self.hr_mean
        return HRPrediction(heart_rate_bpm=hr_bpm, normalized_model_output=normalized)


def predict_hr(
    ppg_window: np.ndarray,
    imu_window: np.ndarray,
    checkpoint_path: str | Path = DEFAULT_CHECKPOINT_PATH,
) -> HRPrediction:
    """Convenience one-shot function. Loads the checkpoint fresh on every
    call — fine for a single prediction or a test, but for a live/replay
    stream, construct one `PPGDaliaHRPredictor` and call `.predict()`
    repeatedly instead, to avoid reloading the checkpoint per window."""

    return PPGDaliaHRPredictor(checkpoint_path=checkpoint_path).predict(ppg_window, imu_window)


__all__ = ["PPGDaliaHRPredictor", "HRPrediction", "predict_hr", "FlatSignalError", "HR_MEAN", "HR_STD", "DEFAULT_CHECKPOINT_PATH"]
