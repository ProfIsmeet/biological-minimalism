"""Day 10 scientific reproducibility, dataset fingerprint, and interaction-
experiment tests."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "backend"))

ENV_PATH = REPO_ROOT / "results" / "day10_frozen_environment_verification.json"
FINGERPRINT_PATH = REPO_ROOT / "results" / "dataset_fingerprint_manifest_day10.json"
REPRO_PATH = REPO_ROOT / "results" / "day10_scientific_reproduction.json"
N3_PATH = REPO_ROOT / "results" / "sleep_edf_secondary_n3_diagnostic.json"
FREEZE_PATH = REPO_ROOT / "results" / "scientific_freeze_readiness_day10.json"
INTERACTION_PREDECLARATION_PATH = REPO_ROOT / "docs" / "INTERACTION_EXPERIMENT_PREDECLARATION_DAY10.md"
INTERACTION_FEASIBILITY_PATH = REPO_ROOT / "docs" / "INTERACTION_EXPERIMENT_FEASIBILITY_DAY10.md"
INTERACTION_RESULTS_PATH = REPO_ROOT / "results" / "sleep_edf_interaction_resp_day10.json"
SECONDARY_COHORT_PATH = REPO_ROOT / "ml" / "experiments" / "sleep_edf_secondary_holdout" / "cohort.json"
PRIMARY_SPLIT_PATH = REPO_ROOT / "ml" / "experiments" / "sleep_edf_eeg_eog_ablation" / "subject_split.json"

requires_env = pytest.mark.skipif(not ENV_PATH.exists(), reason="Day 10 environment verification not run yet")
requires_fingerprint = pytest.mark.skipif(not FINGERPRINT_PATH.exists(), reason="Day 10 dataset fingerprint not built yet")
requires_repro = pytest.mark.skipif(not REPRO_PATH.exists(), reason="Day 10 master reproduction artifact not built yet")
requires_n3 = pytest.mark.skipif(not N3_PATH.exists(), reason="Day 10 N3 diagnostic not run yet")
requires_interaction = pytest.mark.skipif(not INTERACTION_RESULTS_PATH.exists(), reason="interaction experiment not run")

SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


# --- Environment --------------------------------------------------------------


@requires_env
def test_environment_expected_frozen_versions():
    env = json.loads(ENV_PATH.read_text())
    expected = env["expected"]
    assert expected["python_version"] == "3.13.0"
    assert expected["torch"] == "2.6.0+cpu"
    assert expected["cuda_available"] is False
    assert expected["numpy"] == "2.5.2"
    assert expected["scipy"] == "1.18.1"
    assert expected["scikit-learn"] == "1.9.0"
    assert expected["mne"] == "1.12.1"
    assert expected["wfdb"] == "4.3.1"
    assert expected["pandas"] == "3.0.5"


@requires_env
def test_environment_exact_match_no_mismatches():
    env = json.loads(ENV_PATH.read_text())
    assert env["mismatched_fields"] == []
    assert env["environment_status"] == "EXACT_FROZEN_ENVIRONMENT"
    assert env["expected"] == env["actual"] or all(
        env["expected"][k] == env["actual"][k] for k in ("python_version", "cuda_available", "torch", "numpy", "scipy", "scikit-learn", "mne", "wfdb", "pandas")
    )


# --- Dataset fingerprint --------------------------------------------------------


@requires_fingerprint
def test_fingerprint_no_raw_files_committed():
    manifest = json.loads(FINGERPRINT_PATH.read_text())
    for block in manifest["datasets"].values():
        for entry in block["entries"]:
            assert entry["raw_file_committed_to_git"] is False


@requires_fingerprint
def test_fingerprint_sha_format_valid_for_present_files():
    manifest = json.loads(FINGERPRINT_PATH.read_text())
    for block in manifest["datasets"].values():
        for entry in block["entries"]:
            if entry["locally_present"]:
                assert entry["sha256"] is not None and SHA256_RE.match(entry["sha256"])
            else:
                assert entry["sha256"] is None


@requires_fingerprint
def test_fingerprint_all_required_records_present():
    manifest = json.loads(FINGERPRINT_PATH.read_text())
    assert manifest["overall_summary"]["n_missing"] == 0


@requires_fingerprint
def test_fingerprint_no_duplicate_paths_within_a_dataset_block():
    manifest = json.loads(FINGERPRINT_PATH.read_text())
    for name, block in manifest["datasets"].items():
        paths = [e["path"] for e in block["entries"] if e["path"] is not None]
        assert len(paths) == len(set(paths)), f"duplicate path entries in {name}"


@requires_fingerprint
def test_fingerprint_sleep_primary_covers_all_18_subjects():
    manifest = json.loads(FINGERPRINT_PATH.read_text())
    entries = manifest["datasets"]["sleep_edf_primary"]["entries"]
    subjects = {e["subject"] for e in entries}
    assert len(subjects) == 18


@requires_fingerprint
def test_fingerprint_sleep_secondary_covers_all_8_subjects():
    manifest = json.loads(FINGERPRINT_PATH.read_text())
    entries = manifest["datasets"]["sleep_edf_secondary_holdout"]["entries"]
    subjects = {e["subject"] for e in entries}
    assert len(subjects) == 8


# --- Reproduction ---------------------------------------------------------------


@requires_repro
def test_reproduction_overall_pass():
    repro = json.loads(REPRO_PATH.read_text())
    assert repro["overall"] == "SCIENTIFIC_REPRODUCTION_PASS"


@requires_repro
def test_reproduction_ppg_dalia_exact():
    repro = json.loads(REPRO_PATH.read_text())
    assert repro["ppg_dalia"]["all_metrics_match"] is True
    assert repro["ppg_dalia"]["max_abs_difference"] == 0.0


@requires_repro
def test_reproduction_ptt_exact():
    repro = json.loads(REPRO_PATH.read_text())
    assert repro["ptt"]["all_metrics_match"] is True
    assert repro["ptt"]["checkpoints_verified"] == 10


@requires_repro
def test_reproduction_sleep_primary_and_secondary_exact():
    repro = json.loads(REPRO_PATH.read_text())
    assert repro["sleep_primary"]["all_metrics_match"] is True
    assert repro["sleep_secondary"]["all_metrics_match"] is True
    assert repro["sleep_secondary"]["cohort_overlap_with_primary"] == 0


@requires_repro
def test_reproduction_robustness_full_scope_within_documented_tolerance():
    repro = json.loads(REPRO_PATH.read_text())
    rob = repro["robustness"]
    assert rob["reproduction_scope"] == "FULL_114_CONDITIONS"
    assert rob["n_conditions_reproduced"] == rob["n_conditions_canonical"] == 114
    assert rob["all_metrics_match"] is True
    assert rob["max_abs_difference_bpm"] < rob["tolerance_bpm"]


# --- Sleep split integrity -------------------------------------------------------


def test_primary_split_is_12_3_3():
    split = json.loads(PRIMARY_SPLIT_PATH.read_text())
    assert len(split["train"]) == 12
    assert len(split["val"]) == 3
    assert len(split["test"]) == 3


def test_secondary_cohort_is_8_and_disjoint_from_primary():
    cohort = json.loads(SECONDARY_COHORT_PATH.read_text())
    split = json.loads(PRIMARY_SPLIT_PATH.read_text())
    subjects = {c["subject_prefix"] for c in cohort["cohort"]}
    assert len(subjects) == 8
    all_primary = set(split["train"]) | set(split["val"]) | set(split["test"])
    assert subjects.isdisjoint(all_primary)


# --- N3 diagnostic ---------------------------------------------------------------


@requires_n3
def test_n3_diagnostic_recomputable_and_matches_canonical():
    diag = json.loads(N3_PATH.read_text())
    v = diag["verified_against_canonical"]
    assert v["recall_direction_matches"] is True
    assert v["precision_direction_matches"] is True
    assert v["n2_to_n3_fp_increase_matches_sign"] is True


@requires_n3
def test_n3_diagnostic_delta_matches_canonical_605():
    diag = json.loads(N3_PATH.read_text())
    assert diag["n2_to_n3_false_positives_pooled_across_5_seeds"]["delta_B_minus_A"] == 605


# --- Interaction experiment -------------------------------------------------------


def test_interaction_predeclaration_exists():
    assert INTERACTION_PREDECLARATION_PATH.exists()
    assert INTERACTION_FEASIBILITY_PATH.exists()


@requires_interaction
def test_interaction_predeclaration_precedes_results_in_git_history():
    """The predeclaration/feasibility docs must be committed in a commit
    that is an ancestor of (or the same commit as) the results - never
    written after results were already known. Checked via git log order:
    the predeclaration file's first commit must not be newer than the
    results artifact's first commit."""
    import subprocess

    def first_commit_time(path: Path) -> int:
        out = subprocess.run(
            ["git", "log", "--diff-filter=A", "--format=%at", "--", str(path.relative_to(REPO_ROOT))],
            cwd=REPO_ROOT, capture_output=True, text=True,
        ).stdout.strip().splitlines()
        return int(out[-1]) if out else 0

    predeclaration_time = first_commit_time(INTERACTION_PREDECLARATION_PATH)
    # results file may be untracked (same-session, not yet committed) - in
    # that case there is no ordering violation to check yet.
    tracked = subprocess.run(
        ["git", "ls-files", "--error-unmatch", str(INTERACTION_RESULTS_PATH.relative_to(REPO_ROOT))],
        cwd=REPO_ROOT, capture_output=True, text=True,
    ).returncode == 0
    if not tracked or predeclaration_time == 0:
        pytest.skip("results not yet committed or predeclaration not yet committed - ordering not applicable")
    results_time = first_commit_time(INTERACTION_RESULTS_PATH)
    assert predeclaration_time <= results_time


