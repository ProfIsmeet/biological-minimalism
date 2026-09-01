"""Switchable synthetic and timestamp-preserving dataset telemetry sources."""

from __future__ import annotations

import math
import threading
import time
from collections import deque
from collections.abc import Callable
from pathlib import Path
from typing import Protocol

from app.core.config import settings
from app.data.ppg_dalia import (
    DATASET_NAME,
    DEFAULT_REPLAY_CHANNELS,
    RawSubjectRecording,
    load_raw_subject,
    list_available_subjects,
)
from app.engine.mock_data_engine import MockDataEngine, engine
from app.schemas.data_source import (
    ChannelMetadata,
    DataSourceStatus,
    DataSourceType,
    RawChannelBatch,
    ReplayPlaybackState,
    TelemetrySourceMetadata,
)
from app.schemas.telemetry import LiveMetricsSnapshot, VitalsSnapshot

SUPPORTED_PLAYBACK_SPEEDS = (1.0, 5.0, 10.0)
PPG_DALIA_UNAVAILABLE_CHANNELS = ("eeg", "bioimpedance", "light")


class ReplayStateError(RuntimeError):
    """A replay control was invoked in an invalid but expected state."""


class UnsupportedPlaybackSpeedError(ValueError):
    """The requested replay speed is outside the supported control set."""


class TelemetrySource(Protocol):
    source_type: DataSourceType

    def tick(self, dt: float, now: float | None = None) -> LiveMetricsSnapshot | None: ...

    def status(self) -> DataSourceStatus: ...


class SyntheticSource:
    source_type = DataSourceType.SYNTHETIC

    def __init__(self, mock_engine: MockDataEngine) -> None:
        self.engine = mock_engine

    def tick(self, dt: float, now: float | None = None) -> LiveMetricsSnapshot:
        del now
        return self.engine.tick(dt)

    def status(self) -> DataSourceStatus:
        return DataSourceStatus(
            source_type=self.source_type,
            dataset_configured=settings.ppg_dalia_path is not None,
        )


