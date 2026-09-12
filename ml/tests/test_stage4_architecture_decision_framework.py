"""Contract tests for the second Stage-4 Science Owner package: the
architecture decision framework, sensor decision sensitivity, scientific
Pareto inputs, acceptance gates, and candidate classes. Also re-runs the
extended claim-consistency validator and a final science non-regression
check via the resolver."""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

import ml.stage3_science_resolver as resolver  # noqa: E402
from ml.validate_stage4_science_claim_consistency import main as run_validator  # noqa: E402


def _load(rel):
    return json.loads((REPO_ROOT / rel).read_text())


def test_extended_validator_passes():
    run_validator()


def test_confidence_framework_defines_six_tiers():
    d = _load("results/stage4_architecture_science_decision_framework.json")
    tiers = d["confidence_tiers"]
    required = {
        "TIER_A_REPLICATED_SUPPORT", "TIER_B_CONTROLLED_SUPPORT", "TIER_C_BOUNDED_SUPPORT",
        "TIER_D_MIXED_OR_FRAGILE", "TIER_E_NEGATIVE_OR_DEPRIORITIZED", "TIER_P_PENDING",
    }
    assert required.issubset(tiers.keys())
    for tier, spec in tiers.items():
        assert "mechanical_definition" in spec
    assert d["final_architecture_status"] == "UNRESOLVED"
    assert d["formal_pareto_status"] == "NOT_READY"


def test_sensor_decision_sensitivity_covers_high_sensitivity_items():
    d = _load("results/stage4_sensor_decision_sensitivity.json")
    by_modality = {s["modality"]: s for s in d["sensors"]}
    assert by_modality["EOG (with EEG)"]["decision_sensitivity"] == "HIGH"
    assert "decision_flip_scenarios" in by_modality["EOG (with EEG)"]
    assert by_modality["sparse vs. full-montage EEG (ds003838-adjacent)"]["decision_sensitivity"] == "HIGH"
    assert by_modality["wrist PPG + wrist IMU"]["decision_sensitivity"] == "LOW"


def test_all_sensitivity_ratings_are_valid_enum():
    d = _load("results/stage4_sensor_decision_sensitivity.json")
    for s in d["sensors"]:
        assert s["decision_sensitivity"] in {"HIGH", "MEDIUM", "LOW"}


def test_pareto_inputs_never_compute_arbitrary_composite_score():
    d = _load("results/stage4_scientific_pareto_inputs.json")
    assert "TOTAL_SCORE" not in d  # not an actual computed field
    assert "explicit_non_goal" in d  # the prohibition is documented, not silently absent
    assert d["final_architecture_status"] == "UNRESOLVED"
    assert d["formal_pareto_status"] == "NOT_READY"


def test_pareto_inputs_define_required_axes():
    d = _load("results/stage4_scientific_pareto_inputs.json")
    axes = d["scientific_pareto_axes"]
    required = {"incremental_value", "breadth", "evidence_maturity", "robustness", "uniqueness", "dependency", "decision_fragility", "mission_relevance"}
    assert required.issubset(axes.keys())


def test_acceptance_gates_cover_required_gates_with_valid_severity():
    d = _load("results/stage4_architecture_acceptance_gates.json")
    gate_ids = {g["gate_id"] for g in d["gates"]}
    required = {
        "GATE_A_SCIENTIFIC_PROVENANCE", "GATE_B_EXCLUDED_SENSOR_RATIONALE", "GATE_C_EVIDENCE_STATUS_HONESTY",
        "GATE_D_BURDEN_COMPLETENESS", "GATE_E_PENDING_SCIENCE_SENSITIVITY", "GATE_F_NEGATIVE_RESULT_PRESERVATION",
        "GATE_G_CLAIM_CONSISTENCY", "GATE_H_DIGITAL_TWIN_SEPARATION",
    }
    assert required.issubset(gate_ids)
    for g in d["gates"]:
        assert g["severity"] in d["severity_enum"]


def test_gate_e_is_coordinator_decision_required_not_hard_block():
    d = _load("results/stage4_architecture_acceptance_gates.json")
    gate_e = next(g for g in d["gates"] if g["gate_id"] == "GATE_E_PENDING_SCIENCE_SENSITIVITY")
    assert gate_e["severity"] == "COORDINATOR_DECISION_REQUIRED"


def test_gate_d_burden_is_not_ready_and_owned_by_integration():
    d = _load("results/stage4_architecture_acceptance_gates.json")
    gate_d = next(g for g in d["gates"] if g["gate_id"] == "GATE_D_BURDEN_COMPLETENESS")
    assert gate_d["current_readiness"].startswith("NOT_READY")
    assert gate_d["owner"] == "INTEGRATION_OWNER"


def test_candidate_classes_never_select_a_winner():
    d = _load("results/stage4_architecture_candidate_classes.json")
    raw = json.dumps(d)
    assert '"selected"' not in raw.lower()
    assert '"winner"' not in raw.lower()
    assert '"recommended": true' not in raw.lower()
    assert d["final_architecture_status"] == "UNRESOLVED"
    assert len(d["classes"]) >= 4


def test_candidate_classes_are_composable_and_traceable():
    d = _load("results/stage4_architecture_candidate_classes.json")
    for c in d["classes"]:
        assert "sensors" in c and "anatomical_regions" in c and "evidence_confidence" in c
        assert "pending_science_exposure" in c


def test_final_science_non_regression_via_resolver():
    galaxy = resolver.resolve_current("galaxyppg_external_replication")
    agg = galaxy["aggregate_across_all_18_eligible_subjects"]
    assert abs(agg["A_to_B"]["mean"] - 0.8342679686016505) < 1e-9
    assert abs(agg["C_to_B"]["mean"] - 0.9162305063671538) < 1e-9
    assert galaxy["final_classification"] == "EXTERNAL_REPLICATION_SUPPORTIVE"

    lbnp = resolver.resolve_current("lbnp_thoracic_eis")
    assert abs(lbnp["aggregate"]["A_mean"] - 20.97267498504867) < 1e-9
    assert abs(lbnp["aggregate"]["B_mean"] - 21.42505992137661) < 1e-9
    assert abs(lbnp["aggregate"]["C_mean"] - 20.13177842144602) < 1e-9
    assert lbnp["classification"] == "COMPLETE_MIXED"

    sleep = resolver.resolve_current("sleep_edf_primary_ab")
    assert abs(sleep["aggregate"]["delta_candidate_minus_baseline"]["mean"] - 0.028202575497334757) < 1e-9

    ppg_dalia = resolver.resolve_current("ppg_dalia_capacity_control")
    assert abs(ppg_dalia["primary_comparisons"]["baseline_Acap_candidate_B"]["mean"] - 0.6053154945373536) < 1e-9
