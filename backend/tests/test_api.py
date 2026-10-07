"""Smoke tests for every REST endpoint plus the core simulation demos.

Run with `pytest` from `backend/`. These exercise the real FastAPI app
(no mocking) against the in-process mock data engine.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor

from fastapi.testclient import TestClient

from app.main import app
from app.engine.mock_data_engine import engine

client = TestClient(app)


def _prime_engine() -> None:
    if engine.last_snapshot is None:
        engine.tick(0.5)


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_metrics_live() -> None:
    _prime_engine()
    response = client.get("/metrics/live")
    assert response.status_code == 200
    body = response.json()
    assert "vitals" in body and "cognitive" in body and "ai_confidence" in body


def test_metrics_history() -> None:
    _prime_engine()
    response = client.get("/metrics/history?limit=5")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_digital_twin() -> None:
    for day in (1, 5, 12, 30):
        response = client.get(f"/digital-twin?day={day}")
        assert response.status_code == 200
        body = response.json()
        assert body["mission_day"] == day or abs(body["mission_day"] - day) < 1
        assert body["scientific_status"] == "ARCHITECTURE_ONLY_UNTRAINED_UNVALIDATED"
        assert "Conceptual architecture checkpoint" in body["milestone_label"]
        assert "No trained model" in body["narrative"]
        assert "systems" not in body
        assert "overall_adaptation" not in body
        assert "score" not in response.text.lower()
        assert "%" not in response.text


def test_sensor_health() -> None:
    response = client.get("/sensor-health")
    assert response.status_code == 200
    assert len(response.json()["sensors"]) == 4


def test_simulation_mode_switch() -> None:
    response = client.post("/simulation/mode", json={"mode": "solar_event"})
    assert response.status_code == 200
    assert response.json()["mission_mode"] == "solar_event"

    reset = client.post("/simulation/mode", json={"mode": "earth_orbit"})
    assert reset.json()["mission_mode"] == "earth_orbit"


def test_sensor_failure_lowers_confidence() -> None:
    client.post("/simulation/failure", json={"sensor": "ppg", "status": "nominal"})
    engine.tick(0.5)
    baseline = client.get("/metrics/live").json()["ai_confidence"]["overall_confidence"]

    response = client.post("/simulation/failure", json={"sensor": "ppg", "status": "offline"})
    assert response.status_code == 200
    engine.tick(0.5)
    degraded = client.get("/metrics/live").json()["ai_confidence"]["overall_confidence"]

    assert degraded < baseline

    # restore for other tests
    client.post("/simulation/failure", json={"sensor": "ppg", "status": "nominal"})


def test_ai_explanation_confidence() -> None:
    _prime_engine()
    response = client.get("/ai/explanation?target=ai_confidence")
    assert response.status_code == 200
    body = response.json()
    assert body["target"] == "ai_confidence"
    assert len(body["contributions"]) == 4
    assert isinstance(body["summary_text"], str) and len(body["summary_text"]) > 0


def test_ai_explanation_fatigue() -> None:
    _prime_engine()
    response = client.get("/ai/explanation?target=fatigue_risk")
    assert response.status_code == 200
    body = response.json()
    assert body["target"] == "fatigue_risk"
    assert len(body["contributions"]) == 5


def test_dashboard_explanation_pair_is_admitted_concurrently() -> None:
    """The two side-by-side panels must not reject one another with 429."""

    _prime_engine()
    with ThreadPoolExecutor(max_workers=2) as pool:
        responses = list(
            pool.map(
                lambda target: client.get(f"/ai/explanation?target={target}"),
                ["ai_confidence", "fatigue_risk"],
            )
        )
    assert [response.status_code for response in responses] == [200, 200]
