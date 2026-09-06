#!/usr/bin/env python
"""Capacity-matched PPG-only control (Model A_cap) for the PPG-DaLiA IMU
sensor-value experiment - addresses master-review Finding A3 (HIGH):
Model A (8,065 params) and Model B/C (29,089 params) were not
capacity-matched, so the original A->B comparison conflated sensing
information with model capacity.

See docs/PPG_DALIA_CAPACITY_CONTROL_PREDECLARATION.md for the full frozen
predeclaration (architecture rationale, exact parameter counts,
interpretation rules for every outcome) - written and committed BEFORE
this script produced any result.

Model A_cap: the same two-encoder + ModalityFusionTransformer + head
architecture as Model B/C, but BOTH encoder branches receive the SAME
real PPG window (an independently-initialized second encoding of PPG,
not IMU, not zeros, not a masked-dead branch). 28,865 parameters vs.
Model B/C's 29,089 (0.77% residual, disclosed, judged immaterial - see
predeclaration SS2).

This does NOT overwrite results/ppg_dalia_imu_ablation.json or
results/ppg_dalia_imu_multiseed_replication.json - it produces a
separate, supplemental artifact:
results/ppg_dalia_capacity_control.json

Frozen split, preprocessing, seeds (42-46), and hyperparameters are
identical to the Day 6 multi-seed replication (imported unmodified where
possible).
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

torch_num_threads = 4  # see Day 6 infrastructure note - not a scientific parameter

import torch  # noqa: E402

torch.set_num_threads(torch_num_threads)

from torch import nn  # noqa: E402

from app.ml.models import Conv1DEncoder, ModalityFusionTransformer  # noqa: E402

from ml.datasets.ppg_dalia import load_cached_subjects  # noqa: E402
from ml.train_ppg_dalia_imu_ablation import (  # noqa: E402
    PPGOnlyHRModel,
    PPGPlusIMUHRModel,
    build_tensors,
    evaluate,
    mae,
    rmse,
    stratified_report,
    train_model,
)

ORIGINAL_EXPERIMENT_DIR = REPO_ROOT / "ml" / "experiments" / "ppg_dalia_imu_ablation"
ORIGINAL_RESULTS_PATH = REPO_ROOT / "results" / "ppg_dalia_imu_ablation.json"
MULTISEED_RESULTS_PATH = REPO_ROOT / "results" / "ppg_dalia_imu_multiseed_replication.json"
CACHE_DIR = REPO_ROOT / "datasets" / "ppg-dalia" / "processed"
OUT_PATH = REPO_ROOT / "results" / "ppg_dalia_capacity_control.json"
CKPT_DIR = REPO_ROOT / "ml" / "checkpoints"

EPOCHS = 20
BATCH_SIZE = 64
LR = 0.001
EMBEDDING_DIM = 32
TRAINING_SEEDS = (42, 43, 44, 45, 46)
DEVICE = "cpu"


class PPGCapacityMatchedModel(nn.Module):
    """Model A_cap: two independent Conv1DEncoder branches, BOTH fed the
    same real PPG window, fused via the same ModalityFusionTransformer
    architecture Model B/C use. No IMU, no zeros, no masked/dead branch -
    every parameter receives real gradient signal from real PPG data."""

    def __init__(self, embedding_dim: int = EMBEDDING_DIM) -> None:
        super().__init__()
        self.ppg_encoder_1 = Conv1DEncoder(in_channels=1, embedding_dim=embedding_dim)
        self.ppg_encoder_2 = Conv1DEncoder(in_channels=1, embedding_dim=embedding_dim)
        self.fusion = ModalityFusionTransformer(embedding_dim=embedding_dim, n_heads=4, n_layers=1, n_modalities=2)
        self.head = nn.Linear(embedding_dim, 1)

    def forward(self, ppg: torch.Tensor, _unused: torch.Tensor | None = None) -> torch.Tensor:
        e1 = self.ppg_encoder_1(ppg)
        e2 = self.ppg_encoder_2(ppg)  # same input, independent weights - redundant encoding, not new information
        tokens = torch.stack([e1, e2], dim=1)
        mask = torch.ones(ppg.shape[0], 2, dtype=torch.bool, device=ppg.device)
        fused = self.fusion(tokens, modality_mask=mask)
        return self.head(fused).squeeze(-1)


def main() -> None:
    split = json.loads((ORIGINAL_EXPERIMENT_DIR / "subject_split.json").read_text())
    original_results = json.loads(ORIGINAL_RESULTS_PATH.read_text())
    multiseed_results = json.loads(MULTISEED_RESULTS_PATH.read_text()) if MULTISEED_RESULTS_PATH.exists() else None

    print("Using FROZEN split (never recomputed):", json.dumps(split))

    train_windows = load_cached_subjects(CACHE_DIR, split["train"])
    val_windows = load_cached_subjects(CACHE_DIR, split["val"])
    test_windows = load_cached_subjects(CACHE_DIR, split["test"])

    train_data = build_tensors(train_windows)
    val_data = build_tensors(val_windows)
    test_data = build_tensors(test_windows)

    hr_mean = float(train_data["hr"].mean())
    hr_std = float(train_data["hr"].std() + 1e-6)
    recorded_norm = original_results["preprocessing"]["hr_target_normalization"]
    assert abs(hr_mean - recorded_norm["mean"]) < 1e-4
    assert abs(hr_std - recorded_norm["std"]) < 1e-4
    print(f"HR normalization (frozen): mean={hr_mean:.6f} std={hr_std:.6f}")

    a_params = sum(p.numel() for p in PPGOnlyHRModel(EMBEDDING_DIM).parameters())
    b_params = sum(p.numel() for p in PPGPlusIMUHRModel(EMBEDDING_DIM).parameters())
    acap_params = sum(p.numel() for p in PPGCapacityMatchedModel(EMBEDDING_DIM).parameters())
    print(f"Model A params: {a_params} | Model A_cap params: {acap_params} | Model B/C params: {b_params}")

    out: dict = {
        "experiment_id": "ppg_dalia_capacity_control",
        "predeclaration": "docs/PPG_DALIA_CAPACITY_CONTROL_PREDECLARATION.md",
        "supplements": "results/ppg_dalia_imu_ablation.json and results/ppg_dalia_imu_multiseed_replication.json (neither is overwritten)",
        "frozen_protocol": {
            "dataset": "PPG-DaLiA",
            "subject_split": split,
            "hr_normalization": {"mean": hr_mean, "std": hr_std},
            "training_seeds": list(TRAINING_SEEDS),
            "training_hyperparameters": {"epochs": EPOCHS, "batch_size": BATCH_SIZE, "lr": LR, "embedding_dim": EMBEDDING_DIM, "optimizer": "AdamW", "loss": "MSELoss on normalized HR"},
        },
        "parameter_counts": {
            "model_a_original": a_params,
            "model_a_cap": acap_params,
            "model_b_and_c_original": b_params,
            "a_cap_residual_vs_b_params": b_params - acap_params,
            "a_cap_residual_vs_b_fraction": (b_params - acap_params) / b_params,
        },
        "runs": {},
        "checkpoint_manifest": [],
    }

    for seed in TRAINING_SEEDS:
        run_id = f"model_a_cap_seed{seed}"
        print(f"\n=== seed {seed}: training {run_id} (params={acap_params}) ===")
        torch.manual_seed(seed)
        model = PPGCapacityMatchedModel(EMBEDDING_DIM)

        start = time.time()
        history = train_model(model, train_data, val_data, hr_mean, hr_std, EPOCHS, BATCH_SIZE, LR, DEVICE)
        elapsed = time.time() - start

        pred = evaluate(model, test_data, hr_mean, hr_std, DEVICE)
        target = test_data["hr"].numpy()
        assert np.all(np.isfinite(pred)), f"seed {seed}: non-finite predictions"

        report = stratified_report(pred, target, test_data)
        report["train_seconds"] = elapsed
        report["train_history"] = history
        report["n_parameters"] = acap_params
        report["seed"] = seed

        print(f"seed {seed} {run_id}: held-out MAE {report['overall']['mae']:.4f} bpm, RMSE {report['overall']['rmse']:.4f} bpm ({elapsed:.1f}s)")
        out["runs"][f"seed{seed}"] = report

        ckpt_path = CKPT_DIR / f"ppg_dalia_{run_id}.pt"
        torch.save(model.state_dict(), ckpt_path)
        ckpt_bytes = ckpt_path.read_bytes()
        out["checkpoint_manifest"].append({
            "run_id": run_id, "model": "a_cap", "seed": seed,
            "path": str(ckpt_path.relative_to(REPO_ROOT)),
            "size_bytes": len(ckpt_bytes), "sha256": hashlib.sha256(ckpt_bytes).hexdigest(),
            "n_parameters": acap_params,
        })

    # --- Aggregate (sample SD, ddof=1 - see stats reporting audit) --------
    seeds = list(TRAINING_SEEDS)
    acap_mae = [out["runs"][f"seed{s}"]["overall"]["mae"] for s in seeds]
    acap_rmse = [out["runs"][f"seed{s}"]["overall"]["rmse"] for s in seeds]

    # Pull comparison numbers from the existing multiseed replication (A, B, C) - not retrained.
    if multiseed_results is not None:
        a_mae = [multiseed_results["runs"]["a"][f"seed{s}"]["overall"]["mae"] for s in seeds]
        b_mae = [multiseed_results["runs"]["b"][f"seed{s}"]["overall"]["mae"] for s in seeds]
        c_mae = [multiseed_results["runs"]["c"][f"seed{s}"]["overall"]["mae"] for s in seeds]
    else:
        a_mae = b_mae = c_mae = None

    def sample_mean_sd(values: list[float]) -> dict:
        arr = np.asarray(values, dtype=np.float64)
        return {"mean": float(arr.mean()), "sd_sample_ddof1": float(arr.std(ddof=1)) if len(arr) > 1 else None, "sd_population_ddof0": float(arr.std(ddof=0)), "per_seed": dict(zip((f"seed{s}" for s in seeds), values))}

    out["aggregate"] = {
        "sd_convention_note": "This artifact reports BOTH sample SD (ddof=1, recommended for n=5 seeds) and population SD (ddof=0, the convention used in prior Day 5/6 artifacts) - see docs/STATISTICAL_REPORTING_AUDIT.md.",
        "model_a_cap": {**sample_mean_sd(acap_mae), "rmse": sample_mean_sd(acap_rmse)},
    }

    if a_mae is not None:
        out["aggregate"]["model_a_original_recomputed_from_multiseed"] = sample_mean_sd(a_mae)
        out["aggregate"]["model_b_original_recomputed_from_multiseed"] = sample_mean_sd(b_mae)
        out["aggregate"]["model_c_original_recomputed_from_multiseed"] = sample_mean_sd(c_mae)

        def paired(baseline: list[float], candidate: list[float]) -> dict:
            """Sign convention matches the project standard everywhere else:
            absolute_benefit = baseline - candidate. Positive = candidate has
            LOWER (better) MAE than baseline."""
            diffs = [b - c for b, c in zip(baseline, candidate)]
            return {**sample_mean_sd(diffs), "n_seeds_candidate_better": sum(1 for d in diffs if d > 0), "n_seeds_total": len(diffs)}

        out["primary_comparisons"] = {
            "baseline_A_candidate_Acap": {"note": "positive = A_cap better (lower MAE) than A", **paired(a_mae, acap_mae)},
            "baseline_Acap_candidate_B": {"note": "positive = B better (lower MAE) than A_cap", **paired(acap_mae, b_mae)},
            "baseline_Acap_candidate_C": {"note": "positive = C better (lower MAE) than A_cap", **paired(acap_mae, c_mae)},
            "baseline_C_candidate_B": {"note": "positive = B better (lower MAE) than C (synchronization increment, already established)", **paired(c_mae, b_mae)},
        }

    out_json = json.dumps(out, indent=2)
    OUT_PATH.write_text(out_json)
    print("\nWrote", OUT_PATH)


if __name__ == "__main__":
    main()
