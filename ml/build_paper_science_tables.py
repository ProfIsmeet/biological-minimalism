#!/usr/bin/env python
"""Day 12: paper-ready table source package. Builds CSV+JSON table sources
programmatically from canonical frozen artifacts - no hand-typed duplicate
constants. Every cell traces to a named source artifact via a companion
_provenance.json per table."""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

OUT_DIR = REPO_ROOT / "results" / "paper_tables"
OUT_DIR.mkdir(exist_ok=True)


def load(name: str) -> dict:
    return json.loads((REPO_ROOT / "results" / name).read_text())


def write_table(name: str, header: list[str], rows: list[list], provenance: dict) -> None:
    csv_path = OUT_DIR / f"{name}.csv"
    json_path = OUT_DIR / f"{name}.json"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)
    json_path.write_text(json.dumps({"header": header, "rows": rows, "provenance": provenance}, indent=2))
    print("Wrote", csv_path, "and", json_path)


def main() -> None:
    master = load("scientific_master_table_day11.json")
    sleep_primary_split = json.loads((REPO_ROOT / "ml/experiments/sleep_edf_eeg_eog_ablation/subject_split.json").read_text())
    sleep_secondary = json.loads((REPO_ROOT / "ml/experiments/sleep_edf_secondary_holdout/cohort.json").read_text())
    ppg_source = load("ppg_dalia_imu_ablation.json")
    ptt_source = load("ptt_ppg_site_ablation.json")

    # --- Table 1: Experimental protocols --------------------------------------
    header1 = ["dataset", "target", "baseline", "candidate", "n_train", "n_val", "n_test", "seeds", "metric", "controls"]
    rows1 = [
        ["PPG-DaLiA", "heart_rate_bpm", "PPG-only (A_cap, capacity-matched)", "PPG+IMU (B)",
         len(ppg_source["train_subjects"]), len(ppg_source["validation_subjects"]), len(ppg_source["test_subjects"]),
         "42-46", "MAE (bpm)", "capacity-matched baseline (A_cap) + shuffled-IMU (C)"],
        ["PhysioNet PTT-PPG v1.1.0", "heart_rate_bpm", "One PPG site (A)", "Two PPG sites (B)",
         15, 3, 4, "42-46", "MAE (bpm)", "none"],
        ["PhysioNet Sleep-EDFx cassette (primary)", "sleep_stage_5class", "EEG only (A)", "EEG+EOG (B)",
         len(sleep_primary_split["train"]), len(sleep_primary_split["val"]), len(sleep_primary_split["test"]),
         "42-46", "macro-F1", "shuffled-EOG (C)"],
        ["PhysioNet Sleep-EDFx cassette (secondary holdout)", "sleep_stage_5class", "EEG only (A)", "EEG+EOG (B)",
         0, 0, sleep_secondary["cohort_size"], "42-46 (existing checkpoints, evaluation only)", "macro-F1", "shuffled-EOG (C), same protocol as primary"],
        ["PhysioNet Sleep-EDFx cassette (interaction, same primary split)", "sleep_stage_5class", "EEG (M0)", "EEG+EOG+Resp (M_AB)",
         len(sleep_primary_split["train"]), len(sleep_primary_split["val"]), len(sleep_primary_split["test"]),
         "42-46", "macro-F1", "capacity-fairness safeguard (constant per-channel param cost)"],
    ]
    write_table("table1_experimental_protocols", header1, rows1, {
        "sources": ["results/ppg_dalia_imu_ablation.json", "results/ptt_ppg_site_ablation.json",
                    "ml/experiments/sleep_edf_eeg_eog_ablation/subject_split.json",
                    "ml/experiments/sleep_edf_secondary_holdout/cohort.json"],
    })

    # --- Table 2: Main marginal-value results ---------------------------------
    header2 = ["experiment_id", "metric", "baseline_value", "candidate_value", "effect", "effect_direction", "evidence_strength"]
    rows2 = [[r["experiment_id"], r["primary_metric"], r["baseline_value"], r["candidate_value"], r["effect"], r["effect_direction"], r["evidence_strength"]] for r in master["rows"]]
    write_table("table2_main_marginal_value_results", header2, rows2, {"source": "results/scientific_master_table_day11.json"})

    # --- Table 3: Subject heterogeneity -----------------------------------
    ppg_sens = load("ppg_dalia_sensitivity_day11.json")
    ptt_sens = load("ptt_sensitivity_day11.json")
    sleep_sens = load("sleep_edf_sensitivity_day11.json")

    header3 = ["experiment_id", "n_subjects", "n_favor_candidate", "dominant_subject", "dominant_share", "single_subject_dominance"]
    rows3 = [
        ["ppg_dalia_imu_hr", 3, sum(1 for v in ppg_sens["subject_level"]["per_subject"].values() if v["delta_a_cap_minus_b_mean"] > 0),
         ppg_sens["subject_level"]["dominant_subject"], ppg_sens["subject_level"]["dominant_subject_share_of_summed_effect"],
         ppg_sens["subject_level"]["single_subject_dominance_flag"]],
        ["ptt_second_ppg_site_hr", 4, ptt_sens["subject_level"]["n_subjects_favor_candidate"],
         ptt_sens["subject_level"]["dominant_subject"], ptt_sens["subject_level"]["dominant_subject_share_of_summed_effect"],
         ptt_sens["subject_level"]["single_subject_dominance_flag"]],
        ["sleep_edf_primary", 3, sum(1 for v in sleep_sens["primary"]["per_subject_b_minus_a"].values() if v > 0),
         sleep_sens["primary"]["dominant_subject_b_minus_a"], sleep_sens["primary"]["dominant_subject_share_b_minus_a"],
         sleep_sens["primary"]["single_subject_dominance_flag"]],
        ["sleep_edf_secondary_holdout", 8, sum(1 for v in sleep_sens["secondary"]["per_subject_b_minus_a"].values() if v > 0),
         sleep_sens["secondary"]["dominant_subject_b_minus_a"], sleep_sens["secondary"]["dominant_subject_share_b_minus_a"],
         sleep_sens["secondary"]["single_subject_dominance_flag"]],
    ]
    write_table("table3_subject_heterogeneity", header3, rows3, {
        "sources": ["results/ppg_dalia_sensitivity_day11.json", "results/ptt_sensitivity_day11.json", "results/sleep_edf_sensitivity_day11.json"],
    })

    # --- Table 4: Reproducibility / provenance --------------------------------
    repro = load("day10_scientific_reproduction.json")
    header4 = ["axis", "n_checkpoints_or_conditions", "all_metrics_match", "max_abs_difference", "tolerance"]
    rows4 = [
        ["ppg_dalia", repro["ppg_dalia"]["checkpoints_verified"], repro["ppg_dalia"]["all_metrics_match"], repro["ppg_dalia"]["max_abs_difference"], repro["ppg_dalia"]["tolerance"]],
        ["robustness", repro["robustness"]["n_conditions_reproduced"], repro["robustness"]["all_metrics_match"], repro["robustness"]["max_abs_difference_bpm"], repro["robustness"]["tolerance_bpm"]],
        ["ptt", repro["ptt"]["checkpoints_verified"], repro["ptt"]["all_metrics_match"], repro["ptt"]["max_abs_difference"], repro["ptt"]["tolerance"]],
        ["sleep_primary", repro["sleep_primary"]["checkpoints_verified"], repro["sleep_primary"]["all_metrics_match"], repro["sleep_primary"]["max_abs_difference"], repro["sleep_primary"]["tolerance"]],
        ["sleep_secondary", repro["sleep_secondary"]["checkpoints_verified"], repro["sleep_secondary"]["all_metrics_match"], repro["sleep_secondary"]["max_abs_difference"], repro["sleep_secondary"]["tolerance"]],
    ]
    write_table("table4_reproducibility_provenance", header4, rows4, {"source": "results/day10_scientific_reproduction.json"})

    # --- Table 5: Interaction experiment ---------------------------------------
    interaction = load("sleep_edf_interaction_resp_day10.json")
    params = interaction["parameter_counts"]
    header5 = ["config", "channels", "n_parameters", "macro_f1_mean", "macro_f1_sample_sd"]
    rows5 = [
        ["M0", "EEG", params["M0"], interaction["aggregate"]["m0_macro_f1"]["mean"], interaction["aggregate"]["m0_macro_f1"]["sd_sample_ddof1"]],
        ["M_A", "EEG+EOG", params["M_A"], interaction["aggregate"]["ma_macro_f1"]["mean"], interaction["aggregate"]["ma_macro_f1"]["sd_sample_ddof1"]],
        ["M_B", "EEG+Resp", params["M_B_eeg_plus_resp"], interaction["aggregate"]["mb_macro_f1"]["mean"], interaction["aggregate"]["mb_macro_f1"]["sd_sample_ddof1"]],
        ["M_AB", "EEG+EOG+Resp", params["M_AB_eeg_plus_eog_plus_resp"], interaction["aggregate"]["mab_macro_f1"]["mean"], interaction["aggregate"]["mab_macro_f1"]["sd_sample_ddof1"]],
    ]
    write_table("table5_interaction_experiment", header5, rows5, {"source": "results/sleep_edf_interaction_resp_day10.json"})

    print("\nAll 5 paper tables written to", OUT_DIR)


if __name__ == "__main__":
    main()
