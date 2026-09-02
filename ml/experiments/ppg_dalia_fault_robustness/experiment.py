"""Reproducible S14-only characterization using production fault semantics.

The experiment deliberately keeps fault application/model prediction separate
from ground-truth scoring. Faults receive only recorded model channels; labels
are joined by verified window index after prediction outcomes are finalized.
"""

from __future__ import annotations

import hashlib
import json
import math
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator, Sequence

import numpy as np

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))
if str(REPOSITORY_ROOT / "backend") not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT / "backend"))

from app.data.ppg_dalia import load_subject_payload  # noqa: E402
from app.engine.fault_injection import ReplayFaultInjector  # noqa: E402
from app.ml.ppg_dalia_hr import (  # noqa: E402
    EXPECTED_CHECKPOINT_SHA256,
    EXPECTED_CHECKPOINT_SIZE_BYTES,
    PPGDaliaHRInferenceBridge,
)
from app.ml.ppg_dalia_windows import (  # noqa: E402
    DATASET_NAME,
    IMU_CHANNEL,
    PPG_CHANNEL,
    PPGDaliaModelWindow,
    PPGDaliaWindowAssembler,
    WindowAssemblyError,
)
from app.schemas.data_source import (  # noqa: E402
    DataSourceType,
    RawChannelBatch,
    ReplayPlaybackState,
    TelemetrySourceMetadata,
)
from app.schemas.fault_injection import (  # noqa: E402
    ReplayFaultConfig,
    ReplayFaultTarget,
    ReplayFaultType,
)
from app.schemas.telemetry import LiveMetricsSnapshot  # noqa: E402
from ml.datasets.ppg_dalia import (  # noqa: E402
    ACC_FS,
    ACC_WINDOW_SAMPLES,
    PPG_FS,
    PPG_WINDOW_SAMPLES,
    STEP_SECONDS,
    WINDOW_SECONDS,
    FlatSignalError,
    zscore_imu_window,
    zscore_ppg_window,
)

DEFAULT_EXPERIMENT_DIR = Path(__file__).resolve().parent
DEFAULT_CONFIG_PATH = DEFAULT_EXPERIMENT_DIR / "config.json"
DEFAULT_PROTOCOL_PATH = DEFAULT_EXPERIMENT_DIR / "PROTOCOL.md"
FAILURE_CATEGORIES = (
    "input_unavailable",
    "canonical_invalid_input",
    "inference_error",
)
VALID_STATUS = "valid"
BATCH_SIZE = 128


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _canonical_json(value: Any) -> str:
    return json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n"


def serialize_results(results: dict[str, Any]) -> str:
    """Serialize byte-for-byte deterministically with no NaN extension values."""

    return _canonical_json(results)


def load_protocol_config(path: str | Path = DEFAULT_CONFIG_PATH) -> dict[str, Any]:
    """Load and validate the frozen configuration without applying defaults."""

    config_path = Path(path)
    config = json.loads(config_path.read_text(encoding="utf-8"))
    required = {
        "schema_version",
        "experiment_id",
        "protocol_status",
        "dataset",
        "model",
        "window",
        "clean_reference",
        "stochastic_seeds",
        "faults",
        "failure_categories",
        "metrics",
        "policies",
        "output",
    }
    if set(config) != required:
        raise ValueError(f"Protocol config keys differ from the frozen schema: {sorted(config)}")
    if config["schema_version"] != 1 or config["protocol_status"] != "frozen_before_results":
        raise ValueError("Only the frozen Phase 5 schema version 1 is accepted.")
    if config["dataset"]["subjects"] != ["S14"] or config["dataset"]["held_out_subjects"] != ["S14"]:
        raise ValueError("Phase 5 is pre-registered for held-out subject S14 only.")
    if config["stochastic_seeds"] != [2026, 2027, 2028, 2029, 2030]:
        raise ValueError("The frozen stochastic seed set changed.")
    if config["failure_categories"] != list(FAILURE_CATEGORIES):
        raise ValueError("Failure categories differ from the frozen protocol.")
    policies = config["policies"]
    forbidden_true = ("missing_sample_fill", "interpolation", "fallback_prediction", "output_clipping", "retraining", "ground_truth_is_model_input")
    if any(policies[name] for name in forbidden_true):
        raise ValueError("The frozen no-fabrication/no-retraining policies must remain false.")
    return config


@dataclass(frozen=True)
class Condition:
    condition_id: str
    group_id: str
    fault_type: str
    target: str | None
    severity: float | None
    seed: int | None
    stochastic: bool

    def replay_config(self) -> ReplayFaultConfig | None:
        if self.fault_type == "clean":
            return None
        return ReplayFaultConfig(
            fault_type=ReplayFaultType(self.fault_type),
            target=ReplayFaultTarget(self.target),
            severity=float(self.severity),
            seed=self.seed if self.seed is not None else 0,
        )


def _severity_token(severity: float) -> str:
    return format(severity, "g").replace(".", "p")


