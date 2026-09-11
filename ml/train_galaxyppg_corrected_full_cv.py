#!/usr/bin/env python
"""GalaxyPPG CORRECTED full 6-fold grouped external replication
(GALAXYPPG_CORRECTED_ELIGIBILITY_CV_PROTOCOL_V2, Stage 3 continuation).

Runs over the real, corrected 18-subject eligible cohort (6 subjects
excluded this sprint for a real reference-ECG-quality defect - see
docs/GALAXYPPG_REFERENCE_SIGNAL_QUALITY_BLOCKER.md and
docs/GALAXYPPG_REFERENCE_QUALITY_THRESHOLD_JUSTIFICATION.md), NOT the
original invalidated 24-subject design. Every one of the 18 real eligible
participants is held out as a test subject exactly once, across 6 folds of
3 subjects each (results/galaxyppg_corrected_full_cv_folds.json - frozen
via the identical random.Random(42) shuffle convention used throughout
this project, before any full-CV training under the corrected cohort).

Fold 5 (test=P02/P06/P12) is IDENTICAL in every respect (train/val/test
membership) to the already-completed corrected single-fold result
(results/galaxyppg_hr_corrected_eligibility_stage3.json) - independently
RE-VERIFIED this sprint (not assumed from the pre-fix claim) by
re-deriving the fold assignment from scratch over the corrected cohort and
confirming exact set equality - so it is reused rather than retrained.
This script trains folds 0-4 only.

Reuses the exact model classes, capacity-matching design, RNG discipline,
and windowing pipeline established in
ml/train_galaxyppg_hr_external_replication.py - only the fold/split loop
and checkpoint naming (galaxyppg_hr_correctedcv_v2_*, distinct from the
invalidated pre-fix galaxyppg_hr_fullcv_* checkpoints) are new.
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

from ml.datasets.galaxyppg import build_participant_windows  # noqa: E402
from ml.train_galaxyppg_hr_external_replication import (  # noqa: E402
    CKPT_DIR,
    DATA_DIR,
    PPGCapacityMatchedModel,
    PPGPlusIMUModel,
    SEEDS,
    deranged_acc_stable,
    evaluate,
    load_split_windows,
    normalize_fit,
    train_one,
)
from ml.fix_galaxyppg_participant_c_evaluation import deranged_acc_for_subject_at_index  # noqa: E402

FOLDS_PATH = REPO_ROOT / "results" / "galaxyppg_corrected_full_cv_folds.json"
SINGLE_FOLD_RESULT_PATH = REPO_ROOT / "results" / "galaxyppg_hr_corrected_eligibility_stage3.json"
OUT_PATH = REPO_ROOT / "results" / "galaxyppg_corrected_full_cv_result.json"

CONTROL_SHUFFLE_SEED_BASE = 200042


def run_fold(fold_idx: int, folds: list[list[str]]) -> dict:
    test_ids = folds[fold_idx]
    val_ids = folds[(fold_idx + 1) % 6]
    train_ids = [p for i, f in enumerate(folds) if i not in (fold_idx, (fold_idx + 1) % 6) for p in f]
    print(f"\n=== FOLD {fold_idx}: test={test_ids} val={val_ids} train={len(train_ids)} subjects ===")

    train = load_split_windows(train_ids)
    val = load_split_windows(val_ids)
    test = load_split_windows(test_ids)
    print(f"fold {fold_idx}: train={len(train['hr'])} val={len(val['hr'])} test={len(test['hr'])} windows")

    hr_mean, hr_std = normalize_fit(train["hr"])
    train_hr_norm = ((train["hr"] - hr_mean) / hr_std).astype(np.float32)
    val_hr_norm = ((val["hr"] - hr_mean) / hr_std).astype(np.float32)

    fold_out: dict = {
        "test_subjects": test_ids, "val_subjects": val_ids, "train_subjects": train_ids,
        "hr_normalization": {"mean": hr_mean, "std": hr_std},
        "window_counts": {"train": len(train["hr"]), "val": len(val["hr"]), "test": len(test["hr"])},
        "runs": {"A_cap": {}, "B": {}, "C": {}},
        "per_subject": {},
        "checkpoint_manifest": [],
    }

    per_subject_preds = {name: {pid: {} for pid in test_ids} for name in ("A_cap", "B", "C")}

    for seed in SEEDS:
        torch.manual_seed(seed)
        model_a = PPGCapacityMatchedModel()
        train_one(model_a, train["bvp"], train["bvp"], train_hr_norm, val["bvp"], val["bvp"], val_hr_norm, seed)
        report_a = evaluate(model_a, test["bvp"], test["bvp"], test["hr"], hr_mean, hr_std)
        fold_out["runs"]["A_cap"][f"seed{seed}"] = report_a

        torch.manual_seed(seed)
        model_b = PPGPlusIMUModel()
        train_one(model_b, train["bvp"], train["acc"], train_hr_norm, val["bvp"], val["acc"], val_hr_norm, seed)
        report_b = evaluate(model_b, test["bvp"], test["acc"], test["hr"], hr_mean, hr_std)
        fold_out["runs"]["B"][f"seed{seed}"] = report_b

        train_acc_d = deranged_acc_stable(train["acc"], train["subject"], CONTROL_SHUFFLE_SEED_BASE + seed)
        val_acc_d = deranged_acc_stable(val["acc"], val["subject"], CONTROL_SHUFFLE_SEED_BASE + seed)
        test_acc_d = deranged_acc_stable(test["acc"], test["subject"], CONTROL_SHUFFLE_SEED_BASE + seed)
        torch.manual_seed(seed)
        model_c = PPGPlusIMUModel()
        train_one(model_c, train["bvp"], train_acc_d, train_hr_norm, val["bvp"], val_acc_d, val_hr_norm, seed)
        report_c = evaluate(model_c, test["bvp"], test_acc_d, test["hr"], hr_mean, hr_std)
        fold_out["runs"]["C"][f"seed{seed}"] = report_c

        print(f"fold {fold_idx} seed {seed}: A_cap={report_a['mae']:.3f} B={report_b['mae']:.3f} C={report_c['mae']:.3f}")

        for name, model in (("A_cap", model_a), ("B", model_b), ("C", model_c)):
            ckpt_path = CKPT_DIR / f"galaxyppg_hr_correctedcv_v2_fold{fold_idx}_{name}_seed{seed}.pt"
            torch.save(model.state_dict(), ckpt_path)
            ckpt_bytes = ckpt_path.read_bytes()
            fold_out["checkpoint_manifest"].append({
                "run_id": f"fold{fold_idx}_{name}_seed{seed}", "fold": fold_idx, "config": name, "seed": seed,
                "path": str(ckpt_path.relative_to(REPO_ROOT)),
                "size_bytes": len(ckpt_bytes), "sha256": hashlib.sha256(ckpt_bytes).hexdigest(),
            })

        # per-subject breakdown for this fold/seed. HIGH-01 fix: condition C
        # must receive the same deranged test ACC used by the fold-level C
        # evaluation above (test_acc_d), never the aligned acc_t - keyed by
        # each subject's position in sorted(test_ids), matching
        # deranged_acc_stable's own internal per-subject indexing exactly.
        sorted_test_ids = sorted(test_ids)
        for pid in test_ids:
            w = build_participant_windows(DATA_DIR, pid)
            if len(w["hr"]) == 0:
                continue
            subject_index = sorted_test_ids.index(pid)
            acc_c_t = torch.from_numpy(
                deranged_acc_for_subject_at_index(w["acc_windows"], CONTROL_SHUFFLE_SEED_BASE + seed, subject_index)
            )
            bvp_t = torch.from_numpy(w["bvp_windows"]).unsqueeze(1)
            acc_t = torch.from_numpy(w["acc_windows"])
            hr_true = w["hr"]
            with torch.no_grad():
                pred_a = model_a(bvp_t, bvp_t).numpy() * hr_std + hr_mean
                pred_b = model_b(bvp_t, acc_t).numpy() * hr_std + hr_mean
                pred_c = model_c(bvp_t, acc_c_t).numpy() * hr_std + hr_mean
            per_subject_preds["A_cap"][pid][f"seed{seed}"] = float(np.abs(pred_a - hr_true).mean())
            per_subject_preds["B"][pid][f"seed{seed}"] = float(np.abs(pred_b - hr_true).mean())
            per_subject_preds["C"][pid][f"seed{seed}"] = float(np.abs(pred_c - hr_true).mean())

    for pid in test_ids:
        a_vals = list(per_subject_preds["A_cap"][pid].values())
        b_vals = list(per_subject_preds["B"][pid].values())
        c_vals = list(per_subject_preds["C"][pid].values())
        fold_out["per_subject"][pid] = {
            "A_cap_mae_mean": float(np.mean(a_vals)), "B_mae_mean": float(np.mean(b_vals)), "C_mae_mean": float(np.mean(c_vals)),
            "A_to_B_mean": float(np.mean(a_vals) - np.mean(b_vals)), "C_to_B_mean": float(np.mean(c_vals) - np.mean(b_vals)),
        }

    return fold_out


def main() -> None:
    folds = json.loads(FOLDS_PATH.read_text())["folds"]
    single_fold_result = json.loads(SINGLE_FOLD_RESULT_PATH.read_text())
    per_subject_single = json.loads((REPO_ROOT / "results" / "galaxyppg_hr_corrected_per_subject_stage3.json").read_text())

    out: dict = {
        "experiment_id": "galaxyppg_hr_corrected_eligibility_full_cv_v2",
        "frozen_folds": folds,
        "fold5_reuse_note": "Fold 5 (test=P02/P06/P12) is identical train/val/test membership to the corrected-eligibility single-fold diagnostic - reused verbatim, not retrained. See results/galaxyppg_hr_corrected_eligibility_stage3.json for its full per-seed detail. (Section 16 fix: this note previously named the wrong test subjects P01/P04/P09/P21 and pointed to the invalidated pre-fix galaxyppg_hr_external_replication_stage2.json - both corrected; the underlying reused data itself, loaded from SINGLE_FOLD_RESULT_PATH, was always the correct corrected-eligibility file.)",
        "folds": {},
    }

    # Reuse fold 5 = prior single-fold result
    out["folds"]["5"] = {
        "test_subjects": folds[5], "val_subjects": folds[4],
        "train_subjects": [p for i, f in enumerate(folds) if i not in (5, 4) for p in f],
        "reused_from": "results/galaxyppg_hr_corrected_eligibility_stage3.json",
        "runs": single_fold_result["runs"],
        "window_counts": single_fold_result["window_counts"],
        "per_subject": {pid: per_subject_single["per_subject_summary"][pid] for pid in folds[5]},
    }

    for fold_idx in range(5):
        out["folds"][str(fold_idx)] = run_fold(fold_idx, folds)
        OUT_PATH.write_text(json.dumps(out, indent=2))  # incremental save after each fold
        print(f"Incremental save after fold {fold_idx} written to {OUT_PATH}")

    # --- Aggregate across all 6 folds (subject-level, since every subject appears exactly once as test) ---
    all_subject_results = {}
    for fold_key, fold_data in out["folds"].items():
        for pid, vals in fold_data["per_subject"].items():
            all_subject_results[pid] = vals

    a_mae = [v["A_cap_mae_mean"] for v in all_subject_results.values()]
    b_mae = [v["B_mae_mean"] for v in all_subject_results.values()]
    c_mae = [v["C_mae_mean"] for v in all_subject_results.values()]
    a_to_b = [a - b for a, b in zip(a_mae, b_mae)]
    c_to_b = [c - b for c, b in zip(c_mae, b_mae)]

    def agg(vals):
        arr = np.asarray(vals, dtype=np.float64)
        return {"mean": float(arr.mean()), "sd_sample_ddof1": float(arr.std(ddof=1)), "n": len(vals)}

    out["aggregate_across_all_18_eligible_subjects"] = {
        "A_cap_mae": agg(a_mae), "B_mae": agg(b_mae), "C_mae": agg(c_mae),
        "A_to_B": {**agg(a_to_b), "n_subjects_favor_B": sum(1 for d in a_to_b if d > 0), "n_subjects_total": len(a_to_b)},
        "C_to_B": {**agg(c_to_b), "n_subjects_favor_B": sum(1 for d in c_to_b if d > 0), "n_subjects_total": len(c_to_b)},
    }

    OUT_PATH.write_text(json.dumps(out, indent=2))
    print("\nWrote", OUT_PATH)
    print(json.dumps(out["aggregate_across_all_18_eligible_subjects"], indent=2))


if __name__ == "__main__":
    main()
