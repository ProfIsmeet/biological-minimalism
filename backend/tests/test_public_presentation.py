"""Production-only public presentation safety contracts."""

from __future__ import annotations

import hashlib
import io
import pickle
import urllib.request
from pathlib import Path

import numpy as np
import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from app.core.config import settings
from app.data.ppg_dalia import load_subject_payload
from app.engine.data_sources import DataSourceManager
from app.engine.mock_data_engine import MockDataEngine
from app.main import _SafeAssetRedirectHandler, _provision_asset, app
from scripts import build_public_s14_bundle


class _FakeOpener:
    def __init__(self, payload: bytes) -> None:
        self.payload = payload
        self.request: urllib.request.Request | None = None

    def open(self, request: urllib.request.Request, timeout: int):  # noqa: ARG002
        self.request = request
        return io.BytesIO(self.payload)


def _write_subject(root: Path, duration_seconds: float = 0.02) -> None:
    subject_dir = root / "PPG_FieldStudy" / "S14"
    subject_dir.mkdir(parents=True)

    def scalar(rate: float) -> np.ndarray:
        return np.arange(max(1, int(duration_seconds * rate)), dtype=np.float64).reshape(-1, 1)

    raw = {
        "subject": "S14",
        "signal": {
            "wrist": {
                "BVP": scalar(64.0),
                "ACC": np.column_stack((scalar(32.0), scalar(32.0), scalar(32.0))),
                "TEMP": scalar(4.0),
            },
            "chest": {"ECG": scalar(700.0)},
        },
    }
    with (subject_dir / "S14.pkl").open("wb") as stream:
        pickle.dump(raw, stream, protocol=pickle.HIGHEST_PROTOCOL)


def test_public_mode_blocks_every_http_mutation(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "public_presentation_mode", True)
    client = TestClient(app)
    for method, path in (
        ("post", "/data-source/synthetic"),
        ("post", "/data-source/replay/play"),
        ("delete", "/data-source/replay/fault"),
        ("post", "/simulation/mode"),
        ("post", "/simulation/failure"),
    ):
        response = getattr(client, method)(path, headers={"Origin": settings.allowed_origins[0]})
        assert response.status_code == 403
        assert response.json() == {"detail": "Public presentation is read-only."}
        assert response.headers["access-control-allow-origin"] == settings.allowed_origins[0]


def test_public_websocket_rejects_unapproved_origin(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "public_presentation_mode", True)
    client = TestClient(app)
    with pytest.raises(WebSocketDisconnect) as rejected:
        with client.websocket_connect(
            "/ws/live-feed", headers={"origin": "https://unapproved.example"}
        ):
            pass
    assert rejected.value.code == 1008


def test_public_http_rejects_unapproved_origin(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "public_presentation_mode", True)
    response = TestClient(app).get("/health", headers={"Origin": "https://unapproved.example"})
    assert response.status_code == 403
    assert response.json() == {"detail": "Origin not allowed."}
    assert "access-control-allow-origin" not in response.headers


