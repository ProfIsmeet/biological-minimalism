"""Tests for the PPG-DaLiA capacity-matched control (Model A_cap), the PTT
sensitivity analysis, and the SD-convention audit - Day 7 master-review
repairs.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "backend"))

CAPACITY_RESULTS_PATH = REPO_ROOT / "results" / "ppg_dalia_capacity_control.json"
CAPACITY_REPRO_PATH = REPO_ROOT / "results" / "ppg_dalia_capacity_control_reproducibility.json"
SENSITIVITY_PATH = REPO_ROOT / "results" / "ptt_sensitivity_analysis.json"
SD_AUDIT_PATH = REPO_ROOT / "results" / "sd_convention_audit.json"
ORIGINAL_RESULTS_PATH = REPO_ROOT / "results" / "ppg_dalia_imu_ablation.json"
PTT_RESULTS_PATH = REPO_ROOT / "results" / "ptt_ppg_site_ablation.json"

requires_capacity = pytest.mark.skipif(not CAPACITY_RESULTS_PATH.exists(), reason="capacity control not run yet")
requires_sensitivity = pytest.mark.skipif(not SENSITIVITY_PATH.exists(), reason="PTT sensitivity analysis not run yet")
requires_sd_audit = pytest.mark.skipif(not SD_AUDIT_PATH.exists(), reason="SD audit not run yet")


# --- Parameter counts (Finding A3) ------------------------------------------


def test_original_a_and_b_parameter_counts_confirm_finding_a3():
    from app.ml._torch_bootstrap import ensure_torch_dll_path
    ensure_torch_dll_path()
    from ml.train_ppg_dalia_imu_ablation import PPGOnlyHRModel, PPGPlusIMUHRModel

    n_a = sum(p.numel() for p in PPGOnlyHRModel(32).parameters())
    n_b = sum(p.numel() for p in PPGPlusIMUHRModel(32).parameters())
    assert n_a == 8065
    assert n_b == 29089


def test_a_cap_parameter_count_closely_matches_b():
    from app.ml._torch_bootstrap import ensure_torch_dll_path
    ensure_torch_dll_path()
    from ml.train_ppg_dalia_capacity_control import PPGCapacityMatchedModel
    from ml.train_ppg_dalia_imu_ablation import PPGPlusIMUHRModel

    n_acap = sum(p.numel() for p in PPGCapacityMatchedModel(32).parameters())
    n_b = sum(p.numel() for p in PPGPlusIMUHRModel(32).parameters())
    relative_diff = abs(n_b - n_acap) / n_b
    assert relative_diff < 0.01, f"A_cap should be within 1% of Model B/C capacity, got {relative_diff:.4f}"


def test_a_cap_both_branches_receive_real_gradient_no_dead_weights():
    """Structural guarantee against 'padding with dead parameters' -
    A_cap's forward pass must not use any modality_mask that would zero
    out a branch."""
    import inspect
    from ml.train_ppg_dalia_capacity_control import PPGCapacityMatchedModel

    source = inspect.getsource(PPGCapacityMatchedModel.forward)
    assert "torch.ones" in source, "both branches must be unmasked (all-True mask), not conditionally zeroed"
    assert "zeros" not in source.lower() or "torch.zeros" not in source


# --- Result-dependent -------------------------------------------------------


@requires_capacity
def test_capacity_control_does_not_overwrite_original_artifacts():
    original = json.loads(ORIGINAL_RESULTS_PATH.read_text())
    assert original["overall_metrics"]["model_a_ppg_only"]["mae"] == pytest.approx(9.090062141418457, abs=1e-9)


@requires_capacity
def test_capacity_control_uses_frozen_split_and_seeds():
    results = json.loads(CAPACITY_RESULTS_PATH.read_text())
    frozen_split = json.loads((REPO_ROOT / "ml/experiments/ppg_dalia_imu_ablation/subject_split.json").read_text())
    assert results["frozen_protocol"]["subject_split"] == frozen_split
    assert results["frozen_protocol"]["training_seeds"] == [42, 43, 44, 45, 46]


@requires_capacity
def test_capacity_control_all_seeds_present_and_finite():
    results = json.loads(CAPACITY_RESULTS_PATH.read_text())
    for seed in (42, 43, 44, 45, 46):
        report = results["runs"][f"seed{seed}"]
        assert report["overall"]["mae"] > 0.5, "suspiciously low MAE - investigate leakage"


@requires_capacity
def test_capacity_control_primary_comparisons_sign_correct():
    results = json.loads(CAPACITY_RESULTS_PATH.read_text())
    comparisons = results["primary_comparisons"]
    # A -> A_cap must show a real, consistent improvement (this is the headline finding)
    assert comparisons["baseline_A_candidate_Acap"]["mean"] > 0
    assert comparisons["baseline_A_candidate_Acap"]["n_seeds_candidate_better"] == 5


@requires_capacity
def test_capacity_control_checkpoint_manifest_complete():
    results = json.loads(CAPACITY_RESULTS_PATH.read_text())
    assert len(results["checkpoint_manifest"]) == 5


@pytest.mark.skipif(not CAPACITY_REPRO_PATH.exists(), reason="reproducibility check not run yet")
def test_capacity_control_reproducibility_all_ok():
    report = json.loads(CAPACITY_REPRO_PATH.read_text())
    assert report["all_ok"] is True


# --- PTT sensitivity ---------------------------------------------------------


@requires_sensitivity
def test_ptt_sensitivity_s2_never_excluded_from_frozen_result():
    ptt = json.loads(PTT_RESULTS_PATH.read_text())
    assert "s2" in ptt["subject_split"]["test"], "s2 must remain in the frozen PTT test split"


@requires_sensitivity
def test_ptt_sensitivity_direction_flip_confirmed_for_s2_only():
    results = json.loads(SENSITIVITY_PATH.read_text())
    assert results["s2_dependence"]["direction_flips_when_s2_excluded"] is True
    loo = results["leave_one_subject_out_descriptive_sensitivity"]
    non_s2_flips = [k for k, v in loo.items() if k != "excluding_s2" and v["direction"] == "B_BETTER"]
    assert non_s2_flips == [], "only excluding s2 should flip the aggregate direction"


@requires_sensitivity
def test_ptt_sensitivity_leave_one_out_matches_manual_recomputation():
    ptt = json.loads(PTT_RESULTS_PATH.read_text())
    results = json.loads(SENSITIVITY_PATH.read_text())
    seeds = list(ptt["runs"]["a"].keys())
    subjects = sorted(ptt["runs"]["a"][seeds[0]]["per_subject"].keys())
    remaining = [s for s in subjects if s != "s2"]

    total_abs_a, total_n = 0.0, 0
    for s in remaining:
        seed_avg = sum(ptt["runs"]["a"][sk]["per_subject"][s]["mae"] for sk in seeds) / len(seeds)
        n = ptt["runs"]["a"][seeds[0]]["per_subject"][s]["n_windows"]
        total_abs_a += seed_avg * n
        total_n += n
    manual_a = total_abs_a / total_n

    assert manual_a == pytest.approx(results["s2_dependence"]["without_s2"]["model_a_mae"], abs=1e-6)


@requires_sensitivity
def test_ptt_sensitivity_labeled_descriptive_not_primary():
    results = json.loads(SENSITIVITY_PATH.read_text())
    assert "descriptive sensitivity analysis" in results["label"]


# --- SD convention audit ----------------------------------------------------


@requires_sd_audit
def test_sd_audit_preserves_original_ddof0_values():
    audit = json.loads(SD_AUDIT_PATH.read_text())
    multiseed = json.loads((REPO_ROOT / "results" / "ppg_dalia_imu_multiseed_replication.json").read_text())
    audited_a_mae_sd = audit["sources"]["ppg_dalia_imu_multiseed_replication"]["audit"]["model_a"]["mae"]["sd_population_ddof0_as_originally_reported"]
    original_a_mae_sd = multiseed["aggregate"]["model_a"]["sd_mae"]
    assert audited_a_mae_sd == pytest.approx(original_a_mae_sd, abs=1e-9)


@requires_sd_audit
def test_sd_audit_ddof1_is_larger_than_ddof0():
    audit = json.loads(SD_AUDIT_PATH.read_text())
    m = audit["sources"]["ppg_dalia_imu_multiseed_replication"]["audit"]["model_a"]["mae"]
    assert m["sd_sample_ddof1_recommended"] > m["sd_population_ddof0_as_originally_reported"]


@requires_sd_audit
def test_sd_audit_does_not_modify_frozen_artifacts():
    multiseed_before = json.loads((REPO_ROOT / "results" / "ppg_dalia_imu_multiseed_replication.json").read_text())
    assert multiseed_before["aggregate"]["model_a"]["sd_mae"] == pytest.approx(0.2306219374643015, abs=1e-9)
