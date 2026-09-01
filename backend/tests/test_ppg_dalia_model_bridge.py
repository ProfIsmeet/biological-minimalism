"""Phase 2 tests for synchronized replay windows and canonical HR inference."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from app.ml.ppg_dalia_hr import (
    DEFAULT_CHECKPOINT_PATH,
    EXPECTED_CHECKPOINT_SHA256,
    EXPECTED_CHECKPOINT_SIZE_BYTES,
    CheckpointIdentityError,
    ModelUnavailableError,
    PPGDaliaHRInferenceBridge,
)
from app.ml.ppg_dalia_windows import (
    ACC_FS,
    ACC_WINDOW_SAMPLES,
    DATASET_NAME,
    IMU_CHANNEL,
    PPG_FS,
    PPG_WINDOW_SAMPLES,
    PPG_CHANNEL,
    STEP_SECONDS,
    WINDOW_SECONDS,
    PPGDaliaModelWindow,
    PPGDaliaWindowAssembler,
    WindowChannelError,
    WindowIdentityError,
)
from app.engine.data_sources import DatasetReplaySource
from app.schemas.data_source import (
    DataSourceType,
    RawChannelBatch,
    ReplayPlaybackState,
    TelemetrySourceMetadata,
)
from app.schemas.model_prediction import EvidenceLevel
from app.schemas.telemetry import LiveMetricsSnapshot
from ml.datasets.ppg_dalia import (
    zscore_imu_window as training_zscore_imu_window,
    zscore_ppg_window as training_zscore_ppg_window,
)
from ml.inference import ppg_dalia_hr as canonical_inference
from ml.inference.ppg_dalia_hr import PPGDaliaHRPredictor

REPO_ROOT = Path(__file__).resolve().parents[2]
RAW_ARCHIVE = REPO_ROOT / "datasets" / "ppg-dalia" / "raw_uci" / "ppg_dalia_uci.zip"
GOLDEN_REFERENCE = REPO_ROOT / "results" / "ppg_dalia_integration_reference.json"


def _ppg_values(start: int, count: int, *, offset: float = 0.0) -> np.ndarray:
    return np.arange(start, start + count, dtype=np.float64) + offset


def _imu_values(start: int, count: int, *, offset: float = 0.0) -> np.ndarray:
    base = np.arange(start, start + count, dtype=np.float64) + offset
    return np.column_stack((base, base + 10_000.0, base + 20_000.0))


def _batch(
    channel_name: str,
    start_index: int,
    samples: np.ndarray,
    *,
    subject_id: str = "S1",
) -> RawChannelBatch:
    if channel_name == PPG_CHANNEL:
        rate, axes, device, role = PPG_FS, ["bvp"], "Empatica E4 (wrist)", "physiological"
    elif channel_name == IMU_CHANNEL:
        rate, axes, device, role = ACC_FS, ["x", "y", "z"], "Empatica E4 (wrist)", "context_artifact_reference"
    else:
        raise AssertionError(f"Unsupported test channel {channel_name}")
    return RawChannelBatch(
        dataset_name=DATASET_NAME,
        subject_id=subject_id,
        channel_name=channel_name,
        device=device,
        role=role,
        axes=axes,
        units="device units",
        sample_rate_hz=rate,
        sample_start_index=start_index,
        start_timestamp_seconds=start_index / rate,
        end_timestamp_seconds=(start_index + len(samples) - 1) / rate,
        samples=samples.tolist(),
    )


def _replay_snapshot(
    *,
    ppg_start: int,
    ppg: np.ndarray,
    imu_start: int,
    imu: np.ndarray,
    subject_id: str = "S1",
    replay_position: float | None = None,
    batch_subject_id: str | None = None,
) -> LiveMetricsSnapshot:
    position = replay_position if replay_position is not None else max(
        (ppg_start + len(ppg)) / PPG_FS,
        (imu_start + len(imu)) / ACC_FS,
    )
    batch_subject = batch_subject_id or subject_id
    return LiveMetricsSnapshot(
        timestamp=1_700_000_000.0 + position,
        source=TelemetrySourceMetadata(
            source_type=DataSourceType.DATASET_REPLAY,
            display_label="REAL RECORDED DATA — REPLAY MODE",
            dataset_name=DATASET_NAME,
            subject_id=subject_id,
            replay_position_seconds=position,
            playback_state=ReplayPlaybackState.PLAYING,
            playback_speed=1.0,
            available_channels=[PPG_CHANNEL, IMU_CHANNEL],
        ),
        channels=[
            _batch(PPG_CHANNEL, ppg_start, ppg, subject_id=batch_subject),
            _batch(IMU_CHANNEL, imu_start, imu, subject_id=batch_subject),
        ],
    )


def _synthetic_snapshot() -> LiveMetricsSnapshot:
    return LiveMetricsSnapshot(
        timestamp=1_700_000_000.0,
        source=TelemetrySourceMetadata(
            source_type=DataSourceType.SYNTHETIC,
            display_label="SYNTHETIC DEMO",
        ),
    )


def _model_window(subject_id: str = "S14") -> PPGDaliaModelWindow:
    ppg = np.sin(np.linspace(0.0, 12.0, PPG_WINDOW_SAMPLES, dtype=np.float64))
    imu = np.vstack(
        [
            np.cos(np.linspace(0.0, 8.0, ACC_WINDOW_SAMPLES, dtype=np.float64)),
            np.sin(np.linspace(0.0, 5.0, ACC_WINDOW_SAMPLES, dtype=np.float64)),
            np.linspace(-1.0, 1.0, ACC_WINDOW_SAMPLES, dtype=np.float64),
        ]
    )
    return PPGDaliaModelWindow(
        dataset_name=DATASET_NAME,
        subject_id=subject_id,
        window_index=0,
        window_start_seconds=0.0,
        window_duration_seconds=WINDOW_SECONDS,
        ppg_start_index=0,
        imu_start_index=0,
        ppg=ppg,
        imu=imu,
    )


def test_no_window_until_both_channels_have_exact_eight_seconds() -> None:
    assembler = PPGDaliaWindowAssembler()
    first = _replay_snapshot(
        ppg_start=0,
        ppg=_ppg_values(0, 480),
        imu_start=0,
        imu=_imu_values(0, 240),
        replay_position=7.5,
    )
    assert assembler.ingest(first) == []

    second = _replay_snapshot(
        ppg_start=480,
        ppg=_ppg_values(480, 32),
        imu_start=240,
        imu=_imu_values(240, 16),
        replay_position=8.0,
    )
    windows = assembler.ingest(second)

    assert len(windows) == 1
    window = windows[0]
    assert window.ppg.shape == (512,)
    assert window.imu.shape == (3, 256)
    assert window.window_start_seconds == 0.0
    assert window.ppg_start_index == 0
    assert window.imu_start_index == 0
    assert np.array_equal(window.ppg, _ppg_values(0, 512))
    assert np.array_equal(window.imu, _imu_values(0, 256).T)


def test_windows_use_exact_two_second_stride_and_native_alignment() -> None:
    assembler = PPGDaliaWindowAssembler()
    windows = assembler.ingest(
        _replay_snapshot(
            ppg_start=0,
            ppg=_ppg_values(0, 12 * int(PPG_FS)),
            imu_start=0,
            imu=_imu_values(0, 12 * int(ACC_FS)),
            replay_position=12.0,
        )
    )

    assert [window.window_index for window in windows] == [0, 1, 2]
    assert [window.window_start_seconds for window in windows] == [0.0, 2.0, 4.0]
    assert [window.ppg_start_index for window in windows] == [0, 128, 256]
    assert [window.imu_start_index for window in windows] == [0, 64, 128]
    assert all(window.ppg.shape == (PPG_WINDOW_SAMPLES,) for window in windows)
    assert all(window.imu.shape == (3, ACC_WINDOW_SAMPLES) for window in windows)


def test_pause_without_batches_preserves_partial_window() -> None:
    assembler = PPGDaliaWindowAssembler()
    first = _replay_snapshot(
        ppg_start=0,
        ppg=_ppg_values(0, 256),
        imu_start=0,
        imu=_imu_values(0, 128),
        replay_position=4.0,
    )
    assert assembler.ingest(first) == []
    before_pause = assembler.buffered_samples

    # DatasetReplaySource emits no snapshot while paused, so the assembler is
    # intentionally untouched until the next contiguous resumed batch.
    assert assembler.buffered_samples == before_pause
    resumed = _replay_snapshot(
        ppg_start=256,
        ppg=_ppg_values(256, 256),
        imu_start=128,
        imu=_imu_values(128, 128),
        replay_position=8.0,
    )
    windows = assembler.ingest(resumed)
    assert len(windows) == 1
    assert windows[0].window_index == 0


def test_reset_and_subject_switch_clear_partial_buffers() -> None:
    assembler = PPGDaliaWindowAssembler()
    partial_s1 = _replay_snapshot(
        ppg_start=0,
        ppg=_ppg_values(0, 256, offset=1_000.0),
        imu_start=0,
        imu=_imu_values(0, 128, offset=1_000.0),
        subject_id="S1",
        replay_position=4.0,
    )
    assert assembler.ingest(partial_s1) == []

    full_s2 = _replay_snapshot(
        ppg_start=0,
        ppg=_ppg_values(0, 512, offset=2_000.0),
        imu_start=0,
        imu=_imu_values(0, 256, offset=2_000.0),
        subject_id="S2",
        replay_position=8.0,
    )
    windows = assembler.ingest(full_s2)
    assert len(windows) == 1
    assert windows[0].subject_id == "S2"
    assert windows[0].ppg[0] == 2_000.0
    assert assembler.identity == (DATASET_NAME, "S2")

    assembler.reset()
    assert assembler.identity is None
    assert assembler.buffered_samples == {PPG_CHANNEL: 0, IMU_CHANNEL: 0}
    repeated = assembler.ingest(full_s2)
    assert len(repeated) == 1
    assert repeated[0].window_index == 0


def test_source_change_clears_buffers() -> None:
    assembler = PPGDaliaWindowAssembler()
    partial = _replay_snapshot(
        ppg_start=0,
        ppg=_ppg_values(0, 256),
        imu_start=0,
        imu=_imu_values(0, 128),
        replay_position=4.0,
    )
    assembler.ingest(partial)
    assert assembler.ingest(_synthetic_snapshot()) == []
    assert assembler.identity is None
    assert assembler.buffered_samples == {PPG_CHANNEL: 0, IMU_CHANNEL: 0}


def test_batch_subject_mismatch_is_rejected() -> None:
    assembler = PPGDaliaWindowAssembler()
    mismatched = _replay_snapshot(
        ppg_start=0,
        ppg=_ppg_values(0, 512),
        imu_start=0,
        imu=_imu_values(0, 256),
        subject_id="S1",
        batch_subject_id="S2",
        replay_position=8.0,
    )
    with pytest.raises(WindowIdentityError, match="refusing to mix subjects"):
        assembler.ingest(mismatched)


def test_imu_axis_order_is_validated() -> None:
    assembler = PPGDaliaWindowAssembler()
    snapshot = _replay_snapshot(
        ppg_start=0,
        ppg=_ppg_values(0, 512),
        imu_start=0,
        imu=_imu_values(0, 256),
        replay_position=8.0,
    )
    snapshot.channels[1].axes = ["z", "y", "x"]
    with pytest.raises(WindowChannelError, match="axis order"):
        assembler.ingest(snapshot)


def test_same_subject_replay_index_rollback_resets_window_state() -> None:
    assembler = PPGDaliaWindowAssembler()
    full = _replay_snapshot(
        ppg_start=0,
        ppg=_ppg_values(0, 512),
        imu_start=0,
        imu=_imu_values(0, 256),
        replay_position=8.0,
    )
    first = assembler.ingest(full)
    repeated_after_reset = assembler.ingest(full)

    assert [window.window_index for window in first] == [0]
    assert [window.window_index for window in repeated_after_reset] == [0]
    assert np.array_equal(first[0].ppg, repeated_after_reset[0].ppg)


def test_model_window_rejects_wrong_shapes() -> None:
    with pytest.raises(WindowChannelError, match="raw PPG shape"):
        PPGDaliaModelWindow(
            dataset_name=DATASET_NAME,
            subject_id="S1",
            window_index=0,
            window_start_seconds=0.0,
            window_duration_seconds=WINDOW_SECONDS,
            ppg_start_index=0,
            imu_start_index=0,
            ppg=np.zeros(PPG_WINDOW_SAMPLES - 1),
            imu=np.zeros((3, ACC_WINDOW_SAMPLES)),
        )


def test_canonical_inference_reuses_training_preprocessing_functions() -> None:
    assert canonical_inference.zscore_ppg_window is training_zscore_ppg_window
    assert canonical_inference.zscore_imu_window is training_zscore_imu_window


def test_missing_or_wrong_checkpoint_fails_without_fallback(tmp_path: Path) -> None:
    with pytest.raises(ModelUnavailableError, match="no synthetic or rule-based fallback"):
        PPGDaliaHRInferenceBridge(tmp_path / "missing.pt")

    wrong = tmp_path / "wrong.pt"
    wrong.write_bytes(b"not the validated checkpoint")
    with pytest.raises(CheckpointIdentityError, match="size mismatch"):
        PPGDaliaHRInferenceBridge(wrong)


@pytest.mark.skipif(not DEFAULT_CHECKPOINT_PATH.exists(), reason="validated checkpoint not transferred")
def test_bridge_uses_canonical_predictor_and_is_deterministic() -> None:
    bridge = PPGDaliaHRInferenceBridge()
    assert isinstance(bridge.canonical_predictor, PPGDaliaHRPredictor)
    assert bridge.canonical_predictor.checkpoint_path.resolve() == DEFAULT_CHECKPOINT_PATH.resolve()

    window = _model_window()
    first = bridge.predict(window)
    second = bridge.predict(window)
    assert first == second
    assert first.prediction_type == "heart_rate"
    assert first.unit == "bpm"
    assert first.evidence_level == EvidenceLevel.AI_ESTIMATED
    assert first.uncertainty is None
    assert first.provenance.subject_id == "S14"
    assert first.provenance.checkpoint_sha256 == EXPECTED_CHECKPOINT_SHA256


def test_checkpoint_identity_constants_match_golden_reference() -> None:
    reference = json.loads(GOLDEN_REFERENCE.read_text())
    assert reference["checkpoint_size_bytes"] == EXPECTED_CHECKPOINT_SIZE_BYTES
    assert reference["checkpoint_sha256"] == EXPECTED_CHECKPOINT_SHA256


@pytest.mark.skipif(
    not DEFAULT_CHECKPOINT_PATH.exists() or not RAW_ARCHIVE.exists(),
    reason="validated checkpoint and official S14 archive are required",
)
def test_replay_window_assembler_and_bridge_match_all_golden_windows() -> None:
    reference = json.loads(GOLDEN_REFERENCE.read_text())
    final_window_index = max(item["window_index"] for item in reference["windows"])
    duration_seconds = final_window_index * STEP_SECONDS + WINDOW_SECONDS
    replay = DatasetReplaySource(
        RAW_ARCHIVE,
        monotonic_clock=lambda: 0.0,
        wall_clock=lambda: 1_700_000_000.0,
    )
    replay.load_subject("S14", channel_names=[PPG_CHANNEL, IMU_CHANNEL])
    replay.play()
    snapshot = replay.tick(0.0, now=duration_seconds)
    assert snapshot is not None

    assembler = PPGDaliaWindowAssembler()
    windows = assembler.ingest(snapshot)
    by_index = {window.window_index: window for window in windows}
    bridge = PPGDaliaHRInferenceBridge()

    for item in reference["windows"]:
        window = by_index[item["window_index"]]
        prediction = bridge.predict(window)
        assert prediction.provenance.subject_id == "S14"
        assert prediction.provenance.window_start_seconds == item["window_start_seconds"]
        assert prediction.value == pytest.approx(item["expected_model_hr_prediction_bpm"], abs=1e-3)
