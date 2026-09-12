"""Contract tests for the Stage-4 Gate D Burden Closure sprint (bounded
contact/electrode topology, battery/MCU-radio topology scenarios,
configuration-level burden matrix, and the resulting Gate D reassessment).
These artifacts are real, frozen, committed files - these tests confirm
the API serves them faithfully and that this sprint's own success
criteria hold, not that any underlying engineering judgment call is
optimal (that remains open for Coordinator/engineering review).

Failure modes under test: shared electrodes double-counted; an unbounded
decision-changing unknown coexisting with READY/CONDITIONALLY_READY;
candidate ordering not actually robustness-tested; Gate D history
silently deleted; final architecture or formal Pareto quietly resolved.
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


# ---------------------------------------------------------------------------
# Contact/electrode topology - bounded, never unbounded UNKNOWN, no
# double-counted shared electrodes.
# ---------------------------------------------------------------------------


def test_contact_electrode_burden_covers_7_modalities_with_bounded_ranges():
    resp = client.get("/research/stage4-contact-electrode-burden")
    assert resp.status_code == 200
    body = resp.json()
    assert body["availability"] == "available"
    modalities = body["burden"]["modalities"]
    assert len(modalities) == 7
    for m in modalities:
        tc = m["total_contacts"]
        assert tc["min"] <= tc["most_likely"] <= tc["max"], f"{m['modality']}: min/most_likely/max out of order"
        assert m["confidence"] != "", f"{m['modality']}: missing confidence basis"


def test_eog_does_not_double_count_frontal_eeg_reference_or_ground():
    resp = client.get("/research/stage4-contact-electrode-burden")
    modalities = {m["modality"]: m for m in resp.json()["burden"]["modalities"]}
    eog = modalities["eog"]
    frontal_eeg = modalities["frontal_eeg"]
    # EOG's own reference/ground counts must be zero (shared from EEG, not additive).
    assert eog["reference_electrodes"].get("count") == 0
    assert eog["ground_bias_electrodes"].get("count") == 0
    assert any("frontal_eeg" in s for s in eog["shared_with"])
    # Frontal EEG's own total must not already include EOG's incremental electrodes.
    assert frontal_eeg["total_contacts"]["most_likely"] < frontal_eeg["total_contacts"]["most_likely"] + eog["total_contacts"]["most_likely"]


def test_ecg_and_thoracic_bioz_do_not_credit_unvalidated_sharing():
    resp = client.get("/research/stage4-contact-electrode-burden")
    modalities = {m["modality"]: m for m in resp.json()["burden"]["modalities"]}
    thoracic = modalities["thoracic_bioz"]
    # Explicitly no sharing credited - incremental == total (full count charged).
    assert thoracic["shared_with"] == []
    assert thoracic["incremental_contacts_if_added"]["most_likely"] == thoracic["total_contacts"]["most_likely"]


def test_leg_bioz_surfaces_bilateral_topology_question():
    resp = client.get("/research/stage4-contact-electrode-burden")
    modalities = {m["modality"]: m for m in resp.json()["burden"]["modalities"]}
    leg = modalities["leg_bioz"]
    assert leg["unresolved_topology_question"] is not None
    assert leg["total_contacts"]["max"] == 8
    assert leg["total_contacts"]["min"] == 4


# ---------------------------------------------------------------------------
# Battery/electronics topology scenarios - both modeled, no selection made.
# ---------------------------------------------------------------------------


def test_battery_topology_models_both_scenarios_without_selecting_one():
    resp = client.get("/research/stage4-battery-topology-scenarios")
    assert resp.status_code == 200
    body = resp.json()["scenarios"]
    assert set(body["scenarios"].keys()) == {"SHARED_HUB", "DISTRIBUTED_PER_MODULE"}
    assert body["not_a_final_battery_selection"] is True
    assert body["operating_duration_requirement_status"]["status"] == "ABSENT"


def test_battery_cell_mass_is_scenario_neutral_per_class():
    resp = client.get("/research/stage4-battery-topology-scenarios")
    for row in resp.json()["scenarios"]["candidate_class_comparison"]:
        assert row["battery_mass_delta_g"] == 0.0
        assert row["shared_hub_total_battery_g"] == row["distributed_per_module_total_battery_g"]


# ---------------------------------------------------------------------------
# Candidate burden matrix - robustness computed, not asserted; ordering
# preserved across every tested bound/topology.
# ---------------------------------------------------------------------------


def test_candidate_burden_matrix_covers_4_classes_with_computed_robustness():
    resp = client.get("/research/stage4-candidate-burden-matrix")
    assert resp.status_code == 200
    body = resp.json()["matrix"]
    assert len(body["classes"]) == 4
    assert body["robustness_analysis"]["power_ordering_preserved_across_mcu_radio_interpretations"] is True


def test_evidence_extended_power_range_reflects_mcu_radio_topology_ambiguity():
    resp = client.get("/research/stage4-candidate-burden-matrix")
    by_id = {c["class_id"]: c for c in resp.json()["matrix"]["classes"]}
    evidence_extended = by_id["EVIDENCE_EXTENDED"]
    single = evidence_extended["power_range_mw"]["single_shared_mcu_radio"]["battery_side"]
    per_module = evidence_extended["power_range_mw"]["per_module_mcu_radio"]["battery_side"]
    assert per_module > single, "per-module MCU/radio interpretation must cost more than single-shared for a 4-module class"


def test_candidate_burden_matrix_total_contacts_monotonically_nondecreasing():
    resp = client.get("/research/stage4-candidate-burden-matrix")
    classes = resp.json()["matrix"]["classes"]
    order = ["MINIMAL_CORE", "CORE_PLUS_CONTEXT", "EVIDENCE_EXTENDED", "EXPERIMENTAL_EXTENDED"]
    by_id = {c["class_id"]: c for c in classes}
    most_likely = [by_id[cid]["total_contacts"]["most_likely"] for cid in order]
    assert most_likely == sorted(most_likely), "each candidate class must never have fewer contacts than the prior one"


# ---------------------------------------------------------------------------
# Gate D reassessment - upgraded verdict, history preserved, invariant holds.
# ---------------------------------------------------------------------------


def test_gate_d_no_decision_changing_unknown_remains_unbounded():
    resp = client.get("/research/stage4-gate-d-burden-completeness")
    assessment = resp.json()["assessment"]
    assert assessment["gate_d_burden_completeness"] in ("READY", "CONDITIONALLY_READY")
    violations = [
        u for u in assessment["known_unknowns"] if u["could_be_decision_changing"] and not u["bounded"]
    ]
    assert violations == [], f"decision-changing unbounded unknowns present while gate is {assessment['gate_d_burden_completeness']}: {violations}"


def test_gate_d_history_is_append_only_and_starts_not_ready():
    resp = client.get("/research/stage4-gate-d-burden-completeness")
    assessment = resp.json()["assessment"]
    history = assessment["assessment_history"]
    assert len(history) >= 1
    assert history[0]["gate_d_burden_completeness"] == "NOT_READY"
    assert history[0]["schema_version"] == "1.0.0"
    # The live record must be a genuinely later version than history[0].
    assert assessment["schema_version"] != history[0]["schema_version"]


def test_gate_d_new_findings_are_disclosed_not_hidden():
    resp = client.get("/research/stage4-gate-d-burden-completeness")
    assessment = resp.json()["assessment"]
    items = {u["item"] for u in assessment["known_unknowns"]}
    assert any("MCU/radio" in item for item in items)
    assert any("bilateral" in item.lower() for item in items)


def test_final_architecture_and_formal_pareto_remain_unresolved_everywhere():
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
