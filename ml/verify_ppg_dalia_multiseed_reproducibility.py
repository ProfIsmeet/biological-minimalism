#!/usr/bin/env python
"""Reproducibility check for the Day 6 multi-seed replication: independently
reload each of the 15 saved checkpoints (from disk, not the in-memory
training object) and confirm each reproduces its stored held-out MAE/RMSE
from results/ppg_dalia_imu_multiseed_replication.json within tolerance.
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

from ml.datasets.ppg_dalia import load_cached_subjects  # noqa: E402
from ml.train_ppg_dalia_imu_ablation import (  # noqa: E402
    PPGOnlyHRModel,
    PPGPlusIMUHRModel,
    build_tensors,
    evaluate,
    mae,
    rmse,
    shuffle_imu_within_subject,
)

TOLERANCE_BPM = 1e-4


def main() -> None:
    results_path = REPO_ROOT / "results" / "ppg_dalia_imu_multiseed_replication.json"
    results = json.loads(results_path.read_text())
    split = results["frozen_protocol"]["subject_split"]
    hr_mean = results["frozen_protocol"]["hr_normalization"]["mean"]
    hr_std = results["frozen_protocol"]["hr_normalization"]["std"]
    cache_dir = REPO_ROOT / "datasets" / "ppg-dalia" / "processed"

    test_windows = load_cached_subjects(cache_dir, split["test"])
    test_data = build_tensors(test_windows)

    model_classes = {"a": PPGOnlyHRModel, "b": PPGPlusIMUHRModel, "c": PPGPlusIMUHRModel}

    all_ok = True
    report = []

    for entry in results["checkpoint_manifest"]:
        model_key = entry["model"]
        seed = entry["seed"]
        ckpt_path = REPO_ROOT / entry["path"]

        this_test = shuffle_imu_within_subject(test_data, seed=seed) if model_key == "c" else test_data

        model = model_classes[model_key](32)
        state_dict = torch.load(ckpt_path, map_location="cpu")
        model.load_state_dict(state_dict)
        model.eval()

        pred = evaluate(model, this_test, hr_mean, hr_std, "cpu")
        reproduced_mae = mae(pred, this_test["hr"].numpy())
        reproduced_rmse = rmse(pred, this_test["hr"].numpy())

        stored = results["runs"][model_key][f"seed{seed}"]["overall"]
        mae_diff = abs(reproduced_mae - stored["mae"])
        rmse_diff = abs(reproduced_rmse - stored["rmse"])
        ok = mae_diff < TOLERANCE_BPM and rmse_diff < TOLERANCE_BPM
        all_ok = all_ok and ok

        report.append({
            "run_id": entry["run_id"], "ok": ok,
            "stored_mae": stored["mae"], "reproduced_mae": reproduced_mae, "mae_diff": mae_diff,
            "stored_rmse": stored["rmse"], "reproduced_rmse": reproduced_rmse, "rmse_diff": rmse_diff,
        })
        print(f"{entry['run_id']}: {'OK' if ok else 'MISMATCH'} (dMAE={mae_diff:.2e}, dRMSE={rmse_diff:.2e})")

    out_path = REPO_ROOT / "results" / "ppg_dalia_imu_multiseed_replication_reproducibility.json"
    out_path.write_text(json.dumps({"tolerance_bpm": TOLERANCE_BPM, "all_ok": all_ok, "runs": report}, indent=2))
    print(f"\n{'ALL CHECKPOINTS REPRODUCED WITHIN TOLERANCE' if all_ok else 'REPRODUCIBILITY FAILURE - SEE REPORT'}")
    print("Wrote", out_path)
    if not all_ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
