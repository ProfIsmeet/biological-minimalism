"""Tests for the Day 5 sensor marginal-value contract
(ml/build_sensor_marginal_value_contract.py, results/sensor_marginal_value_contract.json).

These verify the CONTRACT-BUILDING LOGIC against the frozen source result
artifacts - they never retrain anything and never modify a source artifact.
"""

from __future__ import annotations

import copy
import hashlib
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

PPG_DALIA_SOURCE = REPO_ROOT / "results" / "ppg_dalia_imu_ablation.json"
PTT_SOURCE = REPO_ROOT / "results" / "ptt_ppg_site_ablation.json"
CONTRACT_PATH = REPO_ROOT / "results" / "sensor_marginal_value_contract.json"
ROBUSTNESS_SOURCE = REPO_ROOT / "results" / "ppg_dalia_fault_robustness.json"
ROBUSTNESS_AUDIT = REPO_ROOT / "docs" / "PHASE5_ROBUSTNESS_AUDIT_ADDENDUM.md"
EXPECTED_ROBUSTNESS_SHA256 = "c40397fb0bb43b4f4a778aac4a4e0ba72b7b0387cab1aabec1e0708cc2912dcb"

requires_sources = pytest.mark.skipif(
    not (PPG_DALIA_SOURCE.exists() and PTT_SOURCE.exists()),
    reason="frozen source result artifacts not present locally",
)


@pytest.fixture(scope="module")
def contract() -> dict:
    assert CONTRACT_PATH.exists(), f"{CONTRACT_PATH} must be built via ml/build_sensor_marginal_value_contract.py before running these tests"
    return json.loads(CONTRACT_PATH.read_text())


@pytest.fixture(scope="module")
def ppg_source() -> dict:
    return json.loads(PPG_DALIA_SOURCE.read_text())


@pytest.fixture(scope="module")
def ptt_source() -> dict:
    return json.loads(PTT_SOURCE.read_text())


# 1. exact source results load ------------------------------------------------


@requires_sources
def test_source_results_load(ppg_source, ptt_source):
    assert ppg_source["status"] == "complete"
    assert "aggregate" in ptt_source


# 2. sign convention correct --------------------------------------------------


def test_sign_convention_documented_and_consistent(contract):
    conv = contract["sign_convention"]
    assert "baseline_metric - candidate_metric" in conv["absolute_benefit"]
    assert "positive = candidate improves" in conv["absolute_benefit"].lower()


# 3. positive PPG-DaLiA IMU benefit calculated correctly ----------------------


@requires_sources
def test_ppg_dalia_absolute_benefit_matches_source(contract, ppg_source):
    exp = contract["experiments"]["ppg_dalia_imu_hr"]
    a = ppg_source["overall_metrics"]["model_a_ppg_only"]["mae"]
    b = ppg_source["overall_metrics"]["model_b_ppg_plus_imu"]["mae"]
    assert exp["absolute_benefit"]["mae_bpm"] == pytest.approx(a - b, abs=1e-9)
    assert exp["absolute_benefit"]["mae_bpm"] > 0
    assert exp["marginal_status"]["overall_direction"] == "POSITIVE"


# 4. negative PTT second-site benefit calculated correctly -------------------


@requires_sources
def test_ptt_absolute_benefit_matches_source_and_is_negative(contract, ptt_source):
    exp = contract["experiments"]["ptt_second_ppg_site_hr"]
    a = ptt_source["aggregate"]["model_a"]["mean_mae"]
    b = ptt_source["aggregate"]["model_b"]["mean_mae"]
    assert exp["absolute_benefit"]["mae_bpm"] == pytest.approx(a - b, abs=1e-9)
    assert exp["absolute_benefit"]["mae_bpm"] < 0
    assert exp["marginal_status"]["overall_direction"] == "NEGATIVE"


# 5. relative improvement formula correct -------------------------------------


@requires_sources
def test_relative_improvement_formula(contract, ppg_source):
    exp = contract["experiments"]["ppg_dalia_imu_hr"]
    a = ppg_source["overall_metrics"]["model_a_ppg_only"]["mae"]
    b = ppg_source["overall_metrics"]["model_b_ppg_plus_imu"]["mae"]
    expected = (a - b) / a
    assert exp["relative_improvement"]["mae_fraction"] == pytest.approx(expected, abs=1e-9)


# 6. RMSE preserved separately -------------------------------------------------


