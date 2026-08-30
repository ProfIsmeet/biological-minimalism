#!/usr/bin/env python
"""Real training run: `Conv1DEncoder` (from `backend/app/ml/models.py`)
trained on real BIDMC PPG data to predict real heart rate and respiration
rate from 8-second PPG windows - real regression targets, directly matching
two of this project's actual `OUTPUT_TARGETS` (`heart_rate_bpm`,
`respiration_rate_bpm`).

See `ml/datasets/bidmc_ppg.py`'s module docstring for why BIDMC was used in
place of WESAD (WESAD's two official links were both confirmed dead - see
`ml/datasets/sleep_edf.py`).

Usage:
    python train_ppg.py --data-dir ../datasets/bidmc-ppg/raw --epochs 15
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

from ml.datasets.bidmc_ppg import load_dataset_windows  # noqa: E402


class PPGVitalsRegressor(nn.Module):
    """Real `Conv1DEncoder` (unmodified) + two real regression heads
    (heart rate, respiration rate) - the same two-headed structure
    `BiologicalDigitalTwinNet` uses per-target, just for one modality."""

    def __init__(self, embedding_dim: int = 64) -> None:
        super().__init__()
        self.encoder = Conv1DEncoder(in_channels=1, embedding_dim=embedding_dim)
        self.hr_head = nn.Linear(embedding_dim, 1)
        self.resp_head = nn.Linear(embedding_dim, 1)

    def forward(self, x: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        embedding = self.encoder(x)
        return self.hr_head(embedding).squeeze(-1), self.resp_head(embedding).squeeze(-1)


def subject_level_split(subject_ids: np.ndarray, test_fraction: float, seed: int) -> tuple[np.ndarray, np.ndarray]:
    unique_subjects = np.unique(subject_ids)
    rng = np.random.default_rng(seed)
    rng.shuffle(unique_subjects)
    n_test = max(1, int(round(len(unique_subjects) * test_fraction)))
    test_subjects = set(unique_subjects[:n_test].tolist())
    test_mask = np.isin(subject_ids, list(test_subjects))
    return ~test_mask, test_mask


def run_epoch(
    model: nn.Module,
    loader: DataLoader,
    optimizer: optim.Optimizer | None,
    device: str,
    hr_mean: float,
    hr_std: float,
    resp_mean: float,
    resp_std: float,
) -> tuple[float, float, float]:
    is_train = optimizer is not None
    model.train(is_train)
    loss_fn = nn.MSELoss()
    total_loss, hr_abs_err, resp_abs_err, n = 0.0, 0.0, 0.0, 0

    for xb, hr_b, resp_b in loader:
        xb, hr_b, resp_b = xb.to(device), hr_b.to(device), resp_b.to(device)
        hr_target_norm = (hr_b - hr_mean) / hr_std
        resp_target_norm = (resp_b - resp_mean) / resp_std
        with torch.set_grad_enabled(is_train):
            hr_pred_norm, resp_pred_norm = model(xb)
            loss = loss_fn(hr_pred_norm, hr_target_norm) + loss_fn(resp_pred_norm, resp_target_norm)
            if is_train:
                optimizer.zero_grad()
                loss.backward()
                optimizer.step()
        total_loss += float(loss.item()) * len(hr_b)
        hr_pred = hr_pred_norm.detach() * hr_std + hr_mean
        resp_pred = resp_pred_norm.detach() * resp_std + resp_mean
        hr_abs_err += float((hr_pred - hr_b).abs().sum().item())
        resp_abs_err += float((resp_pred - resp_b).abs().sum().item())
        n += len(hr_b)

    return total_loss / max(n, 1), hr_abs_err / max(n, 1), resp_abs_err / max(n, 1)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=str, default=str(REPO_ROOT / "datasets" / "bidmc-ppg" / "raw"))
    parser.add_argument("--epochs", type=int, default=15)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--test-fraction", type=float, default=0.3)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output", type=str, default=str(Path(__file__).parent / "checkpoints" / "ppg_encoder_bidmc.pt"))
    args = parser.parse_args()

    torch.manual_seed(args.seed)

    print(f"Loading real BIDMC PPG windows from {args.data_dir} ...")
    x, hr, resp, subject_ids = load_dataset_windows(args.data_dir)
    print(f"Loaded {len(hr)} real 8s PPG windows from {len(np.unique(subject_ids))} subjects.")
    print(f"Real HR range: {hr.min():.0f}-{hr.max():.0f} bpm, real RESP range: {resp.min():.0f}-{resp.max():.0f} /min.")

    train_mask, test_mask = subject_level_split(subject_ids, args.test_fraction, args.seed)
    print(f"Subject-level split: {train_mask.sum()} train windows, {test_mask.sum()} test windows "
          f"({len(np.unique(subject_ids[train_mask]))} train subjects, {len(np.unique(subject_ids[test_mask]))} test subjects).")

    hr_mean, hr_std = float(hr[train_mask].mean()), float(hr[train_mask].std() + 1e-6)
    resp_mean, resp_std = float(resp[train_mask].mean()), float(resp[train_mask].std() + 1e-6)

    device = "cuda" if torch.cuda.is_available() else "cpu"
    train_loader = DataLoader(
        TensorDataset(torch.from_numpy(x[train_mask]), torch.from_numpy(hr[train_mask]), torch.from_numpy(resp[train_mask])),
        batch_size=args.batch_size, shuffle=True,
    )
    test_loader = DataLoader(
        TensorDataset(torch.from_numpy(x[test_mask]), torch.from_numpy(hr[test_mask]), torch.from_numpy(resp[test_mask])),
        batch_size=args.batch_size, shuffle=False,
    )

    model = PPGVitalsRegressor().to(device)
    optimizer = optim.AdamW(model.parameters(), lr=args.lr)

    naive_hr_mae = float(np.abs(hr[test_mask] - hr_mean).mean())
    naive_resp_mae = float(np.abs(resp[test_mask] - resp_mean).mean())
    print(f"Naive baseline (predict train-set mean): HR MAE {naive_hr_mae:.2f} bpm, RESP MAE {naive_resp_mae:.2f} /min.")

    print(f"Training real Conv1DEncoder on device={device} ...")
    for epoch in range(1, args.epochs + 1):
        train_loss, train_hr_mae, train_resp_mae = run_epoch(model, train_loader, optimizer, device, hr_mean, hr_std, resp_mean, resp_std)
        _, test_hr_mae, test_resp_mae = run_epoch(model, test_loader, None, device, hr_mean, hr_std, resp_mean, resp_std)
        print(f"epoch {epoch:2d}/{args.epochs} - train loss {train_loss:.4f} (HR MAE {train_hr_mae:.2f}, RESP MAE {train_resp_mae:.2f}) | "
              f"held-out HR MAE {test_hr_mae:.2f} bpm, RESP MAE {test_resp_mae:.2f} /min")

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(
        {
            "encoder_state_dict": model.encoder.state_dict(),
            "hr_head_state_dict": model.hr_head.state_dict(),
            "resp_head_state_dict": model.resp_head.state_dict(),
            "hr_mean": hr_mean, "hr_std": hr_std, "resp_mean": resp_mean, "resp_std": resp_std,
            "final_test_hr_mae": test_hr_mae, "final_test_resp_mae": test_resp_mae,
            "naive_hr_mae": naive_hr_mae, "naive_resp_mae": naive_resp_mae,
            "train_subjects": int(len(np.unique(subject_ids[train_mask]))),
            "test_subjects": int(len(np.unique(subject_ids[test_mask]))),
        },
        output_path,
    )
    print(f"Saved real trained checkpoint to {output_path}.")
    print(f"Final: held-out HR MAE {test_hr_mae:.2f} bpm (naive {naive_hr_mae:.2f}), "
          f"RESP MAE {test_resp_mae:.2f} /min (naive {naive_resp_mae:.2f}).")


if __name__ == "__main__":
    main()
