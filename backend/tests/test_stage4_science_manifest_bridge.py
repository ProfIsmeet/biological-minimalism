"""Tests for the Ismet Stage-4 science handoff package bridge (governing
prompt Part XI). This package is AUTHORITATIVE: these tests confirm the
API serves it verbatim and stays in sync with the live resolver, not that
its content is scientifically correct (that is Science Owner's job)."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_science_manifest_has_10_allowlisted_families():
    resp = client.get("/research/stage4-science-manifest")
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["families"]) == 10
    assert body["final_architecture_status"] == "UNRESOLVED"


def test_science_manifest_agrees_with_live_resolver_for_every_family():
    import ml.stage3_science_resolver as resolver

    resp = client.get("/research/stage4-science-manifest")
    for family in resp.json()["families"]:
        assert resolver.resolve_governing_path(family["family_id"]) == family["governing_artifact"]


def test_sensor_value_matrix_has_11_modalities_and_no_keep_remove_vocabulary():
    resp = client.get("/research/stage4-sensor-value-matrix")
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["modalities"]) == 11
    for m in body["modalities"]:
        assert m["architecture_implication"] not in {"KEEP", "REMOVE"}


def test_claim_ledger_lbnp_and_qde_negative_evidence_stays_visible():
    resp = client.get("/research/stage4-science-claims")
    all_governing_evidence = {
        family_id for c in resp.json()["claims"] for family_id in c["governing_evidence"]
    }
    assert "lbnp_thoracic_eis" in all_governing_evidence
    assert "qde_v2_leg_bioz" in all_governing_evidence


def test_architecture_decision_inputs_never_select_a_final_architecture():
    resp = client.get("/research/stage4-architecture-decision-inputs-science")
    body = resp.json()
    assert body["final_architecture_status"] == "UNRESOLVED"
    assert body["formal_pareto_status"] == "NOT_READY"


def test_drift_between_frozen_manifest_and_live_resolver_fails_closed(monkeypatch):
    from app.research import stage4_science_manifest as bridge

    original = bridge.resolve_governing_path
    monkeypatch.setattr(bridge, "resolve_governing_path", lambda family_id: "results/some_other_file.json")
    try:
        import pytest

        with pytest.raises(bridge.Stage4ScienceManifestDrift):
            bridge.get_science_consumption_manifest()
    finally:
        monkeypatch.setattr(bridge, "resolve_governing_path", original)