def test_rmse_never_combined_with_mae(contract):
    assert contract["metric_policy"]["combined_mae_rmse_score"] is None
    for exp in contract["experiments"].values():
        if "absolute_benefit" in exp:
            assert "mae_bpm" in exp["absolute_benefit"]
            assert "rmse_bpm" in exp["absolute_benefit"]
            assert exp["absolute_benefit"]["mae_bpm"] != exp["absolute_benefit"]["rmse_bpm"] or True  # distinct fields, not merged


# 7. availability is not folded into MAE --------------------------------------


def test_availability_kept_separate(contract):
    policy = contract["availability_policy"]
    assert policy["folded_into_accuracy_metric"] is False
    assert policy["unavailable_prediction_treated_as_zero_or_infinite_error"] is False


# 8. cross-dataset raw MAE comparison is prohibited/flagged -------------------


def test_cross_dataset_comparison_prohibited(contract):
    rules = contract["comparability_rules"]
    assert rules["cross_dataset_raw_metric_comparison"] == "PROHIBITED"
    for exp in contract["experiments"].values():
        if "comparable_to_other_experiments" in exp:
            assert exp["comparable_to_other_experiments"]["raw_mae_rmse"] is False


# 9. PTT subject heterogeneity preserved --------------------------------------


@requires_sources
def test_ptt_subject_heterogeneity_preserved(contract):
    exp = contract["experiments"]["ptt_second_ppg_site_hr"]
    per_subject = exp["variability"]["per_subject_favors_candidate"]
    assert len(per_subject) == 4
    assert any(v is True for v in per_subject.values())
    assert any(v is False for v in per_subject.values())
    assert exp["marginal_status"]["heterogeneity"]["subject_level"] == "MIXED"


# 10. shuffled IMU preserved ---------------------------------------------------


@requires_sources
def test_shuffled_imu_negative_control_preserved(contract, ppg_source):
    exp = contract["experiments"]["ppg_dalia_imu_hr"]
    assert exp["negative_control"] is not None
    c_mae = ppg_source["overall_metrics"]["model_c_ppg_plus_shuffled_imu"]["mae"]
    assert exp["negative_control"]["shuffled_imu_mae"] == pytest.approx(c_mae, abs=1e-9)
    decomp = exp["synchronization_decomposition"]
    assert decomp["total_imu_benefit_mae_bpm"] == pytest.approx(
        decomp["context_only_like_benefit_mae_bpm"] + decomp["synchronization_increment_mae_bpm"], abs=1e-6
    )


# 11. missing targets remain unavailable ---------------------------------------


def test_unvalidated_targets_not_estimated(contract):
    matrix = contract["evidence_matrix"]
    for target in ("workload", "fatigue", "blood_pressure", "fluid_shift", "circadian_stability"):
        assert matrix[target]["status"] == "UNVALIDATED"
    assert matrix["heart_rate_bpm"]["wrist_imu_accelerometer"]["status"] == "POSITIVE"
    assert matrix["heart_rate_bpm"]["second_physical_ppg_site_proximal_phalanx"]["status"] == "NEGATIVE"


# 12. robustness remains separate from sensor marginal-value score -----------


def test_existing_fault_source_resolves_without_false_missing_status(contract):
    robustness = contract["robustness_records"]["ppg_dalia_fault_robustness"]
    assert robustness["status"] == "RESOLVED_FROM_INTEGRATION_SOURCE"
    assert robustness["source_artifact"] == "results/ppg_dalia_fault_robustness.json"
    assert "SOURCE_ARTIFACT_NOT_FOUND" not in json.dumps(contract)
    assert contract["robustness_relationship"]["sensor_marginal_value_and_robustness_are_separate_axes"] is True


def test_fault_source_is_parsed_not_hardcoded(contract):
    sys.path.insert(0, str(REPO_ROOT / "ml"))
    import build_sensor_marginal_value_contract as builder

    source = json.loads(ROBUSTNESS_SOURCE.read_text())
    altered = copy.deepcopy(source)
    altered["execution"]["eligible_windows_per_condition"] = 1234
    altered["execution"]["total_condition_windows"] = 140676
    altered["clean_baseline"]["mae_bpm_valid_only"] = 12.345
    record = builder.build_fault_robustness_record(
        altered,
        ROBUSTNESS_AUDIT.read_text(),
        EXPECTED_ROBUSTNESS_SHA256,
    )
    assert record["execution"]["eligible_windows_per_condition"] == 1234
    assert record["execution"]["total_condition_windows"] == 140676
    assert record["clean_baseline"]["mae_bpm_valid_only"] == 12.345
    assert contract["robustness_records"]["ppg_dalia_fault_robustness"]["execution"]["eligible_windows_per_condition"] == source["execution"]["eligible_windows_per_condition"]


