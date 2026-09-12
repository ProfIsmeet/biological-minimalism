#!/usr/bin/env python
"""PTT second-PPG-site heterogeneity / sensitivity analysis (master-review
requirement): the aggregate negative result (Model B worse than Model A)
is strongly dependent on held-out subject s2. This script quantifies that
dependence using ONLY the existing frozen results/ptt_ppg_site_ablation.json
- NO retraining, NO new checkpoints, s2 is NEVER removed from the frozen
result itself.

Leave-one-subject-out reconstruction is EXACT (not approximate) for MAE:
pooled MAE over N windows equals the window-count-weighted average of
per-subject MAE, since MAE is linear in per-window absolute error. This
lets us recompute "aggregate excluding subject X" directly from the
already-stored per_subject MAE + n_windows fields, with no need to re-run
inference.

This is explicitly a DESCRIPTIVE SENSITIVITY ANALYSIS, not a new primary
result and not grounds for excluding s2 from the frozen experiment.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

PTT_RESULTS_PATH = REPO_ROOT / "results" / "ptt_ppg_site_ablation.json"
OUT_PATH = REPO_ROOT / "results" / "ptt_sensitivity_analysis.json"


def weighted_mae(per_subject: dict, subjects: list[str]) -> tuple[float, int]:
    """Exact reconstruction of pooled MAE over exactly `subjects` (a subset
    of the real held-out test subjects), from stored per-subject MAE and
    window counts. Returns (mae, n_windows)."""

    total_abs_error = sum(per_subject[s]["mae"] * per_subject[s]["n_windows"] for s in subjects)
    total_windows = sum(per_subject[s]["n_windows"] for s in subjects)
    return total_abs_error / total_windows, total_windows


def main() -> None:
    data = json.loads(PTT_RESULTS_PATH.read_text())
    seeds = list(data["runs"]["a"].keys())
    all_subjects = sorted(data["runs"]["a"][seeds[0]]["per_subject"].keys())

    out: dict = {
        "experiment_id": "ptt_sensitivity_analysis",
        "label": "descriptive sensitivity analysis - NOT a new primary result, NOT grounds for subject exclusion",
        "source_artifact": "results/ptt_ppg_site_ablation.json (unchanged, no retraining)",
        "held_out_subjects": all_subjects,
        "seeds": seeds,
    }

    # --- 7.1 Full held-out aggregate (as originally reported) --------------
    out["full_aggregate"] = {
        "model_a_mean_mae": data["aggregate"]["model_a"]["mean_mae"],
        "model_b_mean_mae": data["aggregate"]["model_b"]["mean_mae"],
        "paired_delta_b_minus_a_mean": data["aggregate"]["paired_delta_mae_b_minus_a"]["mean"],
        "note": "positive delta = B (candidate, two-site) worse than A (baseline, one-site)",
    }

    # --- 7.2 Per-subject effect (seed-averaged) -----------------------------
    per_subject_effect = {}
    for s in all_subjects:
        a_vals = [data["runs"]["a"][sk]["per_subject"][s]["mae"] for sk in seeds]
        b_vals = [data["runs"]["b"][sk]["per_subject"][s]["mae"] for sk in seeds]
        a_mean = sum(a_vals) / len(a_vals)
        b_mean = sum(b_vals) / len(b_vals)
        per_subject_effect[s] = {
            "model_a_mae_seed_mean": a_mean,
            "model_b_mae_seed_mean": b_mean,
            "delta_b_minus_a": b_mean - a_mean,
            "direction": "B_WORSE" if b_mean > a_mean else "B_BETTER",
            "per_seed_a_mae": dict(zip(seeds, a_vals)),
            "per_seed_b_mae": dict(zip(seeds, b_vals)),
        }
    out["per_subject_effect"] = per_subject_effect

    # --- 7.3 Leave-one-subject-out descriptive sensitivity ------------------
    # Uses SEED-AVERAGED per-subject MAE (averaging over the 5 training seeds
    # first, then pooling across the remaining 3 subjects by window count) -
    # consistent with how "aggregate" is understood throughout this project.
    seed_avg_per_subject_a = {s: per_subject_effect[s]["model_a_mae_seed_mean"] for s in all_subjects}
    seed_avg_per_subject_b = {s: per_subject_effect[s]["model_b_mae_seed_mean"] for s in all_subjects}
    n_windows_per_subject = {s: data["runs"]["a"][seeds[0]]["per_subject"][s]["n_windows"] for s in all_subjects}

    def loo_weighted(values: dict[str, float], excluded: str) -> float:
        remaining = [s for s in all_subjects if s != excluded]
        total = sum(values[s] * n_windows_per_subject[s] for s in remaining)
        n = sum(n_windows_per_subject[s] for s in remaining)
        return total / n

    loo_table = {}
    for excluded in all_subjects:
        a_loo = loo_weighted(seed_avg_per_subject_a, excluded)
        b_loo = loo_weighted(seed_avg_per_subject_b, excluded)
        loo_table[f"excluding_{excluded}"] = {
            "model_a_mae": a_loo,
            "model_b_mae": b_loo,
            "delta_b_minus_a": b_loo - a_loo,
            "direction": "B_WORSE" if b_loo > a_loo else "B_BETTER",
        }
    out["leave_one_subject_out_descriptive_sensitivity"] = loo_table

    # --- 7.4 s2 dependence ----------------------------------------------
    all_a = sum(seed_avg_per_subject_a[s] * n_windows_per_subject[s] for s in all_subjects) / sum(n_windows_per_subject.values())
    all_b = sum(seed_avg_per_subject_b[s] * n_windows_per_subject[s] for s in all_subjects) / sum(n_windows_per_subject.values())
    without_s2_subjects = [s for s in all_subjects if s != "s2"]
    a_without_s2 = loo_weighted(seed_avg_per_subject_a, "s2")
    b_without_s2 = loo_weighted(seed_avg_per_subject_b, "s2")

    out["s2_dependence"] = {
        "with_s2": {"model_a_mae": all_a, "model_b_mae": all_b, "delta_b_minus_a": all_b - all_a, "direction": "B_WORSE" if all_b > all_a else "B_BETTER"},
        "without_s2": {"model_a_mae": a_without_s2, "model_b_mae": b_without_s2, "delta_b_minus_a": b_without_s2 - a_without_s2, "direction": "B_WORSE" if b_without_s2 > a_without_s2 else "B_BETTER"},
        "direction_flips_when_s2_excluded": (all_b > all_a) != (b_without_s2 > a_without_s2),
        "magnitude_of_s2_influence_on_delta": (all_b - all_a) - (b_without_s2 - a_without_s2),
        "note": "s2 is RETAINED in the frozen primary result. This is a descriptive sensitivity finding, not a re-run excluding s2.",
    }

    # --- 7.5 Seed vs subject independence -----------------------------------
    out["seed_vs_subject_independence_statement"] = (
        "5/5 training-seed agreement on the aggregate direction (Model B worse) reflects "
        "OPTIMIZATION/TRAINING-SEED replication - the same 4 held-out subjects were evaluated "
        "every time, so this is NOT five independent population replications. Subject-level "
        "evidence comes from only 4 held-out subjects, of which 2 favor the baseline and 2 favor "
        "the candidate (see per_subject_effect above) - a much smaller and more heterogeneous "
        "evidence base than the seed-count alone would suggest. These are two distinct evidence "
        "axes and must not be conflated into a single replication claim."
    )

    # --- 7.6 Revised claim ---------------------------------------------------
    out["revised_claim"] = (
        f"Under the frozen PTT protocol, the single-site baseline has a better aggregate held-out "
        f"HR MAE ({all_a:.3f} bpm) than the two-site candidate ({all_b:.3f} bpm) across all five "
        f"training seeds, but this aggregate direction is strongly heterogeneous across the 4 "
        f"held-out subjects (2 of 4 favor the candidate) and is sensitive to subject s2 specifically "
        f"(excluding s2 changes the aggregate delta by {((all_b - all_a) - (b_without_s2 - a_without_s2)):.3f} bpm"
        f"{', flipping its direction' if out['s2_dependence']['direction_flips_when_s2_excluded'] else ' without flipping its direction'}). "
        "The result does not establish that a second PPG site is globally harmful or unnecessary "
        "for heart-rate estimation - only that, under this specific frozen protocol and this "
        "specific 4-subject held-out set, the aggregate favors the single-site baseline."
    )

    OUT_PATH.write_text(json.dumps(out, indent=2))
    print("Wrote", OUT_PATH)
    print("\nrevised_claim:\n", out["revised_claim"])
    print("\ns2_dependence:", json.dumps(out["s2_dependence"], indent=2))


if __name__ == "__main__":
    main()
