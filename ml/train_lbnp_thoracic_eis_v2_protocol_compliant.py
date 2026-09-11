#!/usr/bin/env python
"""LBNP thoracic EIS marginal-value experiment - HIGH-03 remediation
(Stage 3 Codex fail remediation).

Fixes two real defects found in the original
ml/train_lbnp_thoracic_eis.py (results/lbnp_thoracic_eis_stage3.json,
preserved unchanged as a disclosed, historical, OUT_OF_PROTOCOL_SCOPE
execution - see docs/LBNP_STAGE3_HIGH03_REMEDIATION.md):

1. TARGET-RANGE ENFORCEMENT: the frozen protocol
   (results/lbnp_protocol_stage1b.json) specifies the primary target as
   "the 0-60 mmHg range" with the chosen stages 0/15/30/45/60. The
   original script applied NO range filter - real data inspection this
   sprint found 200/607 windows (33%) at stages 70/80/90/100 mmHg, well
   outside the frozen scope. This script filters to stage <= 60 BEFORE
   building features/targets.

2. C-CONTROL SAME-STAGE LEAKAGE: the frozen protocol's C condition
   requires EIS drawn "from a different stage's real EIS spectrum for the
   SAME subject" - i.e. source_stage != target_stage. The original
   deranged_eis() only guaranteed source_index != target_index (no fixed
   points in the permutation), which does NOT guarantee different stage
   when a subject has multiple real windows at the same stage. Measured
   this sprint: 13-25% of "deranged" C windows retained the SAME stage as
   the original under the old function. This script's derangement
   explicitly excludes same-stage candidates when constructing the
   permutation.

Otherwise identical model family / nested LOSO alpha selection / A-B-C
design to the original script.
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

OUT_PATH = REPO_ROOT / "results" / "lbnp_thoracic_eis_stage3_v2_protocol_compliant.json"
ALPHA_GRID = [0.001, 0.01, 0.1, 1.0, 10.0, 30.0, 100.0, 300.0, 1000.0]
CONTROL_SHUFFLE_SEED_BASE = 200042
FROZEN_MAX_STAGE_MMHG = 60.0  # results/lbnp_protocol_stage1b.json: "focused on the 0-60 mmHg range"


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
    log_mag = np.log(w["eis_mag"] + 1e-9)
    phase = w["eis_phase"]
    b_feats = np.concatenate([a_feats, log_mag, phase], axis=1)
    return {"A": a_feats, "B": b_feats}


def deranged_eis_different_stage(log_mag: np.ndarray, phase: np.ndarray, stage: np.ndarray, seed: int) -> tuple[np.ndarray, np.ndarray, int, int]:
    """HIGH-03 fix: derangement that guarantees source_stage != target_stage
    for every window, not merely source_index != target_index. Predeclared
    rule for the impossible case (a subject with only one real stage value
    in scope, so no different-stage source exists for anyone): raise, so
    the caller can apply the predeclared exclusion rule explicitly rather
    than silently falling back to same-stage - see the predeclared-rule
    note in main()."""
    n = len(log_mag)
    if n < 2:
        return log_mag, phase, 0, n
    unique_stages = sorted(set(stage.tolist()))
    if len(unique_stages) < 2:
        raise ValueError(
            "PREDECLARED RULE: cannot construct a different-stage derangement - "
            "this subject has only one real stage value in scope. No valid "
            "mapping exists; caller must exclude this subject from condition C "
            "per the predeclared rule (never silently fall back to same-stage)."
        )
    rng = np.random.default_rng(seed)
    # candidate index pools per stage, for fast different-stage sampling
    idx_by_stage = {s: np.where(stage == s)[0] for s in unique_stages}
    perm = np.arange(n)
    same_stage_count = 0
    for _ in range(2000):
        rng.shuffle(perm)
        same_stage_count = int(np.sum(stage[perm] == stage))
        if same_stage_count == 0:
            break
    if same_stage_count > 0:
        # Deterministic targeted repair: for any remaining same-stage
        # collisions after the shuffle attempts, swap with another index of
        # a different stage (deterministic scan, seeded rng already
        # exhausted its budget - this only fires in rare dense-single-stage
        # edge cases and is fully deterministic given the seed).
        for i in range(n):
            if stage[perm[i]] == stage[i]:
                for j in range(n):
                    if stage[perm[j]] != stage[i] and stage[perm[i]] != stage[j] and i != j:
                        perm[i], perm[j] = perm[j], perm[i]
                        break
    final_same_stage = int(np.sum(stage[perm] == stage))
    return log_mag[perm], phase[perm], final_same_stage, n


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


def leave_one_subject_out_sensitivity(subject_ids, per_subject_deltas, key):
    vals = {sid: per_subject_deltas[str(sid)][key] for sid in subject_ids}
    full_mean = float(np.mean(list(vals.values())))
    per_loo = {}
    any_reversal = False
    for excluded_sid in subject_ids:
        remaining = [v for sid, v in vals.items() if sid != excluded_sid]
        loo_mean = float(np.mean(remaining))
        reversal = (full_mean > 0) != (loo_mean > 0)
        any_reversal = any_reversal or reversal
        per_loo[str(excluded_sid)] = {"loo_mean_excluding_this_subject": loo_mean, "sign_reversal": reversal}
    return {"full_mean": full_mean, "per_subject_loo": per_loo, "any_single_subject_reverses_sign": any_reversal}


def main() -> None:
    data = load_all()
    eligible = [i for i in range(16) if subject_has_valid_pleth(data["labchart"], i)]
    print("Eligible subjects (valid pleth):", eligible, f"n={len(eligible)}")

    windows = {}
    n_windows_out_of_scope_total = 0
    for sid in eligible:
        w_raw = build_subject_windows(data, sid)
        n_total = len(w_raw["stage"])
        in_scope = w_raw["stage"] <= FROZEN_MAX_STAGE_MMHG
        n_out = int((~in_scope).sum())
        n_windows_out_of_scope_total += n_out
        w = {k: (v[in_scope] if hasattr(v, "__len__") and len(v) == n_total else v) for k, v in w_raw.items()}
        if len(w["stage"]) < 5:
            print(f"  subject {sid}: only {len(w['stage'])} in-scope usable windows - excluding (data-integrity)")
            continue
        windows[sid] = w
        print(f"  subject {sid}: {len(w['stage'])} in-scope real windows (excluded {n_out} out-of-scope >60mmHg), "
              f"stages {sorted(set(w['stage'].tolist()))}")

    print(f"\nTotal windows excluded for being outside the frozen 0-{FROZEN_MAX_STAGE_MMHG:.0f} mmHg scope: {n_windows_out_of_scope_total}")

    subject_ids = sorted(windows.keys())
    n_eligible_final = len(subject_ids)
    print(f"Final eligible cohort: n={n_eligible_final}")

    features = {}
    targets = {}
    c_derangement_diagnostics = {}
    for sid in subject_ids:
        feats = build_features(windows[sid])
        log_mag = np.log(windows[sid]["eis_mag"] + 1e-9)
        phase = windows[sid]["eis_phase"]
        stage = windows[sid]["stage"]
        deranged_log_mag, deranged_phase, same_stage_count, n = deranged_eis_different_stage(
            log_mag, phase, stage, CONTROL_SHUFFLE_SEED_BASE + sid
        )
        c_derangement_diagnostics[str(sid)] = {"n_windows": n, "same_stage_collisions_remaining": same_stage_count}
        a_feats = feats["A"]
        c_feats = np.concatenate([a_feats, deranged_log_mag, deranged_phase], axis=1)
        features[sid] = {"A": feats["A"], "B": feats["B"], "C": c_feats}
        targets[sid] = stage

    total_collisions = sum(v["same_stage_collisions_remaining"] for v in c_derangement_diagnostics.values())
    print(f"\nC-condition same-stage collisions remaining after fix (must be 0): {total_collisions}")
    if total_collisions != 0:
        raise RuntimeError(f"HIGH-03 C-control fix incomplete: {total_collisions} same-stage collisions remain")

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

    loo_a_minus_b = leave_one_subject_out_sensitivity(subject_ids, per_subject_deltas, "A_minus_B")
    loo_c_minus_b = leave_one_subject_out_sensitivity(subject_ids, per_subject_deltas, "C_minus_B")

    out = {
        "experiment_id": "lbnp_thoracic_eis_stage3_v2_protocol_compliant",
        "supersedes": "results/lbnp_thoracic_eis_stage3.json (HISTORICAL, OUT_OF_PROTOCOL_SCOPE - see docs/LBNP_STAGE3_HIGH03_REMEDIATION.md)",
        "frozen_protocol_reference": "results/lbnp_protocol_stage1b.json",
        "high03_fixes_applied": [
            f"target_range_enforcement: filtered to stage <= {FROZEN_MAX_STAGE_MMHG:.0f} mmHg per the frozen protocol's own '0-60 mmHg range' scope; "
            f"{n_windows_out_of_scope_total} out-of-scope windows (70/80/90/100 mmHg) excluded before any feature/model construction",
            "c_control_different_stage_enforcement: deranged_eis_different_stage() guarantees source_stage != target_stage for every window (0 same-stage collisions remaining, verified programmatically)",
        ],
        "real_eligibility_finding": f"Only {len(eligible)}/16 subjects have valid (non-NaN) pleth data. Final cohort after also requiring >=5 in-scope usable windows: n={n_eligible_final}.",
        "eligible_subject_indices_0based": subject_ids,
        "target": f"Real LBNP pressure stage (mmHg), step-function looked up at each real EIS spectrum's timestamp, filtered to the frozen 0-{FROZEN_MAX_STAGE_MMHG:.0f} mmHg scope",
        "window_seconds": 20.0,
        "n_subjects": n_eligible_final,
        "condition_A_ecg_pleth": result_a,
        "condition_B_plus_thoracic_eis": result_b,
        "condition_C_deranged_eis": result_c,
        "c_control_derangement_diagnostics": c_derangement_diagnostics,
        "aggregate": {
            "A_mean": result_a["subject_macro_mae_mean"], "B_mean": result_b["subject_macro_mae_mean"], "C_mean": result_c["subject_macro_mae_mean"],
            "A_minus_B_mean": result_a["subject_macro_mae_mean"] - result_b["subject_macro_mae_mean"],
            "C_minus_B_mean": result_c["subject_macro_mae_mean"] - result_b["subject_macro_mae_mean"],
            "n_subjects_favoring_B_over_A": n_favor_b_over_a, "n_subjects_favoring_B_over_C": n_favor_b_over_c, "n_subjects_total": n_eligible_final,
        },
        "per_subject_deltas": per_subject_deltas,
        "leave_one_subject_out_sensitivity": {
            "A_minus_B": loo_a_minus_b,
            "C_minus_B": loo_c_minus_b,
        },
    }
    OUT_PATH.write_text(json.dumps(out, indent=2))
    print(json.dumps(out["aggregate"], indent=2))
    print("\nLOO sensitivity (A_minus_B) any single subject reverses sign:", loo_a_minus_b["any_single_subject_reverses_sign"])
    print("LOO sensitivity (C_minus_B) any single subject reverses sign:", loo_c_minus_b["any_single_subject_reverses_sign"])
    print("Wrote", OUT_PATH)


if __name__ == "__main__":
    main()
