"""Integrity tests for the frozen Phase 5 experiment framework."""

from __future__ import annotations

import inspect
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "backend"))

from app.ml.ppg_dalia_hr import (
    DEFAULT_CHECKPOINT_PATH,
    EXPECTED_CHECKPOINT_SHA256,
    EXPECTED_CHECKPOINT_SIZE_BYTES,
    CheckpointIdentityError,
    PPGDaliaHRInferenceBridge,
)
from app.ml.ppg_dalia_windows import (
    DATASET_NAME,
    PPGDaliaModelWindow,
)
from ml.datasets.ppg_dalia import ACC_FS, PPG_FS, STEP_SECONDS, WINDOW_SECONDS
from ml.experiments.ppg_dalia_fault_robustness.experiment import (
    DEFAULT_CONFIG_PATH,
    REPOSITORY_ROOT,
    CanonicalBatchEvaluator,
    Condition,
    ExperimentSubject,
    PredictionOutcome,
    _faulted_snapshots,
    _validate_subject_payload,
    build_condition_matrix,
    load_protocol_config,
    score_outcomes,
    serialize_results,
)

RAW_ARCHIVE = REPOSITORY_ROOT / "datasets" / "ppg-dalia" / "raw_uci" / "ppg_dalia_uci.zip"


def _subject(duration_seconds: float = 16.0) -> ExperimentSubject:
    ppg_indexes = np.arange(int(duration_seconds * PPG_FS), dtype=np.float64)
    imu_indexes = np.arange(int(duration_seconds * ACC_FS), dtype=np.float64)
    labels = np.arange(int((duration_seconds - WINDOW_SECONDS) / STEP_SECONDS) + 1, dtype=np.float32) + 70
    return ExperimentSubject(
        subject_id="S14",
        ppg=np.sin(ppg_indexes / 13.0),
        imu=np.column_stack(
            (np.sin(imu_indexes / 7.0), np.cos(imu_indexes / 11.0), imu_indexes / 100.0)
        ),
        labels=labels,
    )


def _condition(
    fault_type: str,
    target: str | None = None,
    severity: float | None = None,
    seed: int | None = None,
    stochastic: bool = False,
) -> Condition:
    group = fault_type if fault_type == "clean" else f"{fault_type}__{target}__{severity}"
    return Condition(group if seed is None else f"{group}__{seed}", group, fault_type, target, severity, seed, stochastic)


def test_frozen_config_loads_deterministically_and_matrix_is_unique() -> None:
    first = load_protocol_config(DEFAULT_CONFIG_PATH)
    second = load_protocol_config(DEFAULT_CONFIG_PATH)
    assert first == second
    assert serialize_results(first) == serialize_results(second)
    matrix = build_condition_matrix(first)
    assert len(matrix) == 114
    assert len({condition.condition_id for condition in matrix}) == 114
    assert first["stochastic_seeds"] == [2026, 2027, 2028, 2029, 2030]
    assert [fault["severities"] for fault in first["faults"]] == [
        [1.0],
        [1.0],
        [0.1, 0.25, 0.5, 1.0],
        [0.1, 0.25, 0.5, 1.0],
        [0.01, 0.05, 0.1, 0.2],
    ]


def test_fixed_fault_and_seed_reproduce_identical_production_corruption() -> None:
    subject = _subject()
    condition = _condition("additive_noise", "ppg", 0.5, 2026, True)
    first = [snapshot.model_dump(mode="json") for snapshot in _faulted_snapshots(subject, condition, 8.0)]
    second = [snapshot.model_dump(mode="json") for snapshot in _faulted_snapshots(subject, condition, 8.0)]
    assert first == second


def test_ground_truth_is_not_accepted_by_fault_or_prediction_boundary() -> None:
    prediction_parameters = set(inspect.signature(CanonicalBatchEvaluator.predict).parameters)
    fault_parameters = set(inspect.signature(_faulted_snapshots).parameters)
    assert prediction_parameters == {"self", "windows"}
    assert fault_parameters == {"subject", "condition", "batch_seconds"}
    assert "labels" not in prediction_parameters | fault_parameters


def test_availability_keeps_failures_and_accuracy_uses_only_valid_predictions() -> None:
    labels = np.asarray([70.0, 1000.0, 80.0, -1000.0], dtype=np.float32)
    condition = _condition("clean")
    outcomes = [
        PredictionOutcome(0, "valid", 72.0),
        PredictionOutcome(1, "input_unavailable"),
        PredictionOutcome(2, "valid", 76.0),
        PredictionOutcome(3, "inference_error"),
    ]
    result = score_outcomes(condition, outcomes, labels)
    assert result["eligible_window_count"] == 4
    assert result["valid_prediction_count"] == 2
    assert result["prediction_availability_rate"] == 0.5
    assert result["mae_bpm_valid_only"] == pytest.approx(3.0)
    assert result["rmse_bpm_valid_only"] == pytest.approx(np.sqrt(10.0))
    assert result["failure_counts"] == {
        "input_unavailable": 1,
        "canonical_invalid_input": 0,
        "inference_error": 1,
    }


def test_availability_rejects_silently_missing_or_duplicate_windows() -> None:
    labels = np.asarray([70.0, 71.0], dtype=np.float32)
    with pytest.raises(ValueError, match="exactly one"):
        score_outcomes(_condition("clean"), [PredictionOutcome(0, "valid", 70.0)], labels)
    with pytest.raises(ValueError, match="exactly one"):
        score_outcomes(
            _condition("clean"),
            [PredictionOutcome(0, "valid", 70.0), PredictionOutcome(0, "valid", 70.0)],
            labels,
        )


