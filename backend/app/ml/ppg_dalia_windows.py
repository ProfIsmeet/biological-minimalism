"""Assemble native-rate replay batches into synchronized PPG+IMU windows."""

from __future__ import annotations

import math
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from app.schemas.data_source import DataSourceType, RawChannelBatch
from app.schemas.telemetry import LiveMetricsSnapshot

# The ML package is a sibling of backend/. Local backend processes commonly
# start with backend/ as their working directory, so make the repository's
# canonical ML contract importable without duplicating its constants here.
REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from ml.datasets.ppg_dalia import (  # noqa: E402
    ACC_FS,
    ACC_WINDOW_SAMPLES,
    PPG_FS,
    PPG_WINDOW_SAMPLES,
    STEP_SECONDS,
    WINDOW_SECONDS,
)

DATASET_NAME = "PPG-DaLiA"
PPG_CHANNEL = "wrist_bvp"
IMU_CHANNEL = "wrist_acc"


class WindowAssemblyError(RuntimeError):
    """Base class for controlled replay-to-window failures."""


class WindowIdentityError(WindowAssemblyError):
    """Replay metadata would mix or relabel datasets/subjects."""


class WindowChannelError(WindowAssemblyError):
    """A required model channel has an invalid rate, shape, or timestamp."""


class WindowSequenceError(WindowAssemblyError):
    """A channel batch contains a gap or unexpected overlap."""


@dataclass(frozen=True)
class PPGDaliaModelWindow:
    """One raw, left-aligned 8-second model input window."""

    dataset_name: str
    subject_id: str
    window_index: int
    window_start_seconds: float
    window_duration_seconds: float
    ppg_start_index: int
    imu_start_index: int
    ppg: np.ndarray
    imu: np.ndarray

    def __post_init__(self) -> None:
        ppg = np.asarray(self.ppg, dtype=np.float64).copy()
        imu = np.asarray(self.imu, dtype=np.float64).copy()
        if self.dataset_name != DATASET_NAME:
            raise WindowIdentityError(f"Expected dataset {DATASET_NAME}, got {self.dataset_name!r}.")
        if not self.subject_id:
            raise WindowIdentityError("A model window requires a non-empty subject_id.")
        if self.window_index < 0 or self.window_start_seconds < 0:
            raise WindowAssemblyError("Window index and start time must be non-negative.")
        if not math.isclose(self.window_duration_seconds, WINDOW_SECONDS):
            raise WindowAssemblyError(
                f"Expected {WINDOW_SECONDS:g}-second model window, got {self.window_duration_seconds:g}."
            )
        if ppg.shape != (PPG_WINDOW_SAMPLES,):
            raise WindowChannelError(
                f"Expected raw PPG shape ({PPG_WINDOW_SAMPLES},), got {ppg.shape}."
            )
        if imu.shape != (3, ACC_WINDOW_SAMPLES):
            raise WindowChannelError(
                f"Expected raw IMU shape (3, {ACC_WINDOW_SAMPLES}), got {imu.shape}."
            )
        expected_ppg_start = int(round(self.window_start_seconds * PPG_FS))
        expected_imu_start = int(round(self.window_start_seconds * ACC_FS))
        if self.ppg_start_index != expected_ppg_start or self.imu_start_index != expected_imu_start:
            raise WindowChannelError("PPG and IMU sample indexes are not left-aligned at the declared t0.")
        ppg.setflags(write=False)
        imu.setflags(write=False)
        object.__setattr__(self, "ppg", ppg)
        object.__setattr__(self, "imu", imu)


