#!/usr/bin/env python
"""Sleep-EDF per-subject decomposition (Day 8 mandatory strengthening).
Uses ONLY the existing frozen checkpoints from
results/sleep_edf_eeg_eog_ablation.json - NO retraining. Reloads each of
the 10 checkpoints (2 configs x 5 seeds) and evaluates each of the 3
held-out test subjects INDIVIDUALLY (rather than pooled), to check
whether the aggregate result is dominated by one subject.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "backend"))

from app.ml._torch_bootstrap import ensure_torch_dll_path  # noqa: E402

ensure_torch_dll_path()

import torch  # noqa: E402

torch.set_num_threads(4)

from ml.datasets.sleep_edf import EEG_CHANNEL, EOG_CHANNEL, STAGE_NAMES, load_dataset_windows_multi  # noqa: E402
from ml.train_sleep_edf_eeg_eog_ablation import SleepStageClassifier, evaluate_full  # noqa: E402

RAW_DIR = REPO_ROOT / "datasets" / "sleep-edfx" / "raw"
RESULTS_PATH = REPO_ROOT / "results" / "sleep_edf_eeg_eog_ablation.json"
OUT_PATH = REPO_ROOT / "results" / "sleep_edf_per_subject_analysis.json"

CONFIGS = {"baseline_eeg_only": (EEG_CHANNEL,), "candidate_eeg_plus_eog": (EEG_CHANNEL, EOG_CHANNEL)}


def main() -> None:
    results = json.loads(RESULTS_PATH.read_text())
    split = results["frozen_protocol"]["subject_split"]
    test_subjects = split["test"]
    seeds = results["frozen_protocol"]["seeds"]

    # Load each test subject's data ONCE per config (not per seed - same data every seed)
    per_subject_data = {}
    for name, channels in CONFIGS.items():
        per_subject_data[name] = {}
        for subj in test_subjects:
            x, y, _idx, _prefixes = load_dataset_windows_multi(RAW_DIR, channels=channels, subject_ids=[subj])
            per_subject_data[name][subj] = (x, y)
            print(f"{name} / {subj}: {len(y)} epochs, label counts {dict(zip(STAGE_NAMES, np.bincount(y, minlength=5).tolist()))}")

    out: dict = {
        "experiment_id": "sleep_edf_per_subject_analysis",
        "label": "descriptive per-subject decomposition of the existing frozen Sleep-EDF result - no retraining",
        "source_artifact": "results/sleep_edf_eeg_eog_ablation.json",
        "test_subjects": test_subjects,
        "seeds": seeds,
        "per_subject": {s: {"baseline": {}, "candidate": {}} for s in test_subjects},
    }

    for name, channels in CONFIGS.items():
        for seed in seeds:
            entry = next(e for e in results["checkpoint_manifest"] if e["config"] == name and e["seed"] == seed)
            model = SleepStageClassifier(in_channels=entry["in_channels"])
            model.load_state_dict(torch.load(REPO_ROOT / entry["path"], map_location="cpu"))
            model.eval()

            for subj in test_subjects:
                x, y = per_subject_data[name][subj]
                report = evaluate_full(model, x, y)
                key = "baseline" if name == "baseline_eeg_only" else "candidate"
                out["per_subject"][subj][key][f"seed{seed}"] = {
                    "macro_f1": report["macro_f1"],
                    "accuracy": report["accuracy"],
                    "balanced_accuracy": report["balanced_accuracy"],
                    "per_class_f1": report["per_class_f1"],
                    "n_epochs": report["n_epochs_eval"],
                }
                print(f"{subj} {key} seed{seed}: macro-F1={report['macro_f1']:.4f}")

    # --- Aggregate per subject (sample SD ddof=1) --------------------------
    def agg(values: list[float]) -> dict:
        arr = np.asarray(values, dtype=np.float64)
        return {"mean": float(arr.mean()), "sd_sample_ddof1": float(arr.std(ddof=1)) if len(arr) > 1 else None, "per_seed": dict(zip((f"seed{s}" for s in seeds), values))}

    subject_summary = {}
    for subj in test_subjects:
        base_f1 = [out["per_subject"][subj]["baseline"][f"seed{s}"]["macro_f1"] for s in seeds]
        cand_f1 = [out["per_subject"][subj]["candidate"][f"seed{s}"]["macro_f1"] for s in seeds]
        deltas = [c - b for b, c in zip(base_f1, cand_f1)]
        n_favor = sum(1 for d in deltas if d > 0)
        subject_summary[subj] = {
            "n_epochs": out["per_subject"][subj]["baseline"]["seed42"]["n_epochs"],
            "baseline_macro_f1": agg(base_f1),
            "candidate_macro_f1": agg(cand_f1),
            "delta_candidate_minus_baseline": {**agg(deltas), "n_seeds_favor_candidate": n_favor, "n_seeds_total": len(seeds)},
            "direction": "IMPROVES" if n_favor >= 4 else ("WORSENS" if n_favor <= 1 else "MIXED"),
        }
    out["subject_summary"] = subject_summary

    # Dominant-subject check: recompute pooled aggregate excluding each subject
    dominant_check = {}
    for excluded in test_subjects:
        remaining = [s for s in test_subjects if s != excluded]
        base_pooled = np.mean([subject_summary[s]["baseline_macro_f1"]["mean"] for s in remaining])
        cand_pooled = np.mean([subject_summary[s]["candidate_macro_f1"]["mean"] for s in remaining])
        dominant_check[f"excluding_{excluded}"] = {"baseline_mean": float(base_pooled), "candidate_mean": float(cand_pooled), "delta": float(cand_pooled - base_pooled)}
    out["dominant_subject_check"] = dominant_check

    directions = [subject_summary[s]["direction"] for s in test_subjects]
    out["global_result_dominated_by_one_subject"] = len(set(directions)) > 1  # heterogeneous directions = at least one subject differs

    OUT_PATH.write_text(json.dumps(out, indent=2))
    print("\nWrote", OUT_PATH)
    for s in test_subjects:
        print(s, subject_summary[s]["direction"], subject_summary[s]["delta_candidate_minus_baseline"]["mean"])


if __name__ == "__main__":
    main()