def test_public_replay_restarts_after_end(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _write_subject(tmp_path)
    subject = DataSourceManager(MockDataEngine(seed=4), tmp_path)
    subject.load_replay("S14")
    subject.set_replay_speed(10)
    subject.play_replay()
    monkeypatch.setattr(settings, "public_presentation_mode", True)
    monkeypatch.setattr(settings, "presentation_loop_replay", True)

    subject.tick(0.5, now=10**12)
    assert subject.status().playback_state.value == "ended"
    subject.tick(0.5)
    status = subject.status()
    assert status.playback_state.value == "playing"
    assert status.replay_position_seconds < status.duration_seconds


def test_local_mode_remains_mutable(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "public_presentation_mode", False)
    response = TestClient(app).post("/data-source/synthetic")
    assert response.status_code == 200
    assert response.json()["public_read_only"] is False


def test_asset_provisioning_is_https_hash_pinned_and_atomic(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    payload = b"licensed-test-asset"
    expected_hash = hashlib.sha256(payload).hexdigest()
    opener = _FakeOpener(payload)
    monkeypatch.setattr("app.main.urllib.request.build_opener", lambda *_handlers: opener)
    monkeypatch.setattr(settings, "presentation_asset_bearer_token", "private-test-token")
    destination = tmp_path / "asset.zip"

    _provision_asset(
        destination,
        "https://assets.example/asset.zip",
        expected_hash,
        max_bytes=1024,
    )

    assert destination.read_bytes() == payload
    assert not destination.with_suffix(".zip.partial").exists()
    assert opener.request is not None
    assert opener.request.get_header("Accept") == "application/octet-stream"
    assert opener.request.get_header("Authorization") == "Bearer private-test-token"


def test_asset_provisioning_rejects_bad_hash_and_plain_http(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(
        "app.main.urllib.request.build_opener",
        lambda *_handlers: _FakeOpener(b"wrong"),
    )
    destination = tmp_path / "asset.zip"
    with pytest.raises(RuntimeError, match="HTTPS"):
        _provision_asset(destination, "http://assets.example/asset.zip", "0" * 64, max_bytes=1024)
    with pytest.raises(RuntimeError, match="identity"):
        _provision_asset(destination, "https://assets.example/asset.zip", "0" * 64, max_bytes=1024)
    assert not destination.exists()


def test_asset_redirect_never_forwards_bearer_token_cross_host() -> None:
    handler = _SafeAssetRedirectHandler()
    request = urllib.request.Request(
        "https://api.github.com/repos/example/private/releases/assets/1",
        headers={"Authorization": "Bearer should-not-leak"},
    )
    redirected = handler.redirect_request(
        request,
        None,
        302,
        "Found",
        {},
        "https://objects.githubusercontent.com/signed-download",
    )
    assert redirected is not None
    assert redirected.get_header("Authorization") is None


def test_reduced_s14_bundle_preserves_selected_arrays_exactly(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _write_subject(tmp_path, duration_seconds=1.0)
    source = tmp_path / "PPG_FieldStudy" / "S14" / "S14.pkl"
    monkeypatch.setattr(build_public_s14_bundle, "SOURCE_SHA256", hashlib.sha256(source.read_bytes()).hexdigest())
    output = tmp_path / "S14-public.zip"

    manifest = build_public_s14_bundle.build_bundle(source, output)
    original = pickle.loads(source.read_bytes())
    reduced = load_subject_payload(output, "S14")

    for path in build_public_s14_bundle.SELECTED_CHANNELS.values():
        expected = original[path[0]][path[1]][path[2]]
        actual = reduced[path[0]][path[1]][path[2]]
        assert np.array_equal(actual, expected)
        assert actual.dtype == expected.dtype
    assert manifest["bundle_sha256"] == hashlib.sha256(output.read_bytes()).hexdigest()


def test_pickle_free_s14_bundle_preserves_selected_arrays_exactly(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _write_subject(tmp_path, duration_seconds=1.0)
    source = tmp_path / "PPG_FieldStudy" / "S14" / "S14.pkl"
    monkeypatch.setattr(build_public_s14_bundle, "SOURCE_SHA256", hashlib.sha256(source.read_bytes()).hexdigest())
    output = tmp_path / "S14-public.npz"

    manifest = build_public_s14_bundle.build_bundle(source, output)
    original = pickle.loads(source.read_bytes())
    reduced = load_subject_payload(output, "S14")

    for path in build_public_s14_bundle.SELECTED_CHANNELS.values():
        expected = original[path[0]][path[1]][path[2]]
        actual = reduced[path[0]][path[1]][path[2]]
        assert np.array_equal(actual, expected)
        assert actual.dtype == expected.dtype
    assert manifest["bundle_sha256"] == hashlib.sha256(output.read_bytes()).hexdigest()