class _NativeChannelBuffer:
    def __init__(
        self,
        *,
        channel_name: str,
        sample_rate_hz: float,
        width: int,
        axes: tuple[str, ...],
    ) -> None:
        self.channel_name = channel_name
        self.sample_rate_hz = sample_rate_hz
        self.width = width
        self.axes = axes
        self.start_index: int | None = None
        self.values = np.empty((0, width), dtype=np.float64)

    @property
    def end_index(self) -> int | None:
        if self.start_index is None:
            return None
        return self.start_index + len(self.values)

    def clear(self) -> None:
        self.start_index = None
        self.values = np.empty((0, self.width), dtype=np.float64)

    def append(self, batch: RawChannelBatch) -> None:
        if not math.isclose(batch.sample_rate_hz, self.sample_rate_hz, abs_tol=1e-9):
            raise WindowChannelError(
                f"{self.channel_name} requires {self.sample_rate_hz:g} Hz, got {batch.sample_rate_hz:g} Hz."
            )
        if tuple(batch.axes) != self.axes:
            raise WindowChannelError(
                f"{self.channel_name} requires axis order {self.axes}, got {tuple(batch.axes)}."
            )
        samples = np.asarray(batch.samples, dtype=np.float64)
        if self.width == 1 and samples.ndim == 1:
            samples = samples.reshape(-1, 1)
        if samples.ndim != 2 or samples.shape[1] != self.width:
            raise WindowChannelError(
                f"{self.channel_name} batch has shape {samples.shape}; expected (samples, {self.width})."
            )
        if not len(samples):
            raise WindowChannelError(f"{self.channel_name} batch contains no samples.")

        expected_start_timestamp = batch.sample_start_index / self.sample_rate_hz
        expected_end_timestamp = (batch.sample_start_index + len(samples) - 1) / self.sample_rate_hz
        if not math.isclose(batch.start_timestamp_seconds, expected_start_timestamp, abs_tol=1e-9):
            raise WindowChannelError(f"{self.channel_name} start timestamp does not match its sample index.")
        if not math.isclose(batch.end_timestamp_seconds, expected_end_timestamp, abs_tol=1e-9):
            raise WindowChannelError(f"{self.channel_name} end timestamp does not match its sample count.")

        if self.start_index is None:
            self.start_index = batch.sample_start_index
        elif batch.sample_start_index != self.end_index:
            raise WindowSequenceError(
                f"{self.channel_name} expected next sample index {self.end_index}, "
                f"got {batch.sample_start_index}."
            )
        self.values = np.concatenate((self.values, samples), axis=0)

    def contains(self, start_index: int, end_index: int) -> bool:
        return (
            self.start_index is not None
            and self.end_index is not None
            and self.start_index <= start_index
            and end_index <= self.end_index
        )

    def slice(self, start_index: int, end_index: int) -> np.ndarray:
        if not self.contains(start_index, end_index) or self.start_index is None:
            raise WindowSequenceError(f"{self.channel_name} does not contain requested sample interval.")
        relative_start = start_index - self.start_index
        relative_end = end_index - self.start_index
        return self.values[relative_start:relative_end].copy()

    def discard_before(self, sample_index: int) -> None:
        if self.start_index is None or self.end_index is None or sample_index <= self.start_index:
            return
        clamped_index = min(sample_index, self.end_index)
        offset = clamped_index - self.start_index
        self.values = self.values[offset:]
        self.start_index = clamped_index


