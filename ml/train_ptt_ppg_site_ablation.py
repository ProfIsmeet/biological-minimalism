#!/usr/bin/env python
"""Full overnight PTT PPG site-value HR ablation (authorized after the Day 3
gate review; see docs/MODEL_CONTRACT_PTT_HR.md, datasets/PTT_DATASET_AUDIT_DAY3.md):

    "Does a second PPG sensor site provide measurable value for heart-rate
    estimation over a single PPG site, particularly during running?"

Model A: single-site PPG (3 wavelength channels, distal phalanx).
Model B: two-site PPG (6 wavelength channels, distal + proximal phalanx).
Both use the exact same architecture family (one Conv1DEncoder + a Linear
head) and the same hyperparameters - the only difference is `in_channels`,
which is the variable under test (a second physical PPG site). No
Transformer/fusion module is used: the two sites are the same physiological
modality (PPG), not separate modalities requiring cross-modal fusion, so a
single encoder over the stacked channels is the smallest architecture that
can answer the sensor-site question (see contract doc "Fairness/Capacity
Policy" for the full rationale and the acknowledged channel-count confound).

Ground truth (HR) comes only from `ml/datasets/pulse_transit_time_ppg.py`'s
real ECG-R-peak-derived per-window label. ECG itself is never a model
input here.
"""

from __future__ import annotations

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

from app.ml.models import Conv1DEncoder  # noqa: E402

from ml.datasets.pulse_transit_time_ppg import (  # noqa: E402
    MODEL_A_CHANNELS,
    MODEL_B_CHANNELS,
    WINDOW_SAMPLES,
    RecordWindows,
)

EXPERIMENT_DIR = Path(__file__).parent / "experiments" / "ptt_ppg_site_ablation"


class PPGSiteHRModel(nn.Module):
    """One Conv1DEncoder over the stacked PPG-site channels + a linear HR
    head. Used for BOTH Model A (in_channels=3) and Model B (in_channels=6)
    - identical depth/width/hyperparameters in both cases, so the only
    thing that differs between the two trained models is the number of
    input channels (the second PPG site itself), not extra model capacity
    added on top of it."""

    def __init__(self, in_channels: int, embedding_dim: int = 32) -> None:
        super().__init__()
        self.encoder = Conv1DEncoder(in_channels=in_channels, embedding_dim=embedding_dim)
        self.head = nn.Linear(embedding_dim, 1)

    def forward(self, ppg: torch.Tensor) -> torch.Tensor:
        return self.head(self.encoder(ppg)).squeeze(-1)


def build_tensors(records: list[RecordWindows], model: str) -> dict[str, np.ndarray]:
    """`model`: "a" or "b". Concatenates windows across records (which may
    span multiple activities/subjects) into flat arrays, preserving
    provenance arrays alongside the tensors."""

    if model not in ("a", "b"):
        raise ValueError("model must be 'a' or 'b'")
    key = "ppg_a" if model == "a" else "ppg_b"

    ppg = np.concatenate([getattr(r, key) for r in records]) if records else np.zeros((0, 0, WINDOW_SAMPLES), dtype=np.float32)
    hr = np.concatenate([r.hr for r in records]) if records else np.zeros((0,), dtype=np.float32)
    subject_id = np.concatenate([np.full(len(r.hr), r.subject_id) for r in records]) if records else np.zeros((0,), dtype="<U8")
    activity = np.concatenate([np.full(len(r.hr), r.activity) for r in records]) if records else np.zeros((0,), dtype="<U8")

    return {"ppg": ppg, "hr": hr, "subject_id": subject_id, "activity": activity}


