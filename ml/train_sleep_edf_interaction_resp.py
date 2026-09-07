#!/usr/bin/env python
"""Sleep-EDF EEG x EOG x Resp interaction experiment (Day 10).

See docs/INTERACTION_EXPERIMENT_PREDECLARATION_DAY10.md - frozen BEFORE
this script produced any result.

M0 (EEG-only) and M_A (EEG+EOG) are the EXISTING frozen checkpoints from
ml/train_sleep_edf_eeg_eog_ablation.py - NOT retrained here. This script
trains only the two NEW configurations:
  M_B  = EEG + Resp oro-nasal
  M_AB = EEG + EOG + Resp oro-nasal
reusing SleepStageClassifier/train_one/evaluate_full unmodified, and
reusing the same frozen primary train/val/test subject split.
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

from ml.datasets.sleep_edf import EEG_CHANNEL, EOG_CHANNEL, RESP_CHANNEL, STAGE_NAMES, load_dataset_windows_multi  # noqa: E402
from ml.train_sleep_edf_eeg_eog_ablation import SleepStageClassifier, evaluate_full, train_one  # noqa: E402

RAW_DIR = REPO_ROOT / "datasets" / "sleep-edfx" / "raw"
ORIGINAL_RESULTS_PATH = REPO_ROOT / "results" / "sleep_edf_eeg_eog_ablation.json"
OUT_PATH = REPO_ROOT / "results" / "sleep_edf_interaction_resp_day10.json"
CKPT_DIR = REPO_ROOT / "ml" / "checkpoints"

SEEDS = (42, 43, 44, 45, 46)

CONFIGS = {
    "M_B_eeg_plus_resp": (EEG_CHANNEL, RESP_CHANNEL),
    "M_AB_eeg_plus_eog_plus_resp": (EEG_CHANNEL, EOG_CHANNEL, RESP_CHANNEL),
}


def load_split_data(subject_ids: list[str], channels: tuple[str, ...]) -> tuple[np.ndarray, np.ndarray]:
    x, y, _subj_idx, _prefixes = load_dataset_windows_multi(RAW_DIR, channels=channels, subject_ids=subject_ids)
    return x, y


def main() -> None:
    original = json.loads(ORIGINAL_RESULTS_PATH.read_text())
    split = original["frozen_protocol"]["subject_split"]
    print("Using FROZEN primary split (unchanged):", json.dumps(split))

    n_params_m0 = original["parameter_counts"]["baseline_eeg_only"]
    n_params_ma = original["parameter_counts"]["candidate_eeg_plus_eog"]
    n_params = {name: sum(p.numel() for p in SleepStageClassifier(len(ch)).parameters()) for name, ch in CONFIGS.items()}
    print("Parameter counts:", {"M0": n_params_m0, "M_A": n_params_ma, **n_params})

    # Capacity-fairness safeguard (predeclared): all four configs must be the
    # SAME class differing only in in_channels. Verify the marginal per-
    # channel parameter cost is identical across every channel-count step -
    # if it is not, abort rather than interpret a confounded result.
    per_channel_cost_0_to_1 = n_params_ma - n_params_m0
    per_channel_cost_1_to_2 = n_params["M_B_eeg_plus_resp"] - n_params_m0
    per_channel_cost_2_to_3 = n_params["M_AB_eeg_plus_eog_plus_resp"] - n_params["M_B_eeg_plus_resp"]
    if not (per_channel_cost_0_to_1 == per_channel_cost_1_to_2 == per_channel_cost_2_to_3):
        raise RuntimeError(
            "Capacity-fairness safeguard failed: per-channel parameter cost is not "
            f"constant across configs ({per_channel_cost_0_to_1}, {per_channel_cost_1_to_2}, "
            f"{per_channel_cost_2_to_3}) - aborting per the Day-7 capacity-confound lesson, "
            "not interpreting a confounded result."
        )
    print(f"Capacity-fairness safeguard OK: constant per-channel parameter cost = {per_channel_cost_0_to_1}")

    out: dict = {
        "experiment_id": "sleep_edf_interaction_eeg_eog_resp",
        "predeclaration": "docs/INTERACTION_EXPERIMENT_PREDECLARATION_DAY10.md",
        "feasibility_audit": "docs/INTERACTION_EXPERIMENT_FEASIBILITY_DAY10.md",
        "m0_source": "results/sleep_edf_eeg_eog_ablation.json (baseline_eeg_only) - NOT retrained",
        "ma_source": "results/sleep_edf_eeg_eog_ablation.json (candidate_eeg_plus_eog) - NOT retrained",
        "frozen_protocol": {
            "dataset": "PhysioNet Sleep-EDF (sleep-cassette)",
            "subject_split": split,
            "channels": {name: list(ch) for name, ch in CONFIGS.items()},
            "seeds": list(SEEDS),
            "primary_metric": "macro_f1",
            "capacity_fairness_per_channel_cost": per_channel_cost_0_to_1,
        },
        "parameter_counts": {"M0": n_params_m0, "M_A": n_params_ma, **n_params},
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

    out["window_counts"] = {
        name: {"train": len(data[1]), "val": len(data[3]), "test": len(data[5])}
        for name, data in per_config_data.items()
    }

    for name, channels in CONFIGS.items():
        train_x, train_y, val_x, val_y, test_x, test_y = per_config_data[name]
        class_weights_np = compute_class_weight("balanced", classes=np.arange(len(STAGE_NAMES)), y=train_y)
        class_weights = torch.tensor(class_weights_np, dtype=torch.float32)

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

            ckpt_path = CKPT_DIR / f"sleep_edf_interaction_{run_id}.pt"
            torch.save(model.state_dict(), ckpt_path)
            ckpt_bytes = ckpt_path.read_bytes()
            out["checkpoint_manifest"].append({
                "run_id": run_id, "config": name, "seed": seed,
                "in_channels": len(channels),
                "path": str(ckpt_path.relative_to(REPO_ROOT)),
                "size_bytes": len(ckpt_bytes), "sha256": hashlib.sha256(ckpt_bytes).hexdigest(),
                "n_parameters": n_params[name],
            })

    # --- Interaction term per seed -------------------------------------------
    m0_f1 = {s: original["runs"]["baseline_eeg_only"][f"seed{s}"]["macro_f1"] for s in SEEDS}
    ma_f1 = {s: original["runs"]["candidate_eeg_plus_eog"][f"seed{s}"]["macro_f1"] for s in SEEDS}
    mb_f1 = {s: out["runs"]["M_B_eeg_plus_resp"][f"seed{s}"]["macro_f1"] for s in SEEDS}
    mab_f1 = {s: out["runs"]["M_AB_eeg_plus_eog_plus_resp"][f"seed{s}"]["macro_f1"] for s in SEEDS}

    benefit_a = {s: ma_f1[s] - m0_f1[s] for s in SEEDS}
    benefit_b = {s: mb_f1[s] - m0_f1[s] for s in SEEDS}
    benefit_ab = {s: mab_f1[s] - m0_f1[s] for s in SEEDS}
    interaction = {s: benefit_ab[s] - benefit_a[s] - benefit_b[s] for s in SEEDS}

    def agg(d: dict) -> dict:
        arr = np.asarray(list(d.values()), dtype=np.float64)
        return {"mean": float(arr.mean()), "sd_sample_ddof1": float(arr.std(ddof=1)), "per_seed": {f"seed{s}": v for s, v in d.items()}}

    interaction_mean = agg(interaction)["mean"]
    interaction_sd = agg(interaction)["sd_sample_ddof1"]
    n_positive = sum(1 for v in interaction.values() if v > 0)
    n_negative = sum(1 for v in interaction.values() if v < 0)

    if interaction_mean > 0 and abs(interaction_mean) > 0.5 * interaction_sd:
        stability = "super_additive_leaning"
    elif interaction_mean < 0 and abs(interaction_mean) > 0.5 * interaction_sd:
        stability = "sub_additive_leaning"
    else:
        stability = "approximately_additive_or_unresolved"

    out["aggregate"] = {
        "m0_macro_f1": agg(m0_f1),
        "ma_macro_f1": agg(ma_f1),
        "mb_macro_f1": agg(mb_f1),
        "mab_macro_f1": agg(mab_f1),
        "benefit_A": agg(benefit_a),
        "benefit_B": agg(benefit_b),
        "benefit_AB": agg(benefit_ab),
        "interaction_term": {**agg(interaction), "n_seeds_positive": n_positive, "n_seeds_negative": n_negative, "n_seeds_total": len(SEEDS)},
        "stability_classification": stability,
    }

    OUT_PATH.write_text(json.dumps(out, indent=2))
    print("\nWrote", OUT_PATH)
    print("Interaction term:", json.dumps(out["aggregate"]["interaction_term"], indent=2))
    print("Stability:", stability)


if __name__ == "__main__":
    main()