def build_condition_matrix(config: dict[str, Any]) -> list[Condition]:
    conditions = [
        Condition(
            condition_id="clean",
            group_id="clean",
            fault_type="clean",
            target=None,
            severity=None,
            seed=None,
            stochastic=False,
        )
    ]
    seeds = config["stochastic_seeds"]
    for fault in config["faults"]:
        for target in fault["targets"]:
            for severity in fault["severities"]:
                group_id = f"{fault['fault_type']}__{target}__severity_{_severity_token(severity)}"
                condition_seeds: list[int | None] = seeds if fault["stochastic"] else [None]
                for seed in condition_seeds:
                    condition_id = group_id if seed is None else f"{group_id}__seed_{seed}"
                    conditions.append(
                        Condition(
                            condition_id=condition_id,
                            group_id=group_id,
                            fault_type=fault["fault_type"],
                            target=target,
                            severity=float(severity),
                            seed=seed,
                            stochastic=bool(fault["stochastic"]),
                        )
                    )
    identifiers = [condition.condition_id for condition in conditions]
    if len(conditions) != 114 or len(set(identifiers)) != len(identifiers):
        raise ValueError(
            f"Frozen condition matrix must contain 114 uniquely identified conditions; got {len(conditions)}."
        )
    return conditions


@dataclass(frozen=True)
class ExperimentSubject:
    subject_id: str
    ppg: np.ndarray
    imu: np.ndarray
    labels: np.ndarray

    @property
    def eligible_window_count(self) -> int:
        return len(self.labels)

    @property
    def experiment_duration_seconds(self) -> float:
        return (self.eligible_window_count - 1) * STEP_SECONDS + WINDOW_SECONDS


def _validate_subject_payload(
    raw: dict[str, Any],
    requested_subject: str,
    expected_windows: int,
) -> ExperimentSubject:
    embedded_subject = str(raw.get("subject", "")).upper()
    if embedded_subject != requested_subject:
        raise ValueError(
            f"Requested {requested_subject}, but payload identifies {raw.get('subject')!r}; "
            "refusing to mix or relabel subjects."
        )
    try:
        ppg_raw = np.asarray(raw["signal"]["wrist"]["BVP"], dtype=np.float64)
        imu = np.asarray(raw["signal"]["wrist"]["ACC"], dtype=np.float64).copy()
        labels = np.asarray(raw["label"], dtype=np.float32).reshape(-1).copy()
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(f"{requested_subject} does not match the official PPG-DaLiA input schema.") from exc
    if ppg_raw.ndim not in (1, 2) or (ppg_raw.ndim == 2 and ppg_raw.shape[1] != 1):
        raise ValueError(f"Expected wrist BVP shape (samples,) or (samples, 1), got {ppg_raw.shape}.")
    ppg = ppg_raw.reshape(-1).copy()
    if imu.ndim != 2 or imu.shape[1] != 3:
        raise ValueError(f"Expected wrist ACC shape (samples, 3), got {imu.shape}.")
    if len(labels) != expected_windows:
        raise ValueError(
            f"Expected {expected_windows} eligible labels for {requested_subject}, got {len(labels)}."
        )
    final_ppg = int(round(((len(labels) - 1) * STEP_SECONDS + WINDOW_SECONDS) * PPG_FS))
    final_imu = int(round(((len(labels) - 1) * STEP_SECONDS + WINDOW_SECONDS) * ACC_FS))
    if len(ppg) < final_ppg or len(imu) < final_imu:
        raise ValueError("Recorded model channels end before the final ECG-derived target window.")
    if not np.isfinite(ppg[:final_ppg]).all() or not np.isfinite(imu[:final_imu]).all():
        raise ValueError("Recorded PPG/IMU model inputs contain non-finite values.")
    if not np.isfinite(labels).all():
        raise ValueError("ECG-derived ground-truth labels contain non-finite values.")
    ppg.setflags(write=False)
    imu.setflags(write=False)
    labels.setflags(write=False)
    return ExperimentSubject(requested_subject, ppg, imu, labels)


def load_experiment_subject(repository_root: Path, config: dict[str, Any]) -> ExperimentSubject:
    subject_id = config["dataset"]["subjects"][0]
    archive_path = repository_root / config["dataset"]["archive_path"]
    raw = load_subject_payload(archive_path, subject_id)
    return _validate_subject_payload(
        raw,
        subject_id,
        int(config["dataset"]["expected_eligible_windows_per_subject"]),
    )


@dataclass(frozen=True)
class PredictionOutcome:
    window_index: int
    status: str
    prediction_bpm: float | None = None
    detail: str | None = None

    def __post_init__(self) -> None:
        allowed = {VALID_STATUS, *FAILURE_CATEGORIES}
        if self.status not in allowed:
            raise ValueError(f"Unknown prediction status {self.status!r}.")
        if self.status == VALID_STATUS:
            if self.prediction_bpm is None or not math.isfinite(self.prediction_bpm):
                raise ValueError("A valid outcome requires a finite prediction.")
        elif self.prediction_bpm is not None:
            raise ValueError("A failed outcome cannot carry a prediction.")


