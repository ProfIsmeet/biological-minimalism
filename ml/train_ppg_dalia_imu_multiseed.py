#!/usr/bin/env python
"""Day 6: multi-seed replication of the frozen PPG-DaLiA IMU sensor-value
experiment (docs/TECHNICAL_HANDOFF_V2.md Priority 2;
results/ppg_dalia_imu_ablation.json is the original single-seed result).

Research question: is the positive marginal value of synchronized wrist
IMU for HR estimation stable across independent model initializations, or
was the original result unusually dependent on seed 42?

**Frozen protocol - identical to the original experiment in every respect
except training/model-initialization randomness:**

- Subject split is loaded from the existing
  `ml/experiments/ppg_dalia_imu_ablation/subject_split.json` file and is
  NEVER recomputed here (the original script derived the split from the
  same `--seed` value that also seeded training - conflating two concerns.
  This script decouples them: the split is frozen data, read once).
- HR target normalization (mean/std) is computed from the SAME frozen
  train-split windows, asserted equal to the recorded values in
  results/ppg_dalia_imu_ablation.json for parity.
- Model classes (`PPGOnlyHRModel`, `PPGPlusIMUHRModel`), `train_model`,
  `evaluate`, `stratified_report`, `build_tensors`, `mae`, `rmse`, and
  `shuffle_imu_within_subject` are IMPORTED UNMODIFIED from
  `ml/train_ppg_dalia_imu_ablation.py` - not reimplemented - so there is
  no possibility of silent protocol drift between the original and this
  replication.
- Hyperparameters (epochs=20, batch_size=64, lr=0.001, embedding_dim=32)
  are hard-coded here identically to
  `ml/experiments/ppg_dalia_imu_ablation/config.json`.

**Shuffle-seed decision (documented before running, per the Day 6 master
prompt's explicit requirement):** the original single-seed script coupled
the shuffle-permutation seed to the same `--seed` value used for
model-init/dataloader-shuffle (there was only one seed variable). This
replication preserves that coupling rather than inventing a new frozen
behavior: for training-seed S, Model C's shuffle permutation also uses
seed S. This means shuffle REALIZATION varies across the 5 replicates,
exactly as model initialization does - both are "training randomness" by
the original design's own logic, not part of the frozen scientific split.

**Success/failure interpretation categories (frozen BEFORE running, per
Day 6 master prompt SS13):**
- STRONGLY_REPLICATED_POSITIVE: synchronized IMU (B) beats PPG-only (A) in
  5/5 or 4/5 seeds AND mean paired MAE benefit (A-B) > 0.
- REPLICATED_BUT_VARIABLE: mean paired benefit > 0 but seed direction is
  3/5 (not 4/5 or 5/5).
- MIXED: mean paired benefit is close to zero or seed direction is <=2/5.
- NON_REPLICATED: mean paired benefit <= 0.
These thresholds are fixed here, before this script has been run.
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

import torch  # noqa: E402

# Runtime/infrastructure fix, NOT a scientific parameter: this CPU-only VM
# has 20 logical cores, and PyTorch's default intra-op thread count (also
# 20) causes severe thread-oversubscription overhead for this small model/
# batch size - measured directly (benchmarked on real cached S1+S3+S4
# windows through this exact train_model() function): default 20 threads
# took ~100s/epoch on 13,542 windows; capping to 4 threads took ~3.6s/epoch
# on the same data (~28x faster). This does not change the model,
# optimizer, data, or any frozen protocol element - only how many CPU
# threads one operation uses.
torch.set_num_threads(4)

from ml.datasets.ppg_dalia import ALL_SUBJECTS, load_cached_subjects  # noqa: E402
from ml.train_ppg_dalia_imu_ablation import (  # noqa: E402
    PPGOnlyHRModel,
    PPGPlusIMUHRModel,
    build_tensors,
    evaluate,
    mae,
    rmse,
    shuffle_imu_within_subject,
    stratified_report,
    train_model,
)

ORIGINAL_EXPERIMENT_DIR = REPO_ROOT / "ml" / "experiments" / "ppg_dalia_imu_ablation"
ORIGINAL_RESULTS_PATH = REPO_ROOT / "results" / "ppg_dalia_imu_ablation.json"
CACHE_DIR = REPO_ROOT / "datasets" / "ppg-dalia" / "processed"
OUT_PATH = REPO_ROOT / "results" / "ppg_dalia_imu_multiseed_replication.json"
CKPT_DIR = REPO_ROOT / "ml" / "checkpoints"

# Frozen hyperparameters - identical to config.json, hard-coded (never
# re-tuned per seed).
EPOCHS = 20
BATCH_SIZE = 64
LR = 0.001
EMBEDDING_DIM = 32
TRAINING_SEEDS = (42, 43, 44, 45, 46)
DEVICE = "cpu"

INTERPRETATION_THRESHOLDS = {
    "STRONGLY_REPLICATED_POSITIVE": "seed_direction_count >= 4 of 5 favor B AND mean(A-B) > 0",
    "REPLICATED_BUT_VARIABLE": "seed_direction_count == 3 of 5 favor B AND mean(A-B) > 0",
    "MIXED": "seed_direction_count <= 2 of 5 favor B, or mean(A-B) approximately 0",
    "NON_REPLICATED": "mean(A-B) <= 0",
}


def classify_replication(mean_delta: float, n_favor: int, n_seeds: int) -> str:
    if mean_delta <= 0:
        return "NON_REPLICATED"
    if n_favor >= 4:
        return "STRONGLY_REPLICATED_POSITIVE"
    if n_favor == 3:
        return "REPLICATED_BUT_VARIABLE"
    return "MIXED"


def main() -> None:
    split = json.loads((ORIGINAL_EXPERIMENT_DIR / "subject_split.json").read_text())
    original_results = json.loads(ORIGINAL_RESULTS_PATH.read_text())

    assert set(split["train"]) | set(split["val"]) | set(split["test"]) == set(ALL_SUBJECTS)
    assert not (set(split["train"]) & set(split["val"]))
    assert not (set(split["train"]) & set(split["test"]))
    assert not (set(split["val"]) & set(split["test"]))

    print("Using FROZEN split (never recomputed):", json.dumps(split))

    train_windows = load_cached_subjects(CACHE_DIR, split["train"])
    val_windows = load_cached_subjects(CACHE_DIR, split["val"])
    test_windows = load_cached_subjects(CACHE_DIR, split["test"])

    train_data = build_tensors(train_windows)
    val_data = build_tensors(val_windows)
    test_data = build_tensors(test_windows)
    print(f"train windows: {len(train_data['hr'])} | val windows: {len(val_data['hr'])} | test windows: {len(test_data['hr'])}")

    hr_mean = float(train_data["hr"].mean())
    hr_std = float(train_data["hr"].std() + 1e-6)
    recorded_norm = original_results["preprocessing"]["hr_target_normalization"]
    assert abs(hr_mean - recorded_norm["mean"]) < 1e-4, f"hr_mean {hr_mean} != recorded {recorded_norm['mean']} - split/cache mismatch"
    assert abs(hr_std - recorded_norm["std"]) < 1e-4, f"hr_std {hr_std} != recorded {recorded_norm['std']} - split/cache mismatch"
    print(f"HR normalization (frozen, matches original): mean={hr_mean:.6f} std={hr_std:.6f}")

    out = {
        "experiment_id": "ppg_dalia_imu_multiseed_replication",
        "replicates": "results/ppg_dalia_imu_ablation.json (original single-seed=42 result, NOT overwritten)",
        "frozen_protocol": {
            "dataset": "PPG-DaLiA",
            "subject_split": split,
            "subject_split_source": "ml/experiments/ppg_dalia_imu_ablation/subject_split.json (loaded, never recomputed)",
            "window_seconds": 8.0,
            "step_seconds": 2.0,
            "ppg_sample_rate_hz": 64.0,
            "imu_sample_rate_hz": 32.0,
            "preprocessing": "per-window PPG z-score; per-axis per-window IMU z-score; train-split-only HR target normalization",
            "hr_normalization": {"mean": hr_mean, "std": hr_std},
            "models": {
                "model_a_ppg_only": "PPGOnlyHRModel (Conv1DEncoder in_channels=1 + Linear head) - imported unmodified from ml/train_ppg_dalia_imu_ablation.py",
                "model_b_ppg_plus_imu": "PPGPlusIMUHRModel (Conv1DEncoder x2 + ModalityFusionTransformer + Linear head) - imported unmodified",
                "model_c_ppg_plus_shuffled_imu": "Same class as Model B; IMU windows shuffled within-subject via shuffle_imu_within_subject() - imported unmodified",
            },
            "training_hyperparameters": {"epochs": EPOCHS, "batch_size": BATCH_SIZE, "lr": LR, "embedding_dim": EMBEDDING_DIM, "optimizer": "AdamW", "loss": "MSELoss on normalized HR"},
            "training_seeds": list(TRAINING_SEEDS),
            "shuffle_seed_policy": "Model C's shuffle-permutation seed == the training seed for that replicate (matches the original script's coupling of shuffle-seed and training-seed into one variable; documented, not silently changed).",
            "only_variable_across_replicates": "training/model-initialization randomness (torch.manual_seed) and, coupled to it by the policy above, the shuffle-C permutation realization",
        },
        "interpretation_thresholds_frozen_before_running": INTERPRETATION_THRESHOLDS,
        "runs": {"a": {}, "b": {}, "c": {}},
        "checkpoint_manifest": [],
    }

    for seed in TRAINING_SEEDS:
        shuffled_train = shuffle_imu_within_subject(train_data, seed=seed)
        shuffled_val = shuffle_imu_within_subject(val_data, seed=seed)
        shuffled_test = shuffle_imu_within_subject(test_data, seed=seed)

        runs = [
            ("a", "model_a_ppg_only", PPGOnlyHRModel, train_data, val_data, test_data),
            ("b", "model_b_ppg_plus_imu", PPGPlusIMUHRModel, train_data, val_data, test_data),
            ("c", "model_c_ppg_plus_shuffled_imu", PPGPlusIMUHRModel, shuffled_train, shuffled_val, shuffled_test),
        ]

        for model_key, run_name, model_cls, this_train, this_val, this_test in runs:
            print(f"\n=== seed {seed}: training {run_name} ===")
            torch.manual_seed(seed)
            model = model_cls(EMBEDDING_DIM)
            n_params = sum(p.numel() for p in model.parameters())

            start = time.time()
            history = train_model(model, this_train, this_val, hr_mean, hr_std, EPOCHS, BATCH_SIZE, LR, DEVICE)
            elapsed = time.time() - start

            pred = evaluate(model, this_test, hr_mean, hr_std, DEVICE)
            target = this_test["hr"].numpy()

            assert np.all(np.isfinite(pred)), f"seed {seed} {run_name}: non-finite predictions"

            report = stratified_report(pred, target, this_test)
            report["train_seconds"] = elapsed
            report["train_history"] = history
            report["n_parameters"] = int(n_params)
            report["seed"] = seed

            print(f"seed {seed} {run_name}: held-out MAE {report['overall']['mae']:.4f} bpm, RMSE {report['overall']['rmse']:.4f} bpm ({elapsed:.1f}s)")

            out["runs"][model_key][f"seed{seed}"] = report

            ckpt_path = CKPT_DIR / f"ppg_dalia_multiseed_{run_name}_seed{seed}.pt"
            torch.save(model.state_dict(), ckpt_path)
            ckpt_bytes = ckpt_path.read_bytes()
            out["checkpoint_manifest"].append({
                "run_id": f"{run_name}_seed{seed}",
                "model": model_key,
                "seed": seed,
                "path": str(ckpt_path.relative_to(REPO_ROOT)),
                "size_bytes": len(ckpt_bytes),
                "sha256": hashlib.sha256(ckpt_bytes).hexdigest(),
                "n_parameters": int(n_params),
            })

    # --- Paired seed-wise aggregation --------------------------------------
    seeds = list(TRAINING_SEEDS)
    a_mae = [out["runs"]["a"][f"seed{s}"]["overall"]["mae"] for s in seeds]
    b_mae = [out["runs"]["b"][f"seed{s}"]["overall"]["mae"] for s in seeds]
    c_mae = [out["runs"]["c"][f"seed{s}"]["overall"]["mae"] for s in seeds]
    a_rmse = [out["runs"]["a"][f"seed{s}"]["overall"]["rmse"] for s in seeds]
    b_rmse = [out["runs"]["b"][f"seed{s}"]["overall"]["rmse"] for s in seeds]
    c_rmse = [out["runs"]["c"][f"seed{s}"]["overall"]["rmse"] for s in seeds]

    a_minus_b = [a - b for a, b in zip(a_mae, b_mae)]
    a_minus_c = [a - c for a, c in zip(a_mae, c_mae)]
    c_minus_b = [c - b for c, b in zip(c_mae, b_mae)]
    a_minus_b_rmse = [a - b for a, b in zip(a_rmse, b_rmse)]
    a_minus_c_rmse = [a - c for a, c in zip(a_rmse, c_rmse)]
    c_minus_b_rmse = [c - b for c, b in zip(c_rmse, b_rmse)]

    rel_imp_b = [(a - b) / a for a, b in zip(a_mae, b_mae)]
    rel_imp_c = [(a - c) / a for a, c in zip(a_mae, c_mae)]

    n_b_beats_a = sum(1 for d in a_minus_b if d > 0)
    n_c_beats_a = sum(1 for d in a_minus_c if d > 0)
    n_b_beats_c = sum(1 for d in c_minus_b if d > 0)

    out["aggregate"] = {
        "model_a": {"mean_mae": float(np.mean(a_mae)), "sd_mae": float(np.std(a_mae)), "mean_rmse": float(np.mean(a_rmse)), "sd_rmse": float(np.std(a_rmse)), "per_seed_mae": dict(zip((f"seed{s}" for s in seeds), a_mae))},
        "model_b": {"mean_mae": float(np.mean(b_mae)), "sd_mae": float(np.std(b_mae)), "mean_rmse": float(np.mean(b_rmse)), "sd_rmse": float(np.std(b_rmse)), "per_seed_mae": dict(zip((f"seed{s}" for s in seeds), b_mae))},
        "model_c": {"mean_mae": float(np.mean(c_mae)), "sd_mae": float(np.std(c_mae)), "mean_rmse": float(np.mean(c_rmse)), "sd_rmse": float(np.std(c_rmse)), "per_seed_mae": dict(zip((f"seed{s}" for s in seeds), c_mae))},
        "total_sync_imu_benefit_mae_A_minus_B": {"per_seed": dict(zip((f"seed{s}" for s in seeds), a_minus_b)), "mean": float(np.mean(a_minus_b)), "sd": float(np.std(a_minus_b)), "n_seeds_favor_B": n_b_beats_a, "n_seeds_total": len(seeds)},
        "shuffled_context_like_benefit_mae_A_minus_C": {"per_seed": dict(zip((f"seed{s}" for s in seeds), a_minus_c)), "mean": float(np.mean(a_minus_c)), "sd": float(np.std(a_minus_c)), "n_seeds_favor_C": n_c_beats_a, "n_seeds_total": len(seeds)},
        "synchronization_increment_mae_C_minus_B": {"per_seed": dict(zip((f"seed{s}" for s in seeds), c_minus_b)), "mean": float(np.mean(c_minus_b)), "sd": float(np.std(c_minus_b)), "n_seeds_favor_B_over_C": n_b_beats_c, "n_seeds_total": len(seeds)},
        "total_sync_imu_benefit_rmse_A_minus_B": {"per_seed": dict(zip((f"seed{s}" for s in seeds), a_minus_b_rmse)), "mean": float(np.mean(a_minus_b_rmse)), "sd": float(np.std(a_minus_b_rmse))},
        "shuffled_context_like_benefit_rmse_A_minus_C": {"per_seed": dict(zip((f"seed{s}" for s in seeds), a_minus_c_rmse)), "mean": float(np.mean(a_minus_c_rmse)), "sd": float(np.std(a_minus_c_rmse))},
        "synchronization_increment_rmse_C_minus_B": {"per_seed": dict(zip((f"seed{s}" for s in seeds), c_minus_b_rmse)), "mean": float(np.mean(c_minus_b_rmse)), "sd": float(np.std(c_minus_b_rmse))},
        "relative_improvement_B_over_A": {"per_seed": dict(zip((f"seed{s}" for s in seeds), rel_imp_b)), "mean": float(np.mean(rel_imp_b)), "sd": float(np.std(rel_imp_b))},
        "relative_improvement_C_over_A": {"per_seed": dict(zip((f"seed{s}" for s in seeds), rel_imp_c)), "mean": float(np.mean(rel_imp_c)), "sd": float(np.std(rel_imp_c))},
    }

    replication_status = classify_replication(out["aggregate"]["total_sync_imu_benefit_mae_A_minus_B"]["mean"], n_b_beats_a, len(seeds))
    out["replication_status"] = replication_status

    # --- Subject-level seed-wise consistency --------------------------------
    subjects = sorted(out["runs"]["a"]["seed42"]["per_subject"].keys())
    per_subject = {}
    for s in subjects:
        a_vals = [out["runs"]["a"][f"seed{sd}"]["per_subject"][s]["mae"] for sd in seeds]
        b_vals = [out["runs"]["b"][f"seed{sd}"]["per_subject"][s]["mae"] for sd in seeds]
        c_vals = [out["runs"]["c"][f"seed{sd}"]["per_subject"][s]["mae"] for sd in seeds]
        favors_b = [a - b > 0 for a, b in zip(a_vals, b_vals)]
        per_subject[s] = {
            "model_a_mae_per_seed": dict(zip((f"seed{sd}" for sd in seeds), a_vals)),
            "model_b_mae_per_seed": dict(zip((f"seed{sd}" for sd in seeds), b_vals)),
            "model_c_mae_per_seed": dict(zip((f"seed{sd}" for sd in seeds), c_vals)),
            "n_seeds_favor_B": sum(favors_b),
            "n_seeds_total": len(seeds),
            "stable_direction": all(favors_b) or not any(favors_b),
        }
    out["subject_level_consistency"] = per_subject

    # --- Motion-quartile seed-wise consistency ------------------------------
    quartiles = sorted(out["runs"]["a"]["seed42"]["per_motion_quartile"].keys())
    per_quartile = {}
    for q in quartiles:
        a_vals = [out["runs"]["a"][f"seed{sd}"]["per_motion_quartile"][q]["mae"] for sd in seeds]
        b_vals = [out["runs"]["b"][f"seed{sd}"]["per_motion_quartile"][q]["mae"] for sd in seeds]
        favors_b = [a - b > 0 for a, b in zip(a_vals, b_vals)]
        per_quartile[q] = {
            "model_a_mae_per_seed": dict(zip((f"seed{sd}" for sd in seeds), a_vals)),
            "model_b_mae_per_seed": dict(zip((f"seed{sd}" for sd in seeds), b_vals)),
            "n_seeds_favor_B": sum(favors_b),
            "n_seeds_total": len(seeds),
        }
    out["motion_quartile_consistency"] = per_quartile

    # --- Activity-level seed-wise consistency -------------------------------
    activities = sorted(out["runs"]["a"]["seed42"]["per_activity"].keys())
    per_activity = {}
    for act in activities:
        a_vals = [out["runs"]["a"][f"seed{sd}"]["per_activity"][act]["mae"] for sd in seeds]
        b_vals = [out["runs"]["b"][f"seed{sd}"]["per_activity"][act]["mae"] for sd in seeds]
        favors_b = [a - b > 0 for a, b in zip(a_vals, b_vals)]
        per_activity[act] = {
            "model_a_mae_per_seed": dict(zip((f"seed{sd}" for sd in seeds), a_vals)),
            "model_b_mae_per_seed": dict(zip((f"seed{sd}" for sd in seeds), b_vals)),
            "n_seeds_favor_B": sum(favors_b),
            "n_seeds_total": len(seeds),
        }
    out["activity_level_consistency"] = per_activity

    out["provenance"] = {
        "original_single_seed_result": "results/ppg_dalia_imu_ablation.json (unmodified)",
        "training_command": "python ml/train_ppg_dalia_imu_multiseed.py",
        "device": DEVICE,
        "torch_backend": "cpu",
        "torch_num_threads": torch.get_num_threads(),
        "performance_note": "torch.set_num_threads(4) set at module import - a runtime/infrastructure choice (measured ~28x faster than the PyTorch default of 20 threads on this 20-logical-core CPU-only VM for this model size), not a scientific parameter.",
    }

    _agg = out["aggregate"]
    out["supported_claims"] = [
        (
            "On PPG-DaLiA held-out subjects under the frozen 8s/2s protocol, adding "
            "synchronized wrist IMU to wrist PPG reduced heart-rate MAE from "
            f"{_agg['model_a']['mean_mae']:.3f} to {_agg['model_b']['mean_mae']:.3f} bpm "
            f"(~{_agg['relative_improvement_B_over_A']['mean'] * 100:.1f}% relative); this "
            f"direction replicated across seeds ({replication_status})."
        ),
        (
            "The capacity-matched comparison (shuffled-IMU control C vs synchronized IMU B) "
            f"gave a synchronization increment of {_agg['synchronization_increment_mae_C_minus_B']['mean']:.3f} bpm. "
            "This C->B comparison is capacity-matched; A->B and A->C are capacity-confounded "
            "(baseline A ~8k params vs candidate B/C ~29k params), so the full A->B benefit is "
            "not attributable to IMU sensor value alone."
        ),
    ]
    out["unsupported_claims"] = [
        "Causal attribution of the exact fraction of benefit to 'synchronization' vs 'context' - the shuffle control is descriptive, not a proof of causal decomposition.",
        "Generalization beyond PPG-DaLiA's population/activities/model family.",
        "Any claim this replicates across datasets - PTT and PPG-DaLiA are separate, non-comparable experiments (see docs/SENSOR_MARGINAL_VALUE_METHODOLOGY.md).",
    ]

    OUT_PATH.write_text(json.dumps(out, indent=2))
    print("\nWrote", OUT_PATH)
    print("Replication status:", replication_status)


if __name__ == "__main__":
    main()
