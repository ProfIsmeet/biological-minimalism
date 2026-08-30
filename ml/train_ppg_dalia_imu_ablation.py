#!/usr/bin/env python
"""Priority 2 experiment (docs/TECHNICAL_HANDOFF_V2.md §18):

    "How much does synchronized IMU motion information improve wrist-PPG
    heart-rate estimation, particularly under increasing motion corruption?"

Trains two independently-initialized models, identical in architecture family,
hyperparameters, optimizer, epochs, seed, and subject split - the only
difference is which modalities are available:

    Model A - PPG only
    Model B - PPG + synchronized wrist IMU (accelerometer)

Both reuse the project's real, unmodified `Conv1DEncoder` and
`ModalityFusionTransformer` (backend/app/ml/models.py) - this is also the
first real exercise of the masked-mean-pooling fix from
docs/TECHNICAL_HANDOFF_V2.md §16.7 / Phase 13 Step B on genuine data.

Strict subject-wise split: subjects are partitioned into train/val/test once
(seeded), and no window from a test or val subject is ever seen during
training - see `subject_wise_split()`. Ground truth is the real ECG-derived
HR label shipped with PPG-DaLiA; no other HR source is used.

Every artifact this script writes to `ml/experiments/ppg_dalia_imu_ablation/`
is small, version-controlled text (JSON/CSV) - config, seed, subject split,
and results. Trained weights (if --save-checkpoints is passed) go to
`ml/checkpoints/`, which is gitignored.

Usage:
    python train_ppg_dalia_imu_ablation.py
"""

from __future__ import annotations

import argparse
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
from torch import nn, optim  # noqa: E402
from torch.utils.data import DataLoader, TensorDataset  # noqa: E402

from app.ml.models import Conv1DEncoder, ModalityFusionTransformer  # noqa: E402

from ml.datasets.ppg_dalia import ACTIVITY_NAMES, ALL_SUBJECTS, load_cached_subjects  # noqa: E402

EXPERIMENT_DIR = Path(__file__).parent / "experiments" / "ppg_dalia_imu_ablation"


class PPGOnlyHRModel(nn.Module):
    """Model A: a single Conv1DEncoder over the PPG channel, no fusion layer
    at all (there is nothing to fuse with one modality) - the simplest model
    that can honestly use only what it is given."""

    def __init__(self, embedding_dim: int) -> None:
        super().__init__()
        self.encoder = Conv1DEncoder(in_channels=1, embedding_dim=embedding_dim)
        self.head = nn.Linear(embedding_dim, 1)

    def forward(self, ppg: torch.Tensor, acc: torch.Tensor | None = None) -> torch.Tensor:
        return self.head(self.encoder(ppg)).squeeze(-1)


class PPGPlusIMUHRModel(nn.Module):
    """Model B: real per-modality Conv1DEncoders (ppg, imu) + the real
    ModalityFusionTransformer, both modalities always present (mask is
    all-True here - the ablation is "trained with vs. without IMU as an
    input at all", not "trained with IMU then masked out at eval time",
    which would conflate two different questions)."""

    def __init__(self, embedding_dim: int) -> None:
        super().__init__()
        self.ppg_encoder = Conv1DEncoder(in_channels=1, embedding_dim=embedding_dim)
        self.imu_encoder = Conv1DEncoder(in_channels=3, embedding_dim=embedding_dim)
        self.fusion = ModalityFusionTransformer(embedding_dim=embedding_dim, n_heads=4, n_layers=1, n_modalities=2)
        self.head = nn.Linear(embedding_dim, 1)

    def forward(self, ppg: torch.Tensor, acc: torch.Tensor) -> torch.Tensor:
        ppg_emb = self.ppg_encoder(ppg)
        imu_emb = self.imu_encoder(acc)
        tokens = torch.stack([ppg_emb, imu_emb], dim=1)  # (batch, 2, dim)
        mask = torch.ones(ppg.shape[0], 2, dtype=torch.bool, device=ppg.device)
        fused = self.fusion(tokens, modality_mask=mask)
        return self.head(fused).squeeze(-1)


def subject_wise_split(subjects: list[str], n_train: int, n_val: int, seed: int) -> dict[str, list[str]]:
    """Partition subjects (never windows) into train/val/test. Deterministic
    given `seed`; saved to disk so the exact split is reproducible and
    auditable, not just "trust the seed"."""

    rng = np.random.default_rng(seed)
    shuffled = list(subjects)
    rng.shuffle(shuffled)
    return {
        "train": sorted(shuffled[:n_train]),
        "val": sorted(shuffled[n_train : n_train + n_val]),
        "test": sorted(shuffled[n_train + n_val :]),
    }


