"""Scientific-integrity and timing tests for PPG-DaLiA dataset replay."""

from __future__ import annotations

import pickle
from pathlib import Path

import numpy as np
import pytest

from app.data.ppg_dalia import (
    PpgDaliaChannelError,
    PpgDaliaSubjectError,
)
from app.engine.data_sources import (
    DataSourceManager,
    DatasetReplaySource,
    ReplayStateError,
    UnsupportedPlaybackSpeedError,
)
from app.engine.mock_data_engine import MockDataEngine
from app.schemas.data_source import DataSourceType, ReplayPlaybackState


class ManualClock:
    def __init__(self) -> None:
        self.value = 0.0

    def __call__(self) -> float:
        return self.value

    def advance(self, seconds: float) -> None:
        self.value += seconds


def _write_subject(
    root: Path,
    subject_id: str,
    duration_seconds: float = 20.0,
    offset: float = 0.0,
    *,
    embedded_subject_id: str | None = None,
) -> None:
    subject_dir = root / "PPG_FieldStudy" / subject_id
    subject_dir.mkdir(parents=True)

    def scalar(rate: float) -> np.ndarray:
        count = int(duration_seconds * rate)
        return (np.arange(count, dtype=np.float64) + offset).reshape(-1, 1)

    def vector(rate: float) -> np.ndarray:
        count = int(duration_seconds * rate)
        base = np.arange(count, dtype=np.float64) + offset
        return np.column_stack((base, base + 0.1, base + 0.2))

    raw = {
        "subject": embedded_subject_id or subject_id,
        "signal": {
            "wrist": {
                "BVP": scalar(64.0),
                "ACC": vector(32.0),
                "EDA": scalar(4.0),
                "TEMP": scalar(4.0),
            },
            "chest": {
                "ECG": scalar(700.0),
                "ACC": vector(700.0),
                "Resp": scalar(700.0),
                "Temp": scalar(700.0),
                "EDA": scalar(700.0),
                "EMG": scalar(700.0),
            },
        },
    }
    with (subject_dir / f"{subject_id}.pkl").open("wb") as stream:
        pickle.dump(raw, stream, protocol=pickle.HIGHEST_PROTOCOL)


@pytest.fixture
def dataset_root(tmp_path: Path) -> Path:
    _write_subject(tmp_path, "S1", offset=1000.0)
    _write_subject(tmp_path, "S2", offset=2000.0)
    return tmp_path


def _source(dataset_root: Path, clock: ManualClock) -> DatasetReplaySource:
    source = DatasetReplaySource(
        dataset_root,
        monotonic_clock=clock,
        wall_clock=lambda: 1_700_000_000.0 + clock.value,
    )
    source.load_subject("S1")
    return source


def _batch(frame, channel_name: str):
    return next(batch for batch in frame.channels if batch.channel_name == channel_name)


def test_no_subject_mixing(dataset_root: Path) -> None:
    clock = ManualClock()
    source = _source(dataset_root, clock)
    assert source.recording.subject_id == "S1"
    assert all(channel.samples[0, 0] < 2000.0 for channel in source.recording.channels.values())

    source.play()
    clock.advance(0.5)
    frame = source.tick(0.5)
    assert frame is not None
    assert frame.source.subject_id == "S1"
    assert {batch.subject_id for batch in frame.channels} == {"S1"}


def test_embedded_subject_mismatch_is_rejected(tmp_path: Path) -> None:
    _write_subject(tmp_path, "S1", embedded_subject_id="S2")
    source = DatasetReplaySource(tmp_path)

    with pytest.raises(
        PpgDaliaSubjectError,
        match=r"Requested S1, but the recording identifies itself as 'S2'; refusing to mix or relabel subjects",
    ):
        source.load_subject("S1")


