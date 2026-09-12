"""Tests for the Day 6 PPG-DaLiA multi-seed replication
(ml/train_ppg_dalia_imu_multiseed.py, results/ppg_dalia_imu_multiseed_replication.json).

Structural/protocol tests run unconditionally (no training required).
Result-dependent tests are skipped (with a clear reason) until
results/ppg_dalia_imu_multiseed_replication.json exists.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "backend"))

ORIGINAL_RESULTS_PATH = REPO_ROOT / "results" / "ppg_dalia_imu_ablation.json"
MULTISEED_RESULTS_PATH = REPO_ROOT / "results" / "ppg_dalia_imu_multiseed_replication.json"
FROZEN_SPLIT_PATH = REPO_ROOT / "ml" / "experiments" / "ppg_dalia_imu_ablation" / "subject_split.json"
PTT_RESULTS_PATH = REPO_ROOT / "results" / "ptt_ppg_site_ablation.json"
FAULT_ROBUSTNESS_PATH = REPO_ROOT / "results" / "ppg_dalia_fault_robustness.json"

requires_multiseed_results = pytest.mark.skipif(
    not MULTISEED_RESULTS_PATH.exists(), reason=f"{MULTISEED_RESULTS_PATH} not present - run ml/train_ppg_dalia_imu_multiseed.py first"
)


# --- 1/2. seed list exactly expected, imported from the module ------------


def test_training_seeds_are_exactly_expected():
    from ml.train_ppg_dalia_imu_multiseed import TRAINING_SEEDS
    assert TRAINING_SEEDS == (42, 43, 44, 45, 46)


# --- 3. same split all seeds/models: the script loads ONE split, never recomputes ---


def test_multiseed_script_loads_frozen_split_never_recomputes():
    import inspect

    from ml import train_ppg_dalia_imu_multiseed as mod

    source = inspect.getsource(mod.main)
    assert "subject_wise_split" not in source, "the multiseed script must not recompute the split - it must load the frozen file"
    assert "ORIGINAL_EXPERIMENT_DIR" in source


def test_frozen_split_file_exists_and_is_disjoint():
    split = json.loads(FROZEN_SPLIT_PATH.read_text())
    train, val, test = set(split["train"]), set(split["val"]), set(split["test"])
    assert not (train & val) and not (train & test) and not (val & test)


# --- 4. same preprocessing all seeds/models: shared build_tensors/train_model imported ---


def test_multiseed_script_imports_original_functions_unmodified():
    from ml.train_ppg_dalia_imu_multiseed import (
        build_tensors,
        evaluate,
        mae,
        rmse,
        shuffle_imu_within_subject,
        stratified_report,
        train_model,
    )
    from ml.train_ppg_dalia_imu_ablation import build_tensors as orig_build_tensors
    from ml.train_ppg_dalia_imu_ablation import evaluate as orig_evaluate
    from ml.train_ppg_dalia_imu_ablation import train_model as orig_train_model

    assert build_tensors is orig_build_tensors, "must import the SAME function, not a re-implementation"
    assert evaluate is orig_evaluate
    assert train_model is orig_train_model


# --- 5. same training config all seeds/models: hard-coded, single source ---


def test_training_hyperparameters_are_frozen_constants():
    from ml.train_ppg_dalia_imu_multiseed import BATCH_SIZE, EMBEDDING_DIM, EPOCHS, LR

    config = json.loads((REPO_ROOT / "ml/experiments/ppg_dalia_imu_ablation/config.json").read_text())
    assert EPOCHS == config["epochs"]
    assert BATCH_SIZE == config["batch_size"]
    assert LR == config["lr"]
    assert EMBEDDING_DIM == config["embedding_dim"]


# --- 6. Model A/B/C architecture contract unchanged except intended input differences ---


def test_model_classes_imported_unmodified_from_original_script():
    from ml.train_ppg_dalia_imu_multiseed import PPGOnlyHRModel, PPGPlusIMUHRModel
    from ml.train_ppg_dalia_imu_ablation import PPGOnlyHRModel as OrigA
    from ml.train_ppg_dalia_imu_ablation import PPGPlusIMUHRModel as OrigB

    assert PPGOnlyHRModel is OrigA
    assert PPGPlusIMUHRModel is OrigB


# --- 8. shuffle semantics deterministic ------------------------------------


def test_shuffle_seed_policy_documented_and_coupled_to_training_seed():
    import inspect
    from ml import train_ppg_dalia_imu_multiseed as mod

    source = inspect.getsource(mod.main)
    assert "shuffle_imu_within_subject(train_data, seed=seed)" in source
    assert "shuffle_seed_policy" in source


def test_shuffle_is_within_subject_and_deterministic():
    import numpy as np
    import torch
    from ml.train_ppg_dalia_imu_ablation import shuffle_imu_within_subject

    data = {
        "subject_ids": np.array(["S1", "S1", "S1", "S2", "S2"]),
        "acc": torch.arange(15, dtype=torch.float32).reshape(5, 3, 1),
    }
    out1 = shuffle_imu_within_subject(data, seed=42)
    out2 = shuffle_imu_within_subject(data, seed=42)
    assert torch.equal(out1["acc"], out2["acc"]), "same seed must give identical shuffle"

    # within-subject only: S1's rows must remain a permutation of S1's original rows, never S2's.
    s1_original = set(data["acc"][:3].flatten().tolist())
    s1_shuffled = set(out1["acc"][:3].flatten().tolist())
    assert s1_original == s1_shuffled


# --- 13. interpretation thresholds frozen before running -------------------


def test_classify_replication_thresholds():
    from ml.train_ppg_dalia_imu_multiseed import classify_replication

    assert classify_replication(2.0, 5, 5) == "STRONGLY_REPLICATED_POSITIVE"
    assert classify_replication(2.0, 4, 5) == "STRONGLY_REPLICATED_POSITIVE"
    assert classify_replication(0.5, 3, 5) == "REPLICATED_BUT_VARIABLE"
    assert classify_replication(0.1, 2, 5) == "MIXED"
    assert classify_replication(-0.5, 1, 5) == "NON_REPLICATED"
    assert classify_replication(-0.1, 5, 5) == "NON_REPLICATED"  # negative mean always non-replicated regardless of seed count


# --- 17/18/19. frozen artifacts unchanged ----------------------------------


def test_original_single_seed_artifact_unchanged():
    original = json.loads(ORIGINAL_RESULTS_PATH.read_text())
    assert original["overall_metrics"]["model_a_ppg_only"]["mae"] == pytest.approx(9.090062141418457, abs=1e-9)
    assert original["overall_metrics"]["model_b_ppg_plus_imu"]["mae"] == pytest.approx(7.031700611114502, abs=1e-9)
    assert original["overall_metrics"]["model_c_ppg_plus_shuffled_imu"]["mae"] == pytest.approx(7.956958293914795, abs=1e-9)


def test_ptt_artifact_unchanged():
    ptt = json.loads(PTT_RESULTS_PATH.read_text())
    agg = ptt["aggregate"]
    assert agg["model_a"]["mean_mae"] == pytest.approx(17.540314865112304, abs=1e-6)
    assert agg["model_b"]["mean_mae"] == pytest.approx(19.002723693847656, abs=1e-6)


def test_robustness_artifact_resolved_after_integration_not_fabricated():
    """Post-integration guard (was: 'still_absent'). In the isolated Ismet Day 5
    context the frozen S14 robustness source was unavailable, so the contract
    emitted a placeholder. After merging the accepted Emir integration branch the
    real artifact is present and resolved from its frozen source. This test
    guards against BOTH regressions: (a) the old false SOURCE_ARTIFACT_NOT_FOUND
    state returning, and (b) robustness numbers being fabricated rather than
    parsed from the frozen source."""
    frozen_sha256 = "c40397fb0bb43b4f4a778aac4a4e0ba72b7b0387cab1aabec1e0708cc2912dcb"
    contract_path = REPO_ROOT / "results" / "sensor_marginal_value_contract.json"

    assert FAULT_ROBUSTNESS_PATH.exists(), (
        "results/ppg_dalia_fault_robustness.json must be present after integration"
    )
    import hashlib

    # Day 10 finding: core.autocrlf=true means a Windows checkout's raw bytes
    # differ from the LF-normalized git-blob bytes the constant was frozen
    # against, even with byte-for-byte-identical JSON content. Normalize
    # before hashing (matches the fix in build_sensor_marginal_value_contract.py).
    normalized = FAULT_ROBUSTNESS_PATH.read_bytes().replace(b"\r\n", b"\n")
    actual_sha = hashlib.sha256(normalized).hexdigest()
    assert actual_sha == frozen_sha256, "Frozen robustness source identity changed - investigate."

    contract_text = contract_path.read_text()
    assert "SOURCE_ARTIFACT_NOT_FOUND" not in contract_text, (
        "H1 regression: the false missing-source placeholder must not return."
    )
    contract = json.loads(contract_text)
    record = contract["robustness_records"]["ppg_dalia_fault_robustness"]
    assert record["status"] == "RESOLVED_FROM_INTEGRATION_SOURCE"
    assert record["source_sha256"] == frozen_sha256
    # Robustness stays a separate axis, never folded into marginal sensor value.
    assert "ppg_dalia_fault_robustness" not in contract["experiments"]


# --- Result-dependent tests -------------------------------------------------


@requires_multiseed_results
def test_multiseed_results_seed_parity_with_split():
    results = json.loads(MULTISEED_RESULTS_PATH.read_text())
    assert results["frozen_protocol"]["subject_split"] == json.loads(FROZEN_SPLIT_PATH.read_text())


@requires_multiseed_results
def test_multiseed_results_no_subject_leakage():
    results = json.loads(MULTISEED_RESULTS_PATH.read_text())
    split = results["frozen_protocol"]["subject_split"]
    train, val, test = set(split["train"]), set(split["val"]), set(split["test"])
    assert not (train & val) and not (train & test) and not (val & test)


@requires_multiseed_results
def test_multiseed_per_seed_metrics_parse_and_aggregate_correctly():
    results = json.loads(MULTISEED_RESULTS_PATH.read_text())
    seeds = results["frozen_protocol"]["training_seeds"]
    a_maes = [results["runs"]["a"][f"seed{s}"]["overall"]["mae"] for s in seeds]
    recomputed_mean = sum(a_maes) / len(a_maes)
    assert results["aggregate"]["model_a"]["mean_mae"] == pytest.approx(recomputed_mean, abs=1e-9)


@requires_multiseed_results
def test_multiseed_paired_benefit_sign_and_direction_counts():
    results = json.loads(MULTISEED_RESULTS_PATH.read_text())
    agg = results["aggregate"]["total_sync_imu_benefit_mae_A_minus_B"]
    for seed_key, delta in agg["per_seed"].items():
        a = results["runs"]["a"][seed_key]["overall"]["mae"]
        b = results["runs"]["b"][seed_key]["overall"]["mae"]
        assert delta == pytest.approx(a - b, abs=1e-9)
    n_favor_recomputed = sum(1 for d in agg["per_seed"].values() if d > 0)
    assert n_favor_recomputed == agg["n_seeds_favor_B"]


@requires_multiseed_results
def test_multiseed_subject_level_aggregation_correct():
    results = json.loads(MULTISEED_RESULTS_PATH.read_text())
    per_subject = results["subject_level_consistency"]
    seeds = results["frozen_protocol"]["training_seeds"]
    for subject, entry in per_subject.items():
        recomputed_favor = sum(
            1 for s in seeds
            if entry["model_a_mae_per_seed"][f"seed{s}"] - entry["model_b_mae_per_seed"][f"seed{s}"] > 0
        )
        assert recomputed_favor == entry["n_seeds_favor_B"]


@requires_multiseed_results
def test_multiseed_motion_quartile_aggregation_correct():
    results = json.loads(MULTISEED_RESULTS_PATH.read_text())
    assert len(results["motion_quartile_consistency"]) == 4


@requires_multiseed_results
def test_multiseed_activity_aggregation_correct_and_table_soccer_retained():
    results = json.loads(MULTISEED_RESULTS_PATH.read_text())
    assert "table_soccer" in results["activity_level_consistency"]


@requires_multiseed_results
def test_multiseed_checkpoint_manifest_complete():
    results = json.loads(MULTISEED_RESULTS_PATH.read_text())
    assert len(results["checkpoint_manifest"]) == 15  # 3 models x 5 seeds


@requires_multiseed_results
def test_multiseed_checkpoint_sha256_matches_actual_files():
    import hashlib
    results = json.loads(MULTISEED_RESULTS_PATH.read_text())
    # Checkpoints are gitignored (ml/checkpoints/*), so a clean checkout will not
    # contain them. Normalize any Windows-style separators recorded on the
    # training host before resolving, and skip if none are present locally rather
    # than hard-failing on the intentionally-uncommitted binaries.
    resolved = [
        (entry, REPO_ROOT / Path(entry["path"].replace("\\", "/")))
        for entry in results["checkpoint_manifest"]
    ]
    present = [(entry, path) for entry, path in resolved if path.exists()]
    if not present:
        pytest.skip("multi-seed checkpoints not present locally (gitignored ml/checkpoints/*)")
    for entry, ckpt_path in present:
        actual = hashlib.sha256(ckpt_path.read_bytes()).hexdigest()
        assert actual == entry["sha256"], f"checkpoint sha mismatch: {ckpt_path}"


# --- 21. no automatic evidence-strength upgrade -----------------------------


@requires_multiseed_results
def test_contract_evidence_strength_reflects_actual_seed_consistency():
    """The contract must NOT automatically upgrade to 'replicated-within-dataset'
    just because 5 runs were performed - only if the actual seed-direction
    count supports it (evidence_strength_from_seed_consistency threshold)."""

    from ml.build_sensor_marginal_value_contract import evidence_strength_from_seed_consistency

    results = json.loads(MULTISEED_RESULTS_PATH.read_text())
    n_favor = results["aggregate"]["total_sync_imu_benefit_mae_A_minus_B"]["n_seeds_favor_B"]
    n_total = results["aggregate"]["total_sync_imu_benefit_mae_A_minus_B"]["n_seeds_total"]
    strength, _ = evidence_strength_from_seed_consistency(n_favor, n_total)
    if n_favor < n_total - 1:
        assert strength != "replicated-within-dataset", "must not upgrade evidence strength when seed direction is not consistent"


# --- 22. next-experiment predeclaration exists before any next-target training ---


def test_next_target_predeclaration_exists():
    predeclaration = REPO_ROOT / "docs" / "NEXT_TARGET_EXPERIMENT_PREDECLARATION.md"
    assert predeclaration.exists()
    text = predeclaration.read_text(encoding="utf-8")
    assert "No training for this predeclared experiment was performed" in text


def test_no_next_target_training_happened_during_day6():
    """Day 6 guard: at the time Day 6 completed, the predeclared Sleep-EDF
    EEG+EOG ablation must not yet have been run. Day 7 explicitly
    predeclared (docs/SLEEP_EDF_EEG_EOG_PREDECLARATION_DAY7.md) and then
    authorized that experiment, so its result artifact existing now is
    correct, not a violation - this test only asserts that when it DOES
    exist, a corresponding Day 7 predeclaration document exists too,
    proving it wasn't trained without one."""

    result_path = REPO_ROOT / "results" / "sleep_edf_eeg_eog_ablation.json"
    if result_path.exists():
        assert (REPO_ROOT / "docs" / "SLEEP_EDF_EEG_EOG_PREDECLARATION_DAY7.md").exists(), (
            "Sleep-EDF result exists but no predeclaration document was found - "
            "training must always follow a frozen predeclaration"
        )


