#!/usr/bin/env python
"""GalaxyPPG external HR replication (Stage 2B): capacity-controlled
PPG-only (A_cap) vs PPG+IMU (B) vs PPG+deranged-IMU (C), on real GalaxyPPG
data. Reuses the project's real Conv1DEncoder/ModalityFusionTransformer
(backend/app/ml/models.py) and the exact capacity-control philosophy
already established for PPG-DaLiA (ml/train_ppg_dalia_capacity_control.py):
A_cap uses two independent encoders BOTH fed real BVP (no IMU, no zeros).

Real reference HR: R-peak-derived from real Polar H10 ECG
(ml/datasets/galaxyppg.py), never any device-derived HR. Real,
UTC+9-corrected cross-device synchronization (the bug found and fixed this
sprint).

BOUNDED_TO_SINGLE_FOLD (see docs/GALAXYPPG_SPLIT_STRATEGY_DEVIATION.md):
one fixed 16/4/4 train/val/test split, not the frozen protocol's full
6-fold grouped CV (compute-infeasible this sprint) - versioned deviation,
frozen before any training.
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

from torch import nn  # noqa: E402
from torch.utils.data import DataLoader, TensorDataset  # noqa: E402

from app.ml.models import Conv1DEncoder, ModalityFusionTransformer  # noqa: E402

from ml.datasets.galaxyppg import build_participant_windows  # noqa: E402

DATA_DIR = REPO_ROOT / "datasets" / "galaxyppg" / "raw" / "extracted" / "Dataset"
SPLIT_PATH = REPO_ROOT / "results" / "galaxyppg_split_stage2_single_fold.json"
OUT_PATH = REPO_ROOT / "results" / "galaxyppg_hr_external_replication_stage2.json"
CKPT_DIR = REPO_ROOT / "ml" / "checkpoints"

EMBEDDING_DIM = 32
EPOCHS = 20
BATCH_SIZE = 64
LR = 0.001
SEEDS = (42, 43, 44, 45, 46)
CONTROL_SHUFFLE_SEED_BASE = 200042


class PPGCapacityMatchedModel(nn.Module):
    """A_cap: two independent encoders, BOTH fed real BVP - capacity-matched
    to B/C, no IMU information, same pattern as
    ml/train_ppg_dalia_capacity_control.py::PPGCapacityMatchedModel."""

    def __init__(self, embedding_dim: int = EMBEDDING_DIM) -> None:
        super().__init__()
        self.ppg_encoder_1 = Conv1DEncoder(in_channels=1, embedding_dim=embedding_dim)
        self.ppg_encoder_2 = Conv1DEncoder(in_channels=1, embedding_dim=embedding_dim)
        self.fusion = ModalityFusionTransformer(embedding_dim=embedding_dim, n_heads=4, n_layers=1, n_modalities=2)
        self.head = nn.Linear(embedding_dim, 1)

    def forward(self, ppg: torch.Tensor, _unused: torch.Tensor | None = None) -> torch.Tensor:
        e1 = self.ppg_encoder_1(ppg)
        e2 = self.ppg_encoder_2(ppg)
        tokens = torch.stack([e1, e2], dim=1)
        mask = torch.ones(ppg.shape[0], 2, dtype=torch.bool, device=ppg.device)
        fused = self.fusion(tokens, modality_mask=mask)
        return self.head(fused).squeeze(-1)


class PPGPlusIMUModel(nn.Module):
    """B/C: real per-modality encoders (BVP 1ch, ACC 3ch) + fusion."""

    def __init__(self, embedding_dim: int = EMBEDDING_DIM) -> None:
        super().__init__()
        self.ppg_encoder = Conv1DEncoder(in_channels=1, embedding_dim=embedding_dim)
        self.acc_encoder = Conv1DEncoder(in_channels=3, embedding_dim=embedding_dim)
        self.fusion = ModalityFusionTransformer(embedding_dim=embedding_dim, n_heads=4, n_layers=1, n_modalities=2)
        self.head = nn.Linear(embedding_dim, 1)

    def forward(self, ppg: torch.Tensor, acc: torch.Tensor) -> torch.Tensor:
        e1 = self.ppg_encoder(ppg)
        e2 = self.acc_encoder(acc)
        tokens = torch.stack([e1, e2], dim=1)
        mask = torch.ones(ppg.shape[0], 2, dtype=torch.bool, device=ppg.device)
        fused = self.fusion(tokens, modality_mask=mask)
        return self.head(fused).squeeze(-1)


def load_split_windows(participant_ids: list[str]) -> dict:
    all_bvp, all_acc, all_hr, all_subj = [], [], [], []
    for pid in participant_ids:
        w = build_participant_windows(DATA_DIR, pid)
        n = len(w["hr"])
        if n == 0:
            continue
        all_bvp.append(w["bvp_windows"])
        all_acc.append(w["acc_windows"])
        all_hr.append(w["hr"])
        all_subj.extend([pid] * n)
    return {
        "bvp": np.concatenate(all_bvp).astype(np.float32),
        "acc": np.concatenate(all_acc).astype(np.float32),
        "hr": np.concatenate(all_hr).astype(np.float32),
        "subject": np.array(all_subj),
    }


def deranged_acc_stable(acc: np.ndarray, subject: np.ndarray, seed_base: int) -> np.ndarray:
    """Within-subject temporal derangement of ACC windows: for each subject,
    permute (no fixed points) which window's ACC segment is attached to
    which BVP/HR window. Never crosses subjects, never touches labels.
    Seed derived from a stable per-subject index (sorted order), not
    Python's non-deterministic string hash()."""
    out = acc.copy()
    unique_subjects = sorted(set(subject.tolist()))
    for i, pid in enumerate(unique_subjects):
        idx = np.where(subject == pid)[0]
        n = len(idx)
        if n < 2:
            continue
        rng = np.random.default_rng(seed_base + i)
        perm = np.arange(n)
        for _ in range(1000):
            rng.shuffle(perm)
            if not np.any(perm == np.arange(n)):
                break
        out[idx] = acc[idx][perm]
    return out