def smoke_test(cache_dir: str | Path) -> None:
    """Day 3 smoke test ONLY (see module docstring) - proves the pipeline
    end-to-end, including a couple of gradient steps to confirm the code
    path executes. **Not a scientific result**: uses whichever locally
    cached records are available (not the full frozen split), tiny data,
    no held-out evaluation reported."""

    from ml.datasets.pulse_transit_time_ppg import ALL_SUBJECTS, ACTIVITIES, load_cached_record

    cache_dir = Path(cache_dir)
    available = []
    for s in ALL_SUBJECTS:
        for a in ACTIVITIES:
            p = cache_dir / f"{s}_{a}.npz"
            if p.exists():
                available.append((s, a))

    if not available:
        raise FileNotFoundError(f"No cached PTT records found in {cache_dir} - run preprocess_record() first.")

    print(f"Smoke test using {len(available)} cached record(s): {available}")
    records = [load_cached_record(cache_dir, s, a) for s, a in available]

    for model_name, channels in (("a", MODEL_A_CHANNELS), ("b", MODEL_B_CHANNELS)):
        data = build_tensors(records, model_name)
        n = len(data["hr"])
        print(f"Model {model_name.upper()}: {n} windows, ppg shape {data['ppg'].shape}, channels={channels}")
        assert data["ppg"].shape[1] == len(channels), "channel count mismatch"
        assert data["ppg"].shape[2] == WINDOW_SAMPLES

        model = PPGSiteHRModel(in_channels=len(channels))
        opt = optim.Adam(model.parameters(), lr=1e-3)
        loss_fn = nn.L1Loss()

        ppg_t = torch.from_numpy(data["ppg"][: min(16, n)])
        hr_t = torch.from_numpy(data["hr"][: min(16, n)])
        hr_mean, hr_std = float(hr_t.mean()), float(hr_t.std() + 1e-6)
        hr_norm = (hr_t - hr_mean) / hr_std

        model.train()
        for step in range(2):
            opt.zero_grad()
            pred = model(ppg_t)
            assert pred.shape == hr_norm.shape, f"prediction shape {pred.shape} != target shape {hr_norm.shape}"
            loss = loss_fn(pred, hr_norm)
            loss.backward()
            opt.step()
            print(f"  Model {model_name.upper()} smoke-train step {step}: loss={loss.item():.4f} (NOT a scientific result)")

    print("SMOKE TEST PASSED - pipeline executes end-to-end. No held-out metric was computed or reported.")


# --- Frozen training hyperparameters (recorded here BEFORE any full run) ---
# These mirror ml/train_ppg_dalia_imu_ablation.py's proven convention
# (AdamW, MSELoss on normalized HR, lr=1e-3, batch_size=64) with two
# genuinely new choices this dataset requires - early stopping and
# checkpoint selection - which PPG-DaLiA's script did not need (it just
# trained a fixed 20 epochs). Both are frozen ONCE here, before any
# held-out result is inspected, and are not tuned per-model or per-seed.
MAX_EPOCHS = 20
BATCH_SIZE = 64
LEARNING_RATE = 1e-3
EARLY_STOPPING_PATIENCE = 5  # stop if val MAE does not improve for 5 consecutive epochs
CHECKPOINT_SELECTION_METRIC = "val_mae"  # lower is better; best-epoch state_dict is kept
EMBEDDING_DIM = 32
TRAINING_SEEDS = (42, 43, 44, 45, 46)  # identical seed set for Model A and Model B (paired replicates)
DEVICE = "cpu"  # torch.cuda.is_available() == False on this machine (verified before this run)


def mae(pred: np.ndarray, target: np.ndarray) -> float:
    return float(np.mean(np.abs(pred - target)))


def rmse(pred: np.ndarray, target: np.ndarray) -> float:
    return float(np.sqrt(np.mean((pred - target) ** 2)))


