#!/usr/bin/env python
"""Sleep-EDF prospective secondary-holdout evaluation (Day 9).

See docs/SLEEP_EDF_SECONDARY_HOLDOUT_PREDECLARATION.md for the full frozen
protocol, written and committed BEFORE this script produced any result and
before the cohort's raw files were even downloaded.

Evaluation-only: loads the 3x5 existing frozen checkpoints from the Day 7/8
Sleep-EDF experiments (A = EEG-only, B = EEG+aligned EOG, C = EEG+shuffled
EOG) and reruns them on n=8 genuinely untouched subjects (SC4181, SC4191,
SC4201, SC4211, SC4221, SC4231, SC4241, SC4251 - PhysioNet Sleep-EDFx
subject indices 18-25, never in primary train/val/test). No retraining, no
tuning, all 5 seeds (42-46) used unconditionally.

Does NOT modify, re-run, or overwrite the primary frozen test result
(results/sleep_edf_eeg_eog_ablation.json,
results/sleep_edf_eeg_eog_control_analysis.json).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "backend"))
sys.path.insert(0, str(REPO_ROOT))

from app.ml._torch_bootstrap import ensure_torch_dll_path  # noqa: E402

ensure_torch_dll_path()

import torch  # noqa: E402

torch.set_num_threads(4)

from ml.datasets.sleep_edf import (  # noqa: E402
    EEG_CHANNEL,
    EOG_CHANNEL,
    STAGE_NAMES,
    load_dataset_windows_multi,
    shuffle_eog_within_subject,
)
from ml.train_sleep_edf_eeg_eog_ablation import SleepStageClassifier, evaluate_full  # noqa: E402

RAW_DIR = REPO_ROOT / "datasets" / "sleep-edfx" / "raw"
COHORT_PATH = REPO_ROOT / "ml" / "experiments" / "sleep_edf_secondary_holdout" / "cohort.json"
CKPT_DIR = REPO_ROOT / "ml" / "checkpoints"
OUT_PATH = REPO_ROOT / "results" / "sleep_edf_secondary_holdout_evaluation.json"

CHANNELS_A = (EEG_CHANNEL,)
CHANNELS_BC = (EEG_CHANNEL, EOG_CHANNEL)
EOG_CHANNEL_INDEX = 1
SEEDS = (42, 43, 44, 45, 46)


def agg(values: list[float]) -> dict:
    arr = np.asarray(values, dtype=np.float64)
    return {
        "mean": float(arr.mean()),
        "sd_sample_ddof1": float(arr.std(ddof=1)) if len(arr) > 1 else None,
        "per_seed": dict(zip((f"seed{s}" for s in SEEDS), values)),
    }


def load_model(ckpt_name: str, in_channels: int) -> torch.nn.Module:
    model = SleepStageClassifier(in_channels=in_channels)
    state = torch.load(CKPT_DIR / ckpt_name, map_location="cpu")
    model.load_state_dict(state)
    model.eval()
    return model


def main() -> None:
    cohort = json.loads(COHORT_PATH.read_text())
    subject_ids = [c["subject_prefix"] for c in cohort["cohort"]]
    print("Frozen secondary-holdout cohort:", subject_ids)

    # Verify no overlap with primary split (hard integrity check, not a metric).
    primary_all = set(cohort["primary_train_subjects"] + cohort["primary_val_subjects"] + cohort["primary_test_subjects"])
    overlap = primary_all & set(subject_ids)
    if overlap:
        raise RuntimeError(f"Secondary cohort overlaps primary split: {overlap}")
    assert len(subject_ids) == len(set(subject_ids)) == cohort["cohort_size"]

    print("Loading real data (EEG-only view for Model A)...")
    x_a, y_a, subj_a, prefixes_a = load_dataset_windows_multi(RAW_DIR, channels=CHANNELS_A, subject_ids=subject_ids)
    print("Loading real data (EEG+EOG view for Models B/C)...")
    x_bc, y_bc, subj_bc, prefixes_bc = load_dataset_windows_multi(RAW_DIR, channels=CHANNELS_BC, subject_ids=subject_ids)

    assert prefixes_a == prefixes_bc
    assert np.array_equal(y_a, y_bc), "label arrays must match exactly between channel views"
    print(f"Total secondary-holdout epochs: {len(y_a)} across {len(subject_ids)} subjects")

    def prefixes_for(subj_idx: np.ndarray) -> list[str]:
        return [prefixes_a[i] for i in subj_idx]

    epoch_subject_a = prefixes_for(subj_a)
    epoch_subject_bc = prefixes_for(subj_bc)

    out: dict = {
        "experiment_id": "sleep_edf_secondary_holdout_evaluation",
        "predeclaration": "docs/SLEEP_EDF_SECONDARY_HOLDOUT_PREDECLARATION.md",
        "cohort_file": "ml/experiments/sleep_edf_secondary_holdout/cohort.json",
        "primary_frozen_test_reference": "results/sleep_edf_eeg_eog_ablation.json (unmodified)",
        "primary_control_reference": "results/sleep_edf_eeg_eog_control_analysis.json (unmodified)",
        "cohort_subjects": subject_ids,
        "cohort_size": len(subject_ids),
        "no_retraining": True,
        "no_tuning": True,
        "seeds": list(SEEDS),
        "total_epochs": int(len(y_a)),
        "per_seed": {},
    }

    per_subject_by_seed: dict[str, dict[str, dict]] = {s: {} for s in subject_ids}

    for seed in SEEDS:
        print(f"\n=== seed {seed} ===")
        model_a = load_model(f"sleep_edf_baseline_eeg_only_seed{seed}.pt", in_channels=1)
        model_b = load_model(f"sleep_edf_candidate_eeg_plus_eog_seed{seed}.pt", in_channels=2)
        model_c = load_model(f"sleep_edf_model_c_shuffled_eog_seed{seed}.pt", in_channels=2)

        shuffled_x_bc = shuffle_eog_within_subject(x_bc, subj_bc, EOG_CHANNEL_INDEX, seed=seed)

        report_a = evaluate_full(model_a, x_a, y_a)
        report_b = evaluate_full(model_b, x_bc, y_bc)
        report_c = evaluate_full(model_c, shuffled_x_bc, y_bc)

        out["per_seed"][f"seed{seed}"] = {"A": report_a, "B": report_b, "C": report_c}
        print(f"seed {seed}: A={report_a['macro_f1']:.4f} B={report_b['macro_f1']:.4f} C={report_c['macro_f1']:.4f}")

        for subj in subject_ids:
            mask_a = np.array([p == subj for p in epoch_subject_a])
            mask_bc = np.array([p == subj for p in epoch_subject_bc])
            if mask_a.sum() == 0:
                continue
            r_a = evaluate_full(model_a, x_a[mask_a], y_a[mask_a])
            r_b = evaluate_full(model_b, x_bc[mask_bc], y_bc[mask_bc])
            r_c = evaluate_full(model_c, shuffled_x_bc[mask_bc], y_bc[mask_bc])
            per_subject_by_seed[subj][f"seed{seed}"] = {
                "A_macro_f1": r_a["macro_f1"], "B_macro_f1": r_b["macro_f1"], "C_macro_f1": r_c["macro_f1"],
                "A_balanced_accuracy": r_a["balanced_accuracy"], "B_balanced_accuracy": r_b["balanced_accuracy"], "C_balanced_accuracy": r_c["balanced_accuracy"],
                "A_per_class_f1": r_a["per_class_f1"], "B_per_class_f1": r_b["per_class_f1"], "C_per_class_f1": r_c["per_class_f1"],
                "n_epochs": r_a["n_epochs_eval"],
            }

    # --- Aggregate over seeds ------------------------------------------------
    a_f1 = [out["per_seed"][f"seed{s}"]["A"]["macro_f1"] for s in SEEDS]
    b_f1 = [out["per_seed"][f"seed{s}"]["B"]["macro_f1"] for s in SEEDS]
    c_f1 = [out["per_seed"][f"seed{s}"]["C"]["macro_f1"] for s in SEEDS]
    a_ba = [out["per_seed"][f"seed{s}"]["A"]["balanced_accuracy"] for s in SEEDS]
    b_ba = [out["per_seed"][f"seed{s}"]["B"]["balanced_accuracy"] for s in SEEDS]
    c_ba = [out["per_seed"][f"seed{s}"]["C"]["balanced_accuracy"] for s in SEEDS]

    a_to_b = [b - a for a, b in zip(a_f1, b_f1)]
    a_to_c = [c - a for a, c in zip(a_f1, c_f1)]
    c_to_b = [b - c for c, b in zip(c_f1, b_f1)]

    out["aggregate"] = {
        "model_a_macro_f1": agg(a_f1),
        "model_b_macro_f1": agg(b_f1),
        "model_c_macro_f1": agg(c_f1),
        "model_a_balanced_accuracy": agg(a_ba),
        "model_b_balanced_accuracy": agg(b_ba),
        "model_c_balanced_accuracy": agg(c_ba),
        "A_to_B": {**agg(a_to_b), "n_seeds_favor_B": sum(1 for d in a_to_b if d > 0), "n_seeds_total": len(SEEDS)},
        "A_to_C": {**agg(a_to_c), "n_seeds_favor_C": sum(1 for d in a_to_c if d > 0), "n_seeds_total": len(SEEDS)},
        "C_to_B": {**agg(c_to_b), "n_seeds_favor_B": sum(1 for d in c_to_b if d > 0), "n_seeds_total": len(SEEDS)},
    }

    # --- Class-level aggregate (mean per-class F1 across seeds, pooled cohort) ---
    class_level = {}
    for stage in STAGE_NAMES:
        a_vals = [out["per_seed"][f"seed{s}"]["A"]["per_class_f1"][stage] for s in SEEDS]
        b_vals = [out["per_seed"][f"seed{s}"]["B"]["per_class_f1"][stage] for s in SEEDS]
        c_vals = [out["per_seed"][f"seed{s}"]["C"]["per_class_f1"][stage] for s in SEEDS]
        class_level[stage] = {
            "A_mean_f1": float(np.mean(a_vals)), "B_mean_f1": float(np.mean(b_vals)), "C_mean_f1": float(np.mean(c_vals)),
            "B_minus_A": float(np.mean(b_vals) - np.mean(a_vals)), "B_minus_C": float(np.mean(b_vals) - np.mean(c_vals)),
        }
    out["class_level_aggregate"] = class_level

    # --- Subject-level summary (mean over 5 seeds per subject) --------------
    subject_summary = {}
    for subj in subject_ids:
        seeds_data = per_subject_by_seed[subj]
        a_vals = [seeds_data[f"seed{s}"]["A_macro_f1"] for s in SEEDS]
        b_vals = [seeds_data[f"seed{s}"]["B_macro_f1"] for s in SEEDS]
        c_vals = [seeds_data[f"seed{s}"]["C_macro_f1"] for s in SEEDS]
        b_minus_a = [b - a for a, b in zip(a_vals, b_vals)]
        c_minus_a = [c - a for a, c in zip(a_vals, c_vals)]
        b_minus_c = [b - c for c, b in zip(c_vals, b_vals)]
        n_epochs = seeds_data["seed42"]["n_epochs"]
        subject_summary[subj] = {
            "n_epochs": n_epochs,
            "A_macro_f1_mean": float(np.mean(a_vals)),
            "B_macro_f1_mean": float(np.mean(b_vals)),
            "C_macro_f1_mean": float(np.mean(c_vals)),
            "B_minus_A_mean": float(np.mean(b_minus_a)),
            "C_minus_A_mean": float(np.mean(c_minus_a)),
            "B_minus_C_mean": float(np.mean(b_minus_c)),
            "n_seeds_favor_B_over_A": sum(1 for d in b_minus_a if d > 0),
            "n_seeds_favor_B_over_C": sum(1 for d in b_minus_c if d > 0),
            "per_seed": seeds_data,
        }
    out["per_subject"] = subject_summary

    n_subjects_b_gt_a = sum(1 for s in subject_summary.values() if s["B_minus_A_mean"] > 0)
    n_subjects_b_gt_c = sum(1 for s in subject_summary.values() if s["B_minus_C_mean"] > 0)
    n_subjects_b_wins_both = sum(1 for s in subject_summary.values() if s["B_minus_A_mean"] > 0 and s["B_minus_C_mean"] > 0)
    deltas_b_minus_a = [s["B_minus_A_mean"] for s in subject_summary.values()]
    dominant_subject = max(subject_summary.items(), key=lambda kv: abs(kv[1]["B_minus_A_mean"]))[0]
    total_effect = sum(deltas_b_minus_a)
    dominant_share = subject_summary[dominant_subject]["B_minus_A_mean"] / total_effect if total_effect != 0 else None

    out["subject_level_generalization_summary"] = {
        "n_subjects_total": len(subject_ids),
        "n_subjects_B_greater_than_A": n_subjects_b_gt_a,
        "n_subjects_B_greater_than_C": n_subjects_b_gt_c,
        "n_subjects_B_wins_both": n_subjects_b_wins_both,
        "distribution_of_B_minus_A_deltas": deltas_b_minus_a,
        "dominant_subject_by_abs_effect": dominant_subject,
        "dominant_subject_share_of_summed_effect": dominant_share,
        "single_subject_dominance_flag": (dominant_share is not None and abs(dominant_share) > 0.5),
    }

    OUT_PATH.write_text(json.dumps(out, indent=2))
    print("\nWrote", OUT_PATH)
    print("Aggregate:", json.dumps(out["aggregate"], indent=2))
    print("Subject-level summary:", json.dumps(out["subject_level_generalization_summary"], indent=2, default=str))


if __name__ == "__main__":
    main()
