#!/usr/bin/env python
"""Sleep-EDF shuffled-EOG negative control (Day 8 mandatory strengthening).
See docs/SLEEP_EDF_SHUFFLED_EOG_PREDECLARATION.md for the full frozen
protocol, written BEFORE this script produced any result.

Model C: EEG + EOG-shuffled-within-subject-and-partition. Same
SleepStageClassifier(in_channels=2) class as Model B (identical
architecture/capacity by construction). Reuses Model A/B's existing
frozen checkpoints and results/sleep_edf_eeg_eog_ablation.json for
comparison - does not retrain A or B.
"""

from __future__ import annotations

import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "backend"))
sys.path.insert(0, str(REPO_ROOT))

from app.ml._torch_bootstrap import ensure_torch_dll_path  # noqa: E402

ensure_torch_dll_path()

import torch  # noqa: E402

torch.set_num_threads(4)

from sklearn.utils.class_weight import compute_class_weight  # noqa: E402

from ml.datasets.sleep_edf import (  # noqa: E402
    EEG_CHANNEL,
    EOG_CHANNEL,
    STAGE_NAMES,
    load_dataset_windows_multi,
    shuffle_eog_within_subject,
)
from ml.train_sleep_edf_eeg_eog_ablation import SleepStageClassifier, evaluate_full, train_one  # noqa: E402

RAW_DIR = REPO_ROOT / "datasets" / "sleep-edfx" / "raw"
EXPERIMENT_DIR = REPO_ROOT / "ml" / "experiments" / "sleep_edf_eeg_eog_ablation"
ORIGINAL_RESULTS_PATH = REPO_ROOT / "results" / "sleep_edf_eeg_eog_ablation.json"
OUT_PATH = REPO_ROOT / "results" / "sleep_edf_eeg_eog_control_analysis.json"
CKPT_DIR = REPO_ROOT / "ml" / "checkpoints"

CHANNELS = (EEG_CHANNEL, EOG_CHANNEL)
EOG_CHANNEL_INDEX = 1  # position of EOG within CHANNELS
SEEDS = (42, 43, 44, 45, 46)


def load_partition(subject_ids: list[str]) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    x, y, subj_idx, _prefixes = load_dataset_windows_multi(RAW_DIR, channels=CHANNELS, subject_ids=subject_ids)
    return x, y, subj_idx