def train_model_with_early_stopping(
    model: "nn.Module",
    train_data: dict,
    val_data: dict,
    hr_mean: float,
    hr_std: float,
    seed: int,
) -> tuple[list[dict], dict, int, float]:
    """Trains with a fixed seed, AdamW + MSELoss, up to MAX_EPOCHS, stopping
    early if val MAE has not improved for EARLY_STOPPING_PATIENCE epochs.
    Returns (history, best_state_dict (CPU tensors), best_epoch, best_val_mae).
    Validation subjects are used ONLY for this early-stopping/checkpoint
    decision - never for gradient updates."""

    from torch.utils.data import DataLoader, TensorDataset

    torch.manual_seed(seed)
    np.random.seed(seed)

    optimizer = optim.AdamW(model.parameters(), lr=LEARNING_RATE)
    loss_fn = nn.MSELoss()

    train_loader = DataLoader(
        TensorDataset(torch.from_numpy(train_data["ppg"]), torch.from_numpy(train_data["hr"])),
        batch_size=BATCH_SIZE, shuffle=True,
    )
    val_loader = DataLoader(
        TensorDataset(torch.from_numpy(val_data["ppg"]), torch.from_numpy(val_data["hr"])),
        batch_size=128, shuffle=False,
    )

    history: list[dict] = []
    best_val_mae = float("inf")
    best_epoch = -1
    best_state = {k: v.clone() for k, v in model.state_dict().items()}
    epochs_since_improvement = 0

    for epoch in range(1, MAX_EPOCHS + 1):
        model.train()
        train_loss = 0.0
        for ppg, hr in train_loader:
            hr_norm = (hr - hr_mean) / hr_std
            optimizer.zero_grad()
            pred = model(ppg)
            loss = loss_fn(pred, hr_norm)
            loss.backward()
            optimizer.step()
            train_loss += float(loss.item()) * len(hr)
        train_loss /= max(1, len(train_data["hr"]))

        model.eval()
        val_abs_err = 0.0
        val_sq_err = 0.0
        with torch.no_grad():
            for ppg, hr in val_loader:
                pred = model(ppg) * hr_std + hr_mean
                val_abs_err += float((pred - hr).abs().sum().item())
                val_sq_err += float(((pred - hr) ** 2).sum().item())
        val_mae = val_abs_err / max(1, len(val_data["hr"]))
        val_rmse = float(np.sqrt(val_sq_err / max(1, len(val_data["hr"]))))

        assert np.isfinite(train_loss), f"non-finite train loss at epoch {epoch}: {train_loss}"
        assert np.isfinite(val_mae), f"non-finite val MAE at epoch {epoch}: {val_mae}"

        history.append({"epoch": epoch, "train_loss": train_loss, "val_mae": val_mae, "val_rmse": val_rmse, "lr": LEARNING_RATE})
        print(f"    epoch {epoch:2d}/{MAX_EPOCHS} - train loss {train_loss:.4f} | val MAE {val_mae:.3f} bpm | val RMSE {val_rmse:.3f} bpm")

        if val_mae < best_val_mae:
            best_val_mae = val_mae
            best_epoch = epoch
            best_state = {k: v.detach().clone() for k, v in model.state_dict().items()}
            epochs_since_improvement = 0
        else:
            epochs_since_improvement += 1
            if epochs_since_improvement >= EARLY_STOPPING_PATIENCE:
                print(f"    early stopping at epoch {epoch} (no val MAE improvement for {EARLY_STOPPING_PATIENCE} epochs)")
                break

    return history, best_state, best_epoch, best_val_mae


@torch.no_grad()
def evaluate_model(model: "nn.Module", data: dict, hr_mean: float, hr_std: float) -> np.ndarray:
    from torch.utils.data import DataLoader, TensorDataset

    model.eval()
    preds = []
    loader = DataLoader(TensorDataset(torch.from_numpy(data["ppg"])), batch_size=128, shuffle=False)
    for (ppg,) in loader:
        pred = model(ppg) * hr_std + hr_mean
        preds.append(pred.numpy())
    return np.concatenate(preds) if preds else np.zeros((0,), dtype=np.float32)


def stratified_report(pred: np.ndarray, target: np.ndarray, data: dict) -> dict:
    report: dict = {"overall": {"mae": mae(pred, target), "rmse": rmse(pred, target), "n_windows": int(len(target))}}

    per_subject = {}
    for subject_id in sorted(set(data["subject_id"].tolist())):
        m = data["subject_id"] == subject_id
        per_subject[subject_id] = {"mae": mae(pred[m], target[m]), "rmse": rmse(pred[m], target[m]), "n_windows": int(m.sum())}
    report["per_subject"] = per_subject

    per_activity = {}
    for activity in sorted(set(data["activity"].tolist())):
        m = data["activity"] == activity
        if m.sum() == 0:
            continue
        per_activity[activity] = {"mae": mae(pred[m], target[m]), "rmse": rmse(pred[m], target[m]), "n_windows": int(m.sum())}
    report["per_activity"] = per_activity

    per_subject_activity = {}
    for subject_id in sorted(set(data["subject_id"].tolist())):
        for activity in sorted(set(data["activity"].tolist())):
            m = (data["subject_id"] == subject_id) & (data["activity"] == activity)
            if m.sum() == 0:
                continue
            per_subject_activity[f"{subject_id}_{activity}"] = {
                "mae": mae(pred[m], target[m]), "rmse": rmse(pred[m], target[m]), "n_windows": int(m.sum()),
            }
    report["per_subject_activity"] = per_subject_activity

    return report


