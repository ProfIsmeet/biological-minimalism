#!/usr/bin/env python
"""Sleep-EDF EEG vs EEG+EOG marginal-value ablation (Day 7 primary
progression). See docs/SLEEP_EDF_EEG_EOG_PREDECLARATION_DAY7.md for the
full frozen protocol - written and committed before this script produced
any result.

Research question: does adding a synchronized EOG channel to a baseline
EEG configuration improve held-out 5-class sleep-stage classification
under a frozen subject-disjoint protocol?

Baseline: EEG Fpz-Cz only (in_channels=1).
Candidate: EEG Fpz-Cz + EOG horizontal (in_channels=2).
Both share one Conv1DEncoder (unmodified) + Linear(embedding_dim, 5) head
- the only architectural difference is the first-layer input-channel
count, disclosed and quantified before results are inspected.

5 seeds (42-46), weighted cross-entropy (train-only class weights),
macro-F1 primary metric. Does not touch the original single-channel
Sleep-EDF training run (ml/train_sleep_edf.py).
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

from torch import nn, optim  # noqa: E402
from torch.utils.data import DataLoader, TensorDataset  # noqa: E402
from sklearn.metrics import balanced_accuracy_score, confusion_matrix, f1_score  # noqa: E402
from sklearn.utils.class_weight import compute_class_weight  # noqa: E402

from app.ml.models import Conv1DEncoder  # noqa: E402

from ml.datasets.sleep_edf import (  # noqa: E402
    EEG_CHANNEL,
    EOG_CHANNEL,
    STAGE_NAMES,
    load_dataset_windows_multi,
)

RAW_DIR = REPO_ROOT / "datasets" / "sleep-edfx" / "raw"
EXPERIMENT_DIR = REPO_ROOT / "ml" / "experiments" / "sleep_edf_eeg_eog_ablation"
OUT_PATH = REPO_ROOT / "results" / "sleep_edf_eeg_eog_ablation.json"
CKPT_DIR = REPO_ROOT / "ml" / "checkpoints"

EMBEDDING_DIM = 32
EPOCHS = 20
BATCH_SIZE = 64
LR = 0.001
SEEDS = (42, 43, 44, 45, 46)
DEVICE = "cpu"


class SleepStageClassifier(nn.Module):
    """One Conv1DEncoder (in_channels=1 for EEG-only, 2 for EEG+EOG) +
    linear 5-class head - identical for baseline and candidate except
    in_channels, exactly the lesson from the PPG-DaLiA capacity-confound
    repair applied from the start here."""

    def __init__(self, in_channels: int, embedding_dim: int = EMBEDDING_DIM) -> None:
        super().__init__()
        self.encoder = Conv1DEncoder(in_channels=in_channels, embedding_dim=embedding_dim)
        self.head = nn.Linear(embedding_dim, len(STAGE_NAMES))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.head(self.encoder(x))


def load_split_data(subject_ids: list[str], channels: tuple[str, ...]) -> tuple[np.ndarray, np.ndarray]:
    x, y, _subj_idx, _prefixes = load_dataset_windows_multi(RAW_DIR, channels=channels, subject_ids=subject_ids)
    return x, y


def train_one(model: nn.Module, train_x, train_y, val_x, val_y, class_weights: torch.Tensor, seed: int) -> list[dict]:
    torch.manual_seed(seed)
    optimizer = optim.AdamW(model.parameters(), lr=LR)
    loss_fn = nn.CrossEntropyLoss(weight=class_weights)

    train_loader = DataLoader(TensorDataset(torch.from_numpy(train_x), torch.from_numpy(train_y)), batch_size=BATCH_SIZE, shuffle=True)
    val_loader = DataLoader(TensorDataset(torch.from_numpy(val_x), torch.from_numpy(val_y)), batch_size=128, shuffle=False)

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

    return history


@torch.no_grad()
def evaluate_full(model: nn.Module, x: np.ndarray, y: np.ndarray) -> dict:
    model.eval()
    loader = DataLoader(TensorDataset(torch.from_numpy(x)), batch_size=128, shuffle=False)
    preds = []
    for (xb,) in loader:
        preds.append(model(xb).argmax(dim=1).numpy())
    preds = np.concatenate(preds)

    macro_f1 = f1_score(y, preds, average="macro", zero_division=0)
    accuracy = float((preds == y).mean())
    balanced_acc = balanced_accuracy_score(y, preds)
    per_class_f1 = f1_score(y, preds, average=None, labels=list(range(len(STAGE_NAMES))), zero_division=0)
    cm = confusion_matrix(y, preds, labels=list(range(len(STAGE_NAMES))))

    return {
        "macro_f1": float(macro_f1),
        "accuracy": accuracy,
        "balanced_accuracy": float(balanced_acc),
        "per_class_f1": {STAGE_NAMES[i]: float(per_class_f1[i]) for i in range(len(STAGE_NAMES))},
        "confusion_matrix": cm.tolist(),
        "n_epochs_eval": len(y),
        "predictions_class_distribution": {STAGE_NAMES[i]: int((preds == i).sum()) for i in range(len(STAGE_NAMES))},
    }


def main() -> None:
    split = json.loads((EXPERIMENT_DIR / "subject_split.json").read_text())
    print("Using FROZEN split:", json.dumps(split))

    configs = {
        "baseline_eeg_only": (EEG_CHANNEL,),
        "candidate_eeg_plus_eog": (EEG_CHANNEL, EOG_CHANNEL),
    }

    n_params = {name: sum(p.numel() for p in SleepStageClassifier(len(ch)).parameters()) for name, ch in configs.items()}
    print("Parameter counts:", n_params)

    out: dict = {
        "experiment_id": "sleep_edf_eeg_eog_ablation",
        "predeclaration": "docs/SLEEP_EDF_EEG_EOG_PREDECLARATION_DAY7.md",
        "frozen_protocol": {
            "dataset": "PhysioNet Sleep-EDF (sleep-cassette)",
            "subject_split": split,
            "epoch_seconds": 30.0,
            "channels": {name: list(ch) for name, ch in configs.items()},
            "training_hyperparameters": {"epochs": EPOCHS, "batch_size": BATCH_SIZE, "lr": LR, "embedding_dim": EMBEDDING_DIM, "optimizer": "AdamW", "loss": "class-weighted CrossEntropyLoss (train-only weights)"},
            "seeds": list(SEEDS),
            "primary_metric": "macro_f1",
        },
        "parameter_counts": n_params,
        "runs": {name: {} for name in configs},
        "checkpoint_manifest": [],
    }

    print("Loading real data (this parses EDF files, may take a while)...")
    per_config_data = {}
    for name, channels in configs.items():
        train_x, train_y = load_split_data(split["train"], channels)
        val_x, val_y = load_split_data(split["val"], channels)
        test_x, test_y = load_split_data(split["test"], channels)
        per_config_data[name] = (train_x, train_y, val_x, val_y, test_x, test_y)
        print(f"{name}: train={len(train_y)} val={len(val_y)} test={len(test_y)} epochs, shape={train_x.shape}")

    out["window_counts"] = {
        name: {"train": len(data[1]), "val": len(data[3]), "test": len(data[5])}
        for name, data in per_config_data.items()
    }

    for name, channels in configs.items():
        train_x, train_y, val_x, val_y, test_x, test_y = per_config_data[name]
        class_weights_np = compute_class_weight("balanced", classes=np.arange(len(STAGE_NAMES)), y=train_y)
        class_weights = torch.tensor(class_weights_np, dtype=torch.float32)
        print(f"\n{name}: train-only class weights = {class_weights_np.tolist()}")

        for seed in SEEDS:
            run_id = f"{name}_seed{seed}"
            print(f"\n=== seed {seed}: training {run_id} (in_channels={len(channels)}) ===")
            model = SleepStageClassifier(in_channels=len(channels))
            start = time.time()
            history = train_one(model, train_x, train_y, val_x, val_y, class_weights, seed)
            elapsed = time.time() - start

            report = evaluate_full(model, test_x, test_y)
            report["train_seconds"] = elapsed
            report["train_history"] = history
            report["n_parameters"] = n_params[name]
            report["seed"] = seed
            print(f"{run_id}: test macro-F1={report['macro_f1']:.4f} accuracy={report['accuracy']:.4f} ({elapsed:.1f}s)")

            out["runs"][name][f"seed{seed}"] = report

            ckpt_path = CKPT_DIR / f"sleep_edf_{run_id}.pt"
            torch.save(model.state_dict(), ckpt_path)
            ckpt_bytes = ckpt_path.read_bytes()
            out["checkpoint_manifest"].append({
                "run_id": run_id, "config": name, "seed": seed,
                "in_channels": len(channels),
                "path": str(ckpt_path.relative_to(REPO_ROOT)),
                "size_bytes": len(ckpt_bytes), "sha256": hashlib.sha256(ckpt_bytes).hexdigest(),
                "n_parameters": n_params[name],
            })

    # --- Aggregate (sample SD, ddof=1) --------------------------------------
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

    OUT_PATH.write_text(json.dumps(out, indent=2))
    print("\nWrote", OUT_PATH)
    print("Baseline macro-F1:", out["aggregate"]["baseline_macro_f1"])
    print("Candidate macro-F1:", out["aggregate"]["candidate_macro_f1"])
    print("Delta:", out["aggregate"]["delta_candidate_minus_baseline"])


if __name__ == "__main__":
    main()
