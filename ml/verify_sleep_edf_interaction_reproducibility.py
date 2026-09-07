#!/usr/bin/env python
"""Reproducibility check for the 10 Day-10 interaction checkpoints (M_B, M_AB
x seeds 42-46): independently reload each from disk and confirm it
reproduces its stored held-out macro-F1."""

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

from ml.datasets.sleep_edf import load_dataset_windows_multi  # noqa: E402
from ml.train_sleep_edf_eeg_eog_ablation import SleepStageClassifier, evaluate_full  # noqa: E402
from ml.train_sleep_edf_interaction_resp import CONFIGS, RAW_DIR  # noqa: E402

RESULTS_PATH = REPO_ROOT / "results" / "sleep_edf_interaction_resp_day10.json"
CKPT_DIR = REPO_ROOT / "ml" / "checkpoints"
OUT_PATH = REPO_ROOT / "results" / "sleep_edf_interaction_resp_day10_reproducibility.json"
SEEDS = (42, 43, 44, 45, 46)


def main() -> None:
    data = json.loads(RESULTS_PATH.read_text())
    split = data["frozen_protocol"]["subject_split"]

    results = []
    all_ok = True
    for name, channels in CONFIGS.items():
        test_x, test_y, _subj, _pref = load_dataset_windows_multi(RAW_DIR, channels=channels, subject_ids=split["test"])
        for seed in SEEDS:
            run_id = f"{name}_seed{seed}"
            ckpt_path = CKPT_DIR / f"sleep_edf_interaction_{run_id}.pt"
            model = SleepStageClassifier(in_channels=len(channels))
            model.load_state_dict(torch.load(ckpt_path, map_location="cpu"))
            model.eval()
            report = evaluate_full(model, test_x, test_y)
            stored_f1 = data["runs"][name][f"seed{seed}"]["macro_f1"]
            ok = report["macro_f1"] == stored_f1
            all_ok = all_ok and ok
            results.append({"run_id": run_id, "recomputed_macro_f1": report["macro_f1"], "stored_macro_f1": stored_f1, "exact_match": ok})
            print(f"{run_id}: exact_match={ok}")

    out = {"all_checkpoints_exact_match": all_ok, "n_checkpoints_checked": len(results), "results": results}
    OUT_PATH.write_text(json.dumps(out, indent=2))
    print("\nWrote", OUT_PATH)
    print("ALL OK" if all_ok else "MISMATCH DETECTED")


if __name__ == "__main__":
    main()
