#!/usr/bin/env python
"""Reproducibility check for the 10 H1 seedfix_v2 checkpoints: independently
reload each from disk and confirm it reproduces its stored held-out
macro-F1."""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "backend"))
sys.path.insert(0, str(REPO_ROOT))

from app.ml._torch_bootstrap import ensure_torch_dll_path  # noqa: E402

ensure_torch_dll_path()

import torch  # noqa: E402

torch.set_num_threads(4)

from ml.datasets.sleep_edf import EEG_CHANNEL, EOG_CHANNEL, load_dataset_windows_multi  # noqa: E402
from ml.train_sleep_edf_eeg_eog_ablation import SleepStageClassifier, evaluate_full  # noqa: E402

RESULTS_PATH = REPO_ROOT / "results" / "sleep_edf_primary_seedfix_v2.json"
CKPT_DIR = REPO_ROOT / "ml" / "checkpoints"
OUT_PATH = REPO_ROOT / "results" / "sleep_edf_primary_seedfix_v2_reproducibility.json"
SEEDS = (42, 43, 44, 45, 46)


def main() -> None:
    data = json.loads(RESULTS_PATH.read_text())
    split = data["frozen_protocol"]["subject_split"]

    x_a, y_a, _subj, _pref = load_dataset_windows_multi(REPO_ROOT / "datasets" / "sleep-edfx" / "raw", channels=(EEG_CHANNEL,), subject_ids=split["test"])
    x_b, y_b, _subj2, _pref2 = load_dataset_windows_multi(REPO_ROOT / "datasets" / "sleep-edfx" / "raw", channels=(EEG_CHANNEL, EOG_CHANNEL), subject_ids=split["test"])

    results = []
    all_ok = True
    for seed in SEEDS:
        model_a = SleepStageClassifier(in_channels=1)
        model_a.load_state_dict(torch.load(CKPT_DIR / f"sleep_edf_baseline_eeg_only_seedfix_v2_seed{seed}.pt", map_location="cpu"))
        model_a.eval()
        model_b = SleepStageClassifier(in_channels=2)
        model_b.load_state_dict(torch.load(CKPT_DIR / f"sleep_edf_candidate_eeg_plus_eog_seedfix_v2_seed{seed}.pt", map_location="cpu"))
        model_b.eval()

        f1_a = evaluate_full(model_a, x_a, y_a)["macro_f1"]
        f1_b = evaluate_full(model_b, x_b, y_b)["macro_f1"]
        stored_a = data["runs"]["baseline_eeg_only"][f"seed{seed}"]["macro_f1"]
        stored_b = data["runs"]["candidate_eeg_plus_eog"][f"seed{seed}"]["macro_f1"]
        ok_a = f1_a == stored_a
        ok_b = f1_b == stored_b
        ok = ok_a and ok_b
        all_ok = all_ok and ok
        results.append({"seed": seed, "recomputed_A": f1_a, "stored_A": stored_a, "recomputed_B": f1_b, "stored_B": stored_b, "exact_match": ok})
        print(f"seed {seed}: exact_match={ok}")

    out = {"all_checkpoints_exact_match": all_ok, "n_checkpoints_checked": len(results) * 2, "results": results}
    OUT_PATH.write_text(json.dumps(out, indent=2))
    print("\nWrote", OUT_PATH)
    print("ALL OK" if all_ok else "MISMATCH DETECTED")


if __name__ == "__main__":
    main()