class CanonicalBatchEvaluator:
    """Batch the frozen canonical model without accepting ground truth."""

    def __init__(self, bridge: PPGDaliaHRInferenceBridge, batch_size: int = BATCH_SIZE) -> None:
        if batch_size <= 0:
            raise ValueError("batch_size must be positive.")
        self.bridge = bridge
        self.batch_size = batch_size

    def predict(self, windows: Sequence[PPGDaliaModelWindow]) -> list[PredictionOutcome]:
        predictor = self.bridge.canonical_predictor
        pending_windows: list[PPGDaliaModelWindow] = []
        ppg_normalized: list[np.ndarray] = []
        imu_normalized: list[np.ndarray] = []
        outcomes: list[PredictionOutcome] = []

        for window in windows:
            try:
                ppg_norm = zscore_ppg_window(window.ppg)
                imu_norm = zscore_imu_window(window.imu)
            except FlatSignalError as exc:
                outcomes.append(
                    PredictionOutcome(window.window_index, "canonical_invalid_input", detail=str(exc))
                )
                continue
            except (TypeError, ValueError) as exc:
                outcomes.append(PredictionOutcome(window.window_index, "inference_error", detail=str(exc)))
                continue
            pending_windows.append(window)
            ppg_normalized.append(ppg_norm)
            imu_normalized.append(imu_norm)

        if pending_windows:
            try:
                import torch

                ppg_array = np.stack(ppg_normalized, axis=0)
                imu_array = np.stack(imu_normalized, axis=0)
                model = predictor.model  # type: ignore[attr-defined]
                device = predictor.device  # type: ignore[attr-defined]
                model.eval()
                predictions: list[np.ndarray] = []
                with torch.no_grad():
                    for start in range(0, len(pending_windows), self.batch_size):
                        end = start + self.batch_size
                        ppg_tensor = torch.from_numpy(ppg_array[start:end]).to(device).view(-1, 1, PPG_WINDOW_SAMPLES)
                        imu_tensor = torch.from_numpy(imu_array[start:end]).to(device).view(-1, 3, ACC_WINDOW_SAMPLES)
                        bpm = model(ppg_tensor, imu_tensor) * predictor.hr_std + predictor.hr_mean  # type: ignore[attr-defined]
                        predictions.append(bpm.detach().cpu().numpy().reshape(-1))
                prediction_values = np.concatenate(predictions)
                if len(prediction_values) != len(pending_windows):
                    raise RuntimeError("Canonical model returned an unexpected batch length.")
                for window, prediction in zip(pending_windows, prediction_values, strict=True):
                    value = float(prediction)
                    if not math.isfinite(value):
                        outcomes.append(
                            PredictionOutcome(window.window_index, "inference_error", detail="non-finite model output")
                        )
                    else:
                        outcomes.append(PredictionOutcome(window.window_index, VALID_STATUS, value))
            except Exception as batch_exc:
                # Preserve per-window failure accounting if a batch-level runtime
                # error occurs. This path calls the canonical bridge one window at
                # a time and never creates a fallback prediction.
                for window in pending_windows:
                    try:
                        prediction = self.bridge.predict(window)
                    except FlatSignalError as exc:
                        outcomes.append(
                            PredictionOutcome(window.window_index, "canonical_invalid_input", detail=str(exc))
                        )
                    except Exception as exc:
                        outcomes.append(
                            PredictionOutcome(
                                window.window_index,
                                "inference_error",
                                detail=f"{batch_exc}; canonical retry: {exc}",
                            )
                        )
                    else:
                        outcomes.append(
                            PredictionOutcome(window.window_index, VALID_STATUS, prediction.value)
                        )
        return sorted(outcomes, key=lambda outcome: outcome.window_index)


def _raw_batch(
    subject: ExperimentSubject,
    channel_name: str,
    start_seconds: float,
    end_seconds: float,
) -> RawChannelBatch:
    if channel_name == PPG_CHANNEL:
        rate = PPG_FS
        axes = ["bvp"]
        role = "physiological"
        start = int(round(start_seconds * rate))
        end = int(round(end_seconds * rate))
        samples: list[float] | list[list[float]] = subject.ppg[start:end].tolist()
    elif channel_name == IMU_CHANNEL:
        rate = ACC_FS
        axes = ["x", "y", "z"]
        role = "context_artifact_reference"
        start = int(round(start_seconds * rate))
        end = int(round(end_seconds * rate))
        samples = subject.imu[start:end].tolist()
    else:
        raise ValueError(f"Unsupported experiment channel {channel_name}.")
    return RawChannelBatch(
        dataset_name=DATASET_NAME,
        subject_id=subject.subject_id,
        channel_name=channel_name,
        device="Empatica E4 (wrist)",
        role=role,
        axes=axes,
        units="device units",
        sample_rate_hz=rate,
        sample_start_index=start,
        start_timestamp_seconds=start / rate,
        end_timestamp_seconds=(end - 1) / rate,
        samples=samples,
    )


