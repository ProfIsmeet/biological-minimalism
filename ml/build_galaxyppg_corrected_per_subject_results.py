#!/usr/bin/env python
"""Re-evaluates the 15 already-trained GalaxyPPG checkpoints per test
subject (4 subjects), without retraining - fast, checkpoint-based
evaluation only."""

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

from ml.datasets.galaxyppg import build_participant_windows  # noqa: E402
from ml.train_galaxyppg_corrected_eligibility import (  # noqa: E402
    CKPT_DIR,
    DATA_DIR,
    PPGCapacityMatchedModel,
    PPGPlusIMUModel,
    SEEDS,
    SPLIT_PATH,
)

RESULT_PATH = REPO_ROOT / "results" / "galaxyppg_hr_corrected_eligibility_stage3.json"


def main() -> None:
    split = json.loads(SPLIT_PATH.read_text())
    result = json.loads(RESULT_PATH.read_text())
    hr_mean = result["hr_normalization"]["mean"]
    hr_std = result["hr_normalization"]["std"]

    per_subject_test = {}
    for pid in split["test"]:
        w = build_participant_windows(DATA_DIR, pid)
        per_subject_test[pid] = w
        print(pid, "n_windows", len(w["hr"]))

    per_subject_results = {name: {pid: {} for pid in split["test"]} for name in ("A_cap", "B", "C")}

    for seed in SEEDS:
        model_a = PPGCapacityMatchedModel()
        model_a.load_state_dict(torch.load(CKPT_DIR / f"galaxyppg_hr_corrected_A_cap_seed{seed}.pt", map_location="cpu"))
        model_a.eval()
        model_b = PPGPlusIMUModel()
        model_b.load_state_dict(torch.load(CKPT_DIR / f"galaxyppg_hr_corrected_B_seed{seed}.pt", map_location="cpu"))
        model_b.eval()
        model_c = PPGPlusIMUModel()
        model_c.load_state_dict(torch.load(CKPT_DIR / f"galaxyppg_hr_corrected_C_seed{seed}.pt", map_location="cpu"))
        model_c.eval()

        for pid, w in per_subject_test.items():
            bvp = torch.from_numpy(w["bvp_windows"]).unsqueeze(1)
            acc = torch.from_numpy(w["acc_windows"])
            hr_true = w["hr"]

            with torch.no_grad():
                pred_a = (model_a(bvp, bvp).numpy() * hr_std + hr_mean)
                pred_b = (model_b(bvp, acc).numpy() * hr_std + hr_mean)
                pred_c = (model_c(bvp, acc).numpy() * hr_std + hr_mean)

            per_subject_results["A_cap"][pid][f"seed{seed}"] = float(np.abs(pred_a - hr_true).mean())
            per_subject_results["B"][pid][f"seed{seed}"] = float(np.abs(pred_b - hr_true).mean())
            per_subject_results["C"][pid][f"seed{seed}"] = float(np.abs(pred_c - hr_true).mean())

    # Aggregate per subject (mean across 5 seeds) and A->B / C->B deltas
    summary = {}
    for pid in split["test"]:
        a_vals = list(per_subject_results["A_cap"][pid].values())
        b_vals = list(per_subject_results["B"][pid].values())
        c_vals = list(per_subject_results["C"][pid].values())
        summary[pid] = {
            "n_windows": len(per_subject_test[pid]["hr"]),
            "A_cap_mae_mean": float(np.mean(a_vals)),
            "B_mae_mean": float(np.mean(b_vals)),
            "C_mae_mean": float(np.mean(c_vals)),
            "A_to_B_mean": float(np.mean(a_vals) - np.mean(b_vals)),
            "C_to_B_mean": float(np.mean(c_vals) - np.mean(b_vals)),
        }

    out = {
        "purpose": "Per-subject GalaxyPPG re-evaluation of the 15 already-trained checkpoints (no retraining) - Section 66 requirement.",
        "per_subject_per_seed": per_subject_results,
        "per_subject_summary": summary,
    }
    out_path = REPO_ROOT / "results" / "galaxyppg_hr_corrected_per_subject_stage3.json"
    out_path.write_text(json.dumps(out, indent=2))
    print(json.dumps(summary, indent=2))
    print("Wrote", out_path)


if __name__ == "__main__":
    main()