def test_reset_replays_identical_first_values_and_indexes(dataset_root: Path) -> None:
    clock = ManualClock()
    source = _source(dataset_root, clock)
    source.play()
    clock.advance(0.5)
    first = source.tick(0.5)
    assert first is not None
    assert any(index > 0 for index in source.channel_indexes.values())

    source.reset()
    assert source.channel_indexes == {name: 0 for name in source.recording.channels}
    assert source.status().replay_position_seconds == 0.0
    source.play()
    clock.advance(0.5)
    repeated = source.tick(0.5)
    assert repeated is not None

    assert _batch(first, "wrist_bvp").samples == _batch(repeated, "wrist_bvp").samples
    assert _batch(first, "wrist_acc").samples == _batch(repeated, "wrist_acc").samples
    assert _batch(first, "chest_ecg").samples == _batch(repeated, "chest_ecg").samples


def test_pause_freezes_position_and_indexes(dataset_root: Path) -> None:
    clock = ManualClock()
    source = _source(dataset_root, clock)
    source.play()
    clock.advance(1.0)
    assert source.tick(0.5) is not None
    source.pause()
    indexes = source.channel_indexes
    position = source.status().replay_position_seconds

    clock.advance(30.0)
    assert source.tick(0.5) is None
    assert source.channel_indexes == indexes
    assert source.status().replay_position_seconds == position


def test_pause_resume_preserves_sample_continuity(dataset_root: Path) -> None:
    clock = ManualClock()
    source = _source(dataset_root, clock)
    source.play()
    clock.advance(1.0)
    before_pause = source.tick(0.5)
    assert before_pause is not None
    source.pause()

    clock.advance(30.0)
    source.play()
    clock.advance(0.5)
    after_resume = source.tick(0.5)
    assert after_resume is not None

    first_batch = _batch(before_pause, "wrist_bvp")
    resumed_batch = _batch(after_resume, "wrist_bvp")
    assert resumed_batch.sample_start_index == first_batch.sample_start_index + len(first_batch.samples)
    assert resumed_batch.samples[0] == first_batch.samples[-1] + 1.0


@pytest.mark.parametrize(("speed", "expected_ppg_samples"), [(1.0, 64), (5.0, 320), (10.0, 640)])
def test_playback_speed_changes_scheduling_not_values(
    dataset_root: Path,
    speed: float,
    expected_ppg_samples: int,
) -> None:
    clock = ManualClock()
    source = _source(dataset_root, clock)
    source.set_speed(speed)
    source.play()
    clock.advance(1.0)
    frame = source.tick(0.5)
    assert frame is not None
    samples = _batch(frame, "wrist_bvp").samples
    assert len(samples) == expected_ppg_samples
    assert samples == list(np.arange(expected_ppg_samples, dtype=float) + 1000.0)


def test_mid_play_speed_change_preserves_sample_continuity(dataset_root: Path) -> None:
    clock = ManualClock()
    source = _source(dataset_root, clock)
    source.play()
    clock.advance(1.0)
    at_one_x = source.tick(0.5)
    assert at_one_x is not None

    source.set_speed(5.0)
    clock.advance(0.2)
    at_five_x = source.tick(0.5)
    assert at_five_x is not None

    first_batch = _batch(at_one_x, "wrist_bvp")
    faster_batch = _batch(at_five_x, "wrist_bvp")
    assert faster_batch.sample_start_index == first_batch.sample_start_index + len(first_batch.samples)
    assert faster_batch.samples[0] == first_batch.samples[-1] + 1.0


def test_channel_timestamps_are_monotonic_across_frames(dataset_root: Path) -> None:
    clock = ManualClock()
    source = _source(dataset_root, clock)
    source.play()
    previous_end: dict[str, float] = {}

    for _ in range(4):
        clock.advance(0.5)
        frame = source.tick(0.5)
        assert frame is not None
        for batch in frame.channels:
            assert batch.end_timestamp_seconds >= batch.start_timestamp_seconds
            if batch.channel_name in previous_end:
                assert batch.start_timestamp_seconds > previous_end[batch.channel_name]
            previous_end[batch.channel_name] = batch.end_timestamp_seconds


def test_cross_channel_alignment_uses_one_common_timeline(dataset_root: Path) -> None:
    clock = ManualClock()
    source = _source(dataset_root, clock)
    source.play()
    clock.advance(2.0)
    frame = source.tick(0.5)
    assert frame is not None

    assert len(_batch(frame, "wrist_bvp").samples) == 128
    assert len(_batch(frame, "wrist_acc").samples) == 64
    assert len(_batch(frame, "chest_ecg").samples) == 1400
    assert len(_batch(frame, "wrist_temp").samples) == 8
    assert {batch.start_timestamp_seconds for batch in frame.channels} == {0.0}
    assert frame.source.replay_position_seconds == 2.0


