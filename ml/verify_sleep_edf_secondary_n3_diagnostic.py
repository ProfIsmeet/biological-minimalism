#!/usr/bin/env python
"""Day 10 Phase E: verify the Day-9 canonical N3 regression diagnostic from
the frozen secondary-holdout prediction/confusion artifacts. Read-only -
recomputes precision/recall/confusion deltas from
results/sleep_edf_secondary_holdout_evaluation.json's stored per-seed
confusion matrices. No retraining, no new predictions.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from ml.datasets.sleep_edf import STAGE_NAMES  # noqa: E402

EVAL_PATH = REPO_ROOT / "results" / "sleep_edf_secondary_holdout_evaluation.json"
OUT_PATH = REPO_ROOT / "results" / "sleep_edf_secondary_n3_diagnostic.json"

N3_INDEX = STAGE_NAMES.index("N3")
N2_INDEX = STAGE_NAMES.index("N2")
SEEDS = (42, 43, 44, 45, 46)


def precision_recall(cm: np.ndarray, class_idx: int) -> tuple[float, float]:
    tp = cm[class_idx, class_idx]
    fp = cm[:, class_idx].sum() - tp
    fn = cm[class_idx, :].sum() - tp
    precision = tp / (tp + fp) if (tp + fp) > 0 else None
    recall = tp / (tp + fn) if (tp + fn) > 0 else None
    return precision, recall


def main() -> None:
    data = json.loads(EVAL_PATH.read_text())

    cm_a_sum = np.zeros((5, 5), dtype=np.int64)
    cm_b_sum = np.zeros((5, 5), dtype=np.int64)
    per_seed_n3 = {}

    for seed in SEEDS:
        cm_a = np.array(data["per_seed"][f"seed{seed}"]["A"]["confusion_matrix"], dtype=np.int64)
        cm_b = np.array(data["per_seed"][f"seed{seed}"]["B"]["confusion_matrix"], dtype=np.int64)
        cm_a_sum += cm_a
        cm_b_sum += cm_b

        prec_a, rec_a = precision_recall(cm_a, N3_INDEX)
        prec_b, rec_b = precision_recall(cm_b, N3_INDEX)
        per_seed_n3[f"seed{seed}"] = {
            "A_N3_precision": prec_a, "A_N3_recall": rec_a,
            "B_N3_precision": prec_b, "B_N3_recall": rec_b,
            "N2_to_N3_false_positives_A": int(cm_a[N2_INDEX, N3_INDEX]),
            "N2_to_N3_false_positives_B": int(cm_b[N2_INDEX, N3_INDEX]),
        }

    prec_a_pooled, rec_a_pooled = precision_recall(cm_a_sum, N3_INDEX)
    prec_b_pooled, rec_b_pooled = precision_recall(cm_b_sum, N3_INDEX)
    n2_to_n3_fp_a_pooled = int(cm_a_sum[N2_INDEX, N3_INDEX])
    n2_to_n3_fp_b_pooled = int(cm_b_sum[N2_INDEX, N3_INDEX])
    n2_to_n3_fp_delta_pooled = n2_to_n3_fp_b_pooled - n2_to_n3_fp_a_pooled

    # Which off-diagonal source contributes most to B's larger N3 false-positive
    # count, pooled across seeds (row = true label, col = predicted = N3).
    fp_by_true_class_a = cm_a_sum[:, N3_INDEX].copy()
    fp_by_true_class_b = cm_b_sum[:, N3_INDEX].copy()
    fp_by_true_class_a[N3_INDEX] = 0  # zero out the true-positive diagonal cell
    fp_by_true_class_b[N3_INDEX] = 0
    fp_delta_by_true_class = (fp_by_true_class_b - fp_by_true_class_a).tolist()
    dominant_fp_source_idx = int(np.argmax(fp_delta_by_true_class))

    out = {
        "source_artifact": "results/sleep_edf_secondary_holdout_evaluation.json",
        "method": "Pooled the 5 per-seed confusion matrices (sklearn convention: rows=true, cols=predicted) for A and B, computed N3 precision/recall from the pooled matrix. No retraining, no new predictions - purely a recomputation from already-stored confusion matrices.",
        "n3_precision_recall_pooled_across_5_seeds": {
            "A_N3_precision": prec_a_pooled, "A_N3_recall": rec_a_pooled,
            "B_N3_precision": prec_b_pooled, "B_N3_recall": rec_b_pooled,
            "precision_change_B_minus_A": prec_b_pooled - prec_a_pooled,
            "recall_change_B_minus_A": rec_b_pooled - rec_a_pooled,
        },
        "n2_to_n3_false_positives_pooled_across_5_seeds": {
            "A": n2_to_n3_fp_a_pooled, "B": n2_to_n3_fp_b_pooled, "delta_B_minus_A": n2_to_n3_fp_delta_pooled,
        },
        "false_positive_source_breakdown_pooled": {
            "description": "For predicted=N3, count of epochs whose TRUE label was something else, by true class, pooled across seeds and summed cohort.",
            "true_class_names": list(STAGE_NAMES),
            "count_A": fp_by_true_class_a.tolist(),
            "count_B": fp_by_true_class_b.tolist(),
            "delta_B_minus_A": fp_delta_by_true_class,
            "dominant_new_false_positive_source": STAGE_NAMES[dominant_fp_source_idx],
        },
        "per_seed": per_seed_n3,
        "canonical_day9_reported_observation": {
            "n3_recall_approx": "0.853 -> 0.884",
            "n3_precision_approx": "0.499 -> 0.430",
            "n2_to_n3_false_positives_approx_delta": "+605",
        },
        "verified_against_canonical": {
            "recall_direction_matches": bool(rec_b_pooled > rec_a_pooled),
            "precision_direction_matches": bool(prec_b_pooled < prec_a_pooled),
            "n2_to_n3_fp_increase_matches_sign": bool(n2_to_n3_fp_delta_pooled > 0),
        },
        "interpretation": (
            "The secondary-cohort N3 regression is primarily precision-driven: aligned EOG "
            "increases N3 recall but also increases N2->N3 false positives. This is a "
            "descriptive statement about confusion-matrix structure, not a physiological "
            "claim - the data do not establish why the model confuses more N2 epochs for N3 "
            "under the aligned-EOG configuration."
        ),
    }

    OUT_PATH.write_text(json.dumps(out, indent=2))
    print("Wrote", OUT_PATH)
    print(json.dumps(out["n3_precision_recall_pooled_across_5_seeds"], indent=2))
    print(json.dumps(out["n2_to_n3_false_positives_pooled_across_5_seeds"], indent=2))
    print(json.dumps(out["verified_against_canonical"], indent=2))


if __name__ == "__main__":
    main()