class PPGDaliaWindowAssembler:
    """Stateful, bounded assembler for the canonical 8 s / 2 s contract.

    Batches remain at 64 Hz (PPG) and 32 Hz (IMU); no resampling or
    interpolation occurs. Source/subject changes and replay index rollback
    clear all buffered state. A pause emits no batches and therefore leaves
    the buffers unchanged.
    """

    def __init__(self) -> None:
        self._ppg = _NativeChannelBuffer(
            channel_name=PPG_CHANNEL,
            sample_rate_hz=PPG_FS,
            width=1,
            axes=("bvp",),
        )
        self._imu = _NativeChannelBuffer(
            channel_name=IMU_CHANNEL,
            sample_rate_hz=ACC_FS,
            width=3,
            axes=("x", "y", "z"),
        )
        self._identity: tuple[str, str] | None = None
        self._next_window_index: int | None = None
        self._last_replay_position: float | None = None

    @property
    def identity(self) -> tuple[str, str] | None:
        return self._identity

    @property
    def next_window_index(self) -> int | None:
        return self._next_window_index

    @property
    def buffered_samples(self) -> dict[str, int]:
        return {PPG_CHANNEL: len(self._ppg.values), IMU_CHANNEL: len(self._imu.values)}

    def reset(self) -> None:
        self._ppg.clear()
        self._imu.clear()
        self._identity = None
        self._next_window_index = None
        self._last_replay_position = None

    def _reset_for_identity(self, identity: tuple[str, str]) -> None:
        self.reset()
        self._identity = identity

    def ingest(self, snapshot: LiveMetricsSnapshot) -> list[PPGDaliaModelWindow]:
        if snapshot.source.source_type != DataSourceType.DATASET_REPLAY:
            self.reset()
            return []

        dataset_name = snapshot.source.dataset_name
        subject_id = snapshot.source.subject_id
        if dataset_name != DATASET_NAME or not subject_id:
            raise WindowIdentityError(
                f"Replay model input requires dataset={DATASET_NAME!r} and a subject_id; "
                f"got dataset={dataset_name!r}, subject={subject_id!r}."
            )
        identity = (dataset_name, subject_id)
        if self._identity != identity:
            self._reset_for_identity(identity)

        replay_position = snapshot.source.replay_position_seconds
        if (
            replay_position is not None
            and self._last_replay_position is not None
            and replay_position < self._last_replay_position
        ):
            self._reset_for_identity(identity)

        relevant_batches = [
            batch for batch in snapshot.channels if batch.channel_name in {PPG_CHANNEL, IMU_CHANNEL}
        ]
        for batch in relevant_batches:
            if (batch.dataset_name, batch.subject_id) != identity:
                raise WindowIdentityError(
                    f"Snapshot identifies {identity}, but {batch.channel_name} identifies "
                    f"{(batch.dataset_name, batch.subject_id)}; refusing to mix subjects."
                )

        # A same-subject replay reset restarts channel indexes at zero. Detect
        # rollback before appending either channel so both buffers reset as
        # one synchronized unit.
        for batch in relevant_batches:
            buffer = self._ppg if batch.channel_name == PPG_CHANNEL else self._imu
            if buffer.end_index is not None and batch.sample_start_index < buffer.end_index:
                self._reset_for_identity(identity)
                break

        for batch in relevant_batches:
            if batch.channel_name == PPG_CHANNEL:
                self._ppg.append(batch)
            else:
                self._imu.append(batch)

        self._last_replay_position = replay_position
        return self._emit_complete_windows(dataset_name, subject_id)

    def _emit_complete_windows(self, dataset_name: str, subject_id: str) -> list[PPGDaliaModelWindow]:
        if self._ppg.start_index is None or self._imu.start_index is None:
            return []
        if self._next_window_index is None:
            first_common_time = max(
                self._ppg.start_index / PPG_FS,
                self._imu.start_index / ACC_FS,
            )
            self._next_window_index = max(0, math.ceil(first_common_time / STEP_SECONDS - 1e-12))

        windows: list[PPGDaliaModelWindow] = []
        while self._next_window_index is not None:
            window_index = self._next_window_index
            t0 = window_index * STEP_SECONDS
            ppg_start = int(round(t0 * PPG_FS))
            imu_start = int(round(t0 * ACC_FS))
            ppg_end = ppg_start + PPG_WINDOW_SAMPLES
            imu_end = imu_start + ACC_WINDOW_SAMPLES
            if not self._ppg.contains(ppg_start, ppg_end) or not self._imu.contains(imu_start, imu_end):
                break

            raw_ppg = self._ppg.slice(ppg_start, ppg_end)[:, 0]
            raw_imu = self._imu.slice(imu_start, imu_end).T
            windows.append(
                PPGDaliaModelWindow(
                    dataset_name=dataset_name,
                    subject_id=subject_id,
                    window_index=window_index,
                    window_start_seconds=t0,
                    window_duration_seconds=WINDOW_SECONDS,
                    ppg_start_index=ppg_start,
                    imu_start_index=imu_start,
                    ppg=raw_ppg,
                    imu=raw_imu,
                )
            )
            self._next_window_index += 1

        # Retain only the six seconds of overlap needed by the next window,
        # bounding memory independently of recording duration.
        if self._next_window_index is not None:
            next_t0 = self._next_window_index * STEP_SECONDS
            self._ppg.discard_before(int(round(next_t0 * PPG_FS)))
            self._imu.discard_before(int(round(next_t0 * ACC_FS)))
        return windows