def test_synthetic_source_regression(dataset_root: Path) -> None:
    manager = DataSourceManager(MockDataEngine(seed=123), dataset_root)
    frame = manager.tick(0.5)
    assert frame is not None
    assert frame.source.source_type == DataSourceType.SYNTHETIC
    assert frame.vitals is not None
    assert frame.cognitive is not None
    assert frame.ai_confidence is not None


def test_subject_switch_clears_prior_replay_history_and_state(dataset_root: Path) -> None:
    manager = DataSourceManager(MockDataEngine(seed=123), dataset_root)
    manager.load_replay("S1")
    manager.play_replay()
    first_source = manager.replay_source
    first_frame = manager.tick(0.5, now=first_source._anchor_monotonic + 0.5)
    assert first_frame is not None
    assert manager.history(10)

    status = manager.load_replay("S2")

    assert status.subject_id == "S2"
    assert status.replay_position_seconds == 0.0
    assert status.playback_state == ReplayPlaybackState.PAUSED
    assert manager.replay_source is not first_source
    assert all(index == 0 for index in manager.replay_source.channel_indexes.values())
    assert manager.history(10) == []
    assert manager.latest_snapshot is None


def test_synthetic_and_replay_histories_do_not_contaminate(dataset_root: Path) -> None:
    manager = DataSourceManager(MockDataEngine(seed=123), dataset_root)
    synthetic_frame = manager.tick(0.5)
    assert synthetic_frame is not None
    synthetic_history = manager.history(10)

    manager.load_replay("S1")
    manager.play_replay()
    replay_source = manager.replay_source
    replay_frame = manager.tick(0.5, now=replay_source._anchor_monotonic + 0.5)
    assert replay_frame is not None
    assert {frame.source.source_type for frame in manager.history(10)} == {DataSourceType.DATASET_REPLAY}

    manager.use_synthetic()
    assert manager.history(10) == synthetic_history
    assert manager.latest_snapshot is synthetic_frame
    assert {frame.source.source_type for frame in manager.history(10)} == {DataSourceType.SYNTHETIC}


def test_invalid_subject_and_channel_fail_cleanly(dataset_root: Path) -> None:
    source = DatasetReplaySource(dataset_root)
    with pytest.raises(PpgDaliaSubjectError, match="expected one of"):
        source.load_subject("S99")
    with pytest.raises(PpgDaliaSubjectError, match="was not found"):
        source.load_subject("S3")
    with pytest.raises(PpgDaliaChannelError, match="Unsupported"):
        source.load_subject("S1", ["wrist_bvp", "imaginary_sensor"])


def test_end_of_recording_stops_without_wrapping(tmp_path: Path) -> None:
    _write_subject(tmp_path, "S1", duration_seconds=2.0)
    clock = ManualClock()
    source = _source(tmp_path, clock)
    source.set_speed(10.0)
    source.play()
    clock.advance(1.0)
    final_frame = source.tick(0.5)
    assert final_frame is not None
    assert final_frame.source.playback_state == ReplayPlaybackState.ENDED
    assert final_frame.source.replay_position_seconds == 2.0
    assert source.status().playback_state == ReplayPlaybackState.ENDED
    assert source.tick(0.5) is None
    with pytest.raises(ReplayStateError, match="reset"):
        source.play()

    source.reset()
    source.play()
    clock.advance(0.1)
    restarted = source.tick(0.5)
    assert restarted is not None
    assert _batch(restarted, "wrist_bvp").sample_start_index == 0


def test_controls_before_load_and_unsupported_speed_are_controlled(dataset_root: Path) -> None:
    source = DatasetReplaySource(dataset_root)
    with pytest.raises(ReplayStateError, match="Load"):
        source.pause()
    with pytest.raises(ReplayStateError, match="Load"):
        source.reset()
    with pytest.raises(UnsupportedPlaybackSpeedError, match="supported speeds"):
        source.set_speed(2.0)