def build_tensors(subjects_windows) -> dict[str, torch.Tensor | np.ndarray]:
    ppg = np.concatenate([s.ppg for s in subjects_windows])[:, None, :]  # (n, 1, 512)
    acc = np.concatenate([s.acc for s in subjects_windows])  # (n, 3, 256)
    hr = np.concatenate([s.hr for s in subjects_windows])
    activity = np.concatenate([s.activity for s in subjects_windows])
    motion_energy = np.concatenate([s.motion_energy for s in subjects_windows])
    subject_ids = np.concatenate(
        [np.full(len(s.hr), s.subject_id) for s in subjects_windows]
    )
    return {
        "ppg": torch.from_numpy(ppg.astype(np.float32)),
        "acc": torch.from_numpy(acc.astype(np.float32)),
        "hr": torch.from_numpy(hr.astype(np.float32)),
        "activity": activity,
        "motion_energy": motion_energy,
        "subject_ids": subject_ids,
    }


def shuffle_imu_within_subject(data: dict, seed: int) -> dict:
    """Negative control: permute each subject's ACC windows among themselves
    (never across subjects, so per-subject motion *statistics* are
    unchanged), breaking the true temporal correspondence between a given
    PPG/HR window and "its" IMU window.

    If Model C (trained on this) performs close to Model B (real
    synchronization), the earlier PPG+IMU gain would be suspect - explained
    by IMU carrying generic extra dimensions/population-level regularities
    rather than genuine synchronized motion information. If Model C instead
    falls back toward Model A's (PPG-only) performance, that supports the
    synchronization itself being what mattered.
    """

    rng = np.random.default_rng(seed)
    shuffled = data.copy()
    acc = data["acc"].clone()
    for subject_id in sorted(set(data["subject_ids"].tolist())):
        idx = np.where(data["subject_ids"] == subject_id)[0]
        permuted = rng.permutation(idx)
        acc[idx] = data["acc"][permuted]
    shuffled["acc"] = acc
    return shuffled


def train_model(
    model: nn.Module,
    train_data: dict,
    val_data: dict,
    hr_mean: float,
    hr_std: float,
    epochs: int,
    batch_size: int,
    lr: float,
    device: str,
) -> list[dict]:
    optimizer = optim.AdamW(model.parameters(), lr=lr)
    loss_fn = nn.MSELoss()

    train_loader = DataLoader(
        TensorDataset(train_data["ppg"], train_data["acc"], train_data["hr"]),
        batch_size=batch_size, shuffle=True,
    )
    val_loader = DataLoader(
        TensorDataset(val_data["ppg"], val_data["acc"], val_data["hr"]),
        batch_size=batch_size, shuffle=False,
    )

    history = []
    for epoch in range(1, epochs + 1):
        model.train()
        train_loss = 0.0
        for ppg, acc, hr in train_loader:
            ppg, acc, hr = ppg.to(device), acc.to(device), hr.to(device)
            hr_norm = (hr - hr_mean) / hr_std
            optimizer.zero_grad()
            pred = model(ppg, acc)
            loss = loss_fn(pred, hr_norm)
            loss.backward()
            optimizer.step()
            train_loss += float(loss.item()) * len(hr)
        train_loss /= len(train_data["hr"])

        model.eval()
        val_abs_err = 0.0
        with torch.no_grad():
            for ppg, acc, hr in val_loader:
                ppg, acc, hr = ppg.to(device), acc.to(device), hr.to(device)
                pred = model(ppg, acc) * hr_std + hr_mean
                val_abs_err += float((pred - hr).abs().sum().item())
        val_mae = val_abs_err / len(val_data["hr"])

        history.append({"epoch": epoch, "train_loss": train_loss, "val_mae": val_mae})
        print(f"  epoch {epoch:2d}/{epochs} - train loss {train_loss:.4f} | val MAE {val_mae:.3f} bpm")

    return history


@torch.no_grad()
def evaluate(model: nn.Module, data: dict, hr_mean: float, hr_std: float, device: str, batch_size: int = 128) -> np.ndarray:
    model.eval()
    preds = []
    loader = DataLoader(TensorDataset(data["ppg"], data["acc"]), batch_size=batch_size, shuffle=False)
    for ppg, acc in loader:
        ppg, acc = ppg.to(device), acc.to(device)
        pred = model(ppg, acc) * hr_std + hr_mean
        preds.append(pred.cpu().numpy())
    return np.concatenate(preds)


def mae(pred: np.ndarray, target: np.ndarray) -> float:
    return float(np.mean(np.abs(pred - target)))


def rmse(pred: np.ndarray, target: np.ndarray) -> float:
    return float(np.sqrt(np.mean((pred - target) ** 2)))


