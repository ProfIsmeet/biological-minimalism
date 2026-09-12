"""Enrich dataset-replay snapshots with validated heart-rate inference."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Protocol

from app.ml.ppg_dalia_hr import (
    DEFAULT_CHECKPOINT_PATH,
    ModelUnavailableError,
    PPGDaliaHRInferenceBridge,
)
from app.ml.ppg_dalia_windows import (
    IMU_CHANNEL,
    PPG_CHANNEL,
    PPGDaliaModelWindow,
    PPGDaliaWindowAssembler,
    WindowAssemblyError,
)
from app.schemas.data_source import DataSourceType
from app.schemas.model_prediction import (
    HeartRateInferenceState,
    HeartRateModelPrediction,
    ModelInferenceStatus,
)
from app.schemas.telemetry import LiveMetricsSnapshot


class HeartRatePredictionBridge(Protocol):
    def predict(self, window: PPGDaliaModelWindow) -> HeartRateModelPrediction: ...


BridgeFactory = Callable[[Path], HeartRatePredictionBridge]


def _default_bridge_factory(checkpoint_path: Path) -> HeartRatePredictionBridge:
    return PPGDaliaHRInferenceBridge(checkpoint_path)


class ReplayHeartRateInferenceService:
    """Stateful replay-only coordinator around the Phase 2 model bridge.

    The service never alters recorded channels or synthetic vitals. It adds a
    separate AI-estimated prediction and an explicit availability state to
    replay snapshots. The model is loaded lazily on the first complete window.
    """

    def __init__(
        self,
        checkpoint_path: str | Path = DEFAULT_CHECKPOINT_PATH,
        *,
        bridge_factory: BridgeFactory = _default_bridge_factory,
    ) -> None:
        self.checkpoint_path = Path(checkpoint_path).expanduser().resolve()
        self._bridge_factory = bridge_factory
        self._assembler = PPGDaliaWindowAssembler()
        self._bridge: HeartRatePredictionBridge | None = None
        self._bridge_error: str | None = None
        self._identity: tuple[str, str] | None = None
        self._latest_prediction: HeartRateModelPrediction | None = None
        self._last_state: HeartRateInferenceState | None = None

    @property
    def latest_prediction(self) -> HeartRateModelPrediction | None:
        return self._latest_prediction

    def reset(self) -> None:
        """Clear replay-session state while retaining an already loaded model."""

        self._assembler.reset()
        self._bridge_error = None
        self._identity = None
        self._latest_prediction = None
        self._last_state = None

    def _state(self, status: ModelInferenceStatus, message: str) -> HeartRateInferenceState:
        state = HeartRateInferenceState(status=status, message=message)
        self._last_state = state
        return state

    @staticmethod
    def _enrich(
        snapshot: LiveMetricsSnapshot,
        *,
        prediction: HeartRateModelPrediction | None,
        state: HeartRateInferenceState | None,
    ) -> LiveMetricsSnapshot:
        return snapshot.model_copy(
            update={
                "heart_rate_prediction": prediction,
                "heart_rate_inference": state,
            }
        )

    def _ensure_bridge(self) -> HeartRatePredictionBridge | None:
        if self._bridge is not None:
            return self._bridge
        if self._bridge_error is not None:
            return None
        try:
            self._bridge = self._bridge_factory(self.checkpoint_path)
        except Exception as exc:  # controlled boundary around checkpoint/model loading
            self._bridge_error = str(exc)
            return None
        return self._bridge

    def process(self, snapshot: LiveMetricsSnapshot) -> LiveMetricsSnapshot:
        if snapshot.source.source_type != DataSourceType.DATASET_REPLAY:
            self.reset()
            return self._enrich(snapshot, prediction=None, state=None)

        dataset_name = snapshot.source.dataset_name
        subject_id = snapshot.source.subject_id
        if not dataset_name or not subject_id:
            self._latest_prediction = None
            state = self._state(
                ModelInferenceStatus.INPUT_UNAVAILABLE,
                "Heart Rate AI unavailable: replay dataset or subject identity is missing.",
            )
            return self._enrich(snapshot, prediction=None, state=state)

        identity = (dataset_name, subject_id)
        if identity != self._identity:
            self.reset()
            self._identity = identity

        missing_channels = [
            channel
            for channel in (PPG_CHANNEL, IMU_CHANNEL)
            if channel not in snapshot.source.available_channels
        ]
        if missing_channels:
            self._assembler.reset()
            self._latest_prediction = None
            state = self._state(
                ModelInferenceStatus.INPUT_UNAVAILABLE,
                f"Heart Rate AI unavailable: missing recorded channel(s): {', '.join(missing_channels)}.",
            )
            return self._enrich(snapshot, prediction=None, state=state)

        try:
            windows = self._assembler.ingest(snapshot)
        except WindowAssemblyError as exc:
            self._assembler.reset()
            self._latest_prediction = None
            state = self._state(
                ModelInferenceStatus.ERROR,
                f"Heart Rate AI input error: {exc}",
            )
            return self._enrich(snapshot, prediction=None, state=state)

        if not windows:
            if self._latest_prediction is not None:
                state = self._state(
                    ModelInferenceStatus.AVAILABLE,
                    "AI-estimated heart rate from synchronized recorded PPG + IMU.",
                )
                return self._enrich(snapshot, prediction=self._latest_prediction, state=state)
            if self._bridge_error is not None:
                state = self._state(
                    ModelInferenceStatus.MODEL_UNAVAILABLE,
                    f"Heart Rate AI model unavailable: {self._bridge_error}",
                )
                return self._enrich(snapshot, prediction=None, state=state)
            if self._last_state is not None and self._last_state.status == ModelInferenceStatus.ERROR:
                return self._enrich(snapshot, prediction=None, state=self._last_state)
            state = self._state(
                ModelInferenceStatus.WARMING_UP,
                "Heart Rate AI waiting for an 8 s synchronized PPG + IMU window.",
            )
            return self._enrich(snapshot, prediction=None, state=state)

        bridge = self._ensure_bridge()
        if bridge is None:
            self._latest_prediction = None
            detail = self._bridge_error or "unknown model-loading error"
            state = self._state(
                ModelInferenceStatus.MODEL_UNAVAILABLE,
                f"Heart Rate AI model unavailable: {detail}",
            )
            return self._enrich(snapshot, prediction=None, state=state)

        try:
            for window in windows:
                prediction = bridge.predict(window)
                if snapshot.fault_injection is not None and snapshot.fault_injection.active:
                    provenance = prediction.provenance.model_copy(
                        update={"fault_injection": snapshot.fault_injection}
                    )
                    prediction = prediction.model_copy(update={"provenance": provenance})
                self._latest_prediction = prediction
        except ModelUnavailableError as exc:
            self._bridge_error = str(exc)
            self._latest_prediction = None
            state = self._state(
                ModelInferenceStatus.MODEL_UNAVAILABLE,
                f"Heart Rate AI model unavailable: {exc}",
            )
            return self._enrich(snapshot, prediction=None, state=state)
        except Exception as exc:  # canonical adapter failures become explicit, never synthetic
            self._latest_prediction = None
            state = self._state(
                ModelInferenceStatus.ERROR,
                f"Heart Rate AI inference failed: {exc}",
            )
            return self._enrich(snapshot, prediction=None, state=state)

        state = self._state(
            ModelInferenceStatus.AVAILABLE,
            "AI-estimated heart rate from synchronized recorded PPG + IMU.",
        )
        return self._enrich(snapshot, prediction=self._latest_prediction, state=state)
