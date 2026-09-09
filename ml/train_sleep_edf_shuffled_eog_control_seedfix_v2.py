#!/usr/bin/env python
"""Stage 2 (Day 12+): corrected shuffled-EOG control (C) under the H1
seed-before-model-init protocol.

Same architecture-matched shuffled-EOG control as
ml/train_sleep_edf_shuffled_eog_control.py (Model C: EEG + EOG-shuffled-
within-subject-and-partition, identical SleepStageClassifier(in_channels=2)
as Model B), but retrained with the CORRECTED seeding order from
ml/sleep_seed_utils.py, and with the EOG-shuffle RNG driven by its own
isolated control_shuffle_seed sub-seed (not the bare run seed reused for
model init, as the V1 script did) - completing the sub-seed isolation the
H1 fix introduced (model_init_seed / data_order_seed / control_shuffle_seed
must each vary independently).

Reuses corrected A/B (results/sleep_edf_primary_seedfix_v2.json) as the
comparison baseline for B-C - does not retrain A or B. Writes to entirely
new output paths/checkpoint names; does not touch or overwrite the V1
control artifact.
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

from ml.datasets.sleep_edf import (  # noqa: E402
    EEG_CHANNEL,
    EOG_CHANNEL,
    STAGE_NAMES,
    load_dataset_windows_multi,
    shuffle_eog_within_subject,
)
from ml.sleep_seed_utils import derive_sleep_run_seeds, seed_for_data_order, seed_for_model_init
from ml.train_sleep_edf_eeg_eog_ablation import SleepStageClassifier, evaluate_full

RAW_DIR = REPO_ROOT / "datasets" / "sleep-edfx" / "raw"
V2_PRIMARY_PATH = REPO_ROOT / "results" / "sleep_edf_primary_seedfix_v2.json"
V1_CONTROL_PATH = REPO_ROOT / "results" / "sleep_edf_eeg_eog_control_analysis.json"
OUT_PATH = REPO_ROOT / "results" / "sleep_edf_shuffled_eog_control_seedfix_v2.json"
CKPT_DIR = REPO_ROOT / "ml" / "checkpoints"

CHANNELS = (EEG_CHANNEL, EOG_CHANNEL)
EOG_CHANNEL_INDEX = 1
SEEDS = (42, 43, 44, 45, 46)


def load_partition(subject_ids: list[str]) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    x, y, subj_idx, _prefixes = load_dataset_windows_multi(RAW_DIR, channels=CHANNELS, subject_ids=subject_ids)
    return x, y, subj_idx


def train_one_seedfix_c(train_x, train_y, val_x, val_y, class_weights: torch.Tensor, run_seed: int):
    """Same corrected order as train_sleep_edf_primary_seedfix_v2.py's
    train_one_seedfix(): seed for model init BEFORE construction, then
    seed for data order BEFORE the DataLoader is built. Identical training
    loop (epochs, AdamW, class-weighted CE, batch size) to train_one()."""
    seeds = derive_sleep_run_seeds(run_seed)

    seed_for_model_init(seeds)
    model = SleepStageClassifier(in_channels=2)

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


def _subject_prefixes_for(subject_ids: list[str], subj_idx: np.ndarray) -> list[str]:
    from ml.datasets.sleep_edf import find_subject_pairs

    pairs = find_subject_pairs(RAW_DIR)
    pairs = [(psg, hyp) for psg, hyp in pairs if psg.name.split("E")[0] in subject_ids]
    prefixes_in_order = [psg.name.split("E")[0] for psg, _ in pairs]
    return [prefixes_in_order[i] for i in subj_idx]


def main() -> None:
    v2_primary = json.loads(V2_PRIMARY_PATH.read_text())
    split = v2_primary["frozen_protocol"]["subject_split"]
    print("Using SAME FROZEN primary split as corrected A/B (unchanged):", json.dumps(split))

    print("Loading real data per partition (aligned copy, to be shuffled independently per-partition)...")
    train_x, train_y, train_subj = load_partition(split["train"])
    val_x, val_y, val_subj = load_partition(split["val"])
    test_x, test_y, test_subj = load_partition(split["test"])
    print(f"train={len(train_y)} val={len(val_y)} test={len(test_y)} epochs")

    class_weights_np = compute_class_weight("balanced", classes=np.arange(len(STAGE_NAMES)), y=train_y)
    class_weights = torch.tensor(class_weights_np, dtype=torch.float32)

    n_params = sum(p.numel() for p in SleepStageClassifier(in_channels=2).parameters())
    n_params_b_v2 = v2_primary["parameter_counts"]["candidate_eeg_plus_eog"]
    assert n_params == n_params_b_v2, f"Model C params ({n_params}) must exactly match corrected Model B ({n_params_b_v2})"
    print(f"Model C params: {n_params} (matches corrected Model B exactly: {n_params_b_v2})")

    out: dict = {
        "experiment_id": "sleep_edf_shuffled_eog_control_seedfix_v2",
        "purpose": "Stage 2: corrected shuffled-EOG control (C) under the H1 seed-before-model-init protocol, with an isolated control_shuffle_seed sub-seed (not the bare run seed reused for model init as the V1 control script did).",
        "seeding_protocol_doc": "docs/SLEEP_SEEDING_PROTOCOL_V2.md",
        "v1_control_reference": "results/sleep_edf_eeg_eog_control_analysis.json (UNCHANGED, NOT overwritten)",
        "v2_primary_reference": "results/sleep_edf_primary_seedfix_v2.json (corrected A/B, NOT retrained here)",
        "does_not_overwrite_v1": True,
        "frozen_protocol": {
            "dataset": "PhysioNet Sleep-EDF (sleep-cassette)",
            "subject_split": split,
            "channels": list(CHANNELS),
            "shuffle_method": "EOG epochs permuted within-subject, within-partition only (see docs/SLEEP_EDF_SHUFFLED_EOG_PREDECLARATION.md)",
            "shuffle_rng_seed_source": "seeds.control_shuffle_seed (run_seed + 200000), isolated from model_init_seed and data_order_seed per ml/sleep_seed_utils.py",
            "seeds": list(SEEDS),
            "n_parameters_model_c": n_params,
            "n_parameters_model_b_v2": n_params_b_v2,
            "capacity_identical_to_b": n_params == n_params_b_v2,
        },
        "runs": {},
        "checkpoint_manifest": [],
    }

    for seed in SEEDS:
        run_id = f"model_c_shuffled_eog_seedfix_v2_seed{seed}"
        print(f"\n=== seed {seed}: training {run_id} (CORRECTED seeding order, isolated control_shuffle_seed) ===")

        seeds = derive_sleep_run_seeds(seed)
        shuffled_train_x = shuffle_eog_within_subject(train_x, train_subj, EOG_CHANNEL_INDEX, seed=seeds.control_shuffle_seed)
        shuffled_val_x = shuffle_eog_within_subject(val_x, val_subj, EOG_CHANNEL_INDEX, seed=seeds.control_shuffle_seed)
        shuffled_test_x = shuffle_eog_within_subject(test_x, test_subj, EOG_CHANNEL_INDEX, seed=seeds.control_shuffle_seed)

        start = time.time()
        model, history, seeds = train_one_seedfix_c(shuffled_train_x, train_y, shuffled_val_x, val_y, class_weights, seed)
        elapsed = time.time() - start

        report = evaluate_full(model, shuffled_test_x, test_y)
        report["train_seconds"] = elapsed
        report["train_history"] = history
        report["n_parameters"] = n_params
        report["seed"] = seed
        report["sub_seeds"] = {"model_init_seed": seeds.model_init_seed, "data_order_seed": seeds.data_order_seed, "control_shuffle_seed": seeds.control_shuffle_seed}
        print(f"{run_id}: test macro-F1={report['macro_f1']:.4f} accuracy={report['accuracy']:.4f} ({elapsed:.1f}s)")

        out["runs"][f"seed{seed}"] = report

        ckpt_path = CKPT_DIR / f"sleep_edf_{run_id}.pt"
        torch.save(model.state_dict(), ckpt_path)
        ckpt_bytes = ckpt_path.read_bytes()
        out["checkpoint_manifest"].append({
            "run_id": run_id, "config": "shuffled_eog_seedfix_v2", "seed": seed, "in_channels": 2,
            "path": str(ckpt_path.relative_to(REPO_ROOT)),
            "size_bytes": len(ckpt_bytes), "sha256": hashlib.sha256(ckpt_bytes).hexdigest(),
            "n_parameters": n_params,
        })

        per_subject = {}
        prefixes = _subject_prefixes_for(split["test"], test_subj)
        for subj_name in split["test"]:
            mask = np.array([p == subj_name for p in prefixes])
            x_s = shuffled_test_x[mask]
            y_s = test_y[mask]
            if len(y_s) == 0:
                continue
            r = evaluate_full(model, x_s, y_s)
            per_subject[subj_name] = {"macro_f1": r["macro_f1"], "balanced_accuracy": r["balanced_accuracy"], "n_epochs": r["n_epochs_eval"]}
        out["runs"][f"seed{seed}"]["per_subject"] = per_subject

    def agg(values: list[float]) -> dict:
        arr = np.asarray(values, dtype=np.float64)
        return {"mean": float(arr.mean()), "sd_sample_ddof1": float(arr.std(ddof=1)) if len(arr) > 1 else None, "per_seed": dict(zip((f"seed{s}" for s in SEEDS), values))}

    a_f1 = [v2_primary["runs"]["baseline_eeg_only"][f"seed{s}"]["macro_f1"] for s in SEEDS]
    b_f1 = [v2_primary["runs"]["candidate_eeg_plus_eog"][f"seed{s}"]["macro_f1"] for s in SEEDS]
    c_f1 = [out["runs"][f"seed{s}"]["macro_f1"] for s in SEEDS]

    a_to_b = [b - a for a, b in zip(a_f1, b_f1)]
    a_to_c = [c - a for a, c in zip(a_f1, c_f1)]
    c_to_b = [b - c for c, b in zip(c_f1, b_f1)]

    out["aggregate"] = {
        "model_a_macro_f1_v2": agg(a_f1),
        "model_b_macro_f1_v2": agg(b_f1),
        "model_c_macro_f1_v2": agg(c_f1),
        "A_to_B": {**agg(a_to_b), "n_seeds_favor_B": sum(1 for d in a_to_b if d > 0), "n_seeds_total": len(SEEDS)},
        "A_to_C": {**agg(a_to_c), "n_seeds_favor_C": sum(1 for d in a_to_c if d > 0), "n_seeds_total": len(SEEDS)},
        "C_to_B": {**agg(c_to_b), "n_seeds_favor_B": sum(1 for d in c_to_b if d > 0), "n_seeds_total": len(SEEDS)},
    }

    OUT_PATH.write_text(json.dumps(out, indent=2))
    print("\nWrote", OUT_PATH)
    print("Aggregate:", json.dumps(out["aggregate"], indent=2))


if __name__ == "__main__":
    main()
