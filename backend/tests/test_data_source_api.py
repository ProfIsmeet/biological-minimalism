"""Integration checks for replay REST controls and the existing WebSocket."""

from __future__ import annotations

import pickle
from pathlib import Path

import numpy as np
from fastapi.testclient import TestClient

from app.engine.data_sources import data_source_manager
from app.main import app


def _write_subject(root: Path) -> None:
    subject_dir = root / "PPG_FieldStudy" / "S1"
    subject_dir.mkdir(parents=True)

    def scalar(rate: float) -> np.ndarray:
        return np.arange(int(2.0 * rate), dtype=np.float64).reshape(-1, 1)

    raw = {
        "subject": "S1",
        "signal": {
            "wrist": {
                "BVP": scalar(64.0),
                "ACC": np.column_stack((scalar(32.0), scalar(32.0), scalar(32.0))),
                "TEMP": scalar(4.0),
            },
            "chest": {"ECG": scalar(700.0)},
        },
    }
    with (subject_dir / "S1.pkl").open("wb") as stream:
        pickle.dump(raw, stream, protocol=pickle.HIGHEST_PROTOCOL)


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