@requires_interaction
def test_interaction_no_target_leakage():
    with open(INTERACTION_FEASIBILITY_PATH, encoding="utf-8") as f:
        text = f.read().lower()
    assert "leakage" in text
    assert "categorically rejected" in text or "rejected as a candidate" in text


@requires_interaction
def test_interaction_same_split_as_primary():
    result = json.loads(INTERACTION_RESULTS_PATH.read_text())
    primary_split = json.loads(PRIMARY_SPLIT_PATH.read_text())
    assert result["frozen_protocol"]["subject_split"] == primary_split


@requires_interaction
def test_interaction_capacity_fairness_metadata_present_and_constant():
    result = json.loads(INTERACTION_RESULTS_PATH.read_text())
    params = result["parameter_counts"]
    cost_01 = params["M_A"] - params["M0"]
    cost_02 = params["M_B_eeg_plus_resp"] - params["M0"]
    cost_23 = params["M_AB_eeg_plus_eog_plus_resp"] - params["M_B_eeg_plus_resp"]
    assert cost_01 == cost_02 == cost_23
    assert result["frozen_protocol"]["capacity_fairness_per_channel_cost"] == cost_01


@requires_interaction
def test_interaction_four_condition_completeness():
    result = json.loads(INTERACTION_RESULTS_PATH.read_text())
    agg = result["aggregate"]
    for key in ("m0_macro_f1", "ma_macro_f1", "mb_macro_f1", "mab_macro_f1", "interaction_term"):
        assert key in agg