def test_subject_identity_is_enforced_before_experiment_arrays_exist() -> None:
    raw = {
        "subject": "S2",
        "signal": {
            "wrist": {
                "BVP": np.ones((int(WINDOW_SECONDS * PPG_FS), 1)),
                "ACC": np.ones((int(WINDOW_SECONDS * ACC_FS), 3)),
            }
        },
        "label": np.asarray([70.0]),
    }
    with pytest.raises(ValueError, match="refusing to mix or relabel subjects"):
        _validate_subject_payload(raw, "S14", 1)


def test_checkpoint_identity_in_config_matches_enforced_bridge_contract(tmp_path: Path) -> None:
    config = load_protocol_config(DEFAULT_CONFIG_PATH)
    assert config["model"]["checkpoint_sha256"] == EXPECTED_CHECKPOINT_SHA256
    assert config["model"]["checkpoint_size_bytes"] == EXPECTED_CHECKPOINT_SIZE_BYTES
    bad_checkpoint = tmp_path / "model.pt"
    bad_checkpoint.write_bytes(b"not the validated checkpoint")
    with pytest.raises(CheckpointIdentityError):
        PPGDaliaHRInferenceBridge(bad_checkpoint)


def test_condition_metadata_changes_with_fault_severity_and_seed() -> None:
    config = load_protocol_config(DEFAULT_CONFIG_PATH)
    matrix = build_condition_matrix(config)
    keys = {
        (item.fault_type, item.target, item.severity, item.seed): item.condition_id
        for item in matrix
    }
    assert len(keys) == len(matrix)
    assert keys[("additive_noise", "ppg", 0.1, 2026)] != keys[("additive_noise", "ppg", 0.25, 2026)]
    assert keys[("packet_loss", "imu", 0.1, 2026)] != keys[("packet_loss", "imu", 0.1, 2027)]


def test_result_serialization_is_deterministic_and_rejects_nan() -> None:
    left = {"z": [2, 1], "a": {"b": None, "a": 0.5}}
    right = {"a": {"a": 0.5, "b": None}, "z": [2, 1]}
    assert serialize_results(left) == serialize_results(right)
    with pytest.raises(ValueError):
        serialize_results({"invalid": float("nan")})


@pytest.mark.skipif(
    not RAW_ARCHIVE.exists() or not DEFAULT_CHECKPOINT_PATH.exists(),
    reason="official S14 archive and validated checkpoint are required",
)
def test_batch_experiment_prediction_matches_canonical_clean_prediction() -> None:
    from app.data.ppg_dalia import load_subject_payload

    raw = load_subject_payload(RAW_ARCHIVE, "S14")
    index = 100
    t0 = index * STEP_SECONDS
    ppg_start = int(round(t0 * PPG_FS))
    imu_start = int(round(t0 * ACC_FS))
    ppg = np.asarray(raw["signal"]["wrist"]["BVP"], dtype=np.float64).reshape(-1)
    imu = np.asarray(raw["signal"]["wrist"]["ACC"], dtype=np.float64)
    window = PPGDaliaModelWindow(
        dataset_name=DATASET_NAME,
        subject_id="S14",
        window_index=index,
        window_start_seconds=t0,
        window_duration_seconds=WINDOW_SECONDS,
        ppg_start_index=ppg_start,
        imu_start_index=imu_start,
        ppg=ppg[ppg_start : ppg_start + int(WINDOW_SECONDS * PPG_FS)],
        imu=imu[imu_start : imu_start + int(WINDOW_SECONDS * ACC_FS)].T,
    )
    bridge = PPGDaliaHRInferenceBridge(DEFAULT_CHECKPOINT_PATH)
    expected = bridge.predict(window).value
    actual = CanonicalBatchEvaluator(bridge).predict([window])
    assert len(actual) == 1
    assert actual[0].window_index == index
    assert actual[0].status == "valid"
    assert actual[0].prediction_bpm == pytest.approx(expected, abs=1e-5)


def test_protocol_file_is_frozen_and_contains_no_result_table() -> None:
    protocol = (DEFAULT_CONFIG_PATH.parent / "PROTOCOL.md").read_text(encoding="utf-8")
    assert "Status: frozen before the first complete result run" in protocol
    assert "510264 condition-window evaluations" in protocol
    assert "## Results" not in protocol


def test_committed_result_preserves_full_accounting_and_frozen_hashes() -> None:
    result_path = REPOSITORY_ROOT / "results" / "ppg_dalia_fault_robustness.json"
    if not result_path.exists():
        pytest.skip("result artifact is created by the complete frozen run")
    raw_text = result_path.read_text(encoding="utf-8")
    result = json.loads(raw_text)
    assert raw_text == serialize_results(result)
    assert len(result["conditions"]) == 114
    assert result["execution"]["total_condition_windows"] == 510_264
    assert result["execution"]["ground_truth_was_model_input"] is False
    for condition in result["conditions"]:
        accounted = condition["valid_prediction_count"] + sum(condition["failure_counts"].values())
        assert accounted == condition["eligible_window_count"] == 4476
    protocol_path = REPOSITORY_ROOT / result["protocol"]["path"]
    config_path = REPOSITORY_ROOT / result["protocol"]["config_path"]
    # Day 10 finding: core.autocrlf=true means these text files check out
    # with CRLF on Windows, while the frozen hashes stored in the committed
    # result were computed against LF-normalized (git-blob) bytes. Verified:
    # git-blob content and working-tree content are byte-for-byte identical
    # once normalized. Normalize before hashing rather than weakening the check.
    assert hashlib.sha256(protocol_path.read_bytes().replace(b"\r\n", b"\n")).hexdigest() == result["protocol"]["sha256"]
    assert hashlib.sha256(config_path.read_bytes().replace(b"\r\n", b"\n")).hexdigest() == result["protocol"]["config_sha256"]