class DatasetReplaySource:
    """Replay one synchronized PPG-DaLiA subject on a monotonic master clock.

    Every channel retains its native sampling rate.  Index targets are
    calculated from the anchored replay position, rather than accumulating
    repeated sleeps, so scheduling delay does not compound into clock drift.
    """

    source_type = DataSourceType.DATASET_REPLAY

    def __init__(
        self,
        data_path: str | Path,
        *,
        monotonic_clock: Callable[[], float] = time.monotonic,
        wall_clock: Callable[[], float] = time.time,
    ) -> None:
        self.data_path = Path(data_path).expanduser()
        self._monotonic_clock = monotonic_clock
        self._wall_clock = wall_clock
        self._recording: RawSubjectRecording | None = None
        self._state = ReplayPlaybackState.UNLOADED
        self._speed = 1.0
        self._position_seconds = 0.0
        self._anchor_position_seconds = 0.0
        self._anchor_monotonic = self._monotonic_clock()
        self._channel_indexes: dict[str, int] = {}

    @property
    def recording(self) -> RawSubjectRecording:
        if self._recording is None:
            raise ReplayStateError("Load a PPG-DaLiA subject before controlling replay.")
        return self._recording

    @property
    def channel_indexes(self) -> dict[str, int]:
        return dict(self._channel_indexes)

    def available_subjects(self) -> list[str]:
        return list_available_subjects(self.data_path)

    def load_subject(self, subject_id: str, channel_names: list[str] | tuple[str, ...] | None = None) -> None:
        self._recording = load_raw_subject(
            self.data_path,
            subject_id,
            tuple(channel_names) if channel_names is not None else DEFAULT_REPLAY_CHANNELS,
        )
        self._state = ReplayPlaybackState.PAUSED
        self._speed = 1.0
        self._position_seconds = 0.0
        self._anchor_position_seconds = 0.0
        self._anchor_monotonic = self._monotonic_clock()
        self._channel_indexes = {name: 0 for name in self._recording.channels}

    def _position_at(self, now: float) -> float:
        if self._state != ReplayPlaybackState.PLAYING:
            return self._position_seconds
        elapsed = max(0.0, now - self._anchor_monotonic)
        return min(
            self.recording.duration_seconds,
            self._anchor_position_seconds + elapsed * self._speed,
        )

    def _sync_position(self, now: float) -> None:
        self._position_seconds = self._position_at(now)
        self._anchor_position_seconds = self._position_seconds
        self._anchor_monotonic = now

    def play(self) -> None:
        self.recording
        if self._state == ReplayPlaybackState.ENDED:
            raise ReplayStateError("Replay reached end-of-recording; reset before playing again.")
        if self._state == ReplayPlaybackState.PLAYING:
            return
        self._anchor_position_seconds = self._position_seconds
        self._anchor_monotonic = self._monotonic_clock()
        self._state = ReplayPlaybackState.PLAYING

    def pause(self) -> None:
        self.recording
        if self._state == ReplayPlaybackState.PLAYING:
            self._sync_position(self._monotonic_clock())
            self._state = ReplayPlaybackState.PAUSED

    def reset(self) -> None:
        self.recording
        self._state = ReplayPlaybackState.PAUSED
        self._position_seconds = 0.0
        self._anchor_position_seconds = 0.0
        self._anchor_monotonic = self._monotonic_clock()
        self._channel_indexes = {name: 0 for name in self.recording.channels}

    def set_speed(self, speed: float) -> None:
        if speed not in SUPPORTED_PLAYBACK_SPEEDS:
            allowed = ", ".join(f"{value:g}x" for value in SUPPORTED_PLAYBACK_SPEEDS)
            raise UnsupportedPlaybackSpeedError(
                f"Unsupported playback speed {speed:g}x; supported speeds are {allowed}."
            )
        if self._state == ReplayPlaybackState.PLAYING:
            self._sync_position(self._monotonic_clock())
        self._speed = float(speed)

    def _source_metadata(self) -> TelemetrySourceMetadata:
        recording = self.recording
        return TelemetrySourceMetadata(
            source_type=self.source_type,
            display_label="REAL RECORDED DATA — REPLAY MODE",
            dataset_name=recording.dataset_name,
            subject_id=recording.subject_id,
            replay_position_seconds=self._position_seconds,
            duration_seconds=recording.duration_seconds,
            playback_state=self._state,
            playback_speed=self._speed,
            end_behavior="stop",
            license=recording.license,
            source_url=recording.source_url,
            available_channels=list(recording.channels),
            unavailable_channels=list(PPG_DALIA_UNAVAILABLE_CHANNELS),
        )

    def status(self) -> DataSourceStatus:
        if self._recording is None:
            return DataSourceStatus(
                source_type=self.source_type,
                dataset_configured=self.data_path.exists(),
                dataset_name=DATASET_NAME,
                playback_state=ReplayPlaybackState.UNLOADED,
                playback_speed=self._speed,
                end_behavior="stop",
            )
        self._position_seconds = self._position_at(self._monotonic_clock())
        return DataSourceStatus(
            source_type=self.source_type,
            dataset_configured=self.data_path.exists(),
            dataset_name=self.recording.dataset_name,
            subject_id=self.recording.subject_id,
            replay_position_seconds=self._position_seconds,
            duration_seconds=self.recording.duration_seconds,
            playback_state=self._state,
            playback_speed=self._speed,
            end_behavior="stop",
            channels=[
                ChannelMetadata(
                    name=channel.definition.name,
                    sample_rate_hz=channel.definition.sample_rate_hz,
                    device=channel.definition.device,
                    role=channel.definition.role,
                    axes=list(channel.definition.axes),
                    units=channel.definition.units,
                )
                for channel in self.recording.channels.values()
            ],
        )

    def tick(self, dt: float, now: float | None = None) -> LiveMetricsSnapshot | None:
        del dt
        if self._state != ReplayPlaybackState.PLAYING:
            return None

        clock_now = self._monotonic_clock() if now is None else now
        target_position = self._position_at(clock_now)
        batches: list[RawChannelBatch] = []
        ppg_waveform: list[float] = []
        ecg_waveform: list[float] = []

        for name, channel in self.recording.channels.items():
            sample_rate = channel.definition.sample_rate_hz
            start_index = self._channel_indexes[name]
            end_index = min(
                len(channel.samples),
                int(math.floor(target_position * sample_rate + 1e-9)),
            )
            if end_index <= start_index:
                continue

            raw_batch = channel.samples[start_index:end_index]
            if raw_batch.shape[1] == 1:
                payload: list[float] | list[list[float]] = raw_batch[:, 0].tolist()
            else:
                payload = raw_batch.tolist()
            start_timestamp = start_index / sample_rate
            end_timestamp = (end_index - 1) / sample_rate
            batches.append(
                RawChannelBatch(
                    dataset_name=self.recording.dataset_name,
                    subject_id=self.recording.subject_id,
                    channel_name=name,
                    device=channel.definition.device,
                    role=channel.definition.role,
                    axes=list(channel.definition.axes),
                    units=channel.definition.units,
                    sample_rate_hz=sample_rate,
                    sample_start_index=start_index,
                    start_timestamp_seconds=start_timestamp,
                    end_timestamp_seconds=end_timestamp,
                    samples=payload,
                )
            )
            self._channel_indexes[name] = end_index
            if name == "wrist_bvp" and isinstance(payload, list):
                ppg_waveform = payload  # type: ignore[assignment]
            elif name == "chest_ecg" and isinstance(payload, list):
                ecg_waveform = payload  # type: ignore[assignment]

        self._position_seconds = target_position
        if target_position >= self.recording.duration_seconds:
            self._state = ReplayPlaybackState.ENDED
            self._anchor_position_seconds = target_position
            self._anchor_monotonic = clock_now

        if not batches and self._state != ReplayPlaybackState.ENDED:
            return None

        return LiveMetricsSnapshot(
            timestamp=self._wall_clock(),
            source=self._source_metadata(),
            channels=batches,
            vitals=VitalsSnapshot(
                ppg_waveform=ppg_waveform,
                ecg_waveform=ecg_waveform,
            ),
        )