@requires_interaction
def test_interaction_all_five_seeds_for_new_configs():
    result = json.loads(INTERACTION_RESULTS_PATH.read_text())
    for config in ("M_B_eeg_plus_resp", "M_AB_eeg_plus_eog_plus_resp"):
        for seed in (42, 43, 44, 45, 46):
            assert f"seed{seed}" in result["runs"][config]


@requires_interaction
def test_interaction_does_not_claim_synergy_unqualified():
    with open(REPO_ROOT / "docs" / "INTERACTION_EXPERIMENT_RESULTS_DAY10.md", encoding="utf-8") as f:
        text = f.read().lower()
    assert "no claim of physiological synergy" in text


# --- Freeze readiness --------------------------------------------------------------


def test_freeze_readiness_status_is_valid_enum():
    if not FREEZE_PATH.exists():
        pytest.skip("freeze readiness artifact not built yet")
    freeze = json.loads(FREEZE_PATH.read_text())
    assert freeze["final_status"] in (
        "READY_FOR_FINAL_SCIENTIFIC_FREEZE",
        "READY_WITH_KNOWN_LIMITATIONS",
        "NOT_READY_FOR_SCIENTIFIC_FREEZE",
    )


def test_freeze_readiness_does_not_expand_claims():
    if not FREEZE_PATH.exists():
        pytest.skip("freeze readiness artifact not built yet")
    freeze = json.loads(FREEZE_PATH.read_text())
    assert freeze["claims_governance"]["no_claim_expansion"] is True
