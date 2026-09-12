#!/usr/bin/env python
"""Statistical reporting audit (master review, Reviewer A): all existing
multi-seed SD figures in this project use numpy's default `ddof=0`
(population standard deviation). For n=5 independent training-seed
samples, the standard convention for ESTIMATING variability of a small
sample is the SAMPLE standard deviation (`ddof=1`, Bessel's correction).

This script does NOT rewrite any frozen result file. It reads the raw
per-seed values already stored in each frozen artifact (which are
authoritative and unchanged) and computes a small, separate companion
overlay recording both conventions side by side, so the discrepancy is
visible without altering historical evidence.

Frozen artifacts audited: results/ppg_dalia_imu_multiseed_replication.json,
results/ptt_ppg_site_ablation.json.

New artifacts going forward (ml/train_ppg_dalia_capacity_control.py) report
BOTH conventions directly, sample SD (ddof=1) labeled as the primary
recommended figure.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

MULTISEED_PATH = REPO_ROOT / "results" / "ppg_dalia_imu_multiseed_replication.json"
PTT_PATH = REPO_ROOT / "results" / "ptt_ppg_site_ablation.json"
OUT_PATH = REPO_ROOT / "results" / "sd_convention_audit.json"


def both_sd(values: list[float]) -> dict:
    arr = np.asarray(values, dtype=np.float64)
    return {
        "mean": float(arr.mean()),
        "sd_population_ddof0_as_originally_reported": float(arr.std(ddof=0)),
        "sd_sample_ddof1_recommended": float(arr.std(ddof=1)) if len(arr) > 1 else None,
        "n": len(arr),
        "per_seed": values,
    }


def audit_multiseed(data: dict) -> dict:
    seeds = data["frozen_protocol"]["training_seeds"]
    out = {}
    for model_key in ("a", "b", "c"):
        mae_vals = [data["runs"][model_key][f"seed{s}"]["overall"]["mae"] for s in seeds]
        rmse_vals = [data["runs"][model_key][f"seed{s}"]["overall"]["rmse"] for s in seeds]
        out[f"model_{model_key}"] = {"mae": both_sd(mae_vals), "rmse": both_sd(rmse_vals)}

    for delta_key in (
        "total_sync_imu_benefit_mae_A_minus_B",
        "shuffled_context_like_benefit_mae_A_minus_C",
        "synchronization_increment_mae_C_minus_B",
    ):
        original = data["aggregate"][delta_key]
        vals = list(original["per_seed"].values())
        out[delta_key] = both_sd(vals)
        # sanity: originally-reported (ddof=0) SD must match what we recompute
        assert abs(out[delta_key]["sd_population_ddof0_as_originally_reported"] - original["sd"]) < 1e-9

    return out


def audit_ptt(data: dict) -> dict:
    out: dict = {}
    seeds_dict = data["runs"]["a"]
    seed_keys = list(seeds_dict.keys())
    a_vals = [data["runs"]["a"][sk]["overall"]["mae"] for sk in seed_keys]
    b_vals = [data["runs"]["b"][sk]["overall"]["mae"] for sk in seed_keys]
    out["model_a"] = both_sd(a_vals)
    out["model_b"] = both_sd(b_vals)

    diffs = [b - a for a, b in zip(a_vals, b_vals)]
    out["paired_delta_mae_b_minus_a"] = both_sd(diffs)
    original_sd = data["aggregate"]["paired_delta_mae_b_minus_a"]["sd"]
    assert abs(out["paired_delta_mae_b_minus_a"]["sd_population_ddof0_as_originally_reported"] - original_sd) < 1e-9
    return out


def main() -> None:
    result = {
        "purpose": (
            "Master-review statistical reporting audit: all existing multi-seed SD figures used "
            "numpy default ddof=0 (population SD). This overlay adds ddof=1 (sample SD, recommended "
            "for n=5 seed estimates) computed from the SAME raw per-seed values already stored in "
            "the frozen source artifacts - those artifacts are NOT modified."
        ),
        "revised_convention": "sample SD (ddof=1) is the recommended figure for all new multi-seed reporting going forward",
        "old_convention_preserved": "population SD (ddof=0) values in the original frozen artifacts are unchanged and remain valid as originally reported",
        "sources": {},
    }

    if MULTISEED_PATH.exists():
        data = json.loads(MULTISEED_PATH.read_text())
        result["sources"]["ppg_dalia_imu_multiseed_replication"] = {
            "source_artifact": "results/ppg_dalia_imu_multiseed_replication.json (unchanged)",
            "audit": audit_multiseed(data),
        }

    if PTT_PATH.exists():
        data = json.loads(PTT_PATH.read_text())
        result["sources"]["ptt_ppg_site_ablation"] = {
            "source_artifact": "results/ptt_ppg_site_ablation.json (unchanged)",
            "audit": audit_ptt(data),
        }

    OUT_PATH.write_text(json.dumps(result, indent=2))
    print("Wrote", OUT_PATH)

    # Print a compact human-readable diff summary
    if "ppg_dalia_imu_multiseed_replication" in result["sources"]:
        a = result["sources"]["ppg_dalia_imu_multiseed_replication"]["audit"]
        for k in ("model_a", "model_b", "model_c"):
            m = a[k]["mae"]
            print(f"PPG-DaLiA {k} MAE: ddof0={m['sd_population_ddof0_as_originally_reported']:.4f} vs ddof1={m['sd_sample_ddof1_recommended']:.4f}")
    if "ptt_ppg_site_ablation" in result["sources"]:
        a = result["sources"]["ptt_ppg_site_ablation"]["audit"]
        for k in ("model_a", "model_b"):
            m = a[k]
            print(f"PTT {k} MAE: ddof0={m['sd_population_ddof0_as_originally_reported']:.4f} vs ddof1={m['sd_sample_ddof1_recommended']:.4f}")


if __name__ == "__main__":
    main()