def stratified_report(pred: np.ndarray, target: np.ndarray, data: dict) -> dict:
    report: dict = {"overall": {"mae": mae(pred, target), "rmse": rmse(pred, target), "n_windows": len(target)}}

    per_subject = {}
    for subject_id in sorted(set(data["subject_ids"].tolist())):
        mask = data["subject_ids"] == subject_id
        per_subject[subject_id] = {
            "mae": mae(pred[mask], target[mask]),
            "rmse": rmse(pred[mask], target[mask]),
            "n_windows": int(mask.sum()),
        }
    report["per_subject"] = per_subject

    per_activity = {}
    for activity_id in sorted(set(data["activity"].tolist())):
        mask = data["activity"] == activity_id
        if mask.sum() == 0:
            continue
        per_activity[ACTIVITY_NAMES.get(int(activity_id), str(activity_id))] = {
            "mae": mae(pred[mask], target[mask]),
            "rmse": rmse(pred[mask], target[mask]),
            "n_windows": int(mask.sum()),
        }
    report["per_activity"] = per_activity

    motion = data["motion_energy"]
    quartile_edges = np.quantile(motion, [0.0, 0.25, 0.5, 0.75, 1.0])
    quartile_labels = ["q1_lowest_motion", "q2", "q3", "q4_highest_motion"]
    per_motion_quartile = {}
    for i, label in enumerate(quartile_labels):
        lo, hi = quartile_edges[i], quartile_edges[i + 1]
        mask = (motion >= lo) & (motion <= hi) if i == len(quartile_labels) - 1 else (motion >= lo) & (motion < hi)
        if mask.sum() == 0:
            continue
        per_motion_quartile[label] = {
            "mae": mae(pred[mask], target[mask]),
            "rmse": rmse(pred[mask], target[mask]),
            "n_windows": int(mask.sum()),
            "motion_energy_range": [float(lo), float(hi)],
        }
    report["per_motion_quartile"] = per_motion_quartile

    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache-dir", type=str, default=str(REPO_ROOT / "datasets" / "ppg-dalia" / "processed"))
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--n-train-subjects", type=int, default=10)
    parser.add_argument("--n-val-subjects", type=int, default=2)
    parser.add_argument("--embedding-dim", type=int, default=32)
    parser.add_argument("--epochs", type=int, default=20)
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--save-checkpoints", action="store_true")
    parser.add_argument(
        "--negative-control",
        action="store_true",
        help="Also train Model C: PPG + temporally shuffled/misaligned IMU (same subject's own "
        "ACC windows, permuted so they no longer correspond to the right PPG/HR window). Tests "
        "whether Model B's gain comes from genuine synchronized motion information or merely from "
        "having extra input dimensions.",
    )
    parser.add_argument(
        "--only-negative-control",
        action="store_true",
        help="Skip re-training Models A and B; reuse their results from an existing results.json "
        "in the experiment directory (must already exist) and train only Model C. Saves ~15-20 "
        "minutes when A/B results are already on disk from a prior run with the same config/seed/split.",
    )
    args = parser.parse_args()

    torch.manual_seed(args.seed)
    np.random.seed(args.seed)

    EXPERIMENT_DIR.mkdir(parents=True, exist_ok=True)

    config = vars(args)
    print("Config:", json.dumps(config, indent=2))
    (EXPERIMENT_DIR / "config.json").write_text(json.dumps(config, indent=2))

    split = subject_wise_split(list(ALL_SUBJECTS), args.n_train_subjects, args.n_val_subjects, args.seed)
    print("Subject split:", json.dumps(split, indent=2))
    (EXPERIMENT_DIR / "subject_split.json").write_text(json.dumps(split, indent=2))

    print("Loading cached windows...")
    train_windows = load_cached_subjects(args.cache_dir, split["train"])
    val_windows = load_cached_subjects(args.cache_dir, split["val"])
    test_windows = load_cached_subjects(args.cache_dir, split["test"])

    train_data = build_tensors(train_windows)
    val_data = build_tensors(val_windows)
    test_data = build_tensors(test_windows)
    print(f"train windows: {len(train_data['hr'])} | val windows: {len(val_data['hr'])} | test windows: {len(test_data['hr'])}")

    hr_mean = float(train_data["hr"].mean())
    hr_std = float(train_data["hr"].std() + 1e-6)

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Device: {device}")

    if args.only_negative_control:
        existing = json.loads((EXPERIMENT_DIR / "results.json").read_text())
        assert existing["subject_split"] == split, (
            "existing results.json was produced with a different subject split - "
            "re-run without --only-negative-control to regenerate A/B consistently first."
        )
        results = existing
        runs: list[tuple[str, type, dict, dict]] = []
    else:
        results = {"config": config, "subject_split": split, "hr_normalization": {"mean": hr_mean, "std": hr_std}}
        runs = [
            ("model_a_ppg_only", PPGOnlyHRModel, train_data, test_data),
            ("model_b_ppg_plus_imu", PPGPlusIMUHRModel, train_data, test_data),
        ]

    if args.negative_control or args.only_negative_control:
        shuffled_train = shuffle_imu_within_subject(train_data, seed=args.seed)
        shuffled_val = shuffle_imu_within_subject(val_data, seed=args.seed)
        shuffled_test = shuffle_imu_within_subject(test_data, seed=args.seed)
        runs.append(("model_c_ppg_plus_shuffled_imu", PPGPlusIMUHRModel, shuffled_train, shuffled_test))

    for name, model_cls, this_train_data, this_test_data in runs:
        print(f"\n=== Training {name} ===")
        torch.manual_seed(args.seed)  # re-seed so all models start from equivalent init conditions
        model = model_cls(args.embedding_dim).to(device)
        start = time.time()
        this_val_data = shuffled_val if name == "model_c_ppg_plus_shuffled_imu" else val_data
        history = train_model(model, this_train_data, this_val_data, hr_mean, hr_std, args.epochs, args.batch_size, args.lr, device)
        elapsed = time.time() - start

        pred = evaluate(model, this_test_data, hr_mean, hr_std, device)
        target = this_test_data["hr"].numpy()
        report = stratified_report(pred, target, this_test_data)
        report["train_seconds"] = elapsed
        report["train_history"] = history

        print(f"{name}: held-out test MAE {report['overall']['mae']:.3f} bpm, RMSE {report['overall']['rmse']:.3f} bpm "
              f"({report['overall']['n_windows']} windows, {elapsed:.1f}s to train)")

        results[name] = report

        if args.save_checkpoints:
            ckpt_dir = Path(__file__).parent / "checkpoints"
            ckpt_dir.mkdir(exist_ok=True)
            torch.save(model.state_dict(), ckpt_dir / f"{name}_ppg_dalia.pt")

    mae_a = results["model_a_ppg_only"]["overall"]["mae"]
    mae_b = results["model_b_ppg_plus_imu"]["overall"]["mae"]
    delta = mae_a - mae_b
    results["summary"] = {
        "model_a_mae": mae_a,
        "model_b_mae": mae_b,
        "mae_improvement_from_imu": delta,
        "imu_helped": bool(delta > 0),
        "note": (
            "Positive mae_improvement_from_imu means Model B (PPG+IMU) had LOWER "
            "error than Model A (PPG-only), i.e. IMU helped. A negative or "
            "near-zero value means IMU did not help (or hurt) under these "
            "conditions - reported as-is, not adjusted."
        ),
    }
    print(f"\n=== Summary ===\nModel A (PPG only) MAE: {mae_a:.3f} bpm\nModel B (PPG+IMU) MAE: {mae_b:.3f} bpm\n"
          f"MAE improvement from IMU: {delta:+.3f} bpm ({'IMU helped' if delta > 0 else 'IMU did NOT help'})")

    if "model_c_ppg_plus_shuffled_imu" in results:
        mae_c = results["model_c_ppg_plus_shuffled_imu"]["overall"]["mae"]
        results["summary"]["model_c_shuffled_imu_mae"] = mae_c
        results["summary"]["negative_control_note"] = (
            "Model C uses the same architecture as Model B but with each subject's own ACC "
            "windows randomly permuted among themselves, breaking true PPG<->IMU temporal "
            "correspondence while preserving per-subject motion statistics. If Model C's MAE is "
            "close to Model B's, Model B's gain over Model A may come from IMU carrying generic "
            "extra dimensions/population regularities rather than genuine synchronization. If "
            "Model C's MAE falls back toward Model A's, that supports synchronization itself "
            "mattering. Reported as observed, not adjusted toward either interpretation."
        )
        print(f"Model C (PPG + shuffled IMU) MAE: {mae_c:.3f} bpm  "
              f"[A={mae_a:.3f}, B={mae_b:.3f}, C={mae_c:.3f}]")

    (EXPERIMENT_DIR / "results.json").write_text(json.dumps(results, indent=2))

    # Small, flat CSV summary alongside the full JSON, for quick scanning/spreadsheet use.
    import csv

    with open(EXPERIMENT_DIR / "results_summary.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["model", "mae_bpm", "rmse_bpm", "n_windows"])
        for name in ("model_a_ppg_only", "model_b_ppg_plus_imu", "model_c_ppg_plus_shuffled_imu"):
            if name not in results:
                continue
            o = results[name]["overall"]
            writer.writerow([name, f"{o['mae']:.4f}", f"{o['rmse']:.4f}", o["n_windows"]])

    print(f"\nResults written to {EXPERIMENT_DIR}")


if __name__ == "__main__":
    main()