class DataSourceManager:
    """Atomic active-source switch while retaining independent histories."""

    def __init__(
        self,
        mock_engine: MockDataEngine,
        ppg_dalia_path: str | Path | None,
    ) -> None:
        self.synthetic_source = SyntheticSource(mock_engine)
        self._ppg_dalia_path = Path(ppg_dalia_path).expanduser() if ppg_dalia_path else None
        self._replay_source: DatasetReplaySource | None = None
        self._active: TelemetrySource = self.synthetic_source
        self._replay_history: deque[LiveMetricsSnapshot] = deque(maxlen=settings.rolling_history_length)
        self._last_replay_snapshot: LiveMetricsSnapshot | None = None
        self._lock = threading.RLock()

    @property
    def source_type(self) -> DataSourceType:
        return self._active.source_type

    @property
    def replay_source(self) -> DatasetReplaySource:
        if self._replay_source is None:
            raise ReplayStateError("Load a PPG-DaLiA subject before controlling replay.")
        return self._replay_source

    @property
    def latest_snapshot(self) -> LiveMetricsSnapshot | None:
        if self.source_type == DataSourceType.SYNTHETIC:
            return self.synthetic_source.engine.last_snapshot
        return self._last_replay_snapshot

    def history(self, limit: int) -> list[LiveMetricsSnapshot]:
        if self.source_type == DataSourceType.SYNTHETIC:
            return list(self.synthetic_source.engine.history)[-limit:]
        return list(self._replay_history)[-limit:]

    def configure_dataset_path(self, path: str | Path | None) -> None:
        """Replace the configured path; primarily useful for isolated tests."""
        with self._lock:
            self._ppg_dalia_path = Path(path).expanduser() if path else None

    def available_subjects(self) -> list[str]:
        if self._ppg_dalia_path is None:
            raise ReplayStateError(
                "PPG-DaLiA is not configured; set BIOMIN_PPG_DALIA_PATH to the "
                "official archive or extracted PPG_FieldStudy directory."
            )
        return list_available_subjects(self._ppg_dalia_path)

    def use_synthetic(self) -> DataSourceStatus:
        with self._lock:
            self._active = self.synthetic_source
            return self.status()

    def load_replay(self, subject_id: str, channel_names: list[str] | None = None) -> DataSourceStatus:
        if self._ppg_dalia_path is None:
            raise ReplayStateError(
                "PPG-DaLiA is not configured; set BIOMIN_PPG_DALIA_PATH to the "
                "official archive or extracted PPG_FieldStudy directory."
            )
        # Loading a 1+ GB pickle is intentionally outside the manager lock so
        # the current source can continue to tick.  Activation occurs only
        # after the new subject has passed its embedded identity check.
        candidate = DatasetReplaySource(self._ppg_dalia_path)
        candidate.load_subject(subject_id, channel_names)
        with self._lock:
            self._replay_source = candidate
            self._active = candidate
            self._replay_history.clear()
            self._last_replay_snapshot = None
            return candidate.status()

    def play_replay(self) -> DataSourceStatus:
        with self._lock:
            self.replay_source.play()
            return self.replay_source.status()

    def pause_replay(self) -> DataSourceStatus:
        with self._lock:
            self.replay_source.pause()
            return self.replay_source.status()

    def reset_replay(self) -> DataSourceStatus:
        with self._lock:
            self.replay_source.reset()
            self._replay_history.clear()
            self._last_replay_snapshot = None
            return self.replay_source.status()

    def set_replay_speed(self, speed: float) -> DataSourceStatus:
        with self._lock:
            self.replay_source.set_speed(speed)
            return self.replay_source.status()

    def tick(self, dt: float, now: float | None = None) -> LiveMetricsSnapshot | None:
        with self._lock:
            snapshot = self._active.tick(dt, now)
            if snapshot is not None and self.source_type == DataSourceType.DATASET_REPLAY:
                self._last_replay_snapshot = snapshot
                self._replay_history.append(snapshot)
            return snapshot

    def status(self) -> DataSourceStatus:
        with self._lock:
            if self.source_type == DataSourceType.SYNTHETIC:
                return DataSourceStatus(
                    source_type=DataSourceType.SYNTHETIC,
                    dataset_configured=self._ppg_dalia_path is not None and self._ppg_dalia_path.exists(),
                )
            return self.replay_source.status()


data_source_manager = DataSourceManager(engine, settings.ppg_dalia_path)