def _clean_snapshots(subject: ExperimentSubject, batch_seconds: float) -> Iterator[LiveMetricsSnapshot]:
    start = 0.0
    while start < subject.experiment_duration_seconds:
        end = min(start + batch_seconds, subject.experiment_duration_seconds)
        yield LiveMetricsSnapshot(
            timestamp=end,
            source=TelemetrySourceMetadata(
                source_type=DataSourceType.DATASET_REPLAY,
                display_label="REAL RECORDED DATA — REPLAY MODE",
                dataset_name=DATASET_NAME,
                subject_id=subject.subject_id,
                replay_position_seconds=end,
                duration_seconds=subject.experiment_duration_seconds,
                playback_state=ReplayPlaybackState.PLAYING,
                playback_speed=1.0,
                license="CC BY 4.0",
                available_channels=[PPG_CHANNEL, IMU_CHANNEL],
            ),
            channels=[
                _raw_batch(subject, PPG_CHANNEL, start, end),
                _raw_batch(subject, IMU_CHANNEL, start, end),
            ],
        )
        start = end


def _faulted_snapshots(
    subject: ExperimentSubject,
    condition: Condition,
    batch_seconds: float,
) -> Iterator[LiveMetricsSnapshot]:
    injector = ReplayFaultInjector()
    replay_config = condition.replay_config()
    if replay_config is not None:
        injector.configure(replay_config)
    for snapshot in _clean_snapshots(subject, batch_seconds):
        yield injector.apply(snapshot)


def _fault_metadata(snapshot: LiveMetricsSnapshot) -> dict[str, Any] | None:
    if snapshot.fault_injection is None:
        return None
    value = snapshot.fault_injection.model_dump(mode="json")
    value["dropped_samples"] = dict(sorted(value["dropped_samples"].items()))
    value["parameters"] = dict(sorted(value["parameters"].items()))
    return value


def _continuous_outcomes(
    subject: ExperimentSubject,
    condition: Condition,
    evaluator: CanonicalBatchEvaluator,
    batch_seconds: float,
) -> tuple[list[PredictionOutcome], dict[str, Any] | None]:
    assembler = PPGDaliaWindowAssembler()
    outcomes: list[PredictionOutcome] = []
    pending: list[PPGDaliaModelWindow] = []
    provenance: dict[str, Any] | None = None
    for snapshot in _faulted_snapshots(subject, condition, batch_seconds):
        if provenance is None and snapshot.fault_injection is not None:
            provenance = _fault_metadata(snapshot)
        try:
            pending.extend(assembler.ingest(snapshot))
        except WindowAssemblyError as exc:
            raise RuntimeError(
                f"Accepted continuous fault {condition.condition_id} broke synchronized assembly: {exc}"
            ) from exc
        if len(pending) >= evaluator.batch_size:
            outcomes.extend(evaluator.predict(pending))
            pending.clear()
    if pending:
        outcomes.extend(evaluator.predict(pending))
    return sorted(outcomes, key=lambda item: item.window_index), provenance


def _dropout_outcomes(
    subject: ExperimentSubject,
    condition: Condition,
    batch_seconds: float,
) -> tuple[list[PredictionOutcome], dict[str, Any] | None]:
    first = next(_faulted_snapshots(subject, condition, batch_seconds))
    if PPG_CHANNEL in first.source.available_channels and condition.target in {"ppg", "both"}:
        raise RuntimeError("Phase 4 dropout did not remove targeted PPG availability.")
    if IMU_CHANNEL in first.source.available_channels and condition.target in {"imu", "both"}:
        raise RuntimeError("Phase 4 dropout did not remove targeted IMU availability.")
    outcomes = [
        PredictionOutcome(index, "input_unavailable", detail="required modality removed by configured dropout")
        for index in range(subject.eligible_window_count)
    ]
    provenance = _fault_metadata(first)
    if provenance is not None:
        target_channels = {
            "ppg": (PPG_CHANNEL,),
            "imu": (IMU_CHANNEL,),
            "both": (PPG_CHANNEL, IMU_CHANNEL),
        }[str(condition.target)]
        provenance["total_dropped_samples"] = {
            channel: int(
                round(
                    subject.experiment_duration_seconds
                    * (PPG_FS if channel == PPG_CHANNEL else ACC_FS)
                )
            )
            for channel in target_channels
        }
        provenance["evaluation_scope"] = (
            "complete recording; binary production semantics verified on the first batch"
        )
    return outcomes, provenance


