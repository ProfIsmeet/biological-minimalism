#!/usr/bin/env python
"""HIGH-01 remediation: recomputes GalaxyPPG participant-level condition-C
evaluation using the correct deranged test ACC (the fold-level/bounded
C evaluation was always correct; only the per-participant breakdown used
aligned ACC by mistake - see
ml/train_galaxyppg_corrected_full_cv.py::run_fold and
ml/build_galaxyppg_corrected_per_subject_results.py, both fixed by this
script's approach and by direct source edits alongside it).

No retraining: loads the already-trained, already-archived C checkpoints
and re-evaluates them with the correctly-deranged per-participant ACC.

Reconstructs the exact same derangement used at fold level by replicating
deranged_acc_stable's per-subject inner loop directly, keyed by each
subject's position in sorted(test_ids) - this is deterministic and
independent of window row order, so it exactly reproduces the array-level
derangement's per-subject permutation.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "backend"))
sys.path.insert(0, str(REPO_ROOT))

from app.ml._torch_bootstrap import ensure_torch_dll_path  # noqa: E402

ensure_torch_dll_path()

import torch  # noqa: E402

from ml.datasets.galaxyppg import build_participant_windows  # noqa: E402
from ml.train_galaxyppg_hr_external_replication import (  # noqa: E402
    CKPT_DIR,
    DATA_DIR,
    PPGPlusIMUModel,
    SEEDS,
)

CONTROL_SHUFFLE_SEED_BASE = 200042


def deranged_acc_for_subject_at_index(acc_windows: np.ndarray, seed_base: int, subject_index: int) -> np.ndarray:
    """Exact replica of deranged_acc_stable's per-subject inner loop for one
    subject known to be at position `subject_index` in sorted(unique test
    subject IDs) - reproduces the identical permutation deranged_acc_stable
    would have applied to that subject's rows within the full test array."""
    n = len(acc_windows)
    if n < 2:
        return acc_windows.copy()
    rng = np.random.default_rng(seed_base + subject_index)
    perm = np.arange(n)
    for _ in range(1000):
        rng.shuffle(perm)
        if not np.any(perm == np.arange(n)):
            break
    return acc_windows[perm]


def recompute_per_subject_c(test_ids: list[str], ckpt_paths: dict[int, Path], hr_mean: float, hr_std: float):
    """Returns (per_subject_per_seed_c_mae, per_seed_concatenated_mae) for one
    fold/split. per_seed_concatenated_mae is the strong-consistency check
    value: concatenating corrected per-participant predictions should
    reproduce the already-valid fold-level C MAE."""
    sorted_test_ids = sorted(test_ids)
    windows = {pid: build_participant_windows(DATA_DIR, pid) for pid in test_ids}

    per_subject_per_seed: dict[str, dict[str, float]] = {pid: {} for pid in test_ids}
    per_seed_concat_mae: dict[str, float] = {}

    for seed in SEEDS:
        model_c = PPGPlusIMUModel()
        model_c.load_state_dict(torch.load(ckpt_paths[seed], map_location="cpu"))
        model_c.eval()

        concat_pred, concat_true = [], []
        for pid in test_ids:
            w = windows[pid]
            if len(w["hr"]) == 0:
                continue
            subject_index = sorted_test_ids.index(pid)
            acc_deranged = deranged_acc_for_subject_at_index(
                w["acc_windows"], CONTROL_SHUFFLE_SEED_BASE + seed, subject_index
            )
            bvp_t = torch.from_numpy(w["bvp_windows"]).unsqueeze(1)
            acc_t = torch.from_numpy(acc_deranged)
            with torch.no_grad():
                pred_c = model_c(bvp_t, acc_t).numpy() * hr_std + hr_mean
            hr_true = w["hr"]
            per_subject_per_seed[pid][f"seed{seed}"] = float(np.abs(pred_c - hr_true).mean())
            concat_pred.append(pred_c)
            concat_true.append(hr_true)

        concat_pred = np.concatenate(concat_pred)
        concat_true = np.concatenate(concat_true)
        per_seed_concat_mae[f"seed{seed}"] = float(np.abs(concat_pred - concat_true).mean())

    return per_subject_per_seed, per_seed_concat_mae


