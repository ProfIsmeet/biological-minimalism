#!/usr/bin/env python
"""Real training run: `Conv1DEncoder` (from `backend/app/ml/models.py`) trained
on real PhysioNet Sleep-EDF EEG data to classify sleep stage (Wake/N1/N2/N3/REM)
from 30-second EEG windows.

Why this script exists: the project's original scope (per the PDD) explicitly
left the CNN+Transformer fusion network untrained, using WESAD/STEW/PulseDB/
NASA OSDR as the eventual real-data source. This script is the first actual
training run against real, downloaded, open physiological data - using the
project's real `Conv1DEncoder` architecture unmodified, on real Sleep-EDF EEG
(substituted for WESAD, whose two official distribution links were both
independently verified dead - see `ml/datasets/sleep_edf.py`'s module
docstring). It does not train the full 4-modality fusion network (no real
PPG/bio-impedance data source was available in this pass) - it trains and
validates the EEG encoder pathway specifically, honestly, on a subject-level
held-out split.

Usage:
    python train_sleep_edf.py --data-dir ../datasets/sleep-edfx/raw \
        --epochs 15 --output checkpoints/eeg_encoder_sleep_edf.pt
"""

from __future__ import annotations

import argparse
import sys
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

from app.ml.models import Conv1DEncoder  # noqa: E402

from ml.datasets.sleep_edf import STAGE_NAMES, load_dataset_windows  # noqa: E402


class EEGSleepStageClassifier(nn.Module):
    """Real `Conv1DEncoder` (unmodified, imported from the project's own
    model file) + a linear classification head over sleep stage."""

    def __init__(self, embedding_dim: int = 64, n_classes: int = 5) -> None:
        super().__init__()
        self.encoder = Conv1DEncoder(in_channels=1, embedding_dim=embedding_dim)
        self.head = nn.Linear(embedding_dim, n_classes)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.head(self.encoder(x))


def subject_level_split(subject_ids: np.ndarray, test_fraction: float, seed: int) -> tuple[np.ndarray, np.ndarray]:
    """Hold out whole subjects for testing, never individual epochs - epoch-
    level splitting would leak the same subject's physiology into both train
    and test and overstate accuracy."""

    unique_subjects = np.unique(subject_ids)
    rng = np.random.default_rng(seed)
    rng.shuffle(unique_subjects)
    n_test = max(1, int(round(len(unique_subjects) * test_fraction)))
    test_subjects = set(unique_subjects[:n_test].tolist())
    test_mask = np.isin(subject_ids, list(test_subjects))
    return ~test_mask, test_mask


def run_epoch(model: nn.Module, loader: DataLoader, optimizer: optim.Optimizer | None, device: str) -> tuple[float, float]:
    is_train = optimizer is not None
    model.train(is_train)
    total_loss, correct, total = 0.0, 0, 0
    loss_fn = nn.CrossEntropyLoss()
    for xb, yb in loader:
        xb, yb = xb.to(device), yb.to(device)
        with torch.set_grad_enabled(is_train):
            logits = model(xb)
            loss = loss_fn(logits, yb)
            if is_train:
                optimizer.zero_grad()
                loss.backward()
                optimizer.step()
        total_loss += float(loss.item()) * len(yb)
        correct += int((logits.argmax(dim=1) == yb).sum().item())
        total += len(yb)
    return total_loss / max(total, 1), correct / max(total, 1)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=str, default=str(REPO_ROOT / "datasets" / "sleep-edfx" / "raw"))
    parser.add_argument("--epochs", type=int, default=15)
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--test-fraction", type=float, default=1.0 / 3.0)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output", type=str, default=str(Path(__file__).parent / "checkpoints" / "eeg_encoder_sleep_edf.pt"))
    args = parser.parse_args()

    torch.manual_seed(args.seed)

    print(f"Loading real Sleep-EDF windows from {args.data_dir} ...")
    x, y, subject_ids = load_dataset_windows(args.data_dir)
    print(f"Loaded {len(y)} real 30s EEG epochs from {len(np.unique(subject_ids))} subjects.")
    for i, name in enumerate(STAGE_NAMES):
        print(f"  {name}: {int((y == i).sum())} epochs")

    train_mask, test_mask = subject_level_split(subject_ids, args.test_fraction, args.seed)
    print(f"Subject-level split: {train_mask.sum()} train epochs, {test_mask.sum()} test epochs "
          f"({len(np.unique(subject_ids[train_mask]))} train subjects, {len(np.unique(subject_ids[test_mask]))} test subjects).")

    device = "cuda" if torch.cuda.is_available() else "cpu"
    train_ds = TensorDataset(torch.from_numpy(x[train_mask]), torch.from_numpy(y[train_mask]))
    test_ds = TensorDataset(torch.from_numpy(x[test_mask]), torch.from_numpy(y[test_mask]))
    train_loader = DataLoader(train_ds, batch_size=args.batch_size, shuffle=True)
    test_loader = DataLoader(test_ds, batch_size=args.batch_size, shuffle=False)

    model = EEGSleepStageClassifier().to(device)
    optimizer = optim.AdamW(model.parameters(), lr=args.lr)

    print(f"Training real Conv1DEncoder on device={device} ...")
    for epoch in range(1, args.epochs + 1):
        train_loss, train_acc = run_epoch(model, train_loader, optimizer, device)
        test_loss, test_acc = run_epoch(model, test_loader, None, device)
        print(f"epoch {epoch:2d}/{args.epochs} - train loss {train_loss:.4f} acc {train_acc:.3f} | "
              f"held-out test loss {test_loss:.4f} acc {test_acc:.3f}")

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(
        {
            "encoder_state_dict": model.encoder.state_dict(),
            "head_state_dict": model.head.state_dict(),
            "stage_names": STAGE_NAMES,
            "final_test_accuracy": test_acc,
            "train_subjects": int(len(np.unique(subject_ids[train_mask]))),
            "test_subjects": int(len(np.unique(subject_ids[test_mask]))),
        },
        output_path,
    )
    print(f"Saved real trained checkpoint to {output_path} (held-out subject test accuracy: {test_acc:.1%}).")


if __name__ == "__main__":
    main()
