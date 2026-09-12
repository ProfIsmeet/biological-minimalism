"""Deterministic, replay-only corruption before model-window assembly."""

from __future__ import annotations

import hashlib

import numpy as np

from app.ml.ppg_dalia_windows import IMU_CHANNEL, PPG_CHANNEL
from app.schemas.data_source import DataSourceType, RawChannelBatch
from app.schemas.fault_injection import (
    FaultParameter,
    ReplayFaultConfig,
    ReplayFaultState,
    ReplayFaultTarget,
    ReplayFaultType,
)
from app.schemas.telemetry import LiveMetricsSnapshot

TARGET_CHANNELS: dict[ReplayFaultTarget, tuple[str, ...]] = {
    ReplayFaultTarget.PPG: (PPG_CHANNEL,),
    ReplayFaultTarget.IMU: (IMU_CHANNEL,),
    ReplayFaultTarget.BOTH: (PPG_CHANNEL, IMU_CHANNEL),
}

SEVERITY_SEMANTICS: dict[ReplayFaultType, str] = {
    ReplayFaultType.MODALITY_DROPOUT: "complete selected-modality removal; severity is not used",
    ReplayFaultType.PACKET_LOSS: "independent per-sample loss probability",
    ReplayFaultType.FROZEN_SENSOR: "complete hold at first observed value; severity is not used",
    ReplayFaultType.ADDITIVE_NOISE: "Gaussian sigma as a fraction of first-batch per-axis standard deviation",
    ReplayFaultType.SATURATION: "fraction of first-batch centered dynamic range removed",
}