def main() -> None:
    report = {"purpose": "HIGH-01 remediation run log: strong-consistency check per fold/seed.", "checks": []}

    # --- Full CV folds 0-4 (correctedcv_v2) ---
    full_cv_path = REPO_ROOT / "results" / "galaxyppg_corrected_full_cv_result.json"
    full_cv = json.loads(full_cv_path.read_text())

    for fold_idx in range(5):
        fold_out = full_cv["folds"][str(fold_idx)]
        test_ids = fold_out["test_subjects"]  # use the actually-recorded test set, not re-derived
        hr_mean = fold_out["hr_normalization"]["mean"]
        hr_std = fold_out["hr_normalization"]["std"]
        ckpt_paths = {
            seed: CKPT_DIR / f"galaxyppg_hr_correctedcv_v2_fold{fold_idx}_C_seed{seed}.pt" for seed in SEEDS
        }
        per_subject_per_seed, per_seed_concat_mae = recompute_per_subject_c(test_ids, ckpt_paths, hr_mean, hr_std)

        for seed in SEEDS:
            fold_level_mae = fold_out["runs"]["C"][f"seed{seed}"]["mae"]
            recomputed_mae = per_seed_concat_mae[f"seed{seed}"]
            diff = abs(fold_level_mae - recomputed_mae)
            report["checks"].append({
                "fold": fold_idx, "seed": seed, "fold_level_C_mae": fold_level_mae,
                "recomputed_concatenated_participant_C_mae": recomputed_mae, "abs_diff": diff,
                "within_tolerance_1e-4": diff < 1e-4,
            })
            if diff >= 1e-4:
                raise RuntimeError(
                    f"STRONG CONSISTENCY CHECK FAILED: fold {fold_idx} seed {seed} "
                    f"fold-level C MAE={fold_level_mae} vs recomputed concatenated "
                    f"participant C MAE={recomputed_mae}, diff={diff}"
                )

        # Overwrite per-subject C values (A_cap and B are untouched - Codex
        # confirmed those credible, and this bug only ever affected C).
        for pid in test_ids:
            a_vals = fold_out["per_subject"][pid]["A_cap_mae_mean"]
            b_vals = fold_out["per_subject"][pid]["B_mae_mean"]
            c_vals = list(per_subject_per_seed[pid].values())
            c_mean = float(np.mean(c_vals))
            fold_out["per_subject"][pid]["C_mae_mean"] = c_mean
            fold_out["per_subject"][pid]["C_mae_mean_per_seed_HIGH01_corrected"] = per_subject_per_seed[pid]
            fold_out["per_subject"][pid]["C_to_B_mean"] = c_mean - b_vals
        print(f"Fold {fold_idx}: HIGH-01 corrected, strong-consistency check passed (max diff "
              f"{max(c['abs_diff'] for c in report['checks'] if c['fold'] == fold_idx):.2e})")

    full_cv["high01_participant_c_correction_note"] = (
        "HIGH-01 remediation: the per-participant condition-C evaluation "
        "previously supplied aligned test ACC to model_c instead of the "
        "deranged test ACC used by the (always-correct) fold-level C "
        "evaluation. Fixed by ml/fix_galaxyppg_participant_c_evaluation.py, "
        "which reconstructs the identical per-subject derangement (keyed by "
        "each subject's position in sorted(test_ids), matching "
        "deranged_acc_stable's internal indexing) and re-evaluates the "
        "already-trained, already-archived C checkpoints - no retraining. "
        "A strong-consistency check (concatenated corrected per-participant "
        "C predictions must reproduce the fold-level C MAE within 1e-4) "
        "passed for every fold/seed - see "
        "results/galaxyppg_high01_strong_consistency_check.json. Only C "
        "values changed; A_cap and B per-subject values are unchanged."
    )
    full_cv_path.write_text(json.dumps(full_cv, indent=2))
    print("Wrote corrected", full_cv_path)

    # --- Bounded single-fold diagnostic (source of fold 5's per-subject data) ---
    split = json.loads((REPO_ROOT / "results" / "galaxyppg_split_stage3_corrected_eligibility.json").read_text())
    bounded_result = json.loads((REPO_ROOT / "results" / "galaxyppg_hr_corrected_eligibility_stage3.json").read_text())
    hr_mean = bounded_result["hr_normalization"]["mean"]
    hr_std = bounded_result["hr_normalization"]["std"]
    test_ids = split["test"]
    ckpt_paths = {seed: CKPT_DIR / f"galaxyppg_hr_corrected_C_seed{seed}.pt" for seed in SEEDS}
    per_subject_per_seed, per_seed_concat_mae = recompute_per_subject_c(test_ids, ckpt_paths, hr_mean, hr_std)

    bounded_checks = []
    for seed in SEEDS:
        fold_level_mae = bounded_result["runs"]["C"][f"seed{seed}"]["mae"]
        recomputed_mae = per_seed_concat_mae[f"seed{seed}"]
        diff = abs(fold_level_mae - recomputed_mae)
        bounded_checks.append({
            "seed": seed, "fold_level_C_mae": fold_level_mae,
            "recomputed_concatenated_participant_C_mae": recomputed_mae, "abs_diff": diff,
            "within_tolerance_1e-4": diff < 1e-4,
        })
        if diff >= 1e-4:
            raise RuntimeError(
                f"STRONG CONSISTENCY CHECK FAILED (bounded diagnostic): seed {seed} "
                f"fold-level C MAE={fold_level_mae} vs recomputed={recomputed_mae}, diff={diff}"
            )
    report["checks"].extend([{"fold": "bounded_diagnostic_5", **c} for c in bounded_checks])
    print(f"Bounded diagnostic (fold 5 source): HIGH-01 corrected, strong-consistency check passed "
          f"(max diff {max(c['abs_diff'] for c in bounded_checks):.2e})")

    # Rewrite the per-subject summary file (fold 5's actual data source)
    per_subject_path = REPO_ROOT / "results" / "galaxyppg_hr_corrected_per_subject_stage3.json"
    per_subject_doc = json.loads(per_subject_path.read_text())
    for pid in test_ids:
        a_vals = list(per_subject_doc["per_subject_per_seed"]["A_cap"][pid].values())
        b_vals = list(per_subject_doc["per_subject_per_seed"]["B"][pid].values())
        c_vals = list(per_subject_per_seed[pid].values())
        per_subject_doc["per_subject_per_seed"]["C"][pid] = per_subject_per_seed[pid]
        c_mean = float(np.mean(c_vals))
        per_subject_doc["per_subject_summary"][pid]["C_mae_mean"] = c_mean
        per_subject_doc["per_subject_summary"][pid]["C_to_B_mean"] = c_mean - float(np.mean(b_vals))
    per_subject_doc["high01_participant_c_correction_note"] = full_cv["high01_participant_c_correction_note"]
    per_subject_path.write_text(json.dumps(per_subject_doc, indent=2))
    print("Wrote corrected", per_subject_path)

    (REPO_ROOT / "results" / "galaxyppg_high01_strong_consistency_check.json").write_text(json.dumps(report, indent=2))
    print("Wrote results/galaxyppg_high01_strong_consistency_check.json -", len(report["checks"]), "checks, all passed")


if __name__ == "__main__":
    main()
