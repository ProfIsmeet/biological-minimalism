#!/usr/bin/env python
"""H1 bounded retraining diagnostic (Day 12): re-trains Sleep-EDF primary
A (EEG-only) and B (EEG+EOG) under the CORRECTED seeding protocol
(ml/sleep_seed_utils.py - seeds torch's global RNG for model init BEFORE
model construction, using a model_init_seed independently derived from
the run seed).

Same split, architecture, preprocessing, epochs, optimizer,
hyperparameters, and nominal seeds (42-46) as the ORIGINAL
ml/train_sleep_edf_eeg_eog_ablation.py. ONLY the seeding protocol changes.
Reuses SleepStageClassifier/train_one/evaluate_full UNMODIFIED - the fix
is purely about WHEN seeding happens, not what the model/training loop
does.

Writes to entirely new output paths/checkpoint names - does NOT touch or
overwrite any original A/B/C artifact or checkpoint.

Scope: bounded diagnostic for A/B only (the headline primary comparison).
C (shuffled-EOG control) and the interaction experiment (M_B/M_AB) are
NOT retrained in this script - see docs/SLEEP_SEEDING_PROTOCOL_V2.md and
results/sleep_scientific_remediation_day12.json for the explicit,
disclosed scope decision and follow-up status.
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

from sklearn.utils.class_weight import compute_class_weight  # noqa: E402

from ml.datasets.sleep_edf import EEG_CHANNEL, EOG_CHANNEL, STAGE_NAMES, load_dataset_windows_multi  # noqa: E402
from ml.sleep_seed_utils import derive_sleep_run_seeds, seed_for_data_order, seed_for_model_init  # noqa: E402
from ml.train_sleep_edf_eeg_eog_ablation import SleepStageClassifier, evaluate_full  # noqa: E402

RAW_DIR = REPO_ROOT / "datasets" / "sleep-edfx" / "raw"
ORIGINAL_RESULTS_PATH = REPO_ROOT / "results" / "sleep_edf_eeg_eog_ablation.json"
OUT_PATH = REPO_ROOT / "results" / "sleep_edf_primary_seedfix_v2.json"
CKPT_DIR = REPO_ROOT / "ml" / "checkpoints"

EMBEDDING_DIM = 32
EPOCHS = 20
BATCH_SIZE = 64
LR = 0.001
SEEDS = (42, 43, 44, 45, 46)

CONFIGS = {
    "baseline_eeg_only": (EEG_CHANNEL,),
    "candidate_eeg_plus_eog": (EEG_CHANNEL, EOG_CHANNEL),
}


def train_one_seedfix(model_channels: int, train_x, train_y, val_x, val_y, class_weights: torch.Tensor, run_seed: int) -> tuple[torch.nn.Module, list[dict]]:
    """Corrected-order training: derive sub-seeds, seed for model init,
    construct the model, THEN seed for data order, THEN build the
    DataLoader and train. Reuses the exact training loop logic of
    ml/train_sleep_edf_eeg_eog_ablation.py's train_one() (epochs, AdamW,
    class-weighted CE, batch size) - only the seeding order changes."""
    seeds = derive_sleep_run_seeds(run_seed)

    seed_for_model_init(seeds)  # <-- FIX: seed BEFORE construction
    model = SleepStageClassifier(in_channels=model_channels, embedding_dim=EMBEDDING_DIM)

    seed_for_data_order(seeds)  # <-- data-order sub-seed, independent of model-init sub-seed
    optimizer = torch.optim.AdamW(model.parameters(), lr=LR)
    loss_fn = torch.nn.CrossEntropyLoss(weight=class_weights)

    from torch.utils.data import DataLoader, TensorDataset

    train_loader = DataLoader(TensorDataset(torch.from_numpy(train_x), torch.from_numpy(train_y)), batch_size=BATCH_SIZE, shuffle=True)
    val_loader = DataLoader(TensorDataset(torch.from_numpy(val_x), torch.from_numpy(val_y)), batch_size=128, shuffle=False)

    from sklearn.metrics import f1_score

    history = []
    for epoch in range(1, EPOCHS + 1):
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
        print(f"    epoch {epoch:2d}/{EPOCHS} - train loss {train_loss:.4f} | val macro-F1 {val_macro_f1:.4f}")

    return model, history


def load_split_data(subject_ids: list[str], channels: tuple[str, ...]) -> tuple[np.ndarray, np.ndarray]:
    x, y, _subj_idx, _prefixes = load_dataset_windows_multi(RAW_DIR, channels=channels, subject_ids=subject_ids)
    return x, y


def main() -> None:
    original = json.loads(ORIGINAL_RESULTS_PATH.read_text())
    split = original["frozen_protocol"]["subject_split"]
    print("Using SAME FROZEN primary split as the original (unchanged):", json.dumps(split))

    n_params = {name: sum(p.numel() for p in SleepStageClassifier(len(ch)).parameters()) for name, ch in CONFIGS.items()}
    print("Parameter counts (must match original exactly):", n_params)
    assert n_params == original["parameter_counts"], "Architecture must be byte-identical to the original - only seeding order changes"

    out: dict = {
        "experiment_id": "sleep_edf_primary_seedfix_v2",
        "purpose": "H1 bounded retraining diagnostic - corrected seeding protocol (model init seeded BEFORE construction), same split/architecture/preprocessing/epochs/optimizer/hyperparameters as the original.",
        "seeding_protocol_doc": "docs/SLEEP_SEEDING_PROTOCOL_V2.md",
        "seed_probe_artifact": "results/sleep_seed_initialization_audit_day12.json",
        "original_reference": "results/sleep_edf_eeg_eog_ablation.json (UNCHANGED, NOT overwritten)",
        "does_not_overwrite_original": True,
        "frozen_protocol": {
            "dataset": "PhysioNet Sleep-EDF (sleep-cassette)",
            "subject_split": split,
            "channels": {name: list(ch) for name, ch in CONFIGS.items()},
            "epoch_seconds": 30.0,
            "training_hyperparameters": {"epochs": EPOCHS, "batch_size": BATCH_SIZE, "lr": LR, "embedding_dim": EMBEDDING_DIM, "optimizer": "AdamW", "loss": "class-weighted CrossEntropyLoss (train-only weights)"},
            "seeds": list(SEEDS),
            "primary_metric": "macro_f1",
        },
        "parameter_counts": n_params,
        "runs": {name: {} for name in CONFIGS},
        "checkpoint_manifest": [],
    }

    print("Loading real data (this parses EDF files, may take a while)...")
    per_config_data = {}
    for name, channels in CONFIGS.items():
        train_x, train_y = load_split_data(split["train"], channels)
        val_x, val_y = load_split_data(split["val"], channels)
        test_x, test_y = load_split_data(split["test"], channels)
        per_config_data[name] = (train_x, train_y, val_x, val_y, test_x, test_y)
        print(f"{name}: train={len(train_y)} val={len(val_y)} test={len(test_y)} epochs, shape={train_x.shape}")

    out["window_counts"] = {name: {"train": len(data[1]), "val": len(data[3]), "test": len(data[5])} for name, data in per_config_data.items()}

    for name, channels in CONFIGS.items():
        train_x, train_y, val_x, val_y, test_x, test_y = per_config_data[name]
        class_weights_np = compute_class_weight("balanced", classes=np.arange(len(STAGE_NAMES)), y=train_y)
        class_weights = torch.tensor(class_weights_np, dtype=torch.float32)

        for seed in SEEDS:
            run_id = f"{name}_seedfix_v2_seed{seed}"
            print(f"\n=== seed {seed}: training {run_id} (in_channels={len(channels)}, CORRECTED seeding order) ===")
            start = time.time()
            model, history = train_one_seedfix(len(channels), train_x, train_y, val_x, val_y, class_weights, seed)
            elapsed = time.time() - start

            report = evaluate_full(model, test_x, test_y)
            report["train_seconds"] = elapsed
            report["train_history"] = history
            report["n_parameters"] = n_params[name]
            report["seed"] = seed
            print(f"{run_id}: test macro-F1={report['macro_f1']:.4f} accuracy={report['accuracy']:.4f} ({elapsed:.1f}s)")

            out["runs"][name][f"seed{seed}"] = report

            ckpt_path = CKPT_DIR / f"sleep_edf_{run_id}.pt"  # NEW filename, never collides with original
            torch.save(model.state_dict(), ckpt_path)
            ckpt_bytes = ckpt_path.read_bytes()
            out["checkpoint_manifest"].append({
                "run_id": run_id, "config": name, "seed": seed,
                "in_channels": len(channels),
                "path": str(ckpt_path.relative_to(REPO_ROOT)),
                "size_bytes": len(ckpt_bytes), "sha256": hashlib.sha256(ckpt_bytes).hexdigest(),
                "n_parameters": n_params[name],
            })

    def agg(values: list[float]) -> dict:
        arr = np.asarray(values, dtype=np.float64)
        return {"mean": float(arr.mean()), "sd_sample_ddof1": float(arr.std(ddof=1)) if len(arr) > 1 else None, "per_seed": dict(zip((f"seed{s}" for s in SEEDS), values))}

    baseline_f1 = [out["runs"]["baseline_eeg_only"][f"seed{s}"]["macro_f1"] for s in SEEDS]
    candidate_f1 = [out["runs"]["candidate_eeg_plus_eog"][f"seed{s}"]["macro_f1"] for s in SEEDS]
    deltas = [c - b for b, c in zip(baseline_f1, candidate_f1)]

    out["aggregate"] = {
        "baseline_macro_f1": agg(baseline_f1),
        "candidate_macro_f1": agg(candidate_f1),
        "delta_candidate_minus_baseline": {**agg(deltas), "n_seeds_candidate_better": sum(1 for d in deltas if d > 0), "n_seeds_total": len(SEEDS)},
    }

    # --- Comparison against the ORIGINAL (buggy-seed-order) result ------------
    orig_baseline_mean = original["aggregate"]["baseline_macro_f1"]["mean"]
    orig_candidate_mean = original["aggregate"]["candidate_macro_f1"]["mean"]
    orig_delta_mean = original["aggregate"]["delta_candidate_minus_baseline"]["mean"]
    orig_n_favor = original["aggregate"]["delta_candidate_minus_baseline"]["n_seeds_candidate_better"]

    out["comparison_vs_original"] = {
        "original_baseline_macro_f1_mean": orig_baseline_mean,
        "corrected_baseline_macro_f1_mean": out["aggregate"]["baseline_macro_f1"]["mean"],
        "original_candidate_macro_f1_mean": orig_candidate_mean,
        "corrected_candidate_macro_f1_mean": out["aggregate"]["candidate_macro_f1"]["mean"],
        "original_delta_mean": orig_delta_mean,
        "corrected_delta_mean": out["aggregate"]["delta_candidate_minus_baseline"]["mean"],
        "original_n_seeds_favor_candidate": orig_n_favor,
        "corrected_n_seeds_favor_candidate": out["aggregate"]["delta_candidate_minus_baseline"]["n_seeds_candidate_better"],
        "same_direction": (orig_delta_mean > 0) == (out["aggregate"]["delta_candidate_minus_baseline"]["mean"] > 0),
    }

    OUT_PATH.write_text(json.dumps(out, indent=2))
    print("\nWrote", OUT_PATH)
    print("Comparison vs original:", json.dumps(out["comparison_vs_original"], indent=2))


if __name__ == "__main__":
    main()
