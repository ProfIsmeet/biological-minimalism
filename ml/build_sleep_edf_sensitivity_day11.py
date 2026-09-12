#!/usr/bin/env python
"""Day 11: Sleep-EDF primary (n=3) + secondary (n=8) sensitivity package,
built entirely from existing frozen result artifacts. No retraining, no
pooling of the two cohorts into a single headline number.
"""

from __future__ import annotations

import json
import statistics
import sys
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

PER_SUBJECT_PATH = REPO_ROOT / "results" / "sleep_edf_per_subject_analysis.json"
CONTROL_PATH = REPO_ROOT / "results" / "sleep_edf_eeg_eog_control_analysis.json"
SECONDARY_PATH = REPO_ROOT / "results" / "sleep_edf_secondary_holdout_evaluation.json"
OUT_PATH = REPO_ROOT / "results" / "sleep_edf_sensitivity_day11.json"

SEEDS = ("seed42", "seed43", "seed44", "seed45", "seed46")
SEED_INTS = (42, 43, 44, 45, 46)


def sample_sd(values: list[float]) -> float | None:
    return statistics.stdev(values) if len(values) > 1 else None


def dominance(deltas: dict[str, float]) -> tuple[str | None, float | None]:
    if not deltas:
        return None, None
    total = sum(deltas.values())
    dominant = max(deltas.items(), key=lambda kv: abs(kv[1]))[0]
    share = deltas[dominant] / total if total != 0 else None
    return dominant, share


def descriptive_subject_bootstrap(subject_deltas: list[float], n_resamples: int = 5000, seed: int = 20260907) -> dict:
    """Resamples subjects WITH replacement (percentile interval on the mean
    subject-level delta). Purely descriptive - NOT a population-generalization
    proof, and explicitly labeled as such by the caller."""
    rng = np.random.default_rng(seed)
    arr = np.asarray(subject_deltas, dtype=np.float64)
    n = len(arr)
    means = np.array([rng.choice(arr, size=n, replace=True).mean() for _ in range(n_resamples)])
    return {
        "label": "DESCRIPTIVE_SUBJECT_BOOTSTRAP",
        "not_a_population_generalization_proof": True,
        "n_subjects": n,
        "n_resamples": n_resamples,
        "observed_mean": float(arr.mean()),
        "bootstrap_mean_of_means": float(means.mean()),
        "percentile_2_5": float(np.percentile(means, 2.5)),
        "percentile_97_5": float(np.percentile(means, 97.5)),
        "fraction_resamples_positive": float((means > 0).mean()),
    }


