"""Cross-layer consistency tests for the Stage-3 evidence bridge (Stage 4
controlled integration, governing prompt Part IV/XII §24-26/§45-46).

These are behavioral invariants, not exhaustive per-field checks: the API
layer must agree with the resolver, must never expose historical/invalidated
content as governing, must fail closed on a corrupted registry, and must
never route through the private unverified resolver helper.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.research import stage3_evidence

# Import AFTER app.research.stage3_evidence: that module's import inserts
# REPOSITORY_ROOT onto sys.path as a side effect, which `ml.*` needs to be
# importable at all when this file is run in isolation (not just as part
# of the full suite, where an earlier-collected module may have already
# done so).
import ml.stage3_science_resolver as resolver  # noqa: E402

client = TestClient(app)


def test_stage3_evidence_envelope_has_all_21_families():
    resp = client.get("/research/stage3-evidence")
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["entries"]) == 21
    assert {e["family_id"] for e in body["entries"]} == set(resolver.list_families())


def test_architecture_and_pareto_remain_unresolved():
    resp = client.get("/research/stage3-evidence")
    body = resp.json()
    assert body["final_architecture_status"] == "UNRESOLVED"
    assert body["formal_pareto_status"] == "FORMAL_PARETO_NOT_READY"


def test_lbnp_current_matches_v2_not_historical_607_window():
    resp = client.get("/research/stage3-evidence/lbnp_thoracic_eis")
    assert resp.status_code == 200
    entry = resp.json()
    assert entry["artifact_path"] == "results/lbnp_thoracic_eis_stage3_v2_protocol_compliant.json"
    assert entry["classification"] == "COMPLETE_MIXED"
    assert entry["biological_subject_n"] == 12


def test_galaxyppg_current_matches_resolver_not_invalidated():
    resp = client.get("/research/stage3-evidence/galaxyppg_external_replication")
    entry = resp.json()
    assert entry["artifact_path"] == resolver.resolve_governing_path("galaxyppg_external_replication")
    assert entry["classification"] == "EXTERNAL_REPLICATION_SUPPORTIVE"
    assert entry["biological_subject_n"] == 18


def test_api_agrees_with_resolver_for_every_family():
    resp = client.get("/research/stage3-evidence")
    for entry in resp.json()["entries"]:
        expected_path = resolver.resolve_governing_path(entry["family_id"])
        assert entry["artifact_path"] == expected_path


def test_relabeled_historical_lbnp_fails_closed_through_the_api(monkeypatch, tmp_path):
    """Reproduces the Gate-3 hostile attack at the API boundary: flip the
    registry so the historical, out-of-protocol LBNP result is the sole
    GOVERNING entry. The bridge must fail closed, never serve it."""
    import json

    registry = json.loads(resolver.REGISTRY_PATH.read_text())
    for artifact in registry["families"]["lbnp_thoracic_eis"]["artifacts"]:
        if artifact["path"] == "results/lbnp_thoracic_eis_stage3_v2_protocol_compliant.json":
            artifact["status"] = "HISTORICAL"
        if artifact["path"] == "results/lbnp_thoracic_eis_stage3.json":
            artifact["status"] = "GOVERNING"

    corrupted = tmp_path / "corrupted_registry.json"
    corrupted.write_text(json.dumps(registry))
    monkeypatch.setattr(resolver, "REGISTRY_PATH", corrupted)

    with pytest.raises(stage3_evidence.Stage3EvidenceUnavailable):
        stage3_evidence.get_stage3_evidence_entry("lbnp_thoracic_eis")


def test_bridge_never_imports_the_private_unverified_helper():
    import inspect

    source = inspect.getsource(stage3_evidence)
    assert "_resolve_current_unverified" not in source
    assert "resolve_current" in source


def test_stage3_and_stage4_architecture_status_agree_and_stay_unresolved():
    """One scientific truth (governing prompt §45): Stage-3's own architecture
    evidence handoff and Stage-4's independently-built engineering-readiness
    artifact must never disagree, and neither may silently promote to a
    decided architecture."""
    stage3_status = client.get("/research/stage3-evidence").json()["final_architecture_status"]
    stage4_status = client.get("/research/stage4-engineering-readiness").json()["readiness"][
        "final_architecture_status"
    ]
    assert stage3_status == "UNRESOLVED"
    assert stage4_status == "UNRESOLVED"
    assert stage3_status == stage4_status