def normalize_fit(x: np.ndarray) -> tuple[float, float]:
    return float(x.mean()), float(x.std() + 1e-6)


def train_one(model: nn.Module, train_bvp, train_acc, train_hr_norm, val_bvp, val_acc, val_hr_norm, run_seed: int) -> list[dict]:
    torch.manual_seed(run_seed)  # seeded before construction by caller
    optimizer = torch.optim.AdamW(model.parameters(), lr=LR)
    loss_fn = nn.MSELoss()

    train_loader = DataLoader(
        TensorDataset(torch.from_numpy(train_bvp), torch.from_numpy(train_acc), torch.from_numpy(train_hr_norm)),
        batch_size=BATCH_SIZE, shuffle=True,
    )
    history = []
    for epoch in range(1, EPOCHS + 1):
        model.train()
        train_loss = 0.0
        for bvp, acc, hr in train_loader:
            optimizer.zero_grad()
            pred = model(bvp.unsqueeze(1), acc)
            loss = loss_fn(pred, hr)
            loss.backward()
            optimizer.step()
            train_loss += float(loss.item()) * len(hr)
        train_loss /= len(train_hr_norm)

        model.eval()
        with torch.no_grad():
            val_pred = model(torch.from_numpy(val_bvp).unsqueeze(1), torch.from_numpy(val_acc))
            val_loss = float(loss_fn(val_pred, torch.from_numpy(val_hr_norm)).item())
        history.append({"epoch": epoch, "train_loss": train_loss, "val_loss": val_loss})
    return history


def evaluate(model: nn.Module, bvp, acc, hr_true, hr_mean, hr_std) -> dict:
    model.eval()
    with torch.no_grad():
        pred_norm = model(torch.from_numpy(bvp).unsqueeze(1), torch.from_numpy(acc)).numpy()
    pred = pred_norm * hr_std + hr_mean
    mae = float(np.abs(pred - hr_true).mean())
    rmse = float(np.sqrt(((pred - hr_true) ** 2).mean()))
    return {"mae": mae, "rmse": rmse, "n_windows": len(hr_true)}


