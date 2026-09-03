"""Tests for the full overnight PTT PPG site-value HR ablation - the
integrity guarantees the Day 3+overnight master prompts require around the
frozen split, the trained checkpoints, and the result artifacts.

All tests here are skipped (with a clear reason) if the corresponding
artifact does not exist locally yet - they are meant to run AFTER
`ml/train_ptt_ppg_site_ablation.py`'s full `main()` has produced
`results/ptt_ppg_site_ablation.json` and the dataset audit scripts have
produced their reports.
"""

from __future__ import annotations

import hashlib
import inspect
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "backend"))

RESULTS_PATH = REPO_ROOT / "results" / "ptt_ppg_site_ablation.json"
FULL_AUDIT_PATH = REPO_ROOT / "datasets" / "pulse-transit-time-ppg" / "download_log" / "full_audit_report.json"
CHECKSUM_PATH = REPO_ROOT / "datasets" / "pulse-transit-time-ppg" / "download_log" / "checksum_report.json"
WINDOW_ACCOUNTING_PATH = REPO_ROOT / "datasets" / "pulse-transit-time-ppg" / "download_log" / "window_accounting.json"
REPRODUCIBILITY_PATH = REPO_ROOT / "results" / "ptt_ppg_site_ablation_reproducibility.json"

requires_results = pytest.mark.skipif(not RESULTS_PATH.exists(), reason=f"{RESULTS_PATH} not present - run the full ablation first")
requires_full_audit = pytest.mark.skipif(not FULL_AUDIT_PATH.exists(), reason=f"{FULL_AUDIT_PATH} not present - run ml/audit_ptt_dataset.py first")
requires_window_accounting = pytest.mark.skipif(not WINDOW_ACCOUNTING_PATH.exists(), reason=f"{WINDOW_ACCOUNTING_PATH} not present - run ml/preprocess_ptt.py first")
requires_reproducibility = pytest.mark.skipif(not REPRODUCIBILITY_PATH.exists(), reason=f"{REPRODUCIBILITY_PATH} not present - run ml/verify_ptt_reproducibility.py first")


# --- 15/16: all 66 record identities, no silent omission -------------------


@requires_full_audit
def test_all_66_records_present_in_full_audit():
    report = json.loads(FULL_AUDIT_PATH.read_text())
    assert report["summary"]["total_records"] == 66
    assert len(report["records"]) == 66


@requires_full_audit
def test_full_audit_reports_zero_load_failures():
    report = json.loads(FULL_AUDIT_PATH.read_text())
    assert report["summary"]["load_failed"] == 0, f"records failed to load: {[k for k, v in report['records'].items() if v['status'] == 'LOAD_FAILED']}"


@requires_full_audit
def test_full_audit_all_records_ok_or_documented_anomaly():
    report = json.loads(FULL_AUDIT_PATH.read_text())
    # every record must be accounted for as OK or an explicitly logged anomaly - never silently missing from the report
    assert report["summary"]["ok"] + report["summary"]["anomaly"] + report["summary"]["load_failed"] == 66


@requires_window_accounting
def test_window_accounting_covers_all_66_records():
    accounting = json.loads(WINDOW_ACCOUNTING_PATH.read_text())
    assert len(accounting) == 66


# --- 9/10: per-subject and per-activity accounting --------------------------


@requires_window_accounting
def test_window_accounting_per_subject_and_activity_sums_are_consistent():
    from ml.datasets.pulse_transit_time_ppg import ACTIVITIES, ALL_SUBJECTS

    accounting = json.loads(WINDOW_ACCOUNTING_PATH.read_text())
    for subject_id in ALL_SUBJECTS:
        for activity in ACTIVITIES:
            key = f"{subject_id}_{activity}"
            assert key in accounting, f"missing accounting entry for {key}"
            entry = accounting[key]
            assert entry["n_valid_windows"] + entry["n_dropped_windows"] == entry["n_candidate_windows"]


# --- Checksum integrity -------------------------------------------------


@pytest.mark.skipif(not CHECKSUM_PATH.exists(), reason=f"{CHECKSUM_PATH} not present")
def test_checksum_report_no_missing_or_mismatch():
    report = json.loads(CHECKSUM_PATH.read_text())
    assert report["summary"]["missing"] == 0, "one or more expected record files are missing locally"
    assert report["summary"]["mismatch"] == 0, "one or more record files do not match the official SHA256SUMS"


# --- 1-6: split/channel/target integrity from results.json -----------------


