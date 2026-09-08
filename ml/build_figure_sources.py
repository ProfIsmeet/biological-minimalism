#!/usr/bin/env python
"""Day 12: figure-source data package. Not final graphic design - just the
values/labels/provenance/claim-boundary data a designer or Furkan needs to
render honest figures. Built programmatically from frozen artifacts."""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

OUT_DIR = REPO_ROOT / "results" / "figure_sources"
OUT_DIR.mkdir(exist_ok=True)


def load(name: str) -> dict:
    return json.loads((REPO_ROOT / "results" / name).read_text())


def write(name: str, data: dict) -> None:
    path = OUT_DIR / f"{name}.json"
    path.write_text(json.dumps(data, indent=2))
    print("Wrote", path)


def main() -> None:
    cap = load("ppg_dalia_capacity_control.json")
    multi = load("ppg_dalia_imu_multiseed_replication.json")
    ppg_sens = load("ppg_dalia_sensitivity_day11.json")
    ptt_sens = load("ptt_sensitivity_day11.json")
    sleep_primary = load("sleep_edf_eeg_eog_ablation.json")
    sleep_control = load("sleep_edf_eeg_eog_control_analysis.json")
    sleep_secondary = load("sleep_edf_secondary_holdout_evaluation.json")
    sleep_sens = load("sleep_edf_sensitivity_day11.json")
    n3_diag = load("sleep_n3_extended_diagnostic_day11.json")
    robustness_repro = load("day10_ppg_dalia_fault_robustness_reproduction.json")
    interaction = load("sleep_edf_interaction_resp_day10.json")
    interaction_sens = load("sleep_interaction_sensitivity_day11.json")

    seeds = ("seed42", "seed43", "seed44", "seed45", "seed46")

    # --- Figure A: PPG capacity control (A, A_cap, B, C) ----------------------
    write("figure_A_ppg_capacity_control", {
        "title": "PPG-DaLiA: capacity-controlled IMU marginal value",
        "metric": "MAE (bpm), lower is better",
        "sample_unit": "training seed (n=5); each point is one independently-initialized model on the SAME held-out subjects",
        "series": {
            "A_cap (capacity-matched PPG-only)": cap["aggregate"]["model_a_cap"]["per_seed"],
            "A_original_uncontrolled (recomputed)": cap["aggregate"]["model_a_original_recomputed_from_multiseed"]["per_seed"],
            "B (PPG+IMU)": cap["aggregate"]["model_b_original_recomputed_from_multiseed"]["per_seed"],
            "C (PPG+shuffled IMU)": {s: multi["runs"]["c"][s]["overall"]["mae"] for s in seeds},
        },
        "uncertainty_meaning": "error bars = sample SD (ddof=1) across the 5 seeds, NOT a population confidence interval",
        "claim_boundary": "A_cap vs B is the capacity-fair comparison; do not visually emphasize the original uncontrolled A vs B gap as the headline.",
        "provenance": ["results/ppg_dalia_capacity_control.json", "results/ppg_dalia_imu_multiseed_replication.json"],
    })

    # --- Figure B: PPG subject/activity heterogeneity -------------------------
    write("figure_B_ppg_subject_activity_heterogeneity", {
        "title": "PPG-DaLiA: per-subject and per-activity A_cap->B delta",
        "metric": "delta MAE (bpm), positive = candidate (B) better",
        "sample_unit": "held-out subject (n=3) / activity (n=9, from the original A-vs-B multiseed breakdown)",
        "per_subject_delta": {s: v["delta_a_cap_minus_b_mean"] for s, v in ppg_sens["subject_level"]["per_subject"].items()},
        "per_activity_delta": {a: v["mean_delta_a_minus_b"] for a, v in ppg_sens["activity_level"]["per_activity_a_to_b"].items()},
        "uncertainty_meaning": "no error bars at n=3 subjects - show individual subject points, not a bar+CI",
        "claim_boundary": "n=3 subjects only for the capacity-matched comparison; activity breakdown is from the original (non-capacity-matched) A-vs-B comparison, must be labeled as such if shown alongside Figure A.",
        "provenance": ["results/ppg_dalia_sensitivity_day11.json"],
    })

    # --- Figure C: PTT subject heterogeneity ----------------------------------
    write("figure_C_ptt_subject_heterogeneity", {
        "title": "PTT: per-subject B-A delta and s2 sensitivity",
        "metric": "delta MAE (bpm), positive = candidate (B, two-site) worse",
        "sample_unit": "held-out subject (n=4)",
        "per_subject_delta": ptt_sens["subject_level"]["per_subject_delta_b_minus_a"],
        "leave_one_subject_out": ptt_sens["leave_one_subject_out"],
        "s2_with_without": ptt_sens["s2_dependence"],
        "uncertainty_meaning": "NO defensible population CI at n=4 - show all 4 subject points individually, never a mean+CI bar",
        "claim_boundary": "Must visually disclose that excluding s2 flips the aggregate sign - do not show only the with-s2 aggregate.",
        "provenance": ["results/ptt_sensitivity_day11.json"],
    })

    # --- Figure D: Sleep primary A/B/C ------------------------------------------
    write("figure_D_sleep_primary_abc", {
        "title": "Sleep-EDF primary: A/B/C macro-F1",
        "metric": "macro-F1, higher is better",
        "sample_unit": "training seed (n=5), held-out test subjects n=3",
        "series": {
            "A (EEG only)": sleep_primary["runs"]["baseline_eeg_only"],
            "B (EEG+aligned EOG)": sleep_primary["runs"]["candidate_eeg_plus_eog"],
            "C (EEG+shuffled EOG)": {s: {"macro_f1": sleep_control["runs"][s]["macro_f1"]} for s in seeds},
        },
        "series_note": "Extract macro_f1 field per seed from each series entry.",
        "uncertainty_meaning": "error bars = sample SD (ddof=1) across seeds",
        "claim_boundary": "n=3 test subjects; primary effect is concentrated in SC4011 - a subject-level panel (Figure F) must accompany this to avoid implying uniformity.",
        "provenance": ["results/sleep_edf_eeg_eog_ablation.json", "results/sleep_edf_eeg_eog_control_analysis.json"],
    })

    # --- Figure E: Sleep secondary A/B/C -----------------------------------------
    write("figure_E_sleep_secondary_abc", {
        "title": "Sleep-EDF prospective secondary holdout: A/B/C macro-F1",
        "metric": "macro-F1, higher is better",
        "sample_unit": "training seed (n=5, existing frozen checkpoints, no retraining), held-out subjects n=8",
        "series": {
            "A": sleep_secondary["aggregate"]["model_a_macro_f1"],
            "B": sleep_secondary["aggregate"]["model_b_macro_f1"],
            "C": sleep_secondary["aggregate"]["model_c_macro_f1"],
        },
        "uncertainty_meaning": "error bars = sample SD (ddof=1) across seeds",
        "claim_boundary": "Must be plotted SEPARATELY from Figure D (primary) - never merged into one n=11 bar/panel. Same dataset/protocol as primary, not an independent replication.",
        "provenance": ["results/sleep_edf_secondary_holdout_evaluation.json"],
    })

    # --- Figure F: Sleep subject-level B-A (primary + secondary) ----------------
    write("figure_F_sleep_subject_level_b_minus_a", {
        "title": "Sleep-EDF: per-subject B-A delta, primary vs. secondary",
        "metric": "delta macro-F1, positive = aligned EOG (B) better",
        "sample_unit": "held-out subject: primary n=3, secondary n=8 (shown as two distinct groups, never merged)",
        "primary_per_subject": sleep_sens["primary"]["per_subject_b_minus_a"],
        "secondary_per_subject": sleep_sens["secondary"]["per_subject_b_minus_a"],
        "uncertainty_meaning": "no error bars - individual subject points; secondary group MAY additionally show the DESCRIPTIVE_SUBJECT_BOOTSTRAP percentile band from results/sleep_edf_sensitivity_day11.json, explicitly labeled as descriptive, not inferential",
        "claim_boundary": "Two visually distinct groups (primary/secondary) on one axis is acceptable; a single pooled distribution is NOT.",
        "provenance": ["results/sleep_edf_sensitivity_day11.json"],
    })

    # --- Figure G: Sleep class-level B-A -----------------------------------------
    write("figure_G_sleep_class_level_b_minus_a", {
        "title": "Sleep-EDF: per-class F1 delta (B-A), primary and secondary, plus N3 diagnostic",
        "metric": "delta per-class F1",
        "sample_unit": "class (Wake/N1/N2/N3/REM) - NOT independent statistical replicates, different base-rate sub-tasks",
        "primary_class_deltas": {
            stage: sleep_primary["runs"]["candidate_eeg_plus_eog"]["seed42"]["per_class_f1"].get(stage) for stage in ("Wake", "N1", "N2", "N3", "REM")
        },
        "secondary_class_deltas": sleep_secondary["class_level_aggregate"],
        "n3_false_positive_breakdown": n3_diag["pooled_false_positive_source_breakdown"],
        "uncertainty_meaning": "descriptive per-class deltas only; no significance testing across classes (multiple-comparison caution, see STATISTICAL_REPORTING_STANDARD_DAY11.md)",
        "claim_boundary": "N3 regresses in the secondary cohort (disclose this, do not omit); REM shows the largest gain in both cohorts.",
        "provenance": ["results/sleep_edf_secondary_holdout_evaluation.json", "results/sleep_n3_extended_diagnostic_day11.json"],
    })

    # --- Figure H: Robustness ------------------------------------------------------
    write("figure_H_robustness", {
        "title": "PPG-DaLiA robustness: per-condition MAE degradation (S14 only)",
        "metric": "MAE (bpm) / prediction availability, per fault condition",
        "sample_unit": "perturbation condition (n=114), single subject S14 - NOT independent subjects",
        "clean_baseline": robustness_repro["clean_baseline"],
        "n_conditions": len(robustness_repro["conditions"]),
        "condition_summary_fields": ["fault_type", "severity", "mae_bpm_valid_only", "prediction_availability_rate"],
        "full_condition_data_source": "results/day10_ppg_dalia_fault_robustness_reproduction.json (conditions array)",
        "uncertainty_meaning": "stochastic conditions have 5 seeds - show seed spread where present; deterministic conditions have none",
        "claim_boundary": "Single-subject (S14) scope must be visible on the figure itself, not only in a caption.",
        "provenance": ["results/day10_ppg_dalia_fault_robustness_reproduction.json"],
    })

    # --- Figure I: EOG x Resp interaction ---------------------------------------
    write("figure_I_interaction", {
        "title": "Sleep-EDF: EOG x Resp interaction term",
        "metric": "interaction = Benefit(AB) - Benefit(A) - Benefit(B), macro-F1 units",
        "sample_unit": "training seed (n=5), held-out subjects n=3 (same primary split)",
        "interaction_per_seed": interaction["aggregate"]["interaction_term"]["per_seed"],
        "subject_level_interaction": interaction_sens["subject_level_interaction"]["per_subject_mean"],
        "class_level_interaction": interaction_sens["class_level_interaction"],
        "uncertainty_meaning": "error bars = sample SD across 5 seeds; SD (0.043) is ~14x the mean (0.003) - this must be visually obvious (e.g. an error bar crossing zero by a wide margin), not hidden by a misleadingly-scaled axis",
        "claim_boundary": "Must not be captioned as 'no interaction' or 'synergy found' - the honest caption is 'approximately additive or unresolved at this sample size'.",
        "provenance": ["results/sleep_edf_interaction_resp_day10.json", "results/sleep_interaction_sensitivity_day11.json"],
    })

    print("\nAll figure sources written to", OUT_DIR)


if __name__ == "__main__":
    main()
