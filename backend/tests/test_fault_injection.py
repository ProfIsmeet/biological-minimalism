"""Phase 4 correctness tests for replay-only deterministic fault injection."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from app.engine.fault_injection import ReplayFaultInjector
from app.ml.ppg_dalia_hr import DEFAULT_CHECKPOINT_PATH
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
from app.schemas.fault_injection import ReplayFaultConfig, ReplayFaultTarget, ReplayFaultType
from app.schemas.model_prediction import (
    HeartRateModelPrediction,
    HeartRateModelProvenance,
    ModelInferenceStatus,
)
from app.schemas.telemetry import LiveMetricsSnapshot


class RecordingBridge:
    def __init__(self) -> None:
        self.windows: list[PPGDaliaModelWindow] = []

    def predict(self, window: PPGDaliaModelWindow) -> HeartRateModelPrediction:
        self.windows.append(window)
        return HeartRateModelPrediction(
            value=71.0,
            normalized_model_output=0.0,
            provenance=HeartRateModelProvenance(
                subject_id=window.subject_id,
                window_index=window.window_index,
                window_start_seconds=window.window_start_seconds,
                window_duration_seconds=window.window_duration_seconds,
                model_id="fault-test-model",
                checkpoint_path="/test/model.pt",
                checkpoint_sha256="fault-test-sha",
            ),
        )


def _batch(channel_name: str, duration_seconds: float, subject_id: str = "S1") -> RawChannelBatch:
    rate = PPG_FS if channel_name == PPG_CHANNEL else ACC_FS
    count = int(round(duration_seconds * rate))
    indexes = np.arange(count, dtype=np.float64)
    if channel_name == PPG_CHANNEL:
        samples: list[float] | list[list[float]] = (np.sin(indexes / 9.0) + indexes / 1000.0).tolist()
        axes = ["bvp"]
    else:
        samples = np.column_stack(
            (np.sin(indexes / 7.0), np.cos(indexes / 11.0), indexes / 100.0)
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
        sample_start_index=0,
        start_timestamp_seconds=0.0,
        end_timestamp_seconds=(count - 1) / rate,
        samples=samples,
    )


def _snapshot(duration_seconds: float = 8.0, subject_id: str = "S1") -> LiveMetricsSnapshot:
    return LiveMetricsSnapshot(
        timestamp=1_700_000_000.0 + duration_seconds,
        source=TelemetrySourceMetadata(
            source_type=DataSourceType.DATASET_REPLAY,
            display_label="REAL RECORDED DATA — REPLAY MODE",
            dataset_name="PPG-DaLiA",
            subject_id=subject_id,
            replay_position_seconds=duration_seconds,
            playback_state=ReplayPlaybackState.PLAYING,
            playback_speed=1.0,
            available_channels=[PPG_CHANNEL, IMU_CHANNEL],
        ),
        channels=[
            _batch(PPG_CHANNEL, duration_seconds, subject_id),
            _batch(IMU_CHANNEL, duration_seconds, subject_id),
        ],
    )


def _synthetic_snapshot() -> LiveMetricsSnapshot:
    return LiveMetricsSnapshot(
        timestamp=1_700_000_100.0,
        source=TelemetrySourceMetadata(
            source_type=DataSourceType.SYNTHETIC,
            display_label="SYNTHETIC DEMO",
        ),
    )


def test_disabled_fault_path_returns_the_clean_snapshot_unchanged() -> None:
    injector = ReplayFaultInjector()
    clean = _snapshot()

    assert injector.apply(clean) is clean
    assert injector.status().active is False


def test_binary_faults_normalize_to_full_severity() -> None:
    dropout = ReplayFaultConfig(
        fault_type=ReplayFaultType.MODALITY_DROPOUT,
        target=ReplayFaultTarget.PPG,
        severity=0.1,
    )
    frozen = ReplayFaultConfig(
        fault_type=ReplayFaultType.FROZEN_SENSOR,
        target=ReplayFaultTarget.IMU,
        severity=0.0,
    )

    assert dropout.severity == 1.0
    assert frozen.severity == 1.0


def test_additive_noise_is_deterministic_for_fixed_config_and_seed() -> None:
    config = ReplayFaultConfig(
        fault_type=ReplayFaultType.ADDITIVE_NOISE,
        target=ReplayFaultTarget.BOTH,
        severity=0.35,
        seed=2026,
    )
    first = ReplayFaultInjector()
    second = ReplayFaultInjector()
    first.configure(config)
    second.configure(config)

    first_output = first.apply(_snapshot()).model_dump(mode="json")
    second_output = second.apply(_snapshot()).model_dump(mode="json")

    assert first_output == second_output
    assert first_output["fault_injection"]["seed"] == 2026


def test_clear_removes_fault_state_and_prevents_data_contamination() -> None:
    injector = ReplayFaultInjector()
    injector.configure(
        ReplayFaultConfig(
            fault_type=ReplayFaultType.FROZEN_SENSOR,
            target=ReplayFaultTarget.PPG,
        )
    )
    assert injector.apply(_snapshot()).fault_injection is not None

    injector.clear()
    clean = _snapshot()
    assert injector.apply(clean) is clean
    assert injector.status().active is False


def test_source_switch_clears_fault_configuration_and_state() -> None:
    injector = ReplayFaultInjector()
    injector.configure(
        ReplayFaultConfig(
            fault_type=ReplayFaultType.ADDITIVE_NOISE,
            target=ReplayFaultTarget.PPG,
            severity=0.2,
            seed=4,
        )
    )
    injector.apply(_snapshot())

    synthetic = _synthetic_snapshot()
    assert injector.apply(synthetic) is synthetic
    assert injector.status().active is False


def test_subject_switch_clears_fault_instead_of_reusing_prior_state() -> None:
    injector = ReplayFaultInjector()
    injector.configure(
        ReplayFaultConfig(
            fault_type=ReplayFaultType.FROZEN_SENSOR,
            target=ReplayFaultTarget.PPG,
        )
    )
    injector.apply(_snapshot(subject_id="S1"))

    clean_s2 = _snapshot(subject_id="S2")
    assert injector.apply(clean_s2) is clean_s2
    assert injector.status().active is False


@pytest.mark.parametrize(
    ("target", "missing"),
    [
        (ReplayFaultTarget.PPG, {PPG_CHANNEL}),
        (ReplayFaultTarget.IMU, {IMU_CHANNEL}),
        (ReplayFaultTarget.BOTH, {PPG_CHANNEL, IMU_CHANNEL}),
    ],
)
def test_modality_dropout_matrix_never_fabricates_heart_rate(
    target: ReplayFaultTarget,
    missing: set[str],
) -> None:
    bridge = RecordingBridge()
    service = ReplayHeartRateInferenceService(bridge_factory=lambda _: bridge)
    injector = ReplayFaultInjector()
    injector.configure(
        ReplayFaultConfig(fault_type=ReplayFaultType.MODALITY_DROPOUT, target=target)
    )

    output = service.process(injector.apply(_snapshot()))

    assert output.heart_rate_prediction is None
    assert output.heart_rate_inference is not None
    assert output.heart_rate_inference.status == ModelInferenceStatus.INPUT_UNAVAILABLE
    assert missing.isdisjoint(output.source.available_channels)
    assert bridge.windows == []


def test_imu_noise_is_passed_to_canonical_contract_with_explicit_provenance() -> None:
    bridge = RecordingBridge()
    service = ReplayHeartRateInferenceService(bridge_factory=lambda _: bridge)
    injector = ReplayFaultInjector()
    injector.configure(
        ReplayFaultConfig(
            fault_type=ReplayFaultType.ADDITIVE_NOISE,
            target=ReplayFaultTarget.IMU,
            severity=0.5,
            seed=19,
        )
    )

    output = service.process(injector.apply(_snapshot()))

    assert output.heart_rate_prediction is not None
    assert output.heart_rate_prediction.uncertainty is None
    provenance = output.heart_rate_prediction.provenance
    assert provenance.fault_injection is not None
    assert provenance.fault_injection.fault_type == ReplayFaultType.ADDITIVE_NOISE
    assert provenance.fault_injection.target == ReplayFaultTarget.IMU
    assert provenance.model_id == "fault-test-model"
    assert len(bridge.windows) == 1


@pytest.mark.skipif(not DEFAULT_CHECKPOINT_PATH.exists(), reason="validated checkpoint is required")
def test_frozen_ppg_reaches_canonical_flat_signal_rejection() -> None:
    injector = ReplayFaultInjector()
    injector.configure(
        ReplayFaultConfig(
            fault_type=ReplayFaultType.FROZEN_SENSOR,
            target=ReplayFaultTarget.PPG,
        )
    )
    service = ReplayHeartRateInferenceService(DEFAULT_CHECKPOINT_PATH)

    output = service.process(injector.apply(_snapshot()))

    assert output.heart_rate_prediction is None
    assert output.heart_rate_inference is not None
    assert output.heart_rate_inference.status == ModelInferenceStatus.ERROR
    assert "flat/dead" in output.heart_rate_inference.message


def test_packet_loss_preserves_original_sample_indexes_and_timestamps() -> None:
    snapshot = _snapshot(duration_seconds=1.0)
    original_ppg = snapshot.channels[0]
    original_ppg.samples = np.arange(int(PPG_FS), dtype=np.float64).tolist()
    injector = ReplayFaultInjector()
    injector.configure(
        ReplayFaultConfig(
            fault_type=ReplayFaultType.PACKET_LOSS,
            target=ReplayFaultTarget.PPG,
            severity=0.35,
            seed=77,
        )
    )

    output = injector.apply(snapshot)
    segments = [batch for batch in output.channels if batch.channel_name == PPG_CHANNEL]
    retained_indexes: list[int] = []
    for segment in segments:
        count = len(segment.samples)
        indexes = list(range(segment.sample_start_index, segment.sample_start_index + count))
        retained_indexes.extend(indexes)
        assert segment.start_timestamp_seconds == segment.sample_start_index / PPG_FS
        assert segment.end_timestamp_seconds == indexes[-1] / PPG_FS
        assert segment.samples == [float(index) for index in indexes]

    assert len(retained_indexes) < int(PPG_FS)
    assert any(right - left > 1 for left, right in zip(retained_indexes, retained_indexes[1:]))
    assert output.fault_injection is not None
    assert output.fault_injection.dropped_samples[PPG_CHANNEL] == int(PPG_FS) - len(retained_indexes)

    bridge = RecordingBridge()
    inferred = ReplayHeartRateInferenceService(bridge_factory=lambda _: bridge).process(output)
    assert inferred.heart_rate_prediction is None
    assert inferred.heart_rate_inference is not None
    assert inferred.heart_rate_inference.status == ModelInferenceStatus.ERROR
    assert "expected next sample index" in inferred.heart_rate_inference.message
    assert bridge.windows == []


def test_full_saturation_is_controlled_flat_corruption_with_metadata() -> None:
    injector = ReplayFaultInjector()
    injector.configure(
        ReplayFaultConfig(
            fault_type=ReplayFaultType.SATURATION,
            target=ReplayFaultTarget.PPG,
            severity=1.0,
            seed=0,
        )
    )

    output = injector.apply(_snapshot(duration_seconds=1.0))
    ppg = next(batch for batch in output.channels if batch.channel_name == PPG_CHANNEL)

    assert np.ptp(np.asarray(ppg.samples)) == 0.0
    assert output.fault_injection is not None
    assert "wrist_bvp.clip_lower" in output.fault_injection.parameters
    assert "wrist_bvp.clip_upper" in output.fault_injection.parameters
