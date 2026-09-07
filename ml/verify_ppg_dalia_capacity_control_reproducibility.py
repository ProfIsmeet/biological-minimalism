#!/usr/bin/env python
"""Reproducibility check for the 5 A_cap checkpoints: independently reload
each from disk and confirm it reproduces its stored held-out MAE/RMSE."""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "backend"))

from app.ml._torch_bootstrap import ensure_torch_dll_path  # noqa: E402

ensure_torch_dll_path()

import torch  # noqa: E402

torch.set_num_threads(4)

from ml.datasets.ppg_dalia import load_cached_subjects  # noqa: E402
from ml.train_ppg_dalia_capacity_control import PPGCapacityMatchedModel  # noqa: E402
from ml.train_ppg_dalia_imu_ablation import build_tensors, evaluate, mae, rmse  # noqa: E402

TOLERANCE_BPM = 1e-4


def main() -> None:
    results_path = REPO_ROOT / "results" / "ppg_dalia_capacity_control.json"
    results = json.loads(results_path.read_text())
    split = results["frozen_protocol"]["subject_split"]
    hr_mean = results["frozen_protocol"]["hr_normalization"]["mean"]
    hr_std = results["frozen_protocol"]["hr_normalization"]["std"]
    cache_dir = REPO_ROOT / "datasets" / "ppg-dalia" / "processed"

    test_windows = load_cached_subjects(cache_dir, split["test"])
    test_data = build_tensors(test_windows)

    all_ok = True
    report = []
    for entry in results["checkpoint_manifest"]:
        seed = entry["seed"]
        ckpt_path = REPO_ROOT / entry["path"]
        model = PPGCapacityMatchedModel(32)
        model.load_state_dict(torch.load(ckpt_path, map_location="cpu"))
        model.eval()
        pred = evaluate(model, test_data, hr_mean, hr_std, "cpu")
        reproduced_mae = mae(pred, test_data["hr"].numpy())
        reproduced_rmse = rmse(pred, test_data["hr"].numpy())
        stored = results["runs"][f"seed{seed}"]["overall"]
        mae_diff = abs(reproduced_mae - stored["mae"])
        rmse_diff = abs(reproduced_rmse - stored["rmse"])
        ok = mae_diff < TOLERANCE_BPM and rmse_diff < TOLERANCE_BPM
        all_ok = all_ok and ok
        report.append({"run_id": entry["run_id"], "ok": ok, "mae_diff": mae_diff, "rmse_diff": rmse_diff})
        print(f"{entry['run_id']}: {'OK' if ok else 'MISMATCH'} (dMAE={mae_diff:.2e}, dRMSE={rmse_diff:.2e})")

    out_path = REPO_ROOT / "results" / "ppg_dalia_capacity_control_reproducibility.json"
    out_path.write_text(json.dumps({"tolerance_bpm": TOLERANCE_BPM, "all_ok": all_ok, "runs": report}, indent=2))
    print(f"\n{'ALL OK' if all_ok else 'MISMATCH FOUND'}")
    if not all_ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
