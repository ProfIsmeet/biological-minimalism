#!/usr/bin/env python
"""Stage 3: HMC Sleep Staging independent-family external replication
(A = EEG-only, B = EEG+aligned-EOG, C = EEG+shuffled-EOG control).

Frozen protocol: results/hmc_protocol_stage1b.json (Stage 1B, commit
fe32384, inspected read-only from origin/stage1b-dataset-expansion-prep -
NOT merged; see docs/HMC_SLEEP_EXTERNAL_REPLICATION_PROTOCOL_STAGE1B.md).
Reduced-cohort deviation (bandwidth-driven, frozen BEFORE any HMC file was
downloaded or opened): docs/HMC_STAGE2_BANDWIDTH_REDUCED_COHORT_DEVIATION.md,
results/hmc_split_stage2.json (12 of the full 151 recordings).

This is a brand-new trainer (per the Stage 1B handoff:
docs/STAGE2_HMC_IMPLEMENTATION_HANDOFF.md) - it uses the H1-corrected
seed-before-model-init protocol from the start (ml/sleep_seed_utils.py),
not a retrofit of a buggy original.

Reuses SleepStageClassifier / evaluate_full unmodified from
ml/train_sleep_edf_eeg_eog_ablation.py - the Conv1DEncoder's global
average pooling makes it sequence-length-agnostic, so the same class
works for HMC's 256 Hz / 7680-samples-per-epoch input without modification
(confirmed architecture-fair: same class, same embedding_dim, only
in_channels and input sequence length differ, exactly like the Sleep-EDF
A/B/C design).
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

torch.set_num_threads(4)

from sklearn.metrics import f1_score  # noqa: E402
from sklearn.utils.class_weight import compute_class_weight  # noqa: E402

from ml.datasets.hmc_sleep import (  # noqa: E402
    EEG_CHANNEL,
    EOG_DERIVED_HORIZONTAL,
    STAGE_NAMES,
    load_dataset_windows,
    shuffle_eog_within_subject,
)
from ml.sleep_seed_utils import derive_sleep_run_seeds, seed_for_data_order, seed_for_model_init
from ml.train_sleep_edf_eeg_eog_ablation import SleepStageClassifier, evaluate_full

RAW_DIR = REPO_ROOT / "datasets" / "hmc-sleep-staging" / "raw"
SPLIT_PATH = REPO_ROOT / "results" / "hmc_split_stage3_full_cohort.json"
PROTOCOL_PATH = REPO_ROOT / "results" / "hmc_protocol_stage1b.json"
OUT_PATH = REPO_ROOT / "results" / "hmc_sleep_external_replication_stage3_full_cohort.json"
CKPT_DIR = REPO_ROOT / "ml" / "checkpoints"

SEEDS = (42, 43, 44, 45, 46)
EOG_CHANNEL_INDEX = 1

CONFIGS = {
    "A_eeg_only": (EEG_CHANNEL,),
    "B_eeg_plus_eog": (EEG_CHANNEL, EOG_DERIVED_HORIZONTAL),
}


def load_partition(subject_ids: list[str], channels: tuple[str, ...]) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    x, y, subj_idx, _prefixes = load_dataset_windows(RAW_DIR, channels=channels, subject_ids=subject_ids)
    return x, y, subj_idx


def train_one_seedfix(in_channels: int, train_x, train_y, val_x, val_y, class_weights: torch.Tensor, run_seed: int):
    seeds = derive_sleep_run_seeds(run_seed)

    seed_for_model_init(seeds)
    model = SleepStageClassifier(in_channels=in_channels)

    seed_for_data_order(seeds)
    optimizer = torch.optim.AdamW(model.parameters(), lr=0.001)
    loss_fn = torch.nn.CrossEntropyLoss(weight=class_weights)

    from torch.utils.data import DataLoader, TensorDataset

    train_loader = DataLoader(TensorDataset(torch.from_numpy(train_x), torch.from_numpy(train_y)), batch_size=64, shuffle=True)
    val_loader = DataLoader(TensorDataset(torch.from_numpy(val_x), torch.from_numpy(val_y)), batch_size=128, shuffle=False)

    history = []
    for epoch in range(1, 21):
        model.train()
        train_loss = 0.0
        for xb, yb in train_loader:
            optimizer.zero_grad()
            logits = model(xb)
            loss = loss_fn(logits, yb)
            loss.backward()
            optimizer.step()
            train_loss += float(loss.item()) * len(yb)
        train_loss /= len(train_y)

        model.eval()
        val_preds, val_targets = [], []
        with torch.no_grad():
            for xb, yb in val_loader:
                logits = model(xb)
                val_preds.append(logits.argmax(dim=1).numpy())
                val_targets.append(yb.numpy())
        val_preds = np.concatenate(val_preds)
        val_targets = np.concatenate(val_targets)
        val_macro_f1 = f1_score(val_targets, val_preds, average="macro", zero_division=0)
        history.append({"epoch": epoch, "train_loss": train_loss, "val_macro_f1": float(val_macro_f1)})
        print(f"    epoch {epoch:2d}/20 - train loss {train_loss:.4f} | val macro-F1 {val_macro_f1:.4f}")

    return model, history, seeds


def main() -> None:
    split_doc = json.loads(SPLIT_PATH.read_text())
    split = split_doc["split"]
    protocol = json.loads(PROTOCOL_PATH.read_text())
    print("Using FROZEN reduced-cohort HMC split (bandwidth deviation documented):", json.dumps(split))

    n_params = {name: sum(p.numel() for p in SleepStageClassifier(len(ch)).parameters()) for name, ch in CONFIGS.items()}
    n_params_c = sum(p.numel() for p in SleepStageClassifier(2).parameters())
    assert n_params["B_eeg_plus_eog"] == n_params_c, "Model C must be capacity-identical to Model B"
    print("Parameter counts:", n_params, "| Model C:", n_params_c)

    out: dict = {
        "experiment_id": "hmc_sleep_external_replication_stage3_FULL_COHORT",
        "scope_disclosure": "FULL 151-recording cohort (106 train/23 val/22 test) - PhysioNet's TLS certificate was renewed this sprint (docs/HMC_CERTIFICATE_RENEWED_FULL_DOWNLOAD_RESUMED.md), unblocking the full download. This IS the canonical full-cohort HMC replication result (superseding the n=7 bounded diagnostic).",
        "frozen_protocol_source": "results/hmc_protocol_stage1b.json (Stage 1B commit fe32384, read-only, not merged)",
        "split_deviation_doc": "docs/HMC_STAGE3_SPLIT_STRATEGY_DEVIATION.md",
        "split_source": "results/hmc_split_stage3_full_cohort.json",
        "seeding_protocol_doc": "docs/SLEEP_SEEDING_PROTOCOL_V2.md",
        "eeg_derivation": protocol["eeg_channel_selection"]["frozen_choice"],
        "eog_derivation": protocol["eog_derivation"]["derived_horizontal_eog"],
        "cohort_type": split_doc["cohort_type"],
        "full_cohort_size": split_doc["full_cohort_size"],
        "frozen_protocol": {
            "dataset": "PhysioNet HMC Sleep Staging v1.1",
            "recording_split": split,
            "channels": {name: list(ch) for name, ch in CONFIGS.items()},
            "native_sfreq_hz": 256.0,
            "epoch_seconds": 30.0,
            "training_hyperparameters": {"epochs": 20, "batch_size": 64, "lr": 0.001, "embedding_dim": 32, "optimizer": "AdamW", "loss": "class-weighted CrossEntropyLoss (train-only weights)"},
            "seeds": list(SEEDS),
            "primary_metric": "macro_f1",
        },
        "parameter_counts": {**n_params, "C_shuffled_eog": n_params_c},
        "runs": {"A_eeg_only": {}, "B_eeg_plus_eog": {}, "C_shuffled_eog": {}},
        "checkpoint_manifest": [],
    }

    print("Loading real HMC data (this parses EDF files, may take a while)...")
    b_channels = CONFIGS["B_eeg_plus_eog"]
    train_x2, train_y, train_subj = load_partition(split["train"], b_channels)
    val_x2, val_y, val_subj = load_partition(split["val"], b_channels)
    test_x2, test_y, test_subj = load_partition(split["test"], b_channels)
    print(f"train={len(train_y)} val={len(val_y)} test={len(test_y)} epochs, shape={train_x2.shape}")

    out["window_counts"] = {"train": len(train_y), "val": len(val_y), "test": len(test_y)}

    data_by_config = {
        "A_eeg_only": (train_x2[:, :1, :], train_y, val_x2[:, :1, :], val_y, test_x2[:, :1, :], test_y),
        "B_eeg_plus_eog": (train_x2, train_y, val_x2, val_y, test_x2, test_y),
    }

    for name in ("A_eeg_only", "B_eeg_plus_eog"):
        train_x, ty, val_x, vy, test_x, tey = data_by_config[name]
        in_channels = len(CONFIGS[name])
        class_weights_np = compute_class_weight("balanced", classes=np.arange(len(STAGE_NAMES)), y=ty)
        class_weights = torch.tensor(class_weights_np, dtype=torch.float32)

        for seed in SEEDS:
            run_id = f"hmc_{name}_seedfix_v2_seed{seed}"
            print(f"\n=== seed {seed}: training {run_id} (in_channels={in_channels}) ===")
            start = time.time()
            model, history, seeds = train_one_seedfix(in_channels, train_x, ty, val_x, vy, class_weights, seed)
            elapsed = time.time() - start

            report = evaluate_full(model, test_x, tey)
            report["train_seconds"] = elapsed
            report["train_history"] = history
            report["n_parameters"] = n_params[name]
            report["seed"] = seed
            report["sub_seeds"] = {"model_init_seed": seeds.model_init_seed, "data_order_seed": seeds.data_order_seed}
            print(f"{run_id}: test macro-F1={report['macro_f1']:.4f} accuracy={report['accuracy']:.4f} ({elapsed:.1f}s)")

            out["runs"][name][f"seed{seed}"] = report

            ckpt_path = CKPT_DIR / f"hmc_fullcohort_{name}_seedfix_v2_seed{seed}.pt"
            torch.save(model.state_dict(), ckpt_path)
            ckpt_bytes = ckpt_path.read_bytes()
            out["checkpoint_manifest"].append({
                "run_id": run_id, "config": name, "seed": seed, "in_channels": in_channels,
                "path": str(ckpt_path.relative_to(REPO_ROOT)),
                "size_bytes": len(ckpt_bytes), "sha256": hashlib.sha256(ckpt_bytes).hexdigest(),
                "n_parameters": n_params[name],
            })

            per_subject = {}
            for i, subj_name in enumerate(split["test"]):
                mask = (test_subj == i)
                x_s = test_x[mask]
                y_s = tey[mask]
                if len(y_s) == 0:
                    continue
                r = evaluate_full(model, x_s, y_s)
                per_subject[subj_name] = {"macro_f1": r["macro_f1"], "balanced_accuracy": r["balanced_accuracy"], "n_epochs": r["n_epochs_eval"]}
            out["runs"][name][f"seed{seed}"]["per_subject"] = per_subject

    # --- C: shuffled-EOG control, isolated control_shuffle_seed ---------------
    class_weights_np = compute_class_weight("balanced", classes=np.arange(len(STAGE_NAMES)), y=train_y)
    class_weights = torch.tensor(class_weights_np, dtype=torch.float32)

    for seed in SEEDS:
        run_id = f"hmc_C_shuffled_eog_seedfix_v2_seed{seed}"
        print(f"\n=== seed {seed}: training {run_id} (CORRECTED seeding order, isolated control_shuffle_seed) ===")
        seeds = derive_sleep_run_seeds(seed)

        shuffled_train_x = shuffle_eog_within_subject(train_x2, train_subj, EOG_CHANNEL_INDEX, seed=seeds.control_shuffle_seed)
        shuffled_val_x = shuffle_eog_within_subject(val_x2, val_subj, EOG_CHANNEL_INDEX, seed=seeds.control_shuffle_seed)
        shuffled_test_x = shuffle_eog_within_subject(test_x2, test_subj, EOG_CHANNEL_INDEX, seed=seeds.control_shuffle_seed)

        start = time.time()
        model, history, seeds = train_one_seedfix(2, shuffled_train_x, train_y, shuffled_val_x, val_y, class_weights, seed)
        elapsed = time.time() - start

        report = evaluate_full(model, shuffled_test_x, test_y)
        report["train_seconds"] = elapsed
        report["train_history"] = history
        report["n_parameters"] = n_params_c
        report["seed"] = seed
        report["sub_seeds"] = {"model_init_seed": seeds.model_init_seed, "data_order_seed": seeds.data_order_seed, "control_shuffle_seed": seeds.control_shuffle_seed}
        print(f"{run_id}: test macro-F1={report['macro_f1']:.4f} accuracy={report['accuracy']:.4f} ({elapsed:.1f}s)")

        out["runs"]["C_shuffled_eog"][f"seed{seed}"] = report

        ckpt_path = CKPT_DIR / f"hmc_fullcohort_c_shuffled_eog_seedfix_v2_seed{seed}.pt"
        torch.save(model.state_dict(), ckpt_path)
        ckpt_bytes = ckpt_path.read_bytes()
        out["checkpoint_manifest"].append({
            "run_id": run_id, "config": "C_shuffled_eog", "seed": seed, "in_channels": 2,
            "path": str(ckpt_path.relative_to(REPO_ROOT)),
            "size_bytes": len(ckpt_bytes), "sha256": hashlib.sha256(ckpt_bytes).hexdigest(),
            "n_parameters": n_params_c,
        })

        per_subject = {}
        for i, subj_name in enumerate(split["test"]):
            mask = (test_subj == i)
            x_s = shuffled_test_x[mask]
            y_s = test_y[mask]
            if len(y_s) == 0:
                continue
            r = evaluate_full(model, x_s, y_s)
            per_subject[subj_name] = {"macro_f1": r["macro_f1"], "balanced_accuracy": r["balanced_accuracy"], "n_epochs": r["n_epochs_eval"]}
        out["runs"]["C_shuffled_eog"][f"seed{seed}"]["per_subject"] = per_subject

    # --- Aggregate (sample SD, ddof=1) ----------------------------------------
    def agg(values: list[float]) -> dict:
        arr = np.asarray(values, dtype=np.float64)
        return {"mean": float(arr.mean()), "sd_sample_ddof1": float(arr.std(ddof=1)) if len(arr) > 1 else None, "per_seed": dict(zip((f"seed{s}" for s in SEEDS), values))}

    a_f1 = [out["runs"]["A_eeg_only"][f"seed{s}"]["macro_f1"] for s in SEEDS]
    b_f1 = [out["runs"]["B_eeg_plus_eog"][f"seed{s}"]["macro_f1"] for s in SEEDS]
    c_f1 = [out["runs"]["C_shuffled_eog"][f"seed{s}"]["macro_f1"] for s in SEEDS]

    a_to_b = [b - a for a, b in zip(a_f1, b_f1)]
    c_to_b = [b - c for c, b in zip(c_f1, b_f1)]

    out["aggregate"] = {
        "model_a_macro_f1": agg(a_f1),
        "model_b_macro_f1": agg(b_f1),
        "model_c_macro_f1": agg(c_f1),
        "B_minus_A": {**agg(a_to_b), "n_seeds_favor_B": sum(1 for d in a_to_b if d > 0), "n_seeds_total": len(SEEDS)},
        "B_minus_C": {**agg(c_to_b), "n_seeds_favor_B": sum(1 for d in c_to_b if d > 0), "n_seeds_total": len(SEEDS)},
    }

    OUT_PATH.write_text(json.dumps(out, indent=2))
    print("\nWrote", OUT_PATH)
    print("Aggregate:", json.dumps(out["aggregate"], indent=2))


if __name__ == "__main__":
    main()
