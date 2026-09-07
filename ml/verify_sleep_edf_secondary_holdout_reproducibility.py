#!/usr/bin/env python
"""Reproducibility verification for the Day 9 secondary-holdout evaluation.

Reloads each of the 15 existing frozen checkpoints (A/B/C x 5 seeds) used by
ml/evaluate_sleep_edf_secondary_holdout.py, regenerates the same
deterministic within-subject EOG shuffle for Model C, re-evaluates on the
frozen secondary cohort, and confirms an EXACT macro-F1 match against the
stored results artifact. No training occurs here.
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

from ml.datasets.sleep_edf import EEG_CHANNEL, EOG_CHANNEL, load_dataset_windows_multi, shuffle_eog_within_subject  # noqa: E402
from ml.train_sleep_edf_eeg_eog_ablation import SleepStageClassifier, evaluate_full  # noqa: E402

RAW_DIR = REPO_ROOT / "datasets" / "sleep-edfx" / "raw"
COHORT_PATH = REPO_ROOT / "ml" / "experiments" / "sleep_edf_secondary_holdout" / "cohort.json"
RESULTS_PATH = REPO_ROOT / "results" / "sleep_edf_secondary_holdout_evaluation.json"
CKPT_DIR = REPO_ROOT / "ml" / "checkpoints"
OUT_PATH = REPO_ROOT / "results" / "sleep_edf_secondary_holdout_reproducibility.json"

SEEDS = (42, 43, 44, 45, 46)
EOG_CHANNEL_INDEX = 1


def load_model(ckpt_name: str, in_channels: int):
    model = SleepStageClassifier(in_channels=in_channels)
    model.load_state_dict(torch.load(CKPT_DIR / ckpt_name, map_location="cpu"))
    model.eval()
    return model


def main() -> None:
    cohort = json.loads(COHORT_PATH.read_text())
    subject_ids = [c["subject_prefix"] for c in cohort["cohort"]]
    stored = json.loads(RESULTS_PATH.read_text())

    x_a, y_a, _subj_a, _pref_a = load_dataset_windows_multi(RAW_DIR, channels=(EEG_CHANNEL,), subject_ids=subject_ids)
    x_bc, y_bc, subj_bc, _pref_bc = load_dataset_windows_multi(RAW_DIR, channels=(EEG_CHANNEL, EOG_CHANNEL), subject_ids=subject_ids)

    results = []
    all_ok = True
    for seed in SEEDS:
        model_a = load_model(f"sleep_edf_baseline_eeg_only_seed{seed}.pt", 1)
        model_b = load_model(f"sleep_edf_candidate_eeg_plus_eog_seed{seed}.pt", 2)
        model_c = load_model(f"sleep_edf_model_c_shuffled_eog_seed{seed}.pt", 2)
        shuffled_x_bc = shuffle_eog_within_subject(x_bc, subj_bc, EOG_CHANNEL_INDEX, seed=seed)

        f1_a = evaluate_full(model_a, x_a, y_a)["macro_f1"]
        f1_b = evaluate_full(model_b, x_bc, y_bc)["macro_f1"]
        f1_c = evaluate_full(model_c, shuffled_x_bc, y_bc)["macro_f1"]

        stored_seed = stored["per_seed"][f"seed{seed}"]
        ok_a = f1_a == stored_seed["A"]["macro_f1"]
        ok_b = f1_b == stored_seed["B"]["macro_f1"]
        ok_c = f1_c == stored_seed["C"]["macro_f1"]
        ok = ok_a and ok_b and ok_c
        all_ok = all_ok and ok
        results.append({"seed": seed, "recomputed_A": f1_a, "recomputed_B": f1_b, "recomputed_C": f1_c,
                         "stored_A": stored_seed["A"]["macro_f1"], "stored_B": stored_seed["B"]["macro_f1"], "stored_C": stored_seed["C"]["macro_f1"],
                         "exact_match": ok})
        print(f"seed {seed}: exact_match={ok}")

    out = {"all_seeds_exact_match": all_ok, "n_seeds_checked": len(SEEDS), "results": results}
    OUT_PATH.write_text(json.dumps(out, indent=2))
    print("\nWrote", OUT_PATH)
    print("ALL OK" if all_ok else "MISMATCH DETECTED")


if __name__ == "__main__":
    main()