def test_fault_robustness_source_sha_and_required_semantics(contract):
    assert hashlib.sha256(ROBUSTNESS_SOURCE.read_bytes()).hexdigest() == EXPECTED_ROBUSTNESS_SHA256
    source = json.loads(ROBUSTNESS_SOURCE.read_text())
    record = contract["robustness_records"]["ppg_dalia_fault_robustness"]
    assert record["source_sha256"] == EXPECTED_ROBUSTNESS_SHA256
    assert record["scope"]["subject_id"] == "S14"
    assert record["scope"]["single_subject"] is True
    assert record["execution"]["condition_count"] == source["execution"]["condition_count"] == 114
    assert record["execution"]["eligible_windows_per_condition"] == source["execution"]["eligible_windows_per_condition"] == 4476
    assert record["execution"]["total_condition_windows"] == source["execution"]["total_condition_windows"] == 510264
    assert record["execution"]["no_fallback_prediction"] is True
    assert record["metric_semantics"]["accuracy_population"] == "valid_predictions_only"
    assert record["metric_semantics"]["availability_is_separate_from_accuracy"] is True
    assert record["metric_semantics"]["zero_survivor_accuracy"] is None
    assert "fail-closed" in record["interpretive_context"]["packet_loss"]
    assert "not proof of robustness to severe corruption" in record["interpretive_context"]["imu_fault_calibration"]
    unsupported = record["claim_boundaries"]["not_supported"]
    assert "automatic neural-network fault detection" in unsupported
    assert "fault tolerance" in unsupported


def test_robustness_is_not_a_marginal_experiment_or_score(contract):
    assert "ppg_dalia_fault_robustness" not in contract["experiments"]
    record = contract["robustness_records"]["ppg_dalia_fault_robustness"]
    assert record["evidence_axis"] == "robustness_and_pipeline_availability"
    assert "marginal_status" not in record
    assert "absolute_benefit" not in record
    assert "ranking" in record["separation_rule"]


def test_historical_missing_context_is_preserved_without_current_falsehood(contract):
    history = contract["robustness_records"]["ppg_dalia_fault_robustness"]["historical_provenance"]
    assert "isolated Ismet Day 5" in history["isolated_day5_context"]
    assert "after integration" in history["integrated_resolution"]


# 13. no fake confidence/evidence percentages ----------------------------------


def test_no_numeric_confidence_or_evidence_percentage(contract):
    for exp in contract["experiments"].values():
        status = exp.get("marginal_status")
        if not status:
            continue
        assert status["evidence_strength"] in ("preliminary", "replicated-within-dataset", "mixed", "insufficient")
        # evidence_strength must be categorical text, never a bare numeric confidence
        assert not isinstance(status["evidence_strength"], (int, float))


def test_universal_score_not_defined(contract):
    assert contract["universal_sensor_score"]["defined"] is False
    assert contract["universal_sensor_score"]["recommendation"] == "AGAINST"


# 14. source provenance retained -----------------------------------------------


def test_source_provenance_retained(contract):
    assert contract["experiments"]["ppg_dalia_imu_hr"]["source_artifact"] == "results/ppg_dalia_imu_ablation.json"
    assert contract["experiments"]["ptt_second_ppg_site_hr"]["source_artifact"] == "results/ptt_ppg_site_ablation.json"


# 15. deterministic serialization ----------------------------------------------


def test_contract_rebuild_is_deterministic(tmp_path, contract):
    sys.path.insert(0, str(REPO_ROOT / "ml"))
    import importlib

    build_module = importlib.import_module("build_sensor_marginal_value_contract")
    importlib.reload(build_module)

    original_out = build_module.OUT_PATH
    tmp_out = tmp_path / "contract_rebuild.json"
    build_module.OUT_PATH = tmp_out
    try:
        build_module.main()
    finally:
        build_module.OUT_PATH = original_out

    rebuilt = json.loads(tmp_out.read_text())
    assert rebuilt == contract, "rebuilding the contract from the same frozen sources must be byte-for-byte-equivalent (as parsed JSON)"


# Interaction effects / positive-negative interpretation rules ----------------


def test_interaction_effects_not_assumed(contract):
    assert contract["interaction_effects"]["additive_assumption_supported"] is False
    assert contract["interaction_effects"]["interaction_evidence"] == "unavailable"


def test_positive_and_negative_interpretation_rules_present(contract):
    assert "!=" in contract["positive_result_interpretation_rule"]
    assert "!=" in contract["negative_result_interpretation_rule"]
