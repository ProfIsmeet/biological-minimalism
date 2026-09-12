"""Contract tests for the Stage-4 Final Architecture Closure sprint's new
artifacts (Gate E coordinator decisions, formal Pareto analysis, final
wearable architecture, final closure manifest), served live via the
`/research/*` API. Covers: final architecture exact class; final
modalities; excluded modalities; Gate D conditional closure; both Gate E
conditional freezes; revision triggers; formal Pareto result; pending
science; Digital Twin separation; cross-layer consistency.
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_final_wearable_architecture_selected_class_is_core_plus_context():
    resp = client.get("/research/final-wearable-architecture")
    assert resp.status_code == 200
    body = resp.json()
    assert body["availability"] == "available"
    architecture = body["architecture"]
    assert architecture["selected_class"] == "CORE_PLUS_CONTEXT"
    assert architecture["final_architecture_status"] == "CORE_PLUS_CONTEXT"


def test_final_architecture_modalities_match_science_owner_candidate_class():
    final_resp = client.get("/research/final-wearable-architecture").json()["architecture"]
    candidate_resp = client.get("/research/stage4-architecture-candidate-classes").json()
    science_class = next(c for c in candidate_resp["classes"] if c["class_id"] == "CORE_PLUS_CONTEXT")
    assert final_resp["selected_modalities"] == science_class["sensors"]


def test_final_architecture_excludes_four_modalities_with_rationale():
    architecture = client.get("/research/final-wearable-architecture").json()["architecture"]
    exclusions = architecture["exclusion_rationale"]
    for key in ("thoracic_bioz_eis", "leg_bioz", "second_site_ppg", "wrist_temperature_light"):
        assert key in exclusions
        assert exclusions[key]["excluded_from_final_architecture"] is True
        assert exclusions[key]["reason"]
        assert exclusions[key]["prohibited_claim"]


def test_gate_d_conditionally_closed_not_silently_ready():
    resp = client.get("/research/stage4-gate-d-burden-completeness")
    assessment = resp.json()["assessment"]
    assert assessment["gate_d_burden_completeness"] == "CONDITIONALLY_READY"
    assert assessment["schema_version"] == "3.0.0"
    acceptance = assessment["coordinator_acceptance"]
    assert acceptance["status"] == "CLOSED_FOR_STAGE4_BY_COORDINATOR_ACCEPTANCE_OF_BOUNDED_ENGINEERING_UNCERTAINTY"
    assert acceptance["state_transition"] == ["NOT_READY", "CONDITIONALLY_READY", "COORDINATOR_ACCEPTED_BOUNDED_UNCERTAINTY"]
    # append-only history still starts from the original NOT_READY v1.0.0 record
    assert assessment["assessment_history"][0]["gate_d_burden_completeness"] == "NOT_READY"
    assert assessment["assessment_history"][0]["schema_version"] == "1.0.0"


def test_gate_e_both_items_frozen_conditionally_with_revision_triggers():
    resp = client.get("/research/stage4-gate-e-coordinator-decisions")
    assert resp.status_code == 200
    body = resp.json()
    assert body["availability"] == "available"
    decisions = body["decisions"]
    assert decisions["no_option_selected"] is False
    assert decisions["gate_e_pending_science_sensitivity"] == "CLOSED_BY_COORDINATOR_DECISION"
    assert len(decisions["decisions"]) == 2
    for d in decisions["decisions"]:
        assert d["decision"] == "FREEZE_CONDITIONALLY"
        assert d["revision_trigger"]


def test_formal_pareto_result_no_score_no_false_unique_winner():
    resp = client.get("/research/stage4-formal-pareto-analysis")
    assert resp.status_code == 200
    analysis = resp.json()["analysis"]
    assert analysis["formal_pareto_status"] == "COMPLETE"
    assert analysis["no_unique_pareto_winner"] is True
    assert set(analysis["pareto_relevant_set"]) == {"MINIMAL_CORE", "CORE_PLUS_CONTEXT"}
    assert set(analysis["potentially_dominated_set"]) == {"EVIDENCE_EXTENDED", "EXPERIMENTAL_EXTENDED"}
    assert analysis["coordinator_selected_architecture"] == "CORE_PLUS_CONTEXT"
    # methodology explicitly disclaims computing a collapsed composite score
    # (the negated statement itself is expected and correct - it is the
    # per-class analysis entries, not the methodology prose, that must never
    # carry an actual numeric score field)
    assert "does not compute" in analysis["methodology"]["explicit_non_goal"].lower()
    for entry in analysis["pairwise_dominance_analysis"]:
        assert "score" not in entry or entry.get("score") is None


def test_pending_science_hmc_and_ds003838_not_marked_complete():
    manifest = client.get("/research/stage4-final-closure-manifest").json()["manifest"]
    pending = manifest["pending_science"]
    assert "PENDING" in pending["hmc_full_cohort"]
    assert "PENDING" in pending["ds003838_full_cohort"]
    assert "COMPLETE" not in pending["hmc_full_cohort"].replace("INCOMPLETE", "")
    assert "COMPLETE" not in pending["ds003838_full_cohort"].replace("INCOMPLETE", "")


def test_digital_twin_separation_untouched_by_closure():
    manifest = client.get("/research/stage4-final-closure-manifest").json()["manifest"]
    digital_twin_note = manifest["pending_science"]["digital_twin"]
    assert "UNTRAINED" in digital_twin_note or "UNVALIDATED" in digital_twin_note
    gate_h = next(g for g in manifest["acceptance_gates"] if g["gate_id"] == "GATE_H_DIGITAL_TWIN_SEPARATION")
    assert gate_h["final_state"].startswith("PASS")


def test_closure_manifest_final_architecture_matches_every_surface():
    manifest = client.get("/research/stage4-final-closure-manifest").json()["manifest"]
    final_arch = client.get("/research/final-wearable-architecture").json()["architecture"]
    pareto = client.get("/research/stage4-formal-pareto-analysis").json()["analysis"]
    assert manifest["final_architecture"] == final_arch["selected_class"] == pareto["coordinator_selected_architecture"] == "CORE_PLUS_CONTEXT"
    assert manifest["formal_pareto_status"] == pareto["formal_pareto_status"] == "COMPLETE"
    assert len(manifest["acceptance_gates"]) == 8
    assert len(manifest["authoritative_artifacts"]) >= 15
    for artifact in manifest["authoritative_artifacts"]:
        assert len(artifact["sha256"]) == 64


def test_stage4_final_architecture_and_formal_pareto_no_longer_unresolved_in_closure_surfaces():
    """Inverse of test_final_architecture_and_formal_pareto_remain_unresolved_everywhere
    (backend/tests/test_stage4_gate_d_burden_closure.py) - THIS is the intentional
    change: the 3 NEW closure surfaces (not the pre-closure inputs) now carry the
    resolved decision."""
    for path, key in (
        ("/research/final-wearable-architecture", "architecture"),
        ("/research/stage4-formal-pareto-analysis", "analysis"),
    ):
        body = client.get(path).json()[key]
        assert body["final_architecture_status"] == "CORE_PLUS_CONTEXT"
        assert body["formal_pareto_status"] == "COMPLETE"


def test_pre_closure_inputs_remain_unresolved_unchanged_by_this_sprint():
    """The pre-closure inputs (Gate D burden completeness's own scope,
    candidate burden matrix, battery topology scenarios) must still say
    UNRESOLVED/NOT_READY - only the NEW closure artifacts resolve."""
    for path in (
        "/research/stage4-gate-d-burden-completeness",
        "/research/stage4-battery-topology-scenarios",
        "/research/stage4-candidate-burden-matrix",
    ):
        resp = client.get(path)
        body = resp.json()
        payload = body.get("assessment") or body.get("scenarios") or body.get("matrix")
        assert payload["final_architecture_status"] == "UNRESOLVED", path
        assert payload["formal_pareto_status"] == "NOT_READY", path