def load_split_records(cache_dir: Path, subject_ids: list[str]) -> list[RecordWindows]:
    from ml.datasets.pulse_transit_time_ppg import ACTIVITIES, load_cached_record

    out = []
    for s in subject_ids:
        for a in ACTIVITIES:
            out.append(load_cached_record(cache_dir, s, a))
    return out


def main() -> None:
    import hashlib
    import json
    import time

    cache_dir = REPO_ROOT / "datasets" / "pulse-transit-time-ppg" / "processed"
    ckpt_dir = REPO_ROOT / "ml" / "checkpoints"
    ckpt_dir.mkdir(exist_ok=True)

    split = json.loads((EXPERIMENT_DIR / "subject_split.json").read_text())
    config = json.loads((EXPERIMENT_DIR / "config.json").read_text())
    print("Using FROZEN split:", json.dumps(split))

    print("Loading cached windows (train/val/test)...")
    train_records = load_split_records(cache_dir, split["train"])
    val_records = load_split_records(cache_dir, split["val"])
    test_records = load_split_records(cache_dir, split["test"])

    train_a = build_tensors(train_records, "a")
    val_a = build_tensors(val_records, "a")
    test_a = build_tensors(test_records, "a")
    train_b = build_tensors(train_records, "b")
    val_b = build_tensors(val_records, "b")
    test_b = build_tensors(test_records, "b")

    assert train_a["hr"].shape == train_b["hr"].shape
    assert np.array_equal(train_a["hr"], train_b["hr"]), "Model A and B must train on identical targets"
    assert np.array_equal(test_a["hr"], test_b["hr"]), "Model A and B must be evaluated on identical held-out targets"
    assert np.array_equal(test_a["subject_id"], test_b["subject_id"])
    assert np.array_equal(test_a["activity"], test_b["activity"])
    assert not (set(split["train"]) & set(split["test"])) and not (set(split["val"]) & set(split["test"]))

    print(f"train windows: {len(train_a['hr'])} | val windows: {len(val_a['hr'])} | test windows: {len(test_a['hr'])}")

    # HR normalization stats computed from TRAIN windows only, frozen once,
    # reused identically for Model A and Model B (both predict the same
    # real target - no separate normalization per model).
    hr_mean = float(train_a["hr"].mean())
    hr_std = float(train_a["hr"].std() + 1e-6)
    print(f"HR normalization (train-only): mean={hr_mean:.4f} std={hr_std:.4f}")

    results: dict = {
        "config": config,
        "subject_split": split,
        "hr_normalization": {"mean": hr_mean, "std": hr_std},
        "training_hyperparameters": {
            "architecture": "PPGSiteHRModel (Conv1DEncoder + Linear head)",
            "embedding_dim": EMBEDDING_DIM,
            "optimizer": "AdamW",
            "weight_decay": "AdamW default (0.01)",
            "learning_rate": LEARNING_RATE,
            "batch_size": BATCH_SIZE,
            "loss_function": "MSELoss (on normalized HR)",
            "max_epochs": MAX_EPOCHS,
            "early_stopping_patience": EARLY_STOPPING_PATIENCE,
            "checkpoint_selection_metric": CHECKPOINT_SELECTION_METRIC,
            "validation_metric": "val_mae (bpm, un-normalized)",
            "training_seeds": list(TRAINING_SEEDS),
            "device": DEVICE,
            "dtype": "float32",
        },
        "window_counts": {
            "train": int(len(train_a["hr"])),
            "val": int(len(val_a["hr"])),
            "test": int(len(test_a["hr"])),
        },
        "runs": {"a": {}, "b": {}},
        "checkpoint_manifest": [],
    }

    for model_name, channels, train_data, val_data, test_data in (
        ("a", MODEL_A_CHANNELS, train_a, val_a, test_a),
        ("b", MODEL_B_CHANNELS, train_b, val_b, test_b),
    ):
        for seed in TRAINING_SEEDS:
            run_id = f"model_{model_name}_seed{seed}"
            print(f"\n=== Training {run_id} (in_channels={len(channels)}) ===")
            torch.manual_seed(seed)
            model = PPGSiteHRModel(in_channels=len(channels), embedding_dim=EMBEDDING_DIM)
            n_params = sum(p.numel() for p in model.parameters())

            start = time.time()
            history, best_state, best_epoch, best_val_mae = train_model_with_early_stopping(
                model, train_data, val_data, hr_mean, hr_std, seed
            )
            elapsed = time.time() - start

            model.load_state_dict(best_state)
            pred = evaluate_model(model, test_data, hr_mean, hr_std)

            assert np.all(np.isfinite(pred)), f"{run_id}: non-finite predictions"
            assert np.std(pred) > 1e-6, f"{run_id}: suspiciously constant predictions - possible collapse"

            report = stratified_report(pred, test_data["hr"], test_data)
            report["best_epoch"] = best_epoch
            report["best_val_mae"] = best_val_mae
            report["n_epochs_trained"] = len(history)
            report["train_seconds"] = elapsed
            report["train_history"] = history
            report["n_parameters"] = int(n_params)
            report["in_channels"] = len(channels)
            report["seed"] = seed

            print(f"{run_id}: held-out MAE {report['overall']['mae']:.4f} bpm | RMSE {report['overall']['rmse']:.4f} bpm "
                  f"(best epoch {best_epoch}, val MAE {best_val_mae:.4f}, {elapsed:.1f}s)")

            results["runs"][model_name][f"seed{seed}"] = report

            ckpt_path = ckpt_dir / f"ptt_{run_id}.pt"
            torch.save(best_state, ckpt_path)
            ckpt_bytes = ckpt_path.read_bytes()
            results["checkpoint_manifest"].append({
                "run_id": run_id,
                "model": model_name,
                "seed": seed,
                "in_channels": len(channels),
                "path": str(ckpt_path.relative_to(REPO_ROOT)),
                "size_bytes": len(ckpt_bytes),
                "sha256": hashlib.sha256(ckpt_bytes).hexdigest(),
                "best_val_mae": best_val_mae,
                "best_epoch": best_epoch,
                "n_parameters": int(n_params),
            })

    # --- Aggregate paired results -------------------------------------------
    seeds = list(TRAINING_SEEDS)
    a_maes = [results["runs"]["a"][f"seed{s}"]["overall"]["mae"] for s in seeds]
    b_maes = [results["runs"]["b"][f"seed{s}"]["overall"]["mae"] for s in seeds]
    a_rmses = [results["runs"]["a"][f"seed{s}"]["overall"]["rmse"] for s in seeds]
    b_rmses = [results["runs"]["b"][f"seed{s}"]["overall"]["rmse"] for s in seeds]
    paired_dmae = [b - a for a, b in zip(a_maes, b_maes)]
    paired_drmse = [b - a for a, b in zip(a_rmses, b_rmses)]

    results["aggregate"] = {
        "model_a": {"mean_mae": float(np.mean(a_maes)), "sd_mae": float(np.std(a_maes)), "mean_rmse": float(np.mean(a_rmses)), "sd_rmse": float(np.std(a_rmses))},
        "model_b": {"mean_mae": float(np.mean(b_maes)), "sd_mae": float(np.std(b_maes)), "mean_rmse": float(np.mean(b_rmses)), "sd_rmse": float(np.std(b_rmses))},
        "paired_delta_mae_b_minus_a": {"per_seed": dict(zip((f"seed{s}" for s in seeds), paired_dmae)), "mean": float(np.mean(paired_dmae)), "sd": float(np.std(paired_dmae))},
        "paired_delta_rmse_b_minus_a": {"per_seed": dict(zip((f"seed{s}" for s in seeds), paired_drmse)), "mean": float(np.mean(paired_drmse)), "sd": float(np.std(paired_drmse))},
    }

    print("\n=== AGGREGATE (overall held-out test) ===")
    print(f"Model A: MAE {results['aggregate']['model_a']['mean_mae']:.4f} +/- {results['aggregate']['model_a']['sd_mae']:.4f} bpm")
    print(f"Model B: MAE {results['aggregate']['model_b']['mean_mae']:.4f} +/- {results['aggregate']['model_b']['sd_mae']:.4f} bpm")
    print(f"Paired dMAE (B-A): mean {results['aggregate']['paired_delta_mae_b_minus_a']['mean']:.4f} +/- {results['aggregate']['paired_delta_mae_b_minus_a']['sd']:.4f} bpm")

    out_path = REPO_ROOT / "results" / "ptt_ppg_site_ablation.json"
    out_path.write_text(json.dumps(results, indent=2))
    print("\nWrote", out_path)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--smoke-test", action="store_true", help="Run the Day 3 smoke test only, not the full ablation.")
    args = parser.parse_args()

    if args.smoke_test:
        smoke_test(REPO_ROOT / "datasets" / "pulse-transit-time-ppg" / "processed")
    else:
        main()