def _packet_loss_outcomes(
    subject: ExperimentSubject,
    condition: Condition,
    evaluator: CanonicalBatchEvaluator,
    batch_seconds: float,
) -> tuple[list[PredictionOutcome], dict[str, Any] | None]:
    target_channels = {
        "ppg": {PPG_CHANNEL},
        "imu": {IMU_CHANNEL},
        "both": {PPG_CHANNEL, IMU_CHANNEL},
    }[str(condition.target)]
    ppg_values = subject.ppg.copy()
    imu_values = subject.imu.copy()
    ppg_present = np.ones(len(ppg_values), dtype=bool)
    imu_present = np.ones(len(imu_values), dtype=bool)
    if PPG_CHANNEL in target_channels:
        ppg_present[:] = False
    if IMU_CHANNEL in target_channels:
        imu_present[:] = False

    provenance: dict[str, Any] | None = None
    total_dropped = {PPG_CHANNEL: 0, IMU_CHANNEL: 0}
    for snapshot in _faulted_snapshots(subject, condition, batch_seconds):
        if provenance is None:
            provenance = _fault_metadata(snapshot)
        if snapshot.fault_injection is not None:
            for channel, count in snapshot.fault_injection.dropped_samples.items():
                total_dropped[channel] += count
        for batch in snapshot.channels:
            start = batch.sample_start_index
            end = start + len(batch.samples)
            values = np.asarray(batch.samples, dtype=np.float64)
            if batch.channel_name == PPG_CHANNEL and PPG_CHANNEL in target_channels:
                ppg_values[start:end] = values
                ppg_present[start:end] = True
            elif batch.channel_name == IMU_CHANNEL and IMU_CHANNEL in target_channels:
                imu_values[start:end] = values
                imu_present[start:end] = True
    if provenance is not None:
        provenance["total_dropped_samples"] = {
            channel: total_dropped[channel]
            for channel in (PPG_CHANNEL, IMU_CHANNEL)
            if channel in target_channels
        }

    outcomes: list[PredictionOutcome] = []
    pending: list[PPGDaliaModelWindow] = []
    for index in range(subject.eligible_window_count):
        start_seconds = index * STEP_SECONDS
        ppg_start = int(round(start_seconds * PPG_FS))
        imu_start = int(round(start_seconds * ACC_FS))
        ppg_end = ppg_start + PPG_WINDOW_SAMPLES
        imu_end = imu_start + ACC_WINDOW_SAMPLES
        if not ppg_present[ppg_start:ppg_end].all() or not imu_present[imu_start:imu_end].all():
            outcomes.append(
                PredictionOutcome(
                    index,
                    "inference_error",
                    detail="native sample discontinuity; no interpolation or time compression permitted",
                )
            )
            continue
        pending.append(
            PPGDaliaModelWindow(
                dataset_name=DATASET_NAME,
                subject_id=subject.subject_id,
                window_index=index,
                window_start_seconds=start_seconds,
                window_duration_seconds=WINDOW_SECONDS,
                ppg_start_index=ppg_start,
                imu_start_index=imu_start,
                ppg=ppg_values[ppg_start:ppg_end],
                imu=imu_values[imu_start:imu_end].T,
            )
        )
        if len(pending) >= evaluator.batch_size:
            outcomes.extend(evaluator.predict(pending))
            pending.clear()
    if pending:
        outcomes.extend(evaluator.predict(pending))
    return sorted(outcomes, key=lambda item: item.window_index), provenance


