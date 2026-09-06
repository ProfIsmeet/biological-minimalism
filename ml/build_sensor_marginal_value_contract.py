#!/usr/bin/env python
"""Builds results/sensor_marginal_value_contract.json - the canonical,
machine-readable scientific marginal-value contract for Biological
Minimalism's sensor-selection framework (Day 5).

This script performs NO training and does not alter any frozen source
result artifact. It only reads already-frozen results and computes
derived comparison metrics (absolute benefit, relative improvement,
consistency counts) directly from them, deterministically.

See docs/SENSOR_MARGINAL_VALUE_METHODOLOGY.md for the full methodology
this contract implements.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

PPG_DALIA_SOURCE = REPO_ROOT / "results" / "ppg_dalia_imu_ablation.json"
PPG_DALIA_MULTISEED_SOURCE = REPO_ROOT / "results" / "ppg_dalia_imu_multiseed_replication.json"
PPG_DALIA_CAPACITY_CONTROL_SOURCE = REPO_ROOT / "results" / "ppg_dalia_capacity_control.json"
PTT_SOURCE = REPO_ROOT / "results" / "ptt_ppg_site_ablation.json"
PTT_SENSITIVITY_SOURCE = REPO_ROOT / "results" / "ptt_sensitivity_analysis.json"
SLEEP_EDF_SOURCE = REPO_ROOT / "results" / "sleep_edf_eeg_eog_ablation.json"
FAULT_ROBUSTNESS_SOURCE = REPO_ROOT / "results" / "ppg_dalia_fault_robustness.json"
OUT_PATH = REPO_ROOT / "results" / "sensor_marginal_value_contract.json"

METHODOLOGY_VERSION = "1.2.0"


def evidence_strength_from_seed_consistency(n_favor: int, n_seeds: int) -> tuple[str, str]:
    """Frozen evidence-strength upgrade rule (Day 6): derived ONLY from the
    actual seed-direction count, never assumed. Returns (evidence_strength,
    rationale). Categories stay within the fixed vocabulary defined in
    docs/SENSOR_MARGINAL_VALUE_METHODOLOGY.md SS8 - no new category is
    invented here."""

    if n_seeds < 3:
        return "insufficient", f"Only {n_seeds} training seed(s) available - too few for a replication claim."
    if n_favor >= n_seeds - 1:  # 5/5 or 4/5 for n_seeds=5
        return (
            "replicated-within-dataset",
            f"{n_favor}/{n_seeds} independent training seeds favor the candidate - a consistent, "
            "replicated-within-dataset direction across independent model initializations.",
        )
    if n_favor >= n_seeds - 2:  # 3/5 for n_seeds=5
        return (
            "mixed",
            f"Only {n_favor}/{n_seeds} training seeds favor the candidate - direction is not "
            "consistently replicated across independent initializations.",
        )
    return (
        "mixed",
        f"{n_favor}/{n_seeds} training seeds favor the candidate - direction is unstable across seeds.",
    )


def absolute_benefit(baseline: float, candidate: float) -> float:
    """baseline - candidate. Positive = candidate improves (lower error)."""
    return baseline - candidate


def relative_improvement(baseline: float, candidate: float) -> float:
    """(baseline - candidate) / baseline. Positive = candidate improves."""
    return (baseline - candidate) / baseline


def build_capacity_confound_status(capacity_control: dict | None) -> dict:
    if capacity_control is None:
        return {
            "status": "UNRESOLVED",
            "note": "Original Model A (8,065 params) vs Model B/C (29,089 params) were not capacity-matched (Finding A3). Not yet addressed - see docs/PPG_DALIA_CAPACITY_CONTROL_PREDECLARATION.md.",
        }

    comparisons = capacity_control["primary_comparisons"]
    return {
        "status": "RESOLVED_WITH_REVISED_CLAIM",
        "source_artifact": "results/ppg_dalia_capacity_control.json",
        "a_cap_parameters": capacity_control["parameter_counts"]["model_a_cap"],
        "b_c_parameters": capacity_control["parameter_counts"]["model_b_and_c_original"],
        "a_cap_residual_vs_b_fraction": capacity_control["parameter_counts"]["a_cap_residual_vs_b_params"] / capacity_control["parameter_counts"]["model_b_and_c_original"],
        "fraction_of_original_gap_explained_by_capacity_alone": comparisons["baseline_A_candidate_Acap"]["mean"] / (comparisons["baseline_A_candidate_Acap"]["mean"] + comparisons["baseline_Acap_candidate_B"]["mean"]),
        "genuine_imu_information_benefit_on_matched_capacity_mae_bpm": comparisons["baseline_Acap_candidate_B"]["mean"],
        "genuine_imu_information_benefit_seed_consistency": f"{comparisons['baseline_Acap_candidate_B']['n_seeds_candidate_better']}/{comparisons['baseline_Acap_candidate_B']['n_seeds_total']}",
        "note": (
            "Model A_cap (capacity-matched PPG-only, 28,865 params) closes most of the "
            "original A->B gap through architecture alone. The remaining, capacity-controlled "
            "IMU-information benefit (A_cap->B) is smaller than originally reported but "
            "remains real and 5/5-seed-consistent. The already-capacity-matched C->B "
            "comparison (shuffled vs. synchronized IMU) is unaffected by this finding."
        ),
    }


def build_ppg_dalia_experiment(ppg: dict, multiseed: dict | None = None, capacity_control: dict | None = None) -> dict:
    a = ppg["overall_metrics"]["model_a_ppg_only"]
    b = ppg["overall_metrics"]["model_b_ppg_plus_imu"]
    c = ppg["overall_metrics"]["model_c_ppg_plus_shuffled_imu"]

    per_subject_a = ppg["per_subject_metrics"]["model_a_ppg_only"]
    per_subject_b = ppg["per_subject_metrics"]["model_b_ppg_plus_imu"]
    subjects = sorted(per_subject_a.keys())
    subject_favors_candidate = [per_subject_b[s]["mae"] < per_subject_a[s]["mae"] for s in subjects]

    per_quartile_a = ppg["motion_quartile_metrics"]["model_a_ppg_only"]
    per_quartile_b = ppg["motion_quartile_metrics"]["model_b_ppg_plus_imu"]
    quartiles = list(per_quartile_a.keys())
    quartile_favors_candidate = [per_quartile_b[q]["mae"] < per_quartile_a[q]["mae"] for q in quartiles]

    per_activity_a = ppg["per_activity_metrics"]["model_a_ppg_only"]
    per_activity_b = ppg["per_activity_metrics"]["model_b_ppg_plus_imu"]
    activities = sorted(per_activity_a.keys())
    activity_favors_candidate = [per_activity_b[act]["mae"] < per_activity_a[act]["mae"] for act in activities]
    activities_worse = [act for act in activities if per_activity_b[act]["mae"] >= per_activity_a[act]["mae"]]

    if multiseed is not None:
        n_seeds_total = multiseed["aggregate"]["total_sync_imu_benefit_mae_A_minus_B"]["n_seeds_total"]
        n_seeds_favor = multiseed["aggregate"]["total_sync_imu_benefit_mae_A_minus_B"]["n_seeds_favor_B"]
        training_seed_replication = f"{n_seeds_favor}/{n_seeds_total} training seeds favor candidate (seeds {multiseed['frozen_protocol']['training_seeds']}, see results/ppg_dalia_imu_multiseed_replication.json)"
        n_training_seeds = n_seeds_total
        evidence_strength, evidence_strength_rationale = evidence_strength_from_seed_consistency(n_seeds_favor, n_seeds_total)
        multiseed_replication_block = {
            "source_artifact": "results/ppg_dalia_imu_multiseed_replication.json",
            "replication_status": multiseed["replication_status"],
            "mean_absolute_benefit_mae_bpm": multiseed["aggregate"]["total_sync_imu_benefit_mae_A_minus_B"]["mean"],
            "sd_absolute_benefit_mae_bpm": multiseed["aggregate"]["total_sync_imu_benefit_mae_A_minus_B"]["sd"],
            "n_seeds_favor_candidate": n_seeds_favor,
            "n_seeds_total": n_seeds_total,
        }
    else:
        training_seed_replication = "1/1 (single seed=42, no multi-seed replication performed for this experiment)"
        n_training_seeds = 1
        evidence_strength = "preliminary"
        evidence_strength_rationale = (
            "Direction is consistent across all held-out subjects and all motion "
            "quartiles, and a negative control was run - methodologically strong "
            "within its scope. Classified 'preliminary' (not 'replicated-within-dataset') "
            "because there is no multi-seed training replication and only one dataset/population."
        )
        multiseed_replication_block = None

    return {
        "experiment_id": "ppg_dalia_imu_hr",
        "target_id": "heart_rate_bpm",
        "dataset_id": "ppg_dalia",
        "population": "15 free-living terrestrial adult subjects (PPG-DaLiA)",
        "baseline_configuration": {
            "candidate_component": None,
            "description": "wrist PPG only",
            "channels": ["PPG (wrist, 1 channel)"],
        },
        "candidate_component_id": "wrist_imu_accelerometer",
        "candidate_configuration": {
            "description": "wrist PPG + synchronized wrist IMU (3-axis accelerometer)",
            "channels": ["PPG (wrist, 1 channel)", "IMU (wrist, 3-axis accelerometer)"],
        },
        "negative_control": {
            "description": "Model C: same architecture as candidate, but each subject's own IMU windows are randomly time-shuffled within-subject (seed 42), breaking true temporal correspondence while preserving per-subject motion statistics.",
            "shuffled_imu_mae": c["mae"],
            "shuffled_imu_rmse": c["rmse"],
        },
        "baseline_metrics": {"mae_bpm": a["mae"], "rmse_bpm": a["rmse"], "n_windows": a["n_windows"]},
        "candidate_metrics": {"mae_bpm": b["mae"], "rmse_bpm": b["rmse"], "n_windows": b["n_windows"]},
        "absolute_benefit": {
            "mae_bpm": absolute_benefit(a["mae"], b["mae"]),
            "rmse_bpm": absolute_benefit(a["rmse"], b["rmse"]),
        },
        "relative_improvement": {
            "mae_fraction": relative_improvement(a["mae"], b["mae"]),
            "rmse_fraction": relative_improvement(a["rmse"], b["rmse"]),
        },
        "synchronization_decomposition": {
            "total_imu_benefit_mae_bpm": absolute_benefit(a["mae"], b["mae"]),
            "context_only_like_benefit_mae_bpm": absolute_benefit(a["mae"], c["mae"]),
            "synchronization_increment_mae_bpm": absolute_benefit(c["mae"], b["mae"]),
            "total_imu_benefit_rmse_bpm": absolute_benefit(a["rmse"], b["rmse"]),
            "context_only_like_benefit_rmse_bpm": absolute_benefit(a["rmse"], c["rmse"]),
            "synchronization_increment_rmse_bpm": absolute_benefit(c["rmse"], b["rmse"]),
            "interpretation_note": (
                "Temporally shuffled same-subject IMU retained some predictive value "
                "(candidate-vs-shuffled and shuffled-vs-baseline are both non-zero), so "
                "the synchronized-IMU benefit is not attributable to synchronization "
                "alone. This decomposition is descriptive, not a proven causal split."
            ),
        },
        "variability": {
            "training_seed_replication": training_seed_replication,
            "subject_direction_consistency": f"{sum(subject_favors_candidate)}/{len(subjects)} held-out subjects favor candidate",
            "motion_quartile_direction_consistency": f"{sum(quartile_favors_candidate)}/{len(quartiles)} motion quartiles favor candidate",
            "activity_direction_consistency": f"{sum(activity_favors_candidate)}/{len(activities)} activities favor candidate",
            "activities_where_candidate_did_not_improve": activities_worse,
            "benefit_monotonic_with_motion": False,
        },
        "evidence_scope": {
            "n_held_out_subjects": len(subjects),
            "n_total_subjects": 15,
            "n_datasets": 1,
            "n_training_seeds": n_training_seeds,
            "independent_ground_truth": "real chest-ECG-derived HR label shipped with PPG-DaLiA (not computed by this project)",
            "negative_control_present": True,
            "subject_disjoint_split": True,
        },
        "multiseed_replication": multiseed_replication_block,
        "capacity_confound_status": build_capacity_confound_status(capacity_control),
        "marginal_status": {
            "overall_direction": "POSITIVE",
            "heterogeneity": {
                "subject_level": "CONSISTENT" if all(subject_favors_candidate) else "MIXED",
                "activity_level": "MOSTLY_CONSISTENT" if 0 < len(activities_worse) < len(activities) else ("CONSISTENT" if not activities_worse else "MIXED"),
            },
            "evidence_strength": evidence_strength,
            "evidence_strength_rationale": evidence_strength_rationale + (
                " IMPORTANT (Day 7 capacity-control revision): a substantial majority "
                "(~68%) of the originally-reported A->B benefit is now attributed to "
                "model capacity/architecture, not IMU sensing information - see "
                "capacity_confound_status below and docs/PPG_DALIA_CAPACITY_CONTROL_RESULTS.md. "
                "The POSITIVE direction survives at reduced magnitude (~0.6bpm, still 5/5 "
                "seed-consistent), not at its originally-reported ~1.9bpm magnitude."
                if capacity_control is not None else ""
            ),
        },
        "limitations": ppg["limitations"],
        "source_artifact": "results/ppg_dalia_imu_ablation.json",
        "source_commit_hash_recorded_in_artifact": ppg.get("commit_hash"),
        "comparable_to_other_experiments": {
            "raw_mae_rmse": False,
            "direction_and_evidence_scope": True,
            "rule": "See methodology doc SS10 - cross-dataset raw-metric comparison is prohibited.",
        },
    }


def build_ptt_experiment(ptt: dict, sensitivity: dict | None = None) -> dict:
    agg = ptt["aggregate"]
    a_mae, b_mae = agg["model_a"]["mean_mae"], agg["model_b"]["mean_mae"]
    a_rmse, b_rmse = agg["model_a"]["mean_rmse"], agg["model_b"]["mean_rmse"]

    seed_deltas = ptt["aggregate"]["paired_delta_mae_b_minus_a"]["per_seed"]
    n_seeds = len(seed_deltas)
    n_seeds_favor_baseline = sum(1 for d in seed_deltas.values() if d > 0)  # positive delta = B worse = baseline favored

    seeds = list(ptt["runs"]["a"].keys())
    subjects = sorted(ptt["runs"]["a"][seeds[0]]["per_subject"].keys())

    def seed_avg_subject_mae(model_key: str, subject: str) -> float:
        vals = [ptt["runs"][model_key][sk]["per_subject"][subject]["mae"] for sk in seeds]
        return sum(vals) / len(vals)

    subject_favors_candidate = {s: seed_avg_subject_mae("b", s) < seed_avg_subject_mae("a", s) for s in subjects}

    activities = sorted(ptt["runs"]["a"][seeds[0]]["per_activity"].keys())

    def seed_avg_activity_mae(model_key: str, activity: str) -> float:
        vals = [ptt["runs"][model_key][sk]["per_activity"][activity]["mae"] for sk in seeds]
        return sum(vals) / len(vals)

    activity_favors_candidate = {act: seed_avg_activity_mae("b", act) < seed_avg_activity_mae("a", act) for act in activities}

    return {
        "experiment_id": "ptt_second_ppg_site_hr",
        "target_id": "heart_rate_bpm",
        "dataset_id": "pulse_transit_time_ppg",
        "population": "22 healthy terrestrial adult subjects, sit/walk/run (PhysioNet Pulse Transit Time PPG Dataset v1.1.0)",
        "baseline_configuration": {
            "candidate_component": None,
            "description": "one physical PPG sensing site (distal phalanx), 3 wavelengths",
            "channels": ptt["config"]["model_a_channels"],
        },
        "candidate_component_id": "second_physical_ppg_site_proximal_phalanx",
        "candidate_configuration": {
            "description": "two physical PPG sensing sites (distal + proximal phalanx), 3 wavelengths each",
            "channels": ptt["config"]["model_b_channels"],
        },
        "negative_control": None,
        "baseline_metrics": {"mae_bpm_mean": a_mae, "mae_bpm_sd": agg["model_a"]["sd_mae"], "rmse_bpm_mean": a_rmse, "rmse_bpm_sd": agg["model_a"]["sd_rmse"]},
        "candidate_metrics": {"mae_bpm_mean": b_mae, "mae_bpm_sd": agg["model_b"]["sd_mae"], "rmse_bpm_mean": b_rmse, "rmse_bpm_sd": agg["model_b"]["sd_rmse"]},
        "absolute_benefit": {
            "mae_bpm": absolute_benefit(a_mae, b_mae),
            "rmse_bpm": absolute_benefit(a_rmse, b_rmse),
        },
        "relative_improvement": {
            "mae_fraction": relative_improvement(a_mae, b_mae),
            "rmse_fraction": relative_improvement(a_rmse, b_rmse),
        },
        "synchronization_decomposition": None,
        "variability": {
            "training_seed_replication": f"{n_seeds}/{n_seeds} seeds trained (seeds {sorted(int(s.replace('seed', '')) for s in seed_deltas)})",
            "seed_direction_consistency": f"{n_seeds_favor_baseline}/{n_seeds} seeds favor baseline (candidate worse in all of these)",
            "subject_direction_consistency": f"{sum(1 for v in subject_favors_candidate.values() if v)}/{len(subjects)} held-out subjects favor candidate",
            "activity_direction_consistency": f"{sum(1 for v in activity_favors_candidate.values() if v)}/{len(activities)} activities favor candidate",
            "per_subject_favors_candidate": subject_favors_candidate,
            "per_activity_favors_candidate": activity_favors_candidate,
            "benefit_monotonic_with_motion": False,
        },
        "evidence_scope": {
            "n_held_out_subjects": len(subjects),
            "n_total_subjects": 22,
            "n_datasets": 1,
            "n_training_seeds": n_seeds,
            "independent_ground_truth": "real ECG R-peak-derived HR (manually-verified .atr annotations)",
            "negative_control_present": False,
            "subject_disjoint_split": True,
        },
        "marginal_status": {
            "overall_direction": "NEGATIVE",
            "heterogeneity": {
                "seed_level": "CONSISTENT (5/5 favor baseline)",
                "subject_level": "MIXED",
                "activity_level": "MIXED",
            },
            "evidence_strength": "replicated-within-dataset",
            "evidence_strength_rationale": (
                "5 independent training seeds all show the candidate configuration "
                "performing worse - a consistent, replicated-within-dataset training-level "
                "signal. However subject-level (2/4) and activity-level (1/3) effects are "
                "heterogeneous, and this is a single dataset/population - the overall "
                "negative direction should not be read as uniform across all subjects/activities."
            ),
        },
        "known_caveats": [
            "Held-out subject s2 has a real HR distribution far outside the training "
            "population's range (verified from raw R-peak data: sit ~121bpm, run ~140bpm "
            "mean, vs. a train-set mean of ~85bpm) - a genuine out-of-distribution subject "
            "that dominates the small (N=4) held-out aggregate for both models. Not excluded "
            "from the frozen result per pre-registered protocol; disclosed here as context, "
            "not as grounds to recompute the headline metric.",
            "Candidate configuration has strictly more input channels (6 vs 3) than baseline "
            "by construction - channel-count and site-value effects are not perfectly separable.",
        ],
        "sensitivity_analysis": (
            {
                "source_artifact": "results/ptt_sensitivity_analysis.json",
                "label": "descriptive sensitivity analysis - s2 NEVER excluded from the frozen primary result",
                "s2_dependence": sensitivity["s2_dependence"],
                "leave_one_subject_out": sensitivity["leave_one_subject_out_descriptive_sensitivity"],
                "revised_claim": sensitivity["revised_claim"],
            }
            if sensitivity is not None
            else {"status": "NOT_YET_COMPUTED"}
        ),
        "source_artifact": "results/ptt_ppg_site_ablation.json",
        "source_reproducibility_artifact": "results/ptt_ppg_site_ablation_reproducibility.json",
        "comparable_to_other_experiments": {
            "raw_mae_rmse": False,
            "direction_and_evidence_scope": True,
            "rule": "See methodology doc SS10 - cross-dataset raw-metric comparison is prohibited.",
        },
    }


def build_sleep_edf_experiment(sleep: dict) -> dict:
    agg = sleep["aggregate"]
    delta = agg["delta_candidate_minus_baseline"]

    return {
        "experiment_id": "sleep_edf_eeg_eog_sleep_stage",
        "target_id": "sleep_stage_5class",
        "dataset_id": "sleep_edf_cassette",
        "population": "18 real subjects, PhysioNet Sleep-EDF (sleep-cassette)",
        "baseline_configuration": {
            "candidate_component": None,
            "description": "single-channel EEG (Fpz-Cz)",
            "channels": sleep["frozen_protocol"]["channels"]["baseline_eeg_only"],
        },
        "candidate_component_id": "eog_horizontal_channel",
        "candidate_configuration": {
            "description": "EEG Fpz-Cz + EOG horizontal",
            "channels": sleep["frozen_protocol"]["channels"]["candidate_eeg_plus_eog"],
        },
        "negative_control": None,
        "primary_metric": "macro_f1",
        "baseline_metrics": {"macro_f1_mean": agg["baseline_macro_f1"]["mean"], "macro_f1_sd_sample_ddof1": agg["baseline_macro_f1"]["sd_sample_ddof1"]},
        "candidate_metrics": {"macro_f1_mean": agg["candidate_macro_f1"]["mean"], "macro_f1_sd_sample_ddof1": agg["candidate_macro_f1"]["sd_sample_ddof1"]},
        "absolute_benefit": {"macro_f1": delta["mean"]},
        "relative_improvement": {"macro_f1_fraction": delta["mean"] / agg["baseline_macro_f1"]["mean"]},
        "variability": {
            "training_seed_replication": f"{delta['n_seeds_total']}/{delta['n_seeds_total']} seeds trained",
            "seed_direction_consistency": f"{delta['n_seeds_candidate_better']}/{delta['n_seeds_total']} seeds favor candidate",
            "candidate_shows_lower_seed_variance": agg["candidate_macro_f1"]["sd_sample_ddof1"] < agg["baseline_macro_f1"]["sd_sample_ddof1"],
        },
        "evidence_scope": {
            "n_held_out_subjects": len(sleep["frozen_protocol"]["subject_split"]["test"]),
            "n_total_subjects": 18,
            "n_datasets": 1,
            "n_training_seeds": delta["n_seeds_total"],
            "independent_ground_truth": "real PSG hypnogram-scored sleep stage annotations (not computed by this project)",
            "negative_control_present": False,
            "subject_disjoint_split": True,
        },
        "capacity_confound_status": {
            "status": "AVOIDED_BY_DESIGN",
            "baseline_parameters": sleep["parameter_counts"]["baseline_eeg_only"],
            "candidate_parameters": sleep["parameter_counts"]["candidate_eeg_plus_eog"],
            "residual_fraction": (sleep["parameter_counts"]["candidate_eeg_plus_eog"] - sleep["parameter_counts"]["baseline_eeg_only"]) / sleep["parameter_counts"]["candidate_eeg_plus_eog"],
            "note": "Designed capacity-fair from the start (shared Conv1DEncoder class, differs only in in_channels), applying the PPG-DaLiA Finding A3 lesson - not a post-hoc repair.",
        },
        "marginal_status": {
            "overall_direction": "POSITIVE",
            "heterogeneity": {
                "seed_level": f"{delta['n_seeds_candidate_better']}/{delta['n_seeds_total']} favor candidate (1 near-tie)",
                "class_level": "every class improves or is flat; largest gains in N1 and REM (physiologically expected classes for EOG); no class regresses",
            },
            "evidence_strength": "preliminary",
            "evidence_strength_rationale": (
                f"Mean effect ({delta['mean']:.4f}) is comparable in magnitude to its own seed-to-seed "
                f"SD ({delta['sd_sample_ddof1']:.4f}), and this is the first experiment for this target/dataset "
                "(1 dataset, no negative control) - classified preliminary despite 4/5 seed consistency and "
                "a physiologically coherent class-level pattern."
            ),
        },
        "limitations": [
            "First and only experiment for this target (sleep stage) - no replication across datasets.",
            "No negative control (e.g. a shuffled-EOG condition) was run for this experiment.",
            "18 subjects total (12/3/3 split) - smaller population than PPG-DaLiA (15) or PTT (22) relative to its 5-class task complexity.",
            "Sleep-EDF cassette recordings include substantial daytime wake time - severe class imbalance was handled via train-only class weighting, disclosed in the predeclaration.",
        ],
        "source_artifact": "results/sleep_edf_eeg_eog_ablation.json",
        "source_reproducibility_artifact": "results/sleep_edf_eeg_eog_ablation_reproducibility.json",
        "predeclaration": "docs/SLEEP_EDF_EEG_EOG_PREDECLARATION_DAY7.md",
        "comparable_to_other_experiments": {
            "raw_mae_rmse": False,
            "raw_macro_f1_vs_other_metrics": False,
            "direction_and_evidence_scope": True,
            "rule": "See methodology doc SS10 - cross-dataset AND cross-metric (MAE vs macro-F1) comparison is prohibited.",
        },
    }


def build_fault_robustness_placeholder() -> dict:
    """The Day 5 master prompt cites results/ppg_dalia_fault_robustness.json
    with specific numbers as 'accepted scientific state', but this file does
    not exist anywhere in this repository (checked: working tree, git log
    --all, every local and remote branch). Per this project's standing rule
    (never fabricate/never transcribe unverified numbers) and the Day 5
    prompt's own SS32/SS36 (stop rather than edit/invent on a frozen-artifact
    mismatch), this record intentionally contains NO copied numbers from the
    prompt - only a flag that the source could not be located."""

    return {
        "experiment_id": "ppg_dalia_fault_robustness",
        "status": "SOURCE_ARTIFACT_NOT_FOUND",
        "expected_source_artifact": "results/ppg_dalia_fault_robustness.json",
        "note": (
            "This experiment was cited in the Day 5 master prompt as an accepted, frozen "
            "result ('Experiment C'), with specific MAE/RMSE/availability figures. That "
            "source file does not exist in this repository - not in the working tree, not "
            "in `git log --all -- results/ppg_dalia_fault_robustness.json`, and not on any "
            "local or remote branch (day2-ml, day3-ml, day5-ml, main, or their origin "
            "counterparts) as of this contract's build time. Per this project's standing "
            "verification rule, the numbers cited in the prompt are NOT reproduced here - "
            "doing so would mean recording unverified figures as if they were sourced from "
            "a real file. This is reported as a discrepancy requiring team review, not "
            "silently resolved. No robustness fields in this contract depend on this record."
        ),
        "action_required": "Locate or re-generate results/ppg_dalia_fault_robustness.json, then re-run ml/build_sensor_marginal_value_contract.py to populate this record from verified source.",
    }


def main() -> None:
    ppg = json.loads(PPG_DALIA_SOURCE.read_text())
    ptt = json.loads(PTT_SOURCE.read_text())
    multiseed = json.loads(PPG_DALIA_MULTISEED_SOURCE.read_text()) if PPG_DALIA_MULTISEED_SOURCE.exists() else None
    capacity_control = json.loads(PPG_DALIA_CAPACITY_CONTROL_SOURCE.read_text()) if PPG_DALIA_CAPACITY_CONTROL_SOURCE.exists() else None
    ptt_sensitivity = json.loads(PTT_SENSITIVITY_SOURCE.read_text()) if PTT_SENSITIVITY_SOURCE.exists() else None
    sleep_edf = json.loads(SLEEP_EDF_SOURCE.read_text()) if SLEEP_EDF_SOURCE.exists() else None

    contract = {
        "methodology_version": METHODOLOGY_VERSION,
        "methodology_doc": "docs/SENSOR_MARGINAL_VALUE_METHODOLOGY.md",
        "generated_by": "ml/build_sensor_marginal_value_contract.py",
        "sign_convention": {
            "absolute_benefit": "baseline_metric - candidate_metric (positive = candidate improves / lower error; negative = candidate worsens)",
            "relative_improvement": "(baseline_metric - candidate_metric) / baseline_metric, as a fraction (positive = candidate improves)",
            "note": "Applied identically to every experiment record in this file - never inverted per-experiment.",
        },
        "metric_policy": {
            "primary_accuracy_metric": "mae",
            "secondary_severity_metric": "rmse",
            "combined_mae_rmse_score": None,
            "combined_score_rationale": "No defensible weighting between MAE and RMSE has been frozen; they are reported separately, never combined into one number.",
        },
        "availability_policy": {
            "definition": "availability = valid_predictions / eligible_windows",
            "folded_into_accuracy_metric": False,
            "unavailable_prediction_treated_as_zero_or_infinite_error": False,
            "note": "Kept as a separate dimension from MAE/RMSE. No availability data is populated in this contract's sensor-value experiment records (Experiments A and B both had full availability); robustness/availability evidence lives in a separate robustness record structure, not the sensor-value records, per the methodology doc's SS13 boundary.",
        },
        "comparability_rules": {
            "cross_dataset_raw_metric_comparison": "PROHIBITED",
            "cross_dataset_relative_improvement_comparison": "DESCRIPTIVE_ONLY_NOT_A_RANKING",
            "allowed_cross_experiment_fields": [
                "marginal_status.overall_direction",
                "evidence_scope.*",
                "variability.*_direction_consistency",
                "marginal_status.evidence_strength",
            ],
            "prohibited_cross_experiment_fields": [
                "baseline_metrics.mae_bpm(_mean)",
                "candidate_metrics.mae_bpm(_mean)",
                "baseline_metrics.rmse_bpm(_mean)",
                "candidate_metrics.rmse_bpm(_mean)",
                "any absolute ranking of one experiment's raw error against another's",
            ],
        },
        "interaction_effects": {
            "additive_assumption_supported": False,
            "note": "Value(component_A + component_B) is not assumed equal to Value(A) + Value(B). No experiment in this project has measured a genuine interaction effect between two candidate components.",
            "interaction_evidence": "unavailable",
            "formal_limitation_doc": "docs/SENSOR_INTERACTION_LIMITATION.md",
            "consequence": "One-at-a-time marginal-value evidence in this contract does NOT establish a globally minimal sensor subset for any target.",
        },
        "robustness_relationship": {
            "sensor_marginal_value_and_robustness_are_separate_axes": True,
            "note": (
                "Sensor marginal-value experiments (this contract) ask whether ADDING a "
                "component improves a target under clean conditions. Robustness experiments "
                "ask what happens when an EXISTING input is degraded or unavailable. These "
                "are related but distinct questions and must not be folded into one scalar. "
                "See docs/SENSOR_MARGINAL_VALUE_METHODOLOGY.md SS13."
            ),
        },
        "experiments": {
            "ppg_dalia_imu_hr": build_ppg_dalia_experiment(ppg, multiseed, capacity_control),
            "ptt_second_ppg_site_hr": build_ptt_experiment(ptt, ptt_sensitivity),
            "ppg_dalia_fault_robustness": build_fault_robustness_placeholder(),
            **({"sleep_edf_eeg_eog_sleep_stage": build_sleep_edf_experiment(sleep_edf)} if sleep_edf is not None else {}),
        },
        "evidence_matrix": {
            "heart_rate_bpm": {
                "wrist_imu_accelerometer": {"status": "POSITIVE_REVISED_SMALLER_EFFECT_POST_CAPACITY_CONTROL" if capacity_control is not None else "POSITIVE", "experiment_id": "ppg_dalia_imu_hr"},
                "second_physical_ppg_site_proximal_phalanx": {"status": "NEGATIVE_AGGREGATE_HETEROGENEOUS_BY_SUBJECT" if ptt_sensitivity is not None else "NEGATIVE", "experiment_id": "ptt_second_ppg_site_hr"},
            },
            **({"sleep_stage_5class": {"eog_horizontal_channel": {"status": "POSITIVE_MODEST", "experiment_id": "sleep_edf_eeg_eog_sleep_stage"}}} if sleep_edf is not None else {}),
            "workload": {"status": "UNVALIDATED"},
            "fatigue": {"status": "UNVALIDATED"},
            "blood_pressure": {"status": "UNVALIDATED"},
            "fluid_shift": {"status": "UNVALIDATED"},
            "circadian_stability": {"status": "UNVALIDATED"},
        },
        "positive_result_interpretation_rule": "positive_for_target != automatic_inclusion_in_final_architecture (see methodology doc SS11)",
        "negative_result_interpretation_rule": "negative_for_target != global_removal_of_component (see methodology doc SS12)",
        "universal_sensor_score": {
            "defined": False,
            "recommendation": "AGAINST",
            "rationale": "A bounded 0-1 (or similar) universal sensor score would require arbitrary cross-target/cross-dataset weighting that no current evidence supports. See methodology doc SS9.",
        },
    }

    OUT_PATH.write_text(json.dumps(contract, indent=2, sort_keys=False, ensure_ascii=False), encoding="utf-8")
    print("Wrote", OUT_PATH)


if __name__ == "__main__":
    main()
