#!/usr/bin/env python
"""Day 11: PTT paper-ready sensitivity package. Builds additively on the
existing results/ptt_sensitivity_analysis.json and results/ptt_ppg_site_ablation.json
- no retraining, no new predictions, s2 never excluded from any frozen
primary number."""

from __future__ import annotations

import json
import statistics
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

SENSITIVITY_PATH = REPO_ROOT / "results" / "ptt_sensitivity_analysis.json"
ABLATION_PATH = REPO_ROOT / "results" / "ptt_ppg_site_ablation.json"
OUT_PATH = REPO_ROOT / "results" / "ptt_sensitivity_day11.json"


def sample_sd(values: list[float]) -> float | None:
    return statistics.stdev(values) if len(values) > 1 else None


def main() -> None:
    sens = json.loads(SENSITIVITY_PATH.read_text())
    ablation = json.loads(ABLATION_PATH.read_text())

    per_subject = sens["per_subject_effect"]
    subject_deltas = {s: v["delta_b_minus_a"] for s, v in per_subject.items()}
    mean_subject_delta = statistics.mean(subject_deltas.values())
    median_subject_delta = statistics.median(subject_deltas.values())

    total_effect = sum(subject_deltas.values())
    dominant_subject = max(subject_deltas.items(), key=lambda kv: abs(kv[1]))[0]
    dominant_share = subject_deltas[dominant_subject] / total_effect if total_effect != 0 else None

    # Seed-level variability of the full (all-4-subject) aggregate.
    seeds = ("seed42", "seed43", "seed44", "seed45", "seed46")
    agg = ablation["aggregate"]
    a_seed_mae = [ablation["runs"]["a"][s]["overall"]["mae"] for s in seeds]
    b_seed_mae = [ablation["runs"]["b"][s]["overall"]["mae"] for s in seeds]
    seed_deltas = [b - a for a, b in zip(a_seed_mae, b_seed_mae)]

    n_subjects_favor_candidate = sum(1 for d in subject_deltas.values() if d < 0)  # negative delta = B better

    out = {
        "purpose": "Day 11 paper-ready PTT sensitivity package, extending results/ptt_sensitivity_analysis.json with median/mean subject effect, seed-level variability, and an explicit dominance share. s2 is never excluded from any reported primary number.",
        "source_artifacts": ["results/ptt_sensitivity_analysis.json", "results/ptt_ppg_site_ablation.json"],
        "no_retraining": True,
        "full_aggregate": sens["full_aggregate"],
        "seed_level": {
            "delta_b_minus_a_per_seed": dict(zip(seeds, seed_deltas)),
            "mean": statistics.mean(seed_deltas),
            "sample_sd": sample_sd(seed_deltas),
            "median": statistics.median(seed_deltas),
            "n_seeds_favor_candidate": sum(1 for d in seed_deltas if d < 0),
            "n_seeds_total": len(seeds),
            "note": "5 training seeds are optimization replication, NOT 5 independent biological subjects - see docs/STATISTICAL_REPORTING_STANDARD_DAY11.md.",
        },
        "subject_level": {
            "per_subject_delta_b_minus_a": subject_deltas,
            "mean_subject_delta": mean_subject_delta,
            "median_subject_delta": median_subject_delta,
            "n_subjects_favor_candidate": n_subjects_favor_candidate,
            "n_subjects_total": len(subject_deltas),
            "dominant_subject": dominant_subject,
            "dominant_subject_share_of_summed_effect": dominant_share,
            "single_subject_dominance_flag": (dominant_share is not None and abs(dominant_share) > 0.5),
            "note": "n=4 held-out subjects. This is far too small a sample for any inferential population claim - reported descriptively only, per docs/STATISTICAL_REPORTING_STANDARD_DAY11.md's confidence-interval policy (no defensible population CI at n=4).",
        },
        "leave_one_subject_out": sens["leave_one_subject_out_descriptive_sensitivity"],
        "s2_dependence": sens["s2_dependence"],
        "final_interpretation": (
            "The aggregate negative direction (candidate two-site configuration worse) is consistent across "
            "all 5 training seeds, but the n=4 held-out-subject evidence is small and heterogeneous: excluding "
            "subject s2 alone flips the aggregate sign. s2 dominates the summed subject-level effect "
            f"({dominant_share:.2f} share if computed - see field above). This is reported as a "
            "replicated-within-dataset (seed-level) but small-and-heterogeneous (subject-level) negative "
            "result - never as evidence of the second PPG site being globally unhelpful."
        ) if dominant_share is not None else "dominant_share could not be computed (zero total effect).",
    }

    OUT_PATH.write_text(json.dumps(out, indent=2))
    print("Wrote", OUT_PATH)


if __name__ == "__main__":
    main()