def main() -> None:
    original = json.loads(ORIGINAL_RESULTS_PATH.read_text())
    split = original["frozen_protocol"]["subject_split"]
    print("Using FROZEN split:", json.dumps(split))

    print("Loading real data per partition (aligned copy, to be shuffled independently per-partition)...")
    train_x, train_y, train_subj = load_partition(split["train"])
    val_x, val_y, val_subj = load_partition(split["val"])
    test_x, test_y, test_subj = load_partition(split["test"])
    print(f"train={len(train_y)} val={len(val_y)} test={len(test_y)} epochs")

    class_weights_np = compute_class_weight("balanced", classes=np.arange(len(STAGE_NAMES)), y=train_y)
    class_weights = torch.tensor(class_weights_np, dtype=torch.float32)

    n_params = sum(p.numel() for p in SleepStageClassifier(in_channels=2).parameters())
    original_b_params = original["parameter_counts"]["candidate_eeg_plus_eog"]
    assert n_params == original_b_params, f"Model C params ({n_params}) must exactly match Model B ({original_b_params})"
    print(f"Model C params: {n_params} (matches Model B exactly: {original_b_params})")

    out: dict = {
        "experiment_id": "sleep_edf_shuffled_eog_control",
        "predeclaration": "docs/SLEEP_EDF_SHUFFLED_EOG_PREDECLARATION.md",
        "supplements": "results/sleep_edf_eeg_eog_ablation.json (A, B - not retrained, not overwritten)",
        "frozen_protocol": {
            "dataset": "PhysioNet Sleep-EDF (sleep-cassette)",
            "subject_split": split,
            "channels": list(CHANNELS),
            "shuffle_method": "EOG epochs permuted within-subject, within-partition only (see predeclaration)",
            "seeds": list(SEEDS),
            "n_parameters_model_c": n_params,
            "n_parameters_model_b_original": original_b_params,
            "capacity_identical_to_b": n_params == original_b_params,
        },
        "runs": {},
        "checkpoint_manifest": [],
    }

    for seed in SEEDS:
        run_id = f"model_c_shuffled_eog_seed{seed}"
        print(f"\n=== seed {seed}: training {run_id} ===")

        shuffled_train_x = shuffle_eog_within_subject(train_x, train_subj, EOG_CHANNEL_INDEX, seed=seed)
        shuffled_val_x = shuffle_eog_within_subject(val_x, val_subj, EOG_CHANNEL_INDEX, seed=seed)
        shuffled_test_x = shuffle_eog_within_subject(test_x, test_subj, EOG_CHANNEL_INDEX, seed=seed)

        model = SleepStageClassifier(in_channels=2)
        start = time.time()
        history = train_one(model, shuffled_train_x, train_y, shuffled_val_x, val_y, class_weights, seed)
        elapsed = time.time() - start

        report = evaluate_full(model, shuffled_test_x, test_y)
        report["train_seconds"] = elapsed
        report["train_history"] = history
        report["n_parameters"] = n_params
        report["seed"] = seed
        print(f"{run_id}: test macro-F1={report['macro_f1']:.4f} accuracy={report['accuracy']:.4f} ({elapsed:.1f}s)")

        out["runs"][f"seed{seed}"] = report

        ckpt_path = CKPT_DIR / f"sleep_edf_{run_id}.pt"
        torch.save(model.state_dict(), ckpt_path)
        ckpt_bytes = ckpt_path.read_bytes()
        out["checkpoint_manifest"].append({
            "run_id": run_id, "config": "shuffled_eog", "seed": seed, "in_channels": 2,
            "path": str(ckpt_path.relative_to(REPO_ROOT)),
            "size_bytes": len(ckpt_bytes), "sha256": hashlib.sha256(ckpt_bytes).hexdigest(),
            "n_parameters": n_params,
        })

        # --- Per-subject evaluation for this seed (shuffled test data, per subject) ---
        per_subject = {}
        for subj_name in split["test"]:
            mask = np.array([p == subj_name for p in _subject_prefixes_for(split["test"], test_subj)])
            x_s = shuffled_test_x[mask]
            y_s = test_y[mask]
            if len(y_s) == 0:
                continue
            r = evaluate_full(model, x_s, y_s)
            per_subject[subj_name] = {"macro_f1": r["macro_f1"], "balanced_accuracy": r["balanced_accuracy"], "n_epochs": r["n_epochs_eval"]}
        out["runs"][f"seed{seed}"]["per_subject"] = per_subject

    # --- Aggregate against original A/B (sample SD ddof=1) -----------------
    def agg(values: list[float]) -> dict:
        arr = np.asarray(values, dtype=np.float64)
        return {"mean": float(arr.mean()), "sd_sample_ddof1": float(arr.std(ddof=1)) if len(arr) > 1 else None, "per_seed": dict(zip((f"seed{s}" for s in SEEDS), values))}

    a_f1 = [original["runs"]["baseline_eeg_only"][f"seed{s}"]["macro_f1"] for s in SEEDS]
    b_f1 = [original["runs"]["candidate_eeg_plus_eog"][f"seed{s}"]["macro_f1"] for s in SEEDS]
    c_f1 = [out["runs"][f"seed{s}"]["macro_f1"] for s in SEEDS]

    a_to_b = [b - a for a, b in zip(a_f1, b_f1)]
    a_to_c = [c - a for a, c in zip(a_f1, c_f1)]
    c_to_b = [b - c for c, b in zip(c_f1, b_f1)]

    out["aggregate"] = {
        "model_a_macro_f1": agg(a_f1),
        "model_b_macro_f1": agg(b_f1),
        "model_c_macro_f1": agg(c_f1),
        "A_to_B": {**agg(a_to_b), "n_seeds_favor_B": sum(1 for d in a_to_b if d > 0), "n_seeds_total": len(SEEDS)},
        "A_to_C": {**agg(a_to_c), "n_seeds_favor_C": sum(1 for d in a_to_c if d > 0), "n_seeds_total": len(SEEDS)},
        "C_to_B": {**agg(c_to_b), "n_seeds_favor_B": sum(1 for d in c_to_b if d > 0), "n_seeds_total": len(SEEDS)},
    }

    OUT_PATH.write_text(json.dumps(out, indent=2))
    print("\nWrote", OUT_PATH)
    print("Aggregate:", json.dumps(out["aggregate"], indent=2))


def _subject_prefixes_for(subject_ids: list[str], subj_idx: np.ndarray) -> list[str]:
    """Maps each epoch's integer subject_idx back to its real subject
    prefix, using the same enumeration order load_dataset_windows_multi
    used (subject_ids filtered from the sorted directory listing, matched
    by that function's own internal find_subject_pairs() order)."""

    from ml.datasets.sleep_edf import find_subject_pairs

    pairs = find_subject_pairs(RAW_DIR)
    pairs = [(psg, hyp) for psg, hyp in pairs if psg.name.split("E")[0] in subject_ids]
    prefixes_in_order = [psg.name.split("E")[0] for psg, _ in pairs]
    return [prefixes_in_order[i] for i in subj_idx]


if __name__ == "__main__":
    main()
