"""Backend-facing bridge to the canonical PPG-DaLiA HR predictor."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Protocol

import numpy as np

from app.ml.ppg_dalia_windows import DATASET_NAME, PPGDaliaModelWindow, REPOSITORY_ROOT
from app.schemas.model_prediction import HeartRateModelPrediction, HeartRateModelProvenance

MODEL_ID = "PPGDaliaHRModelB:PPGPlusIMUHRModel"
EXPECTED_CHECKPOINT_SIZE_BYTES = 138086
EXPECTED_CHECKPOINT_SHA256 = "c53a34586d2d6baf68aae4441b6c15a0f5f623f0ea70c023c7371c2dbded0e77"
DEFAULT_CHECKPOINT_PATH = REPOSITORY_ROOT / "ml" / "checkpoints" / "model_b_ppg_plus_imu_ppg_dalia.pt"


class ModelUnavailableError(RuntimeError):
    """The real model cannot be loaded; no fallback prediction is allowed."""


class CheckpointIdentityError(ModelUnavailableError):
    """Checkpoint bytes differ from the validated Model B artifact."""


class _CanonicalPrediction(Protocol):
    heart_rate_bpm: float
    normalized_model_output: float


class _CanonicalPredictor(Protocol):
    checkpoint_path: Path

    def predict(self, ppg_window: np.ndarray, imu_window: np.ndarray) -> _CanonicalPrediction: ...


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


class PPGDaliaHRInferenceBridge:
    """Validate Model B identity once and reuse the canonical predictor."""

    def __init__(self, checkpoint_path: str | Path = DEFAULT_CHECKPOINT_PATH) -> None:
        self.checkpoint_path = Path(checkpoint_path).expanduser().resolve()
        if not self.checkpoint_path.is_file():
            raise ModelUnavailableError(
                f"Validated PPG-DaLiA HR checkpoint is unavailable at {self.checkpoint_path}; "
                "no synthetic or rule-based fallback is permitted."
            )
        size = self.checkpoint_path.stat().st_size
        if size != EXPECTED_CHECKPOINT_SIZE_BYTES:
            raise CheckpointIdentityError(
                f"Checkpoint size mismatch at {self.checkpoint_path}: expected "
                f"{EXPECTED_CHECKPOINT_SIZE_BYTES} bytes, got {size}."
            )
        checkpoint_sha256 = _sha256(self.checkpoint_path)
        if checkpoint_sha256 != EXPECTED_CHECKPOINT_SHA256:
            raise CheckpointIdentityError(
                f"Checkpoint SHA256 mismatch at {self.checkpoint_path}: expected "
                f"{EXPECTED_CHECKPOINT_SHA256}, got {checkpoint_sha256}."
            )

        try:
            from ml.inference.ppg_dalia_hr import PPGDaliaHRPredictor

            self._predictor: _CanonicalPredictor = PPGDaliaHRPredictor(checkpoint_path=self.checkpoint_path)
        except Exception as exc:
            raise ModelUnavailableError(
                f"Canonical PPG-DaLiA HR predictor could not load {self.checkpoint_path}: {exc}"
            ) from exc
        self.checkpoint_sha256 = checkpoint_sha256

    @property
    def canonical_predictor(self) -> _CanonicalPredictor:
        """Expose identity for audit/tests; callers should use predict()."""

        return self._predictor

    def predict(self, window: PPGDaliaModelWindow) -> HeartRateModelPrediction:
        if window.dataset_name != DATASET_NAME:
            raise ValueError(f"Expected {DATASET_NAME} window, got {window.dataset_name!r}.")
        prediction = self._predictor.predict(window.ppg, window.imu)
        return HeartRateModelPrediction(
            value=prediction.heart_rate_bpm,
            normalized_model_output=prediction.normalized_model_output,
            uncertainty=None,
            provenance=HeartRateModelProvenance(
                subject_id=window.subject_id,
                window_index=window.window_index,
                window_start_seconds=window.window_start_seconds,
                window_duration_seconds=window.window_duration_seconds,
                model_id=MODEL_ID,
                checkpoint_path=str(self.checkpoint_path),
                checkpoint_sha256=self.checkpoint_sha256,
            ),
        )
