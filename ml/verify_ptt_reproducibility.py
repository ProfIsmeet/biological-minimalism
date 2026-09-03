#!/usr/bin/env python
"""Reproducibility check: independently reload each saved PTT checkpoint
(from disk, not the in-memory training object) and confirm it reproduces
its stored held-out MAE/RMSE from results/ptt_ppg_site_ablation.json
within numerical tolerance.
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

from ml.datasets.pulse_transit_time_ppg import MODEL_A_CHANNELS, MODEL_B_CHANNELS  # noqa: E402
from ml.train_ptt_ppg_site_ablation import (  # noqa: E402
    PPGSiteHRModel,
    build_tensors,
    evaluate_model,
    load_split_records,
    mae,
    rmse,
)

TOLERANCE_BPM = 1e-4  # exact reproduction expected: same weights, same deterministic eval path


def main() -> None:
    results_path = REPO_ROOT / "results" / "ptt_ppg_site_ablation.json"
    results = json.loads(results_path.read_text())
    split = results["subject_split"]
    hr_mean = results["hr_normalization"]["mean"]
    hr_std = results["hr_normalization"]["std"]
    cache_dir = REPO_ROOT / "datasets" / "pulse-transit-time-ppg" / "processed"

    test_records = load_split_records(cache_dir, split["test"])
    test_a = build_tensors(test_records, "a")
    test_b = build_tensors(test_records, "b")

    all_ok = True
    report = []

    for model_name, channels, test_data in (("a", MODEL_A_CHANNELS, test_a), ("b", MODEL_B_CHANNELS, test_b)):
        for entry in results["checkpoint_manifest"]:
            if entry["model"] != model_name:
                continue
            seed = entry["seed"]
            ckpt_path = REPO_ROOT / entry["path"]

            model = PPGSiteHRModel(in_channels=len(channels))
            state_dict = torch.load(ckpt_path, map_location="cpu")
            model.load_state_dict(state_dict)
            model.eval()

            pred = evaluate_model(model, test_data, hr_mean, hr_std)
            reproduced_mae = mae(pred, test_data["hr"])
            reproduced_rmse = rmse(pred, test_data["hr"])

            stored = results["runs"][model_name][f"seed{seed}"]["overall"]
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

    out_path = REPO_ROOT / "results" / "ptt_ppg_site_ablation_reproducibility.json"
    out_path.write_text(json.dumps({"tolerance_bpm": TOLERANCE_BPM, "all_ok": all_ok, "runs": report}, indent=2))
    print(f"\n{'ALL CHECKPOINTS REPRODUCED WITHIN TOLERANCE' if all_ok else 'REPRODUCIBILITY FAILURE - SEE REPORT'}")
    print("Wrote", out_path)
    if not all_ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