@requires_results
def test_results_subject_split_matches_frozen_file():
    results = json.loads(RESULTS_PATH.read_text())
    frozen_split = json.loads((REPO_ROOT / "ml" / "experiments" / "ptt_ppg_site_ablation" / "subject_split.json").read_text())
    assert results["subject_split"] == frozen_split


@requires_results
def test_results_no_subject_leakage():
    results = json.loads(RESULTS_PATH.read_text())
    split = results["subject_split"]
    train, val, test = set(split["train"]), set(split["val"]), set(split["test"])
    assert not (train & val) and not (train & test) and not (val & test)


@requires_results
def test_results_model_a_and_b_have_same_window_counts_per_seed():
    results = json.loads(RESULTS_PATH.read_text())
    for seed_key in results["runs"]["a"]:
        n_a = results["runs"]["a"][seed_key]["overall"]["n_windows"]
        n_b = results["runs"]["b"][seed_key]["overall"]["n_windows"]
        assert n_a == n_b, f"{seed_key}: Model A evaluated on {n_a} windows, Model B on {n_b} - must be identical"


@requires_results
def test_results_model_a_in_channels_is_3_and_b_is_6():
    results = json.loads(RESULTS_PATH.read_text())
    for seed_key, report in results["runs"]["a"].items():
        assert report["in_channels"] == 3
    for seed_key, report in results["runs"]["b"].items():
        assert report["in_channels"] == 6


# --- 11: validation-only checkpoint selection -------------------------------


def test_train_function_does_not_accept_test_data_argument():
    """Structural guarantee that the training loop cannot be handed the test
    set: `train_model_with_early_stopping`'s signature only has train/val
    data parameters."""

    from ml.train_ptt_ppg_site_ablation import train_model_with_early_stopping

    sig = inspect.signature(train_model_with_early_stopping)
    params = list(sig.parameters)
    assert "train_data" in params and "val_data" in params
    assert not any("test" in p.lower() for p in params)


@requires_results
def test_checkpoint_selection_uses_best_val_mae_not_final_epoch():
    results = json.loads(RESULTS_PATH.read_text())
    for model_key in ("a", "b"):
        for seed_key, report in results["runs"][model_key].items():
            history = report["train_history"]
            best_epoch = report["best_epoch"]
            best_val_mae_recorded = report["best_val_mae"]
            val_maes_by_epoch = {h["epoch"]: h["val_mae"] for h in history}
            assert val_maes_by_epoch[best_epoch] == pytest.approx(best_val_mae_recorded, abs=1e-6)
            assert best_val_mae_recorded == pytest.approx(min(h["val_mae"] for h in history), abs=1e-6)


# --- 13/14: result serialization and checkpoint identity --------------------


@requires_results
def test_results_json_has_required_top_level_keys():
    results = json.loads(RESULTS_PATH.read_text())
    for key in ("config", "subject_split", "hr_normalization", "training_hyperparameters", "runs", "aggregate", "checkpoint_manifest"):
        assert key in results


@requires_results
def test_checkpoint_manifest_sha256_matches_actual_files():
    results = json.loads(RESULTS_PATH.read_text())
    for entry in results["checkpoint_manifest"]:
        ckpt_path = REPO_ROOT / entry["path"]
        assert ckpt_path.exists(), f"checkpoint missing: {ckpt_path}"
        actual_sha = hashlib.sha256(ckpt_path.read_bytes()).hexdigest()
        assert actual_sha == entry["sha256"], f"checkpoint {ckpt_path} sha256 mismatch"


@requires_results
def test_checkpoint_manifest_has_all_10_runs():
    results = json.loads(RESULTS_PATH.read_text())
    assert len(results["checkpoint_manifest"]) == 10  # 2 models x 5 seeds


# --- Reproducibility ------------------------------------------------------


@requires_reproducibility
def test_reproducibility_all_checkpoints_ok():
    report = json.loads(REPRODUCIBILITY_PATH.read_text())
    assert report["all_ok"] is True, f"reproducibility mismatches: {[r for r in report['runs'] if not r['ok']]}"


# --- No target leakage: sanity check that predictions are not the target ---


@requires_results
def test_no_suspiciously_perfect_held_out_accuracy():
    """A near-zero held-out MAE would indicate target leakage - fail loudly
    rather than silently celebrate it."""

    results = json.loads(RESULTS_PATH.read_text())
    for model_key in ("a", "b"):
        for seed_key, report in results["runs"][model_key].items():
            assert report["overall"]["mae"] > 0.5, (
                f"{model_key}/{seed_key}: held-out MAE {report['overall']['mae']} bpm is suspiciously low - investigate leakage before trusting this result"
            )
