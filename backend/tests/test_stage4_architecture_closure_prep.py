"""Contract tests for the Stage-4 closure-prep sprint (architecture decision
framework ingestion, Gate D/E assessment, candidate burden comparison,
decision projection, final decision packet). These artifacts are real,
frozen, committed files - these tests confirm the API serves them faithfully
and that this sprint's own success criteria hold, not that any underlying
science is correct (that remains Science Owner's authority).

Failure modes under test: framework not wired; Science Owner tiers/severity
altered; Gate D forced READY; Gate E auto-resolved; final architecture or
formal Pareto silently marked resolved/ready; KEEP/REMOVE vocabulary
reintroduced; decision packet missing a required section.
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


# ---------------------------------------------------------------------------
# Framework ingestion (fa71eec) - Science Owner content served verbatim.
# ---------------------------------------------------------------------------


def test_confidence_tier_framework_has_6_tiers_and_is_unresolved():
    resp = client.get("/research/stage4-architecture-science-decision-framework")
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["confidence_tiers"]) == 6
    assert body["final_architecture_status"] == "UNRESOLVED"
    assert body["formal_pareto_status"] == "NOT_READY"


def test_sensor_decision_sensitivity_has_2_high_sensitivity_items():
    resp = client.get("/research/stage4-sensor-decision-sensitivity")
    assert resp.status_code == 200
    sensors = resp.json()["sensors"]
    assert len(sensors) == 8
    high = [s for s in sensors if s["decision_sensitivity"] == "HIGH"]
    assert {s["modality"] for s in high} == {"EOG (with EEG)", "sparse vs. full-montage EEG (ds003838-adjacent)"}


def test_scientific_pareto_inputs_defines_no_composite_score():
    resp = client.get("/research/stage4-scientific-pareto-inputs")
    assert resp.status_code == 200
    body = resp.json()
    assert "no arbitrary" in body["explicit_non_goal"].lower() or "composite" in body["explicit_non_goal"].lower()
    assert len(body["scientific_pareto_axes"]) == 8


def test_acceptance_gates_has_8_gates_with_severity_and_gate_d_is_hard_block():
    resp = client.get("/research/stage4-architecture-acceptance-gates")
    assert resp.status_code == 200
    gates = {g["gate_id"]: g for g in resp.json()["gates"]}
    assert len(gates) == 8
    assert gates["GATE_D_BURDEN_COMPLETENESS"]["severity"] == "HARD_BLOCK"
    assert gates["GATE_E_PENDING_SCIENCE_SENSITIVITY"]["severity"] == "COORDINATOR_DECISION_REQUIRED"


def test_candidate_classes_has_4_classes_and_no_selected_winner():
    resp = client.get("/research/stage4-architecture-candidate-classes")
    assert resp.status_code == 200
    body = resp.json()
    assert [c["class_id"] for c in body["classes"]] == [
        "MINIMAL_CORE",
        "CORE_PLUS_CONTEXT",
        "EVIDENCE_EXTENDED",
        "EXPERIMENTAL_EXTENDED",
    ]
    assert body["final_architecture_status"] == "UNRESOLVED"
    raw = resp.text
    assert '"selected": true' not in raw and '"winner"' not in raw


# ---------------------------------------------------------------------------
# Gate D - upgraded to CONDITIONALLY_READY (Gate D Burden Closure sprint):
# every material unknown is now bounded and ordering-robustness is computed,
# not assumed. Must never silently jump to unconditional READY, and the
# prior NOT_READY assessment must remain in history, never deleted.
# ---------------------------------------------------------------------------


def test_gate_d_is_conditionally_ready_with_all_unknowns_bounded():
    resp = client.get("/research/stage4-gate-d-burden-completeness")
    assert resp.status_code == 200
    body = resp.json()
    assert body["availability"] == "available"
    assessment = body["assessment"]
    assert assessment["gate_d_burden_completeness"] == "CONDITIONALLY_READY"
    decision_changing_unbounded = [
        u for u in assessment["known_unknowns"] if u["could_be_decision_changing"] and not u["bounded"]
    ]
    assert not decision_changing_unbounded, "CONDITIONALLY_READY requires every decision-changing unknown to be bounded"
    assert assessment["final_architecture_status"] == "UNRESOLVED"
    assert assessment["formal_pareto_status"] == "NOT_READY"


def test_gate_d_prior_not_ready_assessment_preserved_in_history():
    resp = client.get("/research/stage4-gate-d-burden-completeness")
    assessment = resp.json()["assessment"]
    assert len(assessment["assessment_history"]) >= 1
    assert assessment["assessment_history"][0]["gate_d_burden_completeness"] == "NOT_READY"
    assert assessment["chest_module_decomposition"] is not None
    assert assessment["eeg_eog_shared_afe_confirmation"]["status"] == "CONFIRMED_BY_STANDARD_ARCHITECTURE"


def test_gate_d_question_is_completeness_not_arithmetic():
    resp = client.get("/research/stage4-gate-d-burden-completeness")
    question = resp.json()["assessment"]["primary_question"]
    assert "arithmetic" in question.lower()
    assert "complete" in question.lower()


# ---------------------------------------------------------------------------
# Candidate burden comparison - no composite score, no confirmed dominance.
# ---------------------------------------------------------------------------


def test_candidate_burden_comparison_covers_all_4_classes_with_allowed_flags_only():
    resp = client.get("/research/stage4-candidate-class-burden-comparison")
    assert resp.status_code == 200
    body = resp.json()["comparison"]
    assert len(body["classes"]) == 4
    allowed = set(body["allowed_dominance_flags"])
    assert allowed == {"PARETO_RELEVANT", "POTENTIALLY_DOMINATED", "BURDEN_DATA_INCOMPLETE"}
    for c in body["classes"]:
        assert c["dominance_flag"] in allowed
        assert "total_score" not in c["power"] and "composite_score" not in c["power"]
    assert body["final_architecture_status"] == "UNRESOLVED"


def test_evidence_extended_and_experimental_extended_flagged_potentially_dominated():
    resp = client.get("/research/stage4-candidate-class-burden-comparison")
    by_id = {c["class_id"]: c for c in resp.json()["comparison"]["classes"]}
    assert by_id["EVIDENCE_EXTENDED"]["dominance_flag"] == "POTENTIALLY_DOMINATED"
    assert by_id["EXPERIMENTAL_EXTENDED"]["dominance_flag"] == "POTENTIALLY_DOMINATED"
    assert by_id["MINIMAL_CORE"]["dominance_flag"] != "POTENTIALLY_DOMINATED"


# ---------------------------------------------------------------------------
# Architecture decision projection - the single authoritative join.
# ---------------------------------------------------------------------------


def test_decision_projection_covers_all_8_decision_units():
    resp = client.get("/research/stage4-architecture-decision-projection")
    assert resp.status_code == 200
    body = resp.json()["projection"]
    assert len(body["units"]) == 8
    high_sensitivity_units = [u for u in body["units"] if u["decision_sensitivity"] == "HIGH"]
    for u in high_sensitivity_units:
        assert "GATE_E_COORDINATOR_DECISION_REQUIRED" in u["coordinator_decision_requirement"]


# ---------------------------------------------------------------------------
# Gate E - options prepared, nothing pre-selected.
# ---------------------------------------------------------------------------


def test_gate_e_prepares_exactly_3_options_per_high_sensitivity_item_with_none_selected():
    resp = client.get("/research/stage4-gate-e-coordinator-options")
    assert resp.status_code == 200
    body = resp.json()["options"]
    assert body["no_option_selected"] is True
    assert len(body["high_sensitivity_items"]) == 2
    for item in body["high_sensitivity_items"]:
        assert set(item["options"].keys()) == {
            "WAIT",
            "FREEZE_CONDITIONALLY",
            "FREEZE_DESPITE_UNCERTAINTY_WITH_DISCLOSURE",
        }


# ---------------------------------------------------------------------------
# Final decision packet - completeness + non-selection.
# ---------------------------------------------------------------------------


def test_final_decision_packet_has_all_required_sections():
    resp = client.get("/research/stage4-final-architecture-decision-packet")
    assert resp.status_code == 200
    packet = resp.json()["packet"]
    for key in (
        "candidate_configurations",
        "scientific_evidence_summary",
        "burden_evidence_summary",
        "uncertainties",
        "pending_science_sensitivity",
        "potential_dominance",
        "acceptance_gate_readiness",
        "decision_blockers",
        "coordinator_choices_required",
    ):
        assert key in packet and packet[key], f"missing or empty section: {key}"
    assert len(packet["acceptance_gate_readiness"]) == 8
    assert packet["final_architecture_status"] == "UNRESOLVED"
    assert packet["formal_pareto_status"] == "NOT_READY"
    assert any("final architecture selection" in c.lower() for c in packet["coordinator_choices_required"])


def test_final_decision_packet_gate_d_reflects_conditionally_ready():
    resp = client.get("/research/stage4-final-architecture-decision-packet")
    packet = resp.json()["packet"]
    gates = {g["gate_id"]: g for g in packet["acceptance_gate_readiness"]}
    assert gates["GATE_D_BURDEN_COMPLETENESS"]["current_readiness"].startswith("CONDITIONALLY_READY")
    assert packet["contact_electrode_burden"] is not None
    assert packet["battery_topology_scenarios"] is not None
    assert len(packet["candidate_burden_matrix"]) == 4
    assert packet["robustness_analysis"]["power_ordering_preserved_across_mcu_radio_interpretations"] is True