def score_outcomes(
    condition: Condition,
    outcomes: Sequence[PredictionOutcome],
    labels: np.ndarray,
    clean_metrics: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Join finalized outcomes with labels and compute honest availability."""

    eligible = len(labels)
    by_index = {outcome.window_index: outcome for outcome in outcomes}
    if len(by_index) != len(outcomes) or set(by_index) != set(range(eligible)):
        raise ValueError("Every eligible window must have exactly one prediction outcome.")
    valid = [by_index[index] for index in range(eligible) if by_index[index].status == VALID_STATUS]
    failure_counts = {
        category: sum(outcome.status == category for outcome in outcomes)
        for category in FAILURE_CATEGORIES
    }
    if len(valid) + sum(failure_counts.values()) != eligible:
        raise ValueError("Availability accounting does not sum to the eligible-window count.")

    if valid:
        predictions = np.asarray([outcome.prediction_bpm for outcome in valid], dtype=np.float32)
        target = np.asarray([labels[outcome.window_index] for outcome in valid], dtype=np.float32)
        mae_value: float | None = float(np.mean(np.abs(predictions - target)))
        rmse_value: float | None = float(np.sqrt(np.mean((predictions - target) ** 2)))
    else:
        mae_value = None
        rmse_value = None
    availability = len(valid) / eligible
    metrics: dict[str, Any] = {
        "condition_id": condition.condition_id,
        "group_id": condition.group_id,
        "fault_type": condition.fault_type,
        "target": condition.target,
        "severity": condition.severity,
        "seed": condition.seed,
        "stochastic": condition.stochastic,
        "eligible_window_count": eligible,
        "valid_prediction_count": len(valid),
        "prediction_availability_rate": availability,
        "mae_bpm_valid_only": mae_value,
        "rmse_bpm_valid_only": rmse_value,
        "failure_counts": failure_counts,
        "failure_rates": {
            category: failure_counts[category] / eligible for category in FAILURE_CATEGORIES
        },
        "delta_from_clean": {
            "mae_bpm": None,
            "rmse_bpm": None,
            "availability": None,
        },
    }
    if clean_metrics is not None:
        clean_mae = clean_metrics["mae_bpm_valid_only"]
        clean_rmse = clean_metrics["rmse_bpm_valid_only"]
        metrics["delta_from_clean"] = {
            "mae_bpm": None if mae_value is None or clean_mae is None else mae_value - clean_mae,
            "rmse_bpm": None if rmse_value is None or clean_rmse is None else rmse_value - clean_rmse,
            "availability": availability - clean_metrics["prediction_availability_rate"],
        }
    return metrics


def _metric_summary(values: Sequence[float | int | None]) -> dict[str, Any]:
    defined = [float(value) for value in values if value is not None]
    all_defined = len(defined) == len(values)
    return {
        "defined_replicates": len(defined),
        "mean": float(np.mean(defined)) if all_defined and defined else None,
        "population_std": float(np.std(defined, ddof=0)) if all_defined and defined else None,
    }


def aggregate_stochastic_conditions(conditions: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for condition in conditions:
        if condition["stochastic"]:
            grouped.setdefault(condition["group_id"], []).append(condition)
    aggregates: list[dict[str, Any]] = []
    for group_id, records in grouped.items():
        records = sorted(records, key=lambda record: record["seed"])
        if [record["seed"] for record in records] != [2026, 2027, 2028, 2029, 2030]:
            raise ValueError(f"Stochastic group {group_id} does not contain the frozen five seeds.")
        aggregates.append(
            {
                "group_id": group_id,
                "fault_type": records[0]["fault_type"],
                "target": records[0]["target"],
                "severity": records[0]["severity"],
                "seeds": [record["seed"] for record in records],
                "valid_prediction_count": _metric_summary(
                    [record["valid_prediction_count"] for record in records]
                ),
                "prediction_availability_rate": _metric_summary(
                    [record["prediction_availability_rate"] for record in records]
                ),
                "mae_bpm_valid_only": _metric_summary(
                    [record["mae_bpm_valid_only"] for record in records]
                ),
                "rmse_bpm_valid_only": _metric_summary(
                    [record["rmse_bpm_valid_only"] for record in records]
                ),
                "failure_counts": {
                    category: _metric_summary(
                        [record["failure_counts"][category] for record in records]
                    )
                    for category in FAILURE_CATEGORIES
                },
                "failure_rates": {
                    category: _metric_summary(
                        [record["failure_rates"][category] for record in records]
                    )
                    for category in FAILURE_CATEGORIES
                },
                "delta_from_clean": {
                    metric: _metric_summary(
                        [record["delta_from_clean"][metric] for record in records]
                    )
                    for metric in ("mae_bpm", "rmse_bpm", "availability")
                },
            }
        )
    return aggregates


def _verify_config_against_code(config: dict[str, Any]) -> None:
    model = config["model"]
    window = config["window"]
    if model["checkpoint_sha256"] != EXPECTED_CHECKPOINT_SHA256:
        raise ValueError("Frozen config checkpoint SHA256 differs from the production bridge.")
    if model["checkpoint_size_bytes"] != EXPECTED_CHECKPOINT_SIZE_BYTES:
        raise ValueError("Frozen config checkpoint size differs from the production bridge.")
    expected_window = {
        "duration_seconds": WINDOW_SECONDS,
        "stride_seconds": STEP_SECONDS,
        "ppg_sample_rate_hz": PPG_FS,
        "imu_sample_rate_hz": ACC_FS,
        "ppg_samples": PPG_WINDOW_SAMPLES,
        "imu_samples_per_axis": ACC_WINDOW_SAMPLES,
    }
    for key, expected in expected_window.items():
        if window[key] != expected:
            raise ValueError(f"Frozen config {key} differs from the canonical code constant.")


def _verify_golden_reference(
    repository_root: Path,
    config: dict[str, Any],
    subject: ExperimentSubject,
    bridge: PPGDaliaHRInferenceBridge,
) -> list[dict[str, float | int]]:
    reference_path = repository_root / config["clean_reference"]["golden_reference_path"]
    golden = json.loads(reference_path.read_text(encoding="utf-8"))
    if golden["subject_id"] != subject.subject_id:
        raise RuntimeError("Golden integration subject differs from the experiment subject.")
    tolerance = float(config["clean_reference"]["absolute_tolerance_bpm"])
    comparisons: list[dict[str, float | int]] = []
    for item in golden["windows"]:
        index = int(item["window_index"])
        start_seconds = index * STEP_SECONDS
        ppg_start = int(round(start_seconds * PPG_FS))
        imu_start = int(round(start_seconds * ACC_FS))
        window = PPGDaliaModelWindow(
            dataset_name=DATASET_NAME,
            subject_id=subject.subject_id,
            window_index=index,
            window_start_seconds=start_seconds,
            window_duration_seconds=WINDOW_SECONDS,
            ppg_start_index=ppg_start,
            imu_start_index=imu_start,
            ppg=subject.ppg[ppg_start : ppg_start + PPG_WINDOW_SAMPLES],
            imu=subject.imu[imu_start : imu_start + ACC_WINDOW_SAMPLES].T,
        )
        actual = bridge.predict(window).value
        expected = float(item["expected_model_hr_prediction_bpm"])
        absolute_error = abs(actual - expected)
        if absolute_error > tolerance:
            raise RuntimeError(
                f"Golden clean prediction mismatch at window {index}: expected {expected}, got {actual}."
            )
        comparisons.append(
            {
                "window_index": index,
                "expected_bpm": expected,
                "actual_bpm": actual,
                "absolute_difference_bpm": absolute_error,
            }
        )
    return comparisons


def _verify_clean_baseline(config: dict[str, Any], clean: dict[str, Any]) -> None:
    reference = config["clean_reference"]
    tolerance = float(reference["absolute_tolerance_bpm"])
    if clean["eligible_window_count"] != reference["eligible_windows"]:
        raise RuntimeError("Clean eligible-window count differs from the frozen canonical evaluation.")
    if clean["valid_prediction_count"] != reference["eligible_windows"]:
        raise RuntimeError("Clean path did not produce one valid prediction for every eligible window.")
    for metric, expected_key in (
        ("mae_bpm_valid_only", "mae_bpm"),
        ("rmse_bpm_valid_only", "rmse_bpm"),
    ):
        if abs(clean[metric] - reference[expected_key]) > tolerance:
            raise RuntimeError(
                f"Clean {metric}={clean[metric]} differs from canonical {reference[expected_key]} "
                f"beyond tolerance {tolerance}."
            )


def _condition_outcomes(
    subject: ExperimentSubject,
    condition: Condition,
    evaluator: CanonicalBatchEvaluator,
    batch_seconds: float,
) -> tuple[list[PredictionOutcome], dict[str, Any] | None]:
    if condition.fault_type == ReplayFaultType.MODALITY_DROPOUT.value:
        return _dropout_outcomes(subject, condition, batch_seconds)
    if condition.fault_type == ReplayFaultType.PACKET_LOSS.value:
        return _packet_loss_outcomes(subject, condition, evaluator, batch_seconds)
    return _continuous_outcomes(subject, condition, evaluator, batch_seconds)


def run_experiment(
    repository_root: str | Path = REPOSITORY_ROOT,
    config_path: str | Path = DEFAULT_CONFIG_PATH,
    *,
    progress: bool = True,
) -> dict[str, Any]:
    repository_root = Path(repository_root).resolve()
    config_path = Path(config_path).resolve()
    config = load_protocol_config(config_path)
    _verify_config_against_code(config)
    conditions = build_condition_matrix(config)
    subject = load_experiment_subject(repository_root, config)
    checkpoint_path = repository_root / config["model"]["checkpoint_path"]
    bridge = PPGDaliaHRInferenceBridge(checkpoint_path)
    evaluator = CanonicalBatchEvaluator(bridge)
    golden_comparisons = _verify_golden_reference(repository_root, config, subject, bridge)
    batch_seconds = float(config["window"]["fault_application_batch_seconds"])

    condition_results: list[dict[str, Any]] = []
    clean_metrics: dict[str, Any] | None = None
    for ordinal, condition in enumerate(conditions, start=1):
        if progress:
            print(f"[{ordinal:03d}/{len(conditions)}] {condition.condition_id}", flush=True)
        outcomes, provenance = _condition_outcomes(subject, condition, evaluator, batch_seconds)
        metrics = score_outcomes(condition, outcomes, subject.labels, clean_metrics)
        metrics["fault_provenance"] = provenance
        if condition.fault_type == "clean":
            _verify_clean_baseline(config, metrics)
            clean_metrics = metrics
        condition_results.append(metrics)
    if clean_metrics is None:
        raise AssertionError("Condition matrix did not contain a clean baseline.")

    stochastic_aggregates = aggregate_stochastic_conditions(condition_results)
    total_windows = sum(result["eligible_window_count"] for result in condition_results)
    expected_total = len(conditions) * subject.eligible_window_count
    if total_windows != expected_total or expected_total != 510_264:
        raise RuntimeError(f"Frozen condition-window count mismatch: got {total_windows}.")

    return {
        "schema_version": 1,
        "experiment_id": config["experiment_id"],
        "scope": "controlled single-subject robustness characterization",
        "protocol": {
            "status": config["protocol_status"],
            "path": str(DEFAULT_PROTOCOL_PATH.relative_to(repository_root)),
            "sha256": _sha256(DEFAULT_PROTOCOL_PATH),
            "config_path": str(config_path.relative_to(repository_root)),
            "config_sha256": _sha256(config_path),
        },
        "dataset": {
            "name": config["dataset"]["name"],
            "source": config["dataset"]["source"],
            "license": config["dataset"]["license"],
            "subject_id": subject.subject_id,
            "subject_role": "held-out test subject; never used in model training",
            "available_verified_subjects_used": [subject.subject_id],
            "ground_truth": config["dataset"]["ground_truth"],
        },
        "model": {
            "name": config["model"]["name"],
            "model_id": "PPGDaliaHRModelB:PPGPlusIMUHRModel",
            "checkpoint_path": config["model"]["checkpoint_path"],
            "checkpoint_size_bytes": checkpoint_path.stat().st_size,
            "checkpoint_sha256": bridge.checkpoint_sha256,
            "preprocessing": config["window"]["preprocessing"],
            "window_duration_seconds": WINDOW_SECONDS,
            "stride_seconds": STEP_SECONDS,
            "retrained": False,
            "output_clipping": False,
            "uncertainty": None,
        },
        "execution": {
            "fault_engine": "backend.app.engine.fault_injection.ReplayFaultInjector",
            "window_assembler": "backend.app.ml.ppg_dalia_windows.PPGDaliaWindowAssembler",
            "canonical_predictor": "ml.inference.ppg_dalia_hr.PPGDaliaHRPredictor",
            "fault_application_batch_seconds": batch_seconds,
            "condition_count": len(condition_results),
            "eligible_windows_per_condition": subject.eligible_window_count,
            "total_condition_windows": total_windows,
            "stochastic_seeds": config["stochastic_seeds"],
            "no_missing_sample_fill": True,
            "no_interpolation": True,
            "no_fallback_prediction": True,
            "ground_truth_was_model_input": False,
        },
        "clean_parity": {
            "reference": config["clean_reference"],
            "golden_windows": golden_comparisons,
            "passed": True,
        },
        "clean_baseline": clean_metrics,
        "conditions": condition_results,
        "stochastic_aggregates": stochastic_aggregates,
        "interpretation_boundary": {
            "supported": "Observed behavior of the frozen canonical pipeline under controlled corruption of official held-out S14 replay data.",
            "not_supported": [
                "population-level robustness",
                "fault tolerance or fault detection",
                "calibrated predictive uncertainty",
                "microgravity performance or astronaut readiness",
                "generalization to missing PPG-DaLiA subjects",
            ],
        },
    }


def _format_number(value: float | int | None, digits: int = 4) -> str:
    if value is None:
        return "N/A"
    if isinstance(value, int):
        return str(value)
    return f"{value:.{digits}f}"


def render_report(results: dict[str, Any]) -> str:
    clean = results["clean_baseline"]
    lines = [
        "# PPG-DaLiA S14 fault-robustness characterization",
        "",
        "This is a controlled single-subject result for official held-out S14, not a population-level robustness claim.",
        "",
        "## Clean baseline",
        "",
        f"- Eligible/valid windows: {clean['eligible_window_count']}/{clean['valid_prediction_count']}",
        f"- Availability: {clean['prediction_availability_rate']:.6f}",
        f"- MAE: {clean['mae_bpm_valid_only']:.6f} bpm",
        f"- RMSE: {clean['rmse_bpm_valid_only']:.6f} bpm",
        "- Canonical and golden parity gates: PASS",
        "",
        "## Full concrete condition table",
        "",
        "MAE/RMSE are valid-prediction-only; failure counts retain every eligible window.",
        "",
        "| Condition | Fault | Target | Severity | Seed | Valid/eligible | Availability | MAE | RMSE | Unavailable | Invalid | Error |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for condition in results["conditions"]:
        failures = condition["failure_counts"]
        lines.append(
            "| "
            + " | ".join(
                [
                    condition["condition_id"],
                    condition["fault_type"],
                    condition["target"] or "—",
                    _format_number(condition["severity"], 2),
                    _format_number(condition["seed"], 0),
                    f"{condition['valid_prediction_count']}/{condition['eligible_window_count']}",
                    _format_number(condition["prediction_availability_rate"], 6),
                    _format_number(condition["mae_bpm_valid_only"], 4),
                    _format_number(condition["rmse_bpm_valid_only"], 4),
                    str(failures["input_unavailable"]),
                    str(failures["canonical_invalid_input"]),
                    str(failures["inference_error"]),
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Stochastic five-seed aggregates",
            "",
            "Values are mean ± population standard deviation across seeds 2026-2030. N/A means the metric was undefined for at least one seed because no valid prediction existed.",
            "",
            "| Group | Availability | MAE bpm | RMSE bpm | Valid count |",
            "|---|---:|---:|---:|---:|",
        ]
    )
    for aggregate in results["stochastic_aggregates"]:
        formatted = []
        for key in (
            "prediction_availability_rate",
            "mae_bpm_valid_only",
            "rmse_bpm_valid_only",
            "valid_prediction_count",
        ):
            summary = aggregate[key]
            if summary["mean"] is None:
                formatted.append(f"N/A ({summary['defined_replicates']}/5 defined)")
            else:
                formatted.append(f"{summary['mean']:.4f} ± {summary['population_std']:.4f}")
        lines.append(f"| {aggregate['group_id']} | " + " | ".join(formatted) + " |")
    lines.extend(
        [
            "",
            "## Interpretation limits",
            "",
            "Accuracy changes and availability collapse are reported separately. Explicit rejection is not called an accuracy failure, and continued output is not evidence of fault detection. No retraining, output clipping, interpolation, missing-modality fill, fallback HR, or predictive uncertainty was introduced.",
            "",
            "These results support only an observation of this frozen pipeline on official held-out S14 under the pre-registered corruptions. They do not establish population-level robustness, fault tolerance, calibrated uncertainty, microgravity performance, or astronaut readiness.",
            "",
        ]
    )
    return "\n".join(lines)


def write_artifacts(results: dict[str, Any], repository_root: Path, config: dict[str, Any]) -> tuple[Path, Path]:
    output_path = repository_root / config["output"]["json_path"]
    report_path = repository_root / config["output"]["report_path"]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(serialize_results(results), encoding="utf-8")
    report_path.write_text(render_report(results), encoding="utf-8")
    return output_path, report_path