def main() -> None:
    split = json.loads(SPLIT_PATH.read_text())
    print("Loading real GalaxyPPG windows (train/val/test) - this parses real CSVs, may take ~1-2 min...")
    train = load_split_windows(split["train"])
    val = load_split_windows(split["val"])
    test = load_split_windows(split["test"])
    print(f"train={len(train['hr'])} val={len(val['hr'])} test={len(test['hr'])} windows")

    hr_mean, hr_std = normalize_fit(train["hr"])
    print(f"HR normalization (train-only): mean={hr_mean:.4f} std={hr_std:.4f}")

    train_hr_norm = ((train["hr"] - hr_mean) / hr_std).astype(np.float32)
    val_hr_norm = ((val["hr"] - hr_mean) / hr_std).astype(np.float32)

    a_params = sum(p.numel() for p in PPGCapacityMatchedModel().parameters())
    b_params = sum(p.numel() for p in PPGPlusIMUModel().parameters())
    print(f"A_cap params: {a_params} | B/C params: {b_params}")

    out: dict = {
        "experiment_id": "galaxyppg_hr_external_replication_stage2",
        "scope_disclosure": "BOUNDED_TO_SINGLE_FOLD - see docs/GALAXYPPG_SPLIT_STRATEGY_DEVIATION.md. Real 16/4/4 subject-held-out split, NOT the frozen protocol's full 6-fold grouped CV (compute-infeasible this sprint).",
        "frozen_protocol_reference": "results/galaxyppg_protocol_stage1b.json",
        "split": split,
        "reference": "Polar H10 raw ECG R-peaks (Pan-Tompkins-lite), never device-derived HR",
        "window_seconds": 8.0, "stride_seconds": 2.0,
        "hr_normalization": {"mean": hr_mean, "std": hr_std, "fit_on": "train split only"},
        "parameter_counts": {"A_cap": a_params, "B_and_C": b_params},
        "window_counts": {"train": len(train["hr"]), "val": len(val["hr"]), "test": len(test["hr"])},
        "runs": {"A_cap": {}, "B": {}, "C": {}},
        "checkpoint_manifest": [],
    }

    for seed in SEEDS:
        torch.manual_seed(seed)
        model_a = PPGCapacityMatchedModel()
        hist_a = train_one(model_a, train["bvp"], train["bvp"], train_hr_norm, val["bvp"], val["bvp"], val_hr_norm, seed)
        report_a = evaluate(model_a, test["bvp"], test["bvp"], test["hr"], hr_mean, hr_std)
        report_a["train_history_len"] = len(hist_a)
        out["runs"]["A_cap"][f"seed{seed}"] = report_a
        print(f"seed {seed} A_cap: MAE={report_a['mae']:.3f} bpm")

        torch.manual_seed(seed)
        model_b = PPGPlusIMUModel()
        hist_b = train_one(model_b, train["bvp"], train["acc"], train_hr_norm, val["bvp"], val["acc"], val_hr_norm, seed)
        report_b = evaluate(model_b, test["bvp"], test["acc"], test["hr"], hr_mean, hr_std)
        report_b["train_history_len"] = len(hist_b)
        out["runs"]["B"][f"seed{seed}"] = report_b
        print(f"seed {seed} B: MAE={report_b['mae']:.3f} bpm")

        train_acc_deranged = deranged_acc_stable(train["acc"], train["subject"], CONTROL_SHUFFLE_SEED_BASE + seed)
        val_acc_deranged = deranged_acc_stable(val["acc"], val["subject"], CONTROL_SHUFFLE_SEED_BASE + seed)
        test_acc_deranged = deranged_acc_stable(test["acc"], test["subject"], CONTROL_SHUFFLE_SEED_BASE + seed)
        torch.manual_seed(seed)
        model_c = PPGPlusIMUModel()
        hist_c = train_one(model_c, train["bvp"], train_acc_deranged, train_hr_norm, val["bvp"], val_acc_deranged, val_hr_norm, seed)
        report_c = evaluate(model_c, test["bvp"], test_acc_deranged, test["hr"], hr_mean, hr_std)
        report_c["train_history_len"] = len(hist_c)
        out["runs"]["C"][f"seed{seed}"] = report_c
        print(f"seed {seed} C: MAE={report_c['mae']:.3f} bpm")

        for name, model in (("A_cap", model_a), ("B", model_b), ("C", model_c)):
            ckpt_path = CKPT_DIR / f"galaxyppg_hr_{name}_seed{seed}.pt"
            torch.save(model.state_dict(), ckpt_path)
            ckpt_bytes = ckpt_path.read_bytes()
            out["checkpoint_manifest"].append({
                "run_id": f"galaxyppg_hr_{name}_seed{seed}", "config": name, "seed": seed,
                "path": str(ckpt_path.relative_to(REPO_ROOT)),
                "size_bytes": len(ckpt_bytes), "sha256": hashlib.sha256(ckpt_bytes).hexdigest(),
            })

    def agg(vals: list[float]) -> dict:
        arr = np.asarray(vals, dtype=np.float64)
        return {"mean": float(arr.mean()), "sd_sample_ddof1": float(arr.std(ddof=1)), "per_seed": dict(zip((f"seed{s}" for s in SEEDS), vals))}

    a_mae = [out["runs"]["A_cap"][f"seed{s}"]["mae"] for s in SEEDS]
    b_mae = [out["runs"]["B"][f"seed{s}"]["mae"] for s in SEEDS]
    c_mae = [out["runs"]["C"][f"seed{s}"]["mae"] for s in SEEDS]
    a_to_b = [a - b for a, b in zip(a_mae, b_mae)]  # positive = B better (lower MAE)
    c_to_b = [c - b for c, b in zip(c_mae, b_mae)]

    out["aggregate"] = {
        "A_cap_mae": agg(a_mae), "B_mae": agg(b_mae), "C_mae": agg(c_mae),
        "A_to_B": {**agg(a_to_b), "n_seeds_favor_B": sum(1 for d in a_to_b if d > 0), "n_seeds_total": len(SEEDS)},
        "C_to_B": {**agg(c_to_b), "n_seeds_favor_B": sum(1 for d in c_to_b if d > 0), "n_seeds_total": len(SEEDS)},
    }

    OUT_PATH.write_text(json.dumps(out, indent=2))
    print("\nWrote", OUT_PATH)
    print(json.dumps(out["aggregate"], indent=2))


if __name__ == "__main__":
    main()