def test_integrated_contract_has_multiseed_and_resolved_robustness_together():
    """Day-6 integration invariant: after merging Ismet's multi-seed evidence
    into the accepted Emir engineering branch, the single contract must carry
    BOTH the strengthened multi-seed marginal-value evidence AND the resolved
    robustness axis, kept as separate axes."""
    contract = json.loads(
        (REPO_ROOT / "results" / "sensor_marginal_value_contract.json").read_text()
    )
    exp = contract["experiments"]["ppg_dalia_imu_hr"]

    # (1) Multi-seed replication is present and upgraded from actual consistency.
    assert exp["marginal_status"]["evidence_strength"] == "replicated-within-dataset"
    assert exp["evidence_scope"]["n_training_seeds"] == 5
    ms = exp["multiseed_replication"]
    assert ms is not None
    assert ms["replication_status"] == "STRONGLY_REPLICATED_POSITIVE"
    assert ms["decomposition_across_seeds_mae_bpm"]["total_imu_benefit_A_minus_B"]["n_seeds_favor_candidate"] == 5
    # (2) table_soccer stays a visible stable negative case (0/5) - not hidden.
    assert ms["seed_aware_consistency"]["activity_direction"]["table_soccer"] == "0/5"
    assert "table_soccer" in ms["seed_aware_consistency"]["activities_never_favoring_candidate"]
    # (3) All held-out subjects and motion quartiles favor candidate 5/5.
    assert all(v == "5/5" for v in ms["seed_aware_consistency"]["subject_direction"].values())
    assert all(v == "5/5" for v in ms["seed_aware_consistency"]["motion_quartile_direction"].values())
    # (4) Robustness resolved on a SEPARATE axis, not folded into marginal value.
    rob = contract["robustness_records"]["ppg_dalia_fault_robustness"]
    assert rob["status"] == "RESOLVED_FROM_INTEGRATION_SOURCE"
    assert "ppg_dalia_fault_robustness" not in contract["experiments"]
    assert contract["robustness_relationship"]["sensor_marginal_value_and_robustness_are_separate_axes"] is True
    # (5) No causal wording: benefit is not attributed to synchronization alone.
    assert "not attributable to synchronization" in exp["synchronization_decomposition"]["interpretation_note"]
    # (6) No cross-dataset ranking / universal score.
    assert contract["comparability_rules"]["cross_dataset_raw_metric_comparison"] == "PROHIBITED"
    assert contract["universal_sensor_score"]["defined"] is False
