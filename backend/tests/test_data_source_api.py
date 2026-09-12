"""Integration checks for replay REST controls and the existing WebSocket."""

from __future__ import annotations

import pickle
from pathlib import Path

import numpy as np
from fastapi.testclient import TestClient

from app.engine.data_sources import DataSourceManager, data_source_manager
from app.engine.mock_data_engine import MockDataEngine
from app.main import app
from app.ml.ppg_dalia_windows import PPGDaliaModelWindow
from app.ml.replay_hr import ReplayHeartRateInferenceService
from app.schemas.fault_injection import (
    ReplayFaultConfig,
    ReplayFaultTarget,
    ReplayFaultType,
)
from app.schemas.model_prediction import HeartRateModelPrediction, HeartRateModelProvenance


def _write_subject(root: Path, duration_seconds: float = 2.0, subject_id: str = "S1") -> None:
    subject_dir = root / "PPG_FieldStudy" / subject_id
    subject_dir.mkdir(parents=True)

    def scalar(rate: float) -> np.ndarray:
        return np.arange(int(duration_seconds * rate), dtype=np.float64).reshape(-1, 1)

    raw = {
        "subject": subject_id,
        "signal": {
            "wrist": {
                "BVP": scalar(64.0),
                "ACC": np.column_stack((scalar(32.0), scalar(32.0), scalar(32.0))),
                "TEMP": scalar(4.0),
            },
            "chest": {"ECG": scalar(700.0)},
        },
    }
    with (subject_dir / f"{subject_id}.pkl").open("wb") as stream:
        pickle.dump(raw, stream, protocol=pickle.HIGHEST_PROTOCOL)


class _WebSocketTestBridge:
    def predict(self, window: PPGDaliaModelWindow) -> HeartRateModelPrediction:
        return HeartRateModelPrediction(
            value=72.5 + window.window_index,
            normalized_model_output=0.0,
            provenance=HeartRateModelProvenance(
                subject_id=window.subject_id,
                window_index=window.window_index,
                window_start_seconds=window.window_start_seconds,
                window_duration_seconds=window.window_duration_seconds,
                model_id="websocket-test-model",
                checkpoint_path="/test/model.pt",
                checkpoint_sha256="test-sha256",
            ),
        )


def test_replay_controls_and_websocket_use_same_subject(tmp_path: Path) -> None:
    _write_subject(tmp_path)
    data_source_manager.configure_dataset_path(tmp_path)
    data_source_manager.use_synthetic()

    try:
        with TestClient(app) as client:
            subjects = client.get("/data-source/subjects")
            assert subjects.status_code == 200
            assert subjects.json() == {"dataset_name": "PPG-DaLiA", "subjects": ["S1"]}

            loaded = client.post("/data-source/replay/load", json={"subject_id": "S1"})
            assert loaded.status_code == 200
            assert loaded.json()["playback_state"] == "paused"
            assert loaded.json()["subject_id"] == "S1"

            speed = client.post("/data-source/replay/speed", json={"speed": 10})
            assert speed.status_code == 200
            assert speed.json()["playback_speed"] == 10

            with client.websocket_connect("/ws/live-feed") as websocket:
                played = client.post("/data-source/replay/play")
                assert played.status_code == 200
                frame = websocket.receive_json()

            assert frame["source"]["source_type"] == "dataset_replay"
            assert frame["source"]["subject_id"] == "S1"
            assert frame["source"]["display_label"] == "REAL RECORDED DATA — REPLAY MODE"
            assert {batch["subject_id"] for batch in frame["channels"]} == {"S1"}
            assert {batch["channel_name"] for batch in frame["channels"]} == {
                "wrist_bvp",
                "wrist_acc",
                "chest_ecg",
                "wrist_temp",
            }
            assert frame["cognitive"] is None
            assert frame["ai_confidence"] is None

            reset = client.post("/data-source/replay/reset")
            assert reset.status_code == 200
            assert reset.json()["replay_position_seconds"] == 0
            assert reset.json()["playback_state"] == "paused"

            assert client.get("/sensor-health").status_code == 409
            assert client.get("/simulation/state").status_code == 409
            assert client.get("/ai/explanation").status_code == 409
            digital_twin = client.get("/digital-twin")
            assert digital_twin.status_code == 409
            assert "synthetic-demo-only" in digital_twin.json()["detail"]
    finally:
        data_source_manager.use_synthetic()
        data_source_manager.configure_dataset_path(None)


def test_missing_dataset_path_is_a_controlled_error() -> None:
    data_source_manager.use_synthetic()
    data_source_manager.configure_dataset_path(None)
    with TestClient(app) as client:
        response = client.post("/data-source/replay/load", json={"subject_id": "S1"})
    assert response.status_code == 409
    assert "BIOMIN_PPG_DALIA_PATH" in response.json()["detail"]


