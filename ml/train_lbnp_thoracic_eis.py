#!/usr/bin/env python
"""LBNP thoracic EIS marginal-value experiment (Stage 3, Priority 2).

Real LOSO ridge-regression training run (small tabular/spectral data at
n=12 eligible subjects - same model-class philosophy as
ml/train_qde_v2_leg_bioz.py: prefer a small model family at this scale,
not a deep architecture).

FROZEN A/B/C (per results/lbnp_protocol_stage1b.json, this session's own
real-data eligibility finding, and the ordinal-MAE metric decision already
recorded there):
  A = ECG + pleth simple time/frequency features (10-dim: mean_abs/std/
      3-band-power per channel).
  B = A + real thoracic EIS features (log-magnitude at all 100 real
      frequencies + phase at all 100 real frequencies = 200-dim).
  C = B-dimensional, EIS-stage correspondence deranged WITHIN SUBJECT
      (real EIS spectrum from a different real timepoint of the SAME
      subject, subject identity/partition preserved, never label-informed).

REAL ELIGIBILITY FINDING (this sprint): only 12 of 16 subjects have valid
(non-NaN) pleth data (ml/datasets/lbnp_impedance.py) - the other 4 are
excluded via a predeclared data-quality rule, not an outcome-based one.

Target: real LBNP pressure stage (mmHg), step-function-looked-up at each
real EIS spectrum's own timestamp. Metric: MAE (mmHg), matching the frozen
ordinal-regression decision (stages are a real physiological ordering, not
unordered categories).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
from sklearn.linear_model import Ridge

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from ml.datasets.lbnp_impedance import build_subject_windows, load_all, subject_has_valid_pleth  # noqa: E402

OUT_PATH = REPO_ROOT / "results" / "lbnp_thoracic_eis_stage3.json"
ALPHA_GRID = [0.001, 0.01, 0.1, 1.0, 10.0, 30.0, 100.0, 300.0, 1000.0]
CONTROL_SHUFFLE_SEED_BASE = 200042


def channel_features(x: np.ndarray, fs: float = 1000.0) -> np.ndarray:
    mean_abs = np.mean(np.abs(x))
    std = np.std(x)
    fft = np.abs(np.fft.rfft(x))
    freqs = np.fft.rfftfreq(len(x), d=1.0 / fs)
    low = fft[(freqs >= 0.5) & (freqs < 5)].mean() if np.any((freqs >= 0.5) & (freqs < 5)) else 0.0
    mid = fft[(freqs >= 5) & (freqs < 15)].mean() if np.any((freqs >= 5) & (freqs < 15)) else 0.0
    high = fft[(freqs >= 15) & (freqs < 40)].mean() if np.any((freqs >= 15) & (freqs < 40)) else 0.0
    return np.array([mean_abs, std, low, mid, high])


def build_features(w: dict) -> dict:
    n = len(w["stage"])
    a_feats = np.zeros((n, 10))
    for i in range(n):
        a_feats[i, :5] = channel_features(w["ecg"][i])
        a_feats[i, 5:] = channel_features(w["pleth"][i])
    log_mag = np.log(w["eis_mag"] + 1e-9)  # (n, 100)
    phase = w["eis_phase"]  # (n, 100)
    b_feats = np.concatenate([a_feats, log_mag, phase], axis=1)
    return {"A": a_feats, "B": b_feats}


def deranged_eis(log_mag: np.ndarray, phase: np.ndarray, seed: int) -> tuple[np.ndarray, np.ndarray]:
    n = len(log_mag)
    if n < 2:
        return log_mag, phase
    rng = np.random.default_rng(seed)
    perm = np.arange(n)
    for _ in range(1000):
        rng.shuffle(perm)
        if not np.any(perm == np.arange(n)):
            break
    return log_mag[perm], phase[perm]


def nested_loso_alpha(train_ids, features, targets, key):
    best_alpha, best_mae = ALPHA_GRID[0], float("inf")
    for alpha in ALPHA_GRID:
        errs = []
        for held in train_ids:
            inner_train = [s for s in train_ids if s != held]
            X_tr = np.concatenate([features[s][key] for s in inner_train], axis=0)
            y_tr = np.concatenate([targets[s] for s in inner_train], axis=0)
            mu, sd = X_tr.mean(axis=0), X_tr.std(axis=0)
            sd[sd == 0] = 1.0
            model = Ridge(alpha=alpha)
            model.fit((X_tr - mu) / sd, y_tr)
            X_val = (features[held][key] - mu) / sd
            pred = model.predict(X_val)
            errs.append(np.abs(pred - targets[held]).mean())
        mae = float(np.mean(errs))
        if mae < best_mae:
            best_mae, best_alpha = mae, alpha
    return best_alpha


def run_condition(subject_ids, features, targets, key):
    per_subject = {}
    for test_sid in subject_ids:
        train_ids = [s for s in subject_ids if s != test_sid]
        alpha = nested_loso_alpha(train_ids, features, targets, key)
        X_tr = np.concatenate([features[s][key] for s in train_ids], axis=0)
        y_tr = np.concatenate([targets[s] for s in train_ids], axis=0)
        mu, sd = X_tr.mean(axis=0), X_tr.std(axis=0)
        sd[sd == 0] = 1.0
        model = Ridge(alpha=alpha)
        model.fit((X_tr - mu) / sd, y_tr)
        X_te = (features[test_sid][key] - mu) / sd
        y_te = targets[test_sid]
        pred = model.predict(X_te)
        mae = float(np.abs(pred - y_te).mean())
        per_subject[str(test_sid)] = {"n_points": len(y_te), "mae": mae, "selected_alpha": alpha}
    maes = np.array([v["mae"] for v in per_subject.values()])
    return {"per_subject": per_subject, "subject_macro_mae_mean": float(maes.mean()), "subject_macro_mae_sd_ddof1": float(maes.std(ddof=1))}


def main() -> None:
    data = load_all()
    eligible = [i for i in range(16) if subject_has_valid_pleth(data["labchart"], i)]
    print("Eligible subjects (valid pleth):", eligible, f"n={len(eligible)}")

    windows = {}
    for sid in eligible:
        w = build_subject_windows(data, sid)
        if len(w["stage"]) < 5:
            print(f"  subject {sid}: only {len(w['stage'])} usable windows - excluding (data-integrity)")
            continue
        windows[sid] = w
        print(f"  subject {sid}: {len(w['stage'])} real windows, stages {sorted(set(w['stage'].tolist()))}")

    subject_ids = sorted(windows.keys())
    n_eligible_final = len(subject_ids)
    print(f"Final eligible cohort: n={n_eligible_final}")

    features = {}
    targets = {}
    for sid in subject_ids:
        feats = build_features(windows[sid])
        log_mag = np.log(windows[sid]["eis_mag"] + 1e-9)
        phase = windows[sid]["eis_phase"]
        deranged_log_mag, deranged_phase = deranged_eis(log_mag, phase, CONTROL_SHUFFLE_SEED_BASE + sid)
        a_feats = feats["A"]
        c_feats = np.concatenate([a_feats, deranged_log_mag, deranged_phase], axis=1)
        features[sid] = {"A": feats["A"], "B": feats["B"], "C": c_feats}
        targets[sid] = windows[sid]["stage"]

    result_a = run_condition(subject_ids, features, targets, "A")
    result_b = run_condition(subject_ids, features, targets, "B")
    result_c = run_condition(subject_ids, features, targets, "C")

    per_subject_deltas = {}
    n_favor_b_over_a, n_favor_b_over_c = 0, 0
    for sid in subject_ids:
        a_mae = result_a["per_subject"][str(sid)]["mae"]
        b_mae = result_b["per_subject"][str(sid)]["mae"]
        c_mae = result_c["per_subject"][str(sid)]["mae"]
        a_minus_b = a_mae - b_mae
        c_minus_b = c_mae - b_mae
        if a_minus_b > 0:
            n_favor_b_over_a += 1
        if c_minus_b > 0:
            n_favor_b_over_c += 1
        per_subject_deltas[str(sid)] = {"A_mae": a_mae, "B_mae": b_mae, "C_mae": c_mae, "A_minus_B": a_minus_b, "C_minus_B": c_minus_b}

    out = {
        "experiment_id": "lbnp_thoracic_eis_stage3",
        "frozen_protocol_reference": "results/lbnp_protocol_stage1b.json",
        "real_eligibility_finding": f"Only {len(eligible)}/16 subjects have valid (non-NaN) pleth data (predeclared data-quality rule, not outcome-based). Final cohort after also requiring >=5 usable windows: n={n_eligible_final}.",
        "eligible_subject_indices_0based": subject_ids,
        "target": "Real LBNP pressure stage (mmHg), step-function looked up at each real EIS spectrum's timestamp",
        "window_seconds": 20.0,
        "n_subjects": n_eligible_final,
        "condition_A_ecg_pleth": result_a,
        "condition_B_plus_thoracic_eis": result_b,
        "condition_C_deranged_eis": result_c,
        "aggregate": {
            "A_mean": result_a["subject_macro_mae_mean"], "B_mean": result_b["subject_macro_mae_mean"], "C_mean": result_c["subject_macro_mae_mean"],
            "A_minus_B_mean": result_a["subject_macro_mae_mean"] - result_b["subject_macro_mae_mean"],
            "C_minus_B_mean": result_c["subject_macro_mae_mean"] - result_b["subject_macro_mae_mean"],
            "n_subjects_favoring_B_over_A": n_favor_b_over_a, "n_subjects_favoring_B_over_C": n_favor_b_over_c, "n_subjects_total": n_eligible_final,
        },
        "per_subject_deltas": per_subject_deltas,
    }
    OUT_PATH.write_text(json.dumps(out, indent=2))
    print(json.dumps(out["aggregate"], indent=2))
    print("Wrote", OUT_PATH)


if __name__ == "__main__":
    main()