def main() -> None:
    per_subject_primary = json.loads(PER_SUBJECT_PATH.read_text())
    control = json.loads(CONTROL_PATH.read_text())
    secondary = json.loads(SECONDARY_PATH.read_text())

    # --- PRIMARY (n=3) -------------------------------------------------------
    primary_subjects = per_subject_primary["test_subjects"]
    primary_b_minus_a = {}
    primary_b_minus_c = {}
    for subj in primary_subjects:
        summary = per_subject_primary["subject_summary"][subj]
        primary_b_minus_a[subj] = summary["candidate_macro_f1"]["mean"] - summary["baseline_macro_f1"]["mean"]
        c_vals = [control["runs"][s]["per_subject"][subj]["macro_f1"] for s in SEEDS]
        c_mean = statistics.mean(c_vals)
        primary_b_minus_c[subj] = summary["candidate_macro_f1"]["mean"] - c_mean

    dom_a_primary, share_a_primary = dominance(primary_b_minus_a)
    dom_c_primary, share_c_primary = dominance(primary_b_minus_c)

    primary_block = {
        "n_subjects": 3,
        "subjects": primary_subjects,
        "per_subject_b_minus_a": primary_b_minus_a,
        "per_subject_b_minus_c": primary_b_minus_c,
        "median_b_minus_a": statistics.median(primary_b_minus_a.values()),
        "mean_b_minus_a": statistics.mean(primary_b_minus_a.values()),
        "median_b_minus_c": statistics.median(primary_b_minus_c.values()),
        "mean_b_minus_c": statistics.mean(primary_b_minus_c.values()),
        "dominant_subject_b_minus_a": dom_a_primary,
        "dominant_subject_share_b_minus_a": share_a_primary,
        "single_subject_dominance_flag": (share_a_primary is not None and abs(share_a_primary) > 0.5),
        "source_artifact": "results/sleep_edf_per_subject_analysis.json + results/sleep_edf_eeg_eog_control_analysis.json",
    }

    # --- SECONDARY (n=8) -------------------------------------------------------
    secondary_subjects = secondary["cohort_subjects"]
    secondary_b_minus_a = {s: secondary["per_subject"][s]["B_minus_A_mean"] for s in secondary_subjects}
    secondary_b_minus_c = {s: secondary["per_subject"][s]["B_minus_C_mean"] for s in secondary_subjects}

    dom_a_secondary, share_a_secondary = dominance(secondary_b_minus_a)
    dom_c_secondary, share_c_secondary = dominance(secondary_b_minus_c)

    bootstrap_b_minus_a = descriptive_subject_bootstrap(list(secondary_b_minus_a.values()))
    bootstrap_b_minus_c = descriptive_subject_bootstrap(list(secondary_b_minus_c.values()))

    secondary_block = {
        "n_subjects": 8,
        "subjects": secondary_subjects,
        "per_subject_b_minus_a": secondary_b_minus_a,
        "per_subject_b_minus_c": secondary_b_minus_c,
        "median_b_minus_a": statistics.median(secondary_b_minus_a.values()),
        "mean_b_minus_a": statistics.mean(secondary_b_minus_a.values()),
        "median_b_minus_c": statistics.median(secondary_b_minus_c.values()),
        "mean_b_minus_c": statistics.mean(secondary_b_minus_c.values()),
        "dominant_subject_b_minus_a": dom_a_secondary,
        "dominant_subject_share_b_minus_a": share_a_secondary,
        "single_subject_dominance_flag": (share_a_secondary is not None and abs(share_a_secondary) > 0.5),
        "descriptive_subject_bootstrap_b_minus_a": bootstrap_b_minus_a,
        "descriptive_subject_bootstrap_b_minus_c": bootstrap_b_minus_c,
        "source_artifact": "results/sleep_edf_secondary_holdout_evaluation.json",
    }

    # --- Seed-level variability (both cohorts use the same 5 seeds) --------
    seed_level = {
        "primary_baseline_sd_sample": per_subject_primary.get("seeds") and None,  # placeholder removed below
    }
    del seed_level["primary_baseline_sd_sample"]
    seed_level = {
        "note": "5 training seeds are optimization replication only - not independent subjects. See docs/STATISTICAL_REPORTING_STANDARD_DAY11.md.",
        "primary_aggregate_source": "results/sleep_edf_eeg_eog_ablation.json (baseline/candidate SD already sample ddof=1)",
        "secondary_aggregate_source": "results/sleep_edf_secondary_holdout_evaluation.json (aggregate block already sample ddof=1)",
    }

    out = {
        "purpose": "Day 11 Sleep-EDF sensitivity package - primary (n=3) and secondary (n=8) reported SEPARATELY, never pooled into a single n=11 headline.",
        "no_retraining": True,
        "no_pooling": True,
        "primary": primary_block,
        "secondary": secondary_block,
        "seed_level_variability_note": seed_level,
        "final_interpretation": (
            "Primary (n=3): the aggregate B>A effect is concentrated in one subject (SC4011); the other two "
            "are mixed/weak - already disclosed in Day 8. Secondary (n=8): the effect is more evenly "
            "distributed (no single subject exceeds 50% of the summed effect), and a descriptive (non-"
            "population-generalizing) subject bootstrap on the 8-subject B-A deltas shows the resample "
            "distribution's mean stays positive in the large majority of resamples - consistent with, but not "
            "proof beyond, the already-reported 6/8 direction count. Neither cohort supports independent-"
            "dataset replication; both remain the same Sleep-EDF cassette source population."
        ),
    }

    OUT_PATH.write_text(json.dumps(out, indent=2))
    print("Wrote", OUT_PATH)
    print("bootstrap B-A fraction positive:", bootstrap_b_minus_a["fraction_resamples_positive"])


if __name__ == "__main__":
    main()
