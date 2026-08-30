#!/usr/bin/env python
"""Real training run: a small regressor trained on real PhysioNet QDE
bio-impedance + temperature data to predict total body water (TBW), as a
real-data proxy for this project's fluid-shift target (PDD Section 8).

See `ml/datasets/qde_bioimpedance.py`'s module docstring for why this dataset
was substituted for NASA OSDR (whose public search API returned no
downloadable raw bio-impedance sensor time series - it is a molecular-biology
repository, not a physiological-signal one - verified directly, not assumed).

This is a small (10 subjects, 90 measurement points), tabular dataset, not a
high-sample-rate waveform - so it uses a small MLP over the real 16 features
(5 bio-impedance + 11 temperature), not `Conv1DEncoder` (which is designed
for windowed time-series, the shape EEG/PPG data actually has - see
`train_sleep_edf.py` / `train_ppg.py`). Reported with this scale's honest
statistical weight: 10 subjects is small, and the held-out result below
should be read as "the real signal carries real information," not as a
production accuracy estimate.

Usage:
    python train_bioimpedance.py --csv ../datasets/qde-bioimpedance/raw/dehydration_estimation.csv
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

from ml.datasets.qde_bioimpedance import FEATURE_COLUMNS, load_dataset  # noqa: E402


class FluidStatusRegressor(nn.Module):
    """Small MLP: real bio-impedance + temperature features -> total body water.

    Kept deliberately small (16 -> 32 -> 16 -> 1) given only 90 real
    measurement points across 10 subjects - a bigger network would just
    memorize subjects rather than learn a generalizable relationship.
    """

    def __init__(self, n_features: int) -> None:
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(n_features, 32),
            nn.GELU(),
            nn.Linear(32, 16),
            nn.GELU(),
            nn.Linear(16, 1),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x).squeeze(-1)


def leave_one_subject_out_cv(x: np.ndarray, y: np.ndarray, subject_ids: np.ndarray, epochs: int, lr: float, seed: int) -> list[float]:
    """Leave-one-subject-out cross-validation - with only 10 subjects, this
    is the honest way to use every subject as a held-out test once, rather
    than a single arbitrary train/test split that could get lucky or unlucky."""

    torch.manual_seed(seed)
    feature_mean, feature_std = x.mean(axis=0), x.std(axis=0) + 1e-6
    x_norm = (x - feature_mean) / feature_std

    maes: list[float] = []
    for held_out in np.unique(subject_ids):
        train_mask = subject_ids != held_out
        test_mask = ~train_mask

        model = FluidStatusRegressor(x.shape[1])
        optimizer = optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-3)
        loss_fn = nn.MSELoss()

        xb_train = torch.from_numpy(x_norm[train_mask])
        yb_train = torch.from_numpy(y[train_mask])
        xb_test = torch.from_numpy(x_norm[test_mask])
        yb_test = torch.from_numpy(y[test_mask])

        model.train()
        for _ in range(epochs):
            optimizer.zero_grad()
            pred = model(xb_train)
            loss = loss_fn(pred, yb_train)
            loss.backward()
            optimizer.step()

        model.eval()
        with torch.no_grad():
            test_pred = model(xb_test)
            mae = float((test_pred - yb_test).abs().mean().item())
        maes.append(mae)
        print(f"  held out subject {held_out}: {test_mask.sum()} points, MAE {mae:.3f} L")

    return maes


def to_within_subject_deltas(x: np.ndarray, y: np.ndarray, subject_ids: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Convert absolute features/target to change-from-each-subject's-own-
    baseline (their first, pre-exercise measurement row).

    This is the more honestly-motivated framing for this project's actual
    use case: the Digital Twin (PDD Section 12) cares about an individual's
    deviation from their *own* baseline, not an absolute cross-subject
    value — and absolute bio-impedance is heavily confounded by body size,
    limb length, and electrode placement, none of which this project's
    fluid-*shift* target is actually trying to predict.
    """

    x_delta = np.zeros_like(x)
    y_delta = np.zeros_like(y)
    for subject in np.unique(subject_ids):
        mask = subject_ids == subject
        idx = np.where(mask)[0]
        baseline_idx = idx[0]  # first (pre-exercise) row for this subject
        x_delta[idx] = x[idx] - x[baseline_idx]
        y_delta[idx] = y[idx] - y[baseline_idx]
    return x_delta, y_delta


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", type=str, default=str(REPO_ROOT / "datasets" / "qde-bioimpedance" / "raw" / "dehydration_estimation.csv"))
    parser.add_argument("--epochs", type=int, default=300)
    parser.add_argument("--lr", type=float, default=5e-3)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument(
        "--target-mode",
        choices=["absolute", "within_subject_delta"],
        default="within_subject_delta",
        help="'absolute': predict raw total body water (confounded by body size across subjects - see README). "
        "'within_subject_delta': predict each subject's change from their own baseline - this project's actual "
        "fluid-*shift* framing (default).",
    )
    args = parser.parse_args()

    print(f"Loading real QDE bio-impedance/temperature data from {args.csv} ...")
    x, y, subject_ids = load_dataset(args.csv)
    print(f"Loaded {len(y)} real measurement points from {len(np.unique(subject_ids))} subjects.")
    print(f"Features: {FEATURE_COLUMNS}")
    print(f"Target (total body water) range: {y.min():.1f}L - {y.max():.1f}L, mean {y.mean():.1f}L")

    if args.target_mode == "within_subject_delta":
        x, y = to_within_subject_deltas(x, y, subject_ids)
        print(f"Reframed as within-subject delta from baseline. Delta range: {y.min():.2f}L to {y.max():.2f}L "
              f"(mean {y.mean():.2f}L, i.e. average fluid loss by end of protocol).")

    print(f"\nRunning leave-one-subject-out cross-validation ({len(np.unique(subject_ids))} folds) ...")
    maes = leave_one_subject_out_cv(x, y, subject_ids, args.epochs, args.lr, args.seed)

    naive_baseline_mae = float(np.mean([np.abs(y[subject_ids == s] - np.mean(y[subject_ids != s])).mean() for s in np.unique(subject_ids)]))

    print(f"\nMean held-out MAE across all {len(maes)} subjects: {np.mean(maes):.3f} L (std {np.std(maes):.3f} L)")
    print(f"Naive baseline (predict other subjects' mean {'TBW' if args.target_mode == 'absolute' else 'TBW delta'}): {naive_baseline_mae:.3f} L MAE")


if __name__ == "__main__":
    main()
