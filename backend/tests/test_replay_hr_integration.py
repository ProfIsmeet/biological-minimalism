"""Phase 3 integration tests for replay-only heart-rate inference state."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from app.engine.data_sources import DataSourceManager
from app.engine.mock_data_engine import MockDataEngine
from app.ml.ppg_dalia_hr import DEFAULT_CHECKPOINT_PATH, ModelUnavailableError
from app.ml.ppg_dalia_windows import (
    ACC_FS,
    IMU_CHANNEL,
    PPG_FS,
    PPG_CHANNEL,
    PPGDaliaModelWindow,
)
from app.ml.replay_hr import ReplayHeartRateInferenceService
from app.schemas.data_source import (
    DataSourceType,
    RawChannelBatch,
    ReplayPlaybackState,
    TelemetrySourceMetadata,
)
from app.schemas.model_prediction import (
    HeartRateModelPrediction,
    HeartRateModelProvenance,
    ModelInferenceStatus,
)
from app.schemas.telemetry import LiveMetricsSnapshot

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
RAW_S14_ARCHIVE = REPOSITORY_ROOT / "datasets" / "ppg-dalia" / "raw_uci" / "ppg_dalia_uci.zip"


class RecordingBridge:
    def __init__(self) -> None:
        self.windows: list[PPGDaliaModelWindow] = []

    def predict(self, window: PPGDaliaModelWindow) -> HeartRateModelPrediction:
        self.windows.append(window)
        return HeartRateModelPrediction(
            value=60.0 + window.window_index,
            normalized_model_output=float(window.window_index),
            provenance=HeartRateModelProvenance(
                subject_id=window.subject_id,
                window_index=window.window_index,
                window_start_seconds=window.window_start_seconds,
                window_duration_seconds=window.window_duration_seconds,
                model_id="test-ppg-plus-imu",
                checkpoint_path="/test/model.pt",
                checkpoint_sha256="test-sha256",
            ),
        )


def _batch(
    channel_name: str,
    start_seconds: float,
    end_seconds: float,
    subject_id: str,
) -> RawChannelBatch:
    rate = PPG_FS if channel_name == PPG_CHANNEL else ACC_FS
    start_index = int(round(start_seconds * rate))
    end_index = int(round(end_seconds * rate))
    indexes = np.arange(start_index, end_index, dtype=np.float64)
    if channel_name == PPG_CHANNEL:
        samples: list[float] | list[list[float]] = np.sin(indexes / 17.0).tolist()
        axes = ["bvp"]
    else:
        samples = np.column_stack(
            (
                np.sin(indexes / 11.0),
                np.cos(indexes / 13.0),
                np.sin(indexes / 19.0),
            )
        ).tolist()
        axes = ["x", "y", "z"]
    return RawChannelBatch(
        dataset_name="PPG-DaLiA",
        subject_id=subject_id,
        channel_name=channel_name,
        device="recorded wrist sensor",
        role="physiological" if channel_name == PPG_CHANNEL else "context_artifact_reference",
        axes=axes,
        units="device units",
        sample_rate_hz=rate,
        sample_start_index=start_index,
        start_timestamp_seconds=start_index / rate,
        end_timestamp_seconds=(end_index - 1) / rate,
        samples=samples,
    )


def _replay_snapshot(
    start_seconds: float,
    end_seconds: float,
    *,
    subject_id: str = "S1",
    channels: tuple[str, ...] = (PPG_CHANNEL, IMU_CHANNEL),
) -> LiveMetricsSnapshot:
    return LiveMetricsSnapshot(
        timestamp=1_700_000_000.0 + end_seconds,
        source=TelemetrySourceMetadata(
            source_type=DataSourceType.DATASET_REPLAY,
            display_label="REAL RECORDED DATA — REPLAY MODE",
            dataset_name="PPG-DaLiA",
            subject_id=subject_id,
            replay_position_seconds=end_seconds,
            playback_state=ReplayPlaybackState.PLAYING,
            playback_speed=1.0,
            available_channels=list(channels),
        ),
        channels=[_batch(name, start_seconds, end_seconds, subject_id) for name in channels],
    )


def _synthetic_snapshot() -> LiveMetricsSnapshot:
    return LiveMetricsSnapshot(
        timestamp=1_700_000_100.0,
        source=TelemetrySourceMetadata(
            source_type=DataSourceType.SYNTHETIC,
            display_label="SYNTHETIC DEMO",
        ),
    )


def test_first_prediction_waits_for_eight_seconds_and_updates_only_on_stride() -> None:
    bridge = RecordingBridge()
    service = ReplayHeartRateInferenceService(
        Path("/test/model.pt"),
        bridge_factory=lambda _: bridge,
    )

    warming = service.process(_replay_snapshot(0.0, 7.5))
    assert warming.heart_rate_prediction is None
    assert warming.heart_rate_inference is not None
    assert warming.heart_rate_inference.status == ModelInferenceStatus.WARMING_UP
    assert bridge.windows == []

    first = service.process(_replay_snapshot(7.5, 8.0))
    assert first.heart_rate_prediction is not None
    assert first.heart_rate_prediction.value == 60.0
    assert first.heart_rate_prediction.provenance.window_start_seconds == 0.0
    assert [window.window_index for window in bridge.windows] == [0]

    for start in (8.0, 8.5, 9.0):
        held = service.process(_replay_snapshot(start, start + 0.5))
        assert held.heart_rate_prediction == first.heart_rate_prediction
    assert [window.window_index for window in bridge.windows] == [0]

    second = service.process(_replay_snapshot(10.0 - 0.5, 10.0))
    assert second.heart_rate_prediction is not None
    assert second.heart_rate_prediction.value == 61.0
    assert second.heart_rate_prediction.provenance.window_start_seconds == 2.0
    assert [window.window_index for window in bridge.windows] == [0, 1]


def test_missing_required_channel_is_explicit_and_never_calls_model() -> None:
    bridge = RecordingBridge()
    service = ReplayHeartRateInferenceService(bridge_factory=lambda _: bridge)

    snapshot = service.process(
        _replay_snapshot(0.0, 8.0, channels=(PPG_CHANNEL,))
    )

    assert snapshot.heart_rate_prediction is None
    assert snapshot.heart_rate_inference is not None
    assert snapshot.heart_rate_inference.status == ModelInferenceStatus.INPUT_UNAVAILABLE
    assert IMU_CHANNEL in snapshot.heart_rate_inference.message
    assert bridge.windows == []


def test_model_load_failure_is_explicit_without_fallback() -> None:
    def unavailable(_: Path) -> RecordingBridge:
        raise ModelUnavailableError("validated checkpoint is absent")

    service = ReplayHeartRateInferenceService(bridge_factory=unavailable)
    snapshot = service.process(_replay_snapshot(0.0, 8.0))

    assert snapshot.heart_rate_prediction is None
    assert snapshot.vitals is None
    assert snapshot.heart_rate_inference is not None
    assert snapshot.heart_rate_inference.status == ModelInferenceStatus.MODEL_UNAVAILABLE
    assert "validated checkpoint is absent" in snapshot.heart_rate_inference.message


def test_source_and_subject_switches_clear_previous_prediction_state() -> None:
    bridge = RecordingBridge()
    service = ReplayHeartRateInferenceService(bridge_factory=lambda _: bridge)
    first = service.process(_replay_snapshot(0.0, 8.0, subject_id="S1"))
    assert first.heart_rate_prediction is not None

    synthetic = service.process(_synthetic_snapshot())
    assert synthetic.heart_rate_prediction is None
    assert synthetic.heart_rate_inference is None

    partial_s2 = service.process(_replay_snapshot(0.0, 4.0, subject_id="S2"))
    assert partial_s2.heart_rate_prediction is None
    assert partial_s2.heart_rate_inference is not None
    assert partial_s2.heart_rate_inference.status == ModelInferenceStatus.WARMING_UP

    complete_s2 = service.process(_replay_snapshot(4.0, 8.0, subject_id="S2"))
    assert complete_s2.heart_rate_prediction is not None
    assert complete_s2.heart_rate_prediction.provenance.subject_id == "S2"
    assert [(window.subject_id, window.window_index) for window in bridge.windows] == [
        ("S1", 0),
        ("S2", 0),
    ]


@pytest.mark.skipif(
    not RAW_S14_ARCHIVE.exists() or not DEFAULT_CHECKPOINT_PATH.exists(),
    reason="official S14 archive and validated checkpoint are required",
)
def test_real_s14_replay_manager_produces_only_validated_hr_prediction() -> None:
    inference = ReplayHeartRateInferenceService(DEFAULT_CHECKPOINT_PATH)
    manager = DataSourceManager(
        MockDataEngine(seed=123),
        RAW_S14_ARCHIVE,
        replay_inference=inference,
    )
    manager.load_replay("S14", [PPG_CHANNEL, IMU_CHANNEL, "chest_ecg", "wrist_temp"])
    manager.play_replay()
    source = manager.replay_source

    snapshot = manager.tick(0.5, now=source._anchor_monotonic + 8.0)

    assert snapshot is not None
    assert snapshot.source.display_label == "REAL RECORDED DATA — REPLAY MODE"
    assert snapshot.source.subject_id == "S14"
    assert snapshot.heart_rate_inference is not None
    assert snapshot.heart_rate_inference.status == ModelInferenceStatus.AVAILABLE
    assert snapshot.heart_rate_prediction is not None
    assert snapshot.heart_rate_prediction.evidence_level.value == "AI_ESTIMATED"
    assert snapshot.heart_rate_prediction.uncertainty is None
    assert snapshot.heart_rate_prediction.provenance.subject_id == "S14"
    assert snapshot.heart_rate_prediction.provenance.window_start_seconds == 0.0
    assert snapshot.vitals is not None
    assert snapshot.vitals.heart_rate_bpm is None
    assert snapshot.cognitive is None
    assert snapshot.space_adaptation is None
    assert snapshot.ai_confidence is None
