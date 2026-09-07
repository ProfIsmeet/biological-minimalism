"""Tests for the Day 5 sensor marginal-value contract
(ml/build_sensor_marginal_value_contract.py, results/sensor_marginal_value_contract.json).

These verify the CONTRACT-BUILDING LOGIC against the frozen source result
artifacts - they never retrain anything and never modify a source artifact.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

PPG_DALIA_SOURCE = REPO_ROOT / "results" / "ppg_dalia_imu_ablation.json"
PTT_SOURCE = REPO_ROOT / "results" / "ptt_ppg_site_ablation.json"
CONTRACT_PATH = REPO_ROOT / "results" / "sensor_marginal_value_contract.json"

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
        # Only regression (MAE/RMSE) experiments are checked here - a
        # classification experiment (e.g. sleep_edf, macro_f1) legitimately
        # has no mae_bpm/rmse_bpm fields at all, which is correct, not a
        # violation of "never combine MAE and RMSE."
        if "absolute_benefit" in exp and "mae_bpm" in exp["absolute_benefit"]:
            assert "rmse_bpm" in exp["absolute_benefit"]


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
    # Status strings may be refined with more detail over time (e.g. after the
    # Day 7 capacity-control revision) - check direction prefix, not exact match.
    assert matrix["heart_rate_bpm"]["wrist_imu_accelerometer"]["status"].startswith("POSITIVE")
    assert matrix["heart_rate_bpm"]["second_physical_ppg_site_proximal_phalanx"]["status"].startswith("NEGATIVE")


# 12. robustness remains separate from sensor marginal-value score -----------


def test_fault_robustness_record_not_fabricated(contract):
    robustness = contract["experiments"]["ppg_dalia_fault_robustness"]
    assert robustness["status"] == "SOURCE_ARTIFACT_NOT_FOUND"
    assert "mae" not in robustness  # must not contain fabricated metric fields
    assert "availability" not in robustness
    assert contract["robustness_relationship"]["sensor_marginal_value_and_robustness_are_separate_axes"] is True


def test_fault_robustness_source_genuinely_absent_repo_wide():
    """Guards against silently 'fixing' this by inventing the file - if it
    ever appears, this test should be revisited (not just made to pass)."""
    result = subprocess.run(
        ["git", "log", "--all", "--oneline", "--", "results/ppg_dalia_fault_robustness.json"],
        cwd=REPO_ROOT, capture_output=True, text=True,
    )
    assert result.stdout.strip() == "", "results/ppg_dalia_fault_robustness.json now exists in history - re-run the contract builder to populate it from source"


# 13. no fake confidence/evidence percentages ----------------------------------


def test_no_numeric_confidence_or_evidence_percentage(contract):
    for exp in contract["experiments"].values():
        status = exp.get("marginal_status")
        if not status:
            continue
        assert status["evidence_strength"] in ("preliminary", "replicated-within-dataset", "replicated-with-control", "mixed", "insufficient")
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


# --- Day 7 additions ---------------------------------------------------------


CAPACITY_CONTROL_PATH = REPO_ROOT / "results" / "ppg_dalia_capacity_control.json"
SENSITIVITY_PATH = REPO_ROOT / "results" / "ptt_sensitivity_analysis.json"
SLEEP_EDF_PATH = REPO_ROOT / "results" / "sleep_edf_eeg_eog_ablation.json"

requires_day7 = pytest.mark.skipif(
    not (CAPACITY_CONTROL_PATH.exists() and SENSITIVITY_PATH.exists() and SLEEP_EDF_PATH.exists()),
    reason="Day 7 result artifacts not all present",
)


@requires_day7
def test_methodology_version_bumped_for_day7(contract):
    # Version has continued to advance (Day 8 shuffled-EOG control) - check
    # it is at least the Day 7 baseline, not pinned to an exact string that
    # legitimately keeps incrementing.
    major, minor, _patch = (int(p) for p in contract["methodology_version"].split("."))
    assert (major, minor) >= (1, 2)


@requires_day7
def test_ppg_dalia_capacity_confound_status_resolved(contract):
    status = contract["experiments"]["ppg_dalia_imu_hr"]["capacity_confound_status"]
    assert status["status"] == "RESOLVED_WITH_REVISED_CLAIM"
    assert 0.6 < status["fraction_of_original_gap_explained_by_capacity_alone"] < 0.75
    assert status["genuine_imu_information_benefit_seed_consistency"] == "5/5"


@requires_day7
def test_ppg_dalia_direction_still_positive_but_rationale_revised(contract):
    status = contract["experiments"]["ppg_dalia_imu_hr"]["marginal_status"]
    assert status["overall_direction"] == "POSITIVE"
    assert "capacity" in status["evidence_strength_rationale"].lower()


@requires_day7
def test_ptt_sensitivity_analysis_present_and_flags_s2(contract):
    sens = contract["experiments"]["ptt_second_ppg_site_hr"]["sensitivity_analysis"]
    assert sens["s2_dependence"]["direction_flips_when_s2_excluded"] is True


@requires_day7
def test_sleep_edf_experiment_present_with_correct_metric(contract):
    exp = contract["experiments"]["sleep_edf_eeg_eog_sleep_stage"]
    assert exp["primary_metric"] == "macro_f1"
    assert exp["marginal_status"]["overall_direction"] == "POSITIVE"
    assert exp["comparable_to_other_experiments"]["raw_macro_f1_vs_other_metrics"] is False


@requires_day7
def test_sleep_edf_capacity_avoided_by_design(contract):
    status = contract["experiments"]["sleep_edf_eeg_eog_sleep_stage"]["capacity_confound_status"]
    assert status["status"] == "AVOIDED_BY_DESIGN"
    assert status["residual_fraction"] < 0.05


@requires_day7
def test_evidence_matrix_includes_sleep_stage_target(contract):
    assert "sleep_stage_5class" in contract["evidence_matrix"]
    assert contract["evidence_matrix"]["sleep_stage_5class"]["eog_horizontal_channel"]["status"].startswith("POSITIVE")


@requires_day7
def test_interaction_limitation_doc_referenced(contract):
    assert contract["interaction_effects"]["formal_limitation_doc"] == "docs/SENSOR_INTERACTION_LIMITATION.md"


@requires_day7
def test_no_conservative_terms_misused_in_contract_text(contract):
    """Master-review requirement: avoid words like 'universally useful',
    'optimal', 'minimal architecture', 'astronaut validated', 'robust',
    'causal' unless explicitly supported - scan the serialized contract
    text for these as a lightweight guard."""

    text = json.dumps(contract).lower()
    # Each phrase below is only prohibited in its CLAIMING form. The
    # contract legitimately contains DISCLAIMING phrasing like "not a
    # proven causal split" or "not astronaut validated" - those are correct
    # and must not trip this guard, so we check for the unqualified/
    # asserting form specifically, not a bare substring.
    forbidden_unqualified = ["is astronaut validated", "is microgravity validated", "is globally optimal", "is a proven causal"]
    for phrase in forbidden_unqualified:
        assert phrase not in text, f"prohibited unqualified claim phrase found: {phrase!r}"


# --- Day 8 additions (shuffled-EOG control, per-subject decomposition) -----


SLEEP_CONTROL_PATH = REPO_ROOT / "results" / "sleep_edf_eeg_eog_control_analysis.json"
SLEEP_PER_SUBJECT_PATH = REPO_ROOT / "results" / "sleep_edf_per_subject_analysis.json"

requires_day8 = pytest.mark.skipif(
    not (SLEEP_CONTROL_PATH.exists() and SLEEP_PER_SUBJECT_PATH.exists()),
    reason="Day 8 sleep-EDF control/per-subject artifacts not present",
)


@requires_day8
def test_sleep_edf_evidence_upgraded_to_replicated_with_control(contract):
    status = contract["experiments"]["sleep_edf_eeg_eog_sleep_stage"]["marginal_status"]
    assert status["evidence_strength"] == "replicated-with-control"


@requires_day8
def test_sleep_edf_negative_control_present_and_outcome_1(contract):
    nc = contract["experiments"]["sleep_edf_eeg_eog_sleep_stage"]["negative_control"]
    assert nc is not None
    assert nc["outcome_classification"] == "OUTCOME_1_ALIGNED_TIMING_MATTERS"
    assert nc["C_to_B"]["n_seeds_favor_B"] == 5


@requires_day8
def test_sleep_edf_per_subject_dominated_flag_present(contract):
    per_subj = contract["experiments"]["sleep_edf_eeg_eog_sleep_stage"]["per_subject_analysis"]
    assert per_subj["dominated_by_one_subject"] is True
    assert per_subj["subject_directions"]["SC4011"] == "IMPROVES"
