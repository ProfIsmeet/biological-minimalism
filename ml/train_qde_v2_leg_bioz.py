#!/usr/bin/env python
"""Real training run: QDE V2 leg-BioZ marginal-value experiment (Stage 2A).

Implements the frozen protocol in results/qde_v2_protocol_stage1b.json
exactly: baseline-relative deltas, LOSO outer / nested-LOSO inner ridge
regression, jointly-deranged-within-subject bilateral leg control. This is
a NEW experiment on the SAME already-in-repo QDE CSV used by
ml/train_bioimpedance.py (which predicts absolute InBody TBW, unrelated
target) - that historical trainer/result is untouched by this script.

Sign convention (frozen, stated explicitly per Section 26 of the master
prompt): target = weight_at_interval_i - weight_at_interval_0 (Kern scale),
so the target becomes increasingly NEGATIVE as dehydration-driven mass loss
accumulates across the 120-minute protocol.

Usage:
    python train_qde_v2_leg_bioz.py
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np
from sklearn.linear_model import Ridge

REPO_ROOT = Path(__file__).resolve().parent.parent
CSV_PATH = REPO_ROOT / "datasets" / "qde-bioimpedance" / "raw" / "dehydration_estimation.csv"
OUT_PATH = REPO_ROOT / "results" / "qde_v2_leg_bioz_stage2.json"

ARM_TRUNK_COLS = [
    "impedance right arm at 1000kHz [Ohm]",
    "impedance left arm at 1000kHz [Ohm]",
    "impedance trunk at 1000kHz [Ohm]",
]
LEG_COLS = [
    "impedance right leg at 1000kHz [Ohm]",
    "impedance left leg at 1000kHz [Ohm]",
]
WEIGHT_COL = "weight measured using Kern DE 150K2D [kg]"
INTERVAL_COL = "running interval"
SUBJECT_COL = "id"

ALPHA_GRID = [0.001, 0.01, 0.1, 1.0, 10.0, 30.0, 100.0, 300.0, 1000.0]
CONTROL_SHUFFLE_SEED = 200042  # ml/sleep_seed_utils.py-style sub-seed: base run seed 42 + 200_000 control-shuffle offset


def load_raw() -> dict[int, list[dict]]:
    by_subject: dict[int, list[dict]] = {}
    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            try:
                sid = int(row[SUBJECT_COL])
                interval = int(row[INTERVAL_COL])
                weight = float(row[WEIGHT_COL])
                arm_trunk = [float(row[c]) for c in ARM_TRUNK_COLS]
                legs = [float(row[c]) for c in LEG_COLS]
            except ValueError:
                continue  # real missing value - skipped, not imputed
            by_subject.setdefault(sid, []).append(
                {"interval": interval, "weight": weight, "arm_trunk": arm_trunk, "legs": legs}
            )
    for sid, rows in by_subject.items():
        rows.sort(key=lambda r: r["interval"])
    return by_subject


def build_subject_arrays(by_subject: dict[int, list[dict]], rng: np.random.Generator) -> dict[int, dict]:
    """Baseline-relative deltas per subject: A (3 feat), B (5 feat), C (5 feat,
    legs jointly deranged within subject across non-baseline intervals),
    target (Kern-scale delta_weight)."""
    subjects: dict[int, dict] = {}
    for sid, rows in by_subject.items():
        assert rows[0]["interval"] == 0, f"subject {sid} missing baseline interval 0"
        baseline_arm_trunk = np.array(rows[0]["arm_trunk"])
        baseline_legs = np.array(rows[0]["legs"])
        baseline_weight = rows[0]["weight"]

        arm_trunk_delta = np.array([r["arm_trunk"] for r in rows]) - baseline_arm_trunk
        legs_delta = np.array([r["legs"] for r in rows]) - baseline_legs
        target = np.array([r["weight"] for r in rows]) - baseline_weight

        # Joint bilateral derangement: permute non-baseline interval indices
        # (1..n-1) as a group, both legs use the SAME donor interval, subject
        # identity and dimensionality preserved. Baseline (index 0, delta=0)
        # is never touched - it is real, not deranged.
        n = len(rows)
        non_baseline_idx = np.arange(1, n)
        deranged_idx = non_baseline_idx.copy()
        # derangement (no fixed points) via rejection sampling, subject-seeded
        subj_rng = np.random.default_rng(CONTROL_SHUFFLE_SEED + sid)
        for _ in range(1000):
            subj_rng.shuffle(deranged_idx)
            if not np.any(deranged_idx == non_baseline_idx):
                break
        legs_delta_deranged = legs_delta.copy()
        legs_delta_deranged[non_baseline_idx] = legs_delta[deranged_idx]

        subjects[sid] = {
            "n_points": n,
            "A": arm_trunk_delta,
            "B": np.concatenate([arm_trunk_delta, legs_delta], axis=1),
            "C": np.concatenate([arm_trunk_delta, legs_delta_deranged], axis=1),
            "y": target,
        }
    return subjects


def nested_loso_select_alpha(train_sids: list[int], subjects: dict[int, dict], key: str) -> float:
    best_alpha, best_mae = ALPHA_GRID[0], float("inf")
    for alpha in ALPHA_GRID:
        errs = []
        for held in train_sids:
            inner_train = [s for s in train_sids if s != held]
            X_tr = np.concatenate([subjects[s][key] for s in inner_train], axis=0)
            y_tr = np.concatenate([subjects[s]["y"] for s in inner_train], axis=0)
            mu, sd = X_tr.mean(axis=0), X_tr.std(axis=0)
            sd[sd == 0] = 1.0
            model = Ridge(alpha=alpha)
            model.fit((X_tr - mu) / sd, y_tr)
            X_val = (subjects[held][key] - mu) / sd
            pred = model.predict(X_val)
            errs.append(np.abs(pred - subjects[held]["y"]).mean())
        mae = float(np.mean(errs))
        if mae < best_mae:
            best_mae, best_alpha = mae, alpha
    return best_alpha


def run_condition(subjects: dict[int, dict], key: str) -> dict:
    all_sids = sorted(subjects.keys())
    per_subject = {}
    for test_sid in all_sids:
        train_sids = [s for s in all_sids if s != test_sid]
        alpha = nested_loso_select_alpha(train_sids, subjects, key)
        X_tr = np.concatenate([subjects[s][key] for s in train_sids], axis=0)
        y_tr = np.concatenate([subjects[s]["y"] for s in train_sids], axis=0)
        mu, sd = X_tr.mean(axis=0), X_tr.std(axis=0)
        sd[sd == 0] = 1.0
        model = Ridge(alpha=alpha)
        model.fit((X_tr - mu) / sd, y_tr)
        X_te = (subjects[test_sid][key] - mu) / sd
        y_te = subjects[test_sid]["y"]
        pred = model.predict(X_te)
        mae = float(np.abs(pred - y_te).mean())
        rmse = float(np.sqrt(((pred - y_te) ** 2).mean()))
        per_subject[str(test_sid)] = {
            "n_points": subjects[test_sid]["n_points"],
            "mae": mae,
            "rmse": rmse,
            "mean_signed_error": float((pred - y_te).mean()),
            "selected_alpha": alpha,
            "y_true": y_te.tolist(),
            "y_pred": pred.tolist(),
        }
    maes = np.array([v["mae"] for v in per_subject.values()])
    return {
        "per_subject": per_subject,
        "subject_macro_mae_mean": float(maes.mean()),
        "subject_macro_mae_sd_ddof1": float(maes.std(ddof=1)),
        "n_subjects": len(all_sids),
    }


def main() -> None:
    by_subject = load_raw()
    assert len(by_subject) == 10, f"expected 10 subjects, found {len(by_subject)}"
    for sid, rows in by_subject.items():
        assert len(rows) == 9, f"subject {sid} has {len(rows)} points, expected 9"

    subjects = build_subject_arrays(by_subject, np.random.default_rng(CONTROL_SHUFFLE_SEED))

    result_a = run_condition(subjects, "A")
    result_b = run_condition(subjects, "B")
    result_c = run_condition(subjects, "C")

    all_sids = sorted(subjects.keys())
    per_subject_deltas = {}
    favorable_a_minus_b = 0
    favorable_c_minus_b = 0
    for sid in all_sids:
        a_mae = result_a["per_subject"][str(sid)]["mae"]
        b_mae = result_b["per_subject"][str(sid)]["mae"]
        c_mae = result_c["per_subject"][str(sid)]["mae"]
        a_minus_b = a_mae - b_mae  # positive => B (legs) better than A
        c_minus_b = c_mae - b_mae  # positive => B beats deranged control
        if a_minus_b > 0:
            favorable_a_minus_b += 1
        if c_minus_b > 0:
            favorable_c_minus_b += 1
        per_subject_deltas[str(sid)] = {
            "A_mae": a_mae, "B_mae": b_mae, "C_mae": c_mae,
            "A_minus_B": a_minus_b, "C_minus_B": c_minus_b,
        }

    out = {
        "purpose": "QDE V2 leg-BioZ marginal-value experiment, real LOSO ridge-regression training run (Stage 2A).",
        "frozen_protocol_reference": "results/qde_v2_protocol_stage1b.json",
        "target_sign_convention": "delta_weight_kg = weight_at_interval_i - weight_at_interval_0 (becomes increasingly negative as dehydration-driven mass loss accumulates)",
        "control_shuffle_seed_base": CONTROL_SHUFFLE_SEED,
        "n_subjects": 10,
        "n_measurement_points": 90,
        "condition_A_arm_trunk_only": result_a,
        "condition_B_arm_trunk_plus_legs": result_b,
        "condition_C_deranged_legs": result_c,
        "aggregate": {
            "A_subject_macro_mae_mean": result_a["subject_macro_mae_mean"],
            "A_subject_macro_mae_sd_ddof1": result_a["subject_macro_mae_sd_ddof1"],
            "B_subject_macro_mae_mean": result_b["subject_macro_mae_mean"],
            "B_subject_macro_mae_sd_ddof1": result_b["subject_macro_mae_sd_ddof1"],
            "C_subject_macro_mae_mean": result_c["subject_macro_mae_mean"],
            "C_subject_macro_mae_sd_ddof1": result_c["subject_macro_mae_sd_ddof1"],
            "A_minus_B_mean": result_a["subject_macro_mae_mean"] - result_b["subject_macro_mae_mean"],
            "C_minus_B_mean": result_c["subject_macro_mae_mean"] - result_b["subject_macro_mae_mean"],
            "n_subjects_favoring_B_over_A": favorable_a_minus_b,
            "n_subjects_favoring_B_over_C": favorable_c_minus_b,
        },
        "per_subject_deltas": per_subject_deltas,
    }
    OUT_PATH.write_text(json.dumps(out, indent=2))
    print(json.dumps(out["aggregate"], indent=2))
    print("\nWrote", OUT_PATH)


if __name__ == "__main__":
    main()