def test_fault_control_and_websocket_expose_replay_provenance_and_reset(tmp_path: Path) -> None:
    _write_subject(tmp_path)
    data_source_manager.configure_dataset_path(tmp_path)
    data_source_manager.use_synthetic()

    try:
        with TestClient(app) as client:
            assert client.post("/data-source/replay/load", json={"subject_id": "S1"}).status_code == 200
            configured = client.post(
                "/data-source/replay/fault",
                json={
                    "fault_type": "modality_dropout",
                    "target": "ppg",
                    "severity": 1.0,
                    "seed": 42,
                },
            )
            assert configured.status_code == 200
            assert configured.json()["fault_injection"] == {
                "active": True,
                "fault_type": "modality_dropout",
                "target": "ppg",
                "target_channels": ["wrist_bvp"],
                "affected_channels": [],
                "severity": 1.0,
                "seed": 42,
                "dropped_samples": {},
                "parameters": {
                    "severity_semantics": "complete selected-modality removal; severity is not used"
                },
            }

            with client.websocket_connect("/ws/live-feed") as websocket:
                assert client.post("/data-source/replay/play").status_code == 200
                frame = websocket.receive_json()

            assert frame["fault_injection"]["active"] is True
            assert frame["fault_injection"]["affected_channels"] == ["wrist_bvp"]
            assert frame["fault_injection"]["dropped_samples"]["wrist_bvp"] > 0
            assert "wrist_bvp" not in frame["source"]["available_channels"]
            assert all(batch["channel_name"] != "wrist_bvp" for batch in frame["channels"])
            assert frame["heart_rate_prediction"] is None
            assert frame["heart_rate_inference"]["status"] == "input_unavailable"

            reset = client.post("/data-source/replay/reset")
            assert reset.status_code == 200
            assert reset.json()["fault_injection"]["active"] is False

            assert client.post("/data-source/synthetic").status_code == 200
            rejected = client.post(
                "/data-source/replay/fault",
                json={"fault_type": "packet_loss", "target": "both", "severity": 0.2, "seed": 1},
            )
            assert rejected.status_code == 409
    finally:
        data_source_manager.clear_replay_fault()
        data_source_manager.use_synthetic()
        data_source_manager.configure_dataset_path(None)


def test_manager_subject_and_source_switches_isolate_faulted_history(tmp_path: Path) -> None:
    _write_subject(tmp_path, subject_id="S1")
    _write_subject(tmp_path, subject_id="S2")
    manager = DataSourceManager(MockDataEngine(seed=12), tmp_path)

    manager.load_replay("S1")
    manager.configure_replay_fault(
        ReplayFaultConfig(
            fault_type=ReplayFaultType.FROZEN_SENSOR,
            target=ReplayFaultTarget.PPG,
        )
    )
    manager.play_replay()
    source = manager.replay_source
    frame = manager.tick(0.5, now=source._anchor_monotonic + 0.5)
    assert frame is not None
    assert frame.fault_injection is not None
    assert frame.fault_injection.active is True
    assert len(manager.history(10)) == 1

    switched_subject = manager.load_replay("S2")
    assert switched_subject.subject_id == "S2"
    assert switched_subject.fault_injection.active is False
    assert manager.latest_snapshot is None
    assert manager.history(10) == []

    manager.configure_replay_fault(
        ReplayFaultConfig(
            fault_type=ReplayFaultType.PACKET_LOSS,
            target=ReplayFaultTarget.BOTH,
            severity=0.25,
            seed=7,
        )
    )
    synthetic = manager.use_synthetic()
    assert synthetic.source_type.value == "synthetic"
    assert synthetic.fault_injection.active is False
    assert manager.history(10) == []


def test_websocket_emits_replay_prediction_and_clears_it_for_synthetic(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _write_subject(tmp_path, duration_seconds=12.0)
    service = ReplayHeartRateInferenceService(
        bridge_factory=lambda _: _WebSocketTestBridge(),
    )
    monkeypatch.setattr(data_source_manager, "_replay_inference", service)
    data_source_manager.configure_dataset_path(tmp_path)
    data_source_manager.use_synthetic()

    try:
        with TestClient(app) as client:
            loaded = client.post(
                "/data-source/replay/load",
                json={"subject_id": "S1", "channels": ["wrist_bvp", "wrist_acc"]},
            )
            assert loaded.status_code == 200
            assert client.post("/data-source/replay/speed", json={"speed": 10}).status_code == 200

            with client.websocket_connect("/ws/live-feed") as websocket:
                assert client.post("/data-source/replay/play").status_code == 200
                replay_frame = None
                for _ in range(4):
                    candidate = websocket.receive_json()
                    if candidate["heart_rate_inference"]["status"] == "available":
                        replay_frame = candidate
                        break

                assert replay_frame is not None
                prediction = replay_frame["heart_rate_prediction"]
                assert prediction["prediction_type"] == "heart_rate"
                assert prediction["evidence_level"] == "AI_ESTIMATED"
                assert prediction["uncertainty"] is None
                assert prediction["provenance"]["dataset_name"] == "PPG-DaLiA"
                assert prediction["provenance"]["subject_id"] == "S1"
                assert prediction["provenance"]["window_duration_seconds"] == 8.0
                assert replay_frame["vitals"]["heart_rate_bpm"] is None
                assert replay_frame["cognitive"] is None
                assert replay_frame["ai_confidence"] is None

                assert client.post("/data-source/synthetic").status_code == 200
                synthetic_frame = websocket.receive_json()
                assert synthetic_frame["source"]["source_type"] == "synthetic"
                assert synthetic_frame["heart_rate_prediction"] is None
                assert synthetic_frame["heart_rate_inference"] is None
                assert synthetic_frame["vitals"]["heart_rate_bpm"] is not None
    finally:
        data_source_manager.use_synthetic()
        data_source_manager.configure_dataset_path(None)