class ReplayFaultInjector:
    """Apply one explicitly configured signal fault to replay batches.

    Clean snapshots are returned by identity when no fault is configured. The
    injector owns all random/reference state, and ``clear`` removes both the
    configuration and that state. It never operates on the synthetic source.
    """

    def __init__(self) -> None:
        self._config: ReplayFaultConfig | None = None
        self._identity: tuple[str, str] | None = None
        self._rngs: dict[str, np.random.Generator] = {}
        self._frozen_values: dict[str, np.ndarray] = {}
        self._reference_std: dict[str, np.ndarray] = {}
        self._clip_bounds: dict[str, tuple[np.ndarray, np.ndarray]] = {}

    @property
    def config(self) -> ReplayFaultConfig | None:
        return self._config

    def configure(self, config: ReplayFaultConfig) -> ReplayFaultState:
        self.clear()
        self._config = config
        return self.status()

    def clear(self) -> ReplayFaultState:
        self._config = None
        self._identity = None
        self._rngs.clear()
        self._frozen_values.clear()
        self._reference_std.clear()
        self._clip_bounds.clear()
        return self.status()

    def status(self) -> ReplayFaultState:
        if self._config is None:
            return ReplayFaultState()
        return ReplayFaultState(
            active=True,
            fault_type=self._config.fault_type,
            target=self._config.target,
            target_channels=list(TARGET_CHANNELS[self._config.target]),
            severity=self._config.severity,
            seed=self._config.seed,
            parameters={
                "severity_semantics": SEVERITY_SEMANTICS[self._config.fault_type],
            },
        )

    def _rng(self, channel_name: str) -> np.random.Generator:
        generator = self._rngs.get(channel_name)
        if generator is not None:
            return generator
        assert self._config is not None
        assert self._identity is not None
        material = (
            f"{self._config.seed}:{self._identity[0]}:{self._identity[1]}:{channel_name}"
        ).encode()
        channel_seed = int.from_bytes(hashlib.sha256(material).digest()[:8], "big")
        generator = np.random.default_rng(channel_seed)
        self._rngs[channel_name] = generator
        return generator

    @staticmethod
    def _array(batch: RawChannelBatch) -> np.ndarray:
        values = np.asarray(batch.samples, dtype=np.float64)
        if values.ndim not in (1, 2):
            raise ValueError(f"{batch.channel_name} fault input must be scalar or two-dimensional.")
        return values

    @staticmethod
    def _payload(values: np.ndarray) -> list[float] | list[list[float]]:
        return values.tolist()

    @staticmethod
    def _faulted_batch(batch: RawChannelBatch, values: np.ndarray) -> RawChannelBatch:
        return batch.model_copy(
            update={
                "role": f"fault_injected_{batch.role}",
                "samples": ReplayFaultInjector._payload(values),
            }
        )

    def _packet_loss_batches(
        self,
        batch: RawChannelBatch,
        values: np.ndarray,
    ) -> tuple[list[RawChannelBatch], int]:
        assert self._config is not None
        keep = self._rng(batch.channel_name).random(len(values)) >= self._config.severity
        dropped = int(len(values) - int(np.count_nonzero(keep)))
        batches: list[RawChannelBatch] = []
        cursor = 0
        while cursor < len(values):
            while cursor < len(values) and not keep[cursor]:
                cursor += 1
            segment_start = cursor
            while cursor < len(values) and keep[cursor]:
                cursor += 1
            if segment_start == cursor:
                continue
            absolute_start = batch.sample_start_index + segment_start
            absolute_end = batch.sample_start_index + cursor - 1
            batches.append(
                batch.model_copy(
                    update={
                        "role": f"fault_injected_{batch.role}",
                        "sample_start_index": absolute_start,
                        "start_timestamp_seconds": absolute_start / batch.sample_rate_hz,
                        "end_timestamp_seconds": absolute_end / batch.sample_rate_hz,
                        "samples": self._payload(values[segment_start:cursor]),
                    }
                )
            )
        return batches, dropped

    def _corrupt_batch(
        self,
        batch: RawChannelBatch,
    ) -> tuple[list[RawChannelBatch], int, dict[str, FaultParameter]]:
        assert self._config is not None
        values = self._array(batch)
        fault_type = self._config.fault_type

        if fault_type == ReplayFaultType.MODALITY_DROPOUT:
            return [], len(values), {}

        if fault_type == ReplayFaultType.PACKET_LOSS:
            batches, dropped = self._packet_loss_batches(batch, values)
            return batches, dropped, {"loss_probability": self._config.severity}

        if fault_type == ReplayFaultType.FROZEN_SENSOR:
            held = self._frozen_values.setdefault(batch.channel_name, values[0].copy())
            corrupted = np.broadcast_to(held, values.shape).copy()
            return [self._faulted_batch(batch, corrupted)], 0, {
                "held_value": np.atleast_1d(held).tolist()
            }

        if fault_type == ReplayFaultType.ADDITIVE_NOISE:
            reference_std = self._reference_std.setdefault(
                batch.channel_name,
                np.atleast_1d(np.std(values, axis=0, dtype=np.float64)),
            )
            noise_std = reference_std * self._config.severity
            noise = self._rng(batch.channel_name).normal(0.0, noise_std, size=values.shape)
            corrupted = values + noise
            return [self._faulted_batch(batch, corrupted)], 0, {
                "reference_standard_deviation": reference_std.tolist(),
                "noise_standard_deviation": noise_std.tolist(),
            }

        if fault_type == ReplayFaultType.SATURATION:
            bounds = self._clip_bounds.get(batch.channel_name)
            if bounds is None:
                minimum = np.atleast_1d(np.min(values, axis=0))
                maximum = np.atleast_1d(np.max(values, axis=0))
                midpoint = (minimum + maximum) / 2.0
                half_range = (maximum - minimum) * (1.0 - self._config.severity) / 2.0
                bounds = (midpoint - half_range, midpoint + half_range)
                self._clip_bounds[batch.channel_name] = bounds
            lower, upper = bounds
            corrupted = np.clip(values, lower, upper)
            return [self._faulted_batch(batch, corrupted)], 0, {
                "clip_lower": lower.tolist(),
                "clip_upper": upper.tolist(),
            }

        raise AssertionError(f"Unhandled replay fault type: {fault_type}")

    def apply(self, snapshot: LiveMetricsSnapshot) -> LiveMetricsSnapshot:
        if snapshot.source.source_type != DataSourceType.DATASET_REPLAY:
            self.clear()
            return snapshot
        if self._config is None:
            return snapshot

        dataset_name = snapshot.source.dataset_name
        subject_id = snapshot.source.subject_id
        if not dataset_name or not subject_id:
            self.clear()
            return snapshot
        identity = (dataset_name, subject_id)
        if self._identity is not None and identity != self._identity:
            self.clear()
            return snapshot
        self._identity = identity

        target_channels = TARGET_CHANNELS[self._config.target]
        output_batches: list[RawChannelBatch] = []
        affected_channels: list[str] = []
        dropped_samples: dict[str, int] = {}
        parameters: dict[str, FaultParameter] = {
            "severity_semantics": SEVERITY_SEMANTICS[self._config.fault_type],
        }
        for batch in snapshot.channels:
            if batch.channel_name not in target_channels:
                output_batches.append(batch)
                continue
            affected_channels.append(batch.channel_name)
            faulted, dropped, details = self._corrupt_batch(batch)
            output_batches.extend(faulted)
            if dropped:
                dropped_samples[batch.channel_name] = dropped
            for key, value in details.items():
                parameters[f"{batch.channel_name}.{key}"] = value

        source = snapshot.source
        if self._config.fault_type == ReplayFaultType.MODALITY_DROPOUT:
            original = list(source.available_channels)
            source = source.model_copy(
                update={
                    "available_channels": [
                        channel for channel in original if channel not in target_channels
                    ]
                }
            )
            parameters["original_available_channels"] = original
            parameters["effective_available_channels"] = list(source.available_channels)

        vitals = snapshot.vitals
        if vitals is not None and PPG_CHANNEL in target_channels:
            ppg_samples: list[float] = []
            for batch in output_batches:
                if batch.channel_name == PPG_CHANNEL:
                    ppg_samples.extend(float(value) for value in batch.samples)  # type: ignore[arg-type]
            vitals = vitals.model_copy(update={"ppg_waveform": ppg_samples})

        state = ReplayFaultState(
            active=True,
            fault_type=self._config.fault_type,
            target=self._config.target,
            target_channels=list(target_channels),
            affected_channels=list(dict.fromkeys(affected_channels)),
            severity=self._config.severity,
            seed=self._config.seed,
            dropped_samples=dropped_samples,
            parameters=parameters,
        )
        return snapshot.model_copy(
            update={
                "source": source,
                "channels": output_batches,
                "vitals": vitals,
                "fault_injection": state,
            }
        )
