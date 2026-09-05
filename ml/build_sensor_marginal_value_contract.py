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

import hashlib
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

PPG_DALIA_SOURCE = REPO_ROOT / "results" / "ppg_dalia_imu_ablation.json"
PTT_SOURCE = REPO_ROOT / "results" / "ptt_ppg_site_ablation.json"
FAULT_ROBUSTNESS_SOURCE = REPO_ROOT / "results" / "ppg_dalia_fault_robustness.json"
FAULT_ROBUSTNESS_AUDIT = REPO_ROOT / "docs" / "PHASE5_ROBUSTNESS_AUDIT_ADDENDUM.md"
OUT_PATH = REPO_ROOT / "results" / "sensor_marginal_value_contract.json"

FROZEN_FAULT_ROBUSTNESS_SHA256 = "c40397fb0bb43b4f4a778aac4a4e0ba72b7b0387cab1aabec1e0708cc2912dcb"

METHODOLOGY_VERSION = "1.0.1"


def absolute_benefit(baseline: float, candidate: float) -> float:
    """baseline - candidate. Positive = candidate improves (lower error)."""
    return baseline - candidate


def relative_improvement(baseline: float, candidate: float) -> float:
    """(baseline - candidate) / baseline. Positive = candidate improves."""
    return (baseline - candidate) / baseline


def build_ppg_dalia_experiment(ppg: dict) -> dict:
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
            "training_seed_replication": "1/1 (single seed=42, no multi-seed replication performed for this experiment)",
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
            "n_training_seeds": 1,
            "independent_ground_truth": "real chest-ECG-derived HR label shipped with PPG-DaLiA (not computed by this project)",
            "negative_control_present": True,
            "subject_disjoint_split": True,
        },
        "marginal_status": {
            "overall_direction": "POSITIVE",
            "heterogeneity": {
                "subject_level": "CONSISTENT" if all(subject_favors_candidate) else "MIXED",
                "activity_level": "MOSTLY_CONSISTENT" if 0 < len(activities_worse) < len(activities) else ("CONSISTENT" if not activities_worse else "MIXED"),
            },
            "evidence_strength": "preliminary",
            "evidence_strength_rationale": (
                "Direction is consistent across all held-out subjects and all motion "
                "quartiles, and a negative control was run - methodologically strong "
                "within its scope. Classified 'preliminary' (not 'replicated-within-dataset') "
                "because there is no multi-seed training replication and only one dataset/population."
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


def build_ptt_experiment(ptt: dict) -> dict:
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
        "source_artifact": "results/ptt_ppg_site_ablation.json",
        "source_reproducibility_artifact": "results/ptt_ppg_site_ablation_reproducibility.json",
        "comparable_to_other_experiments": {
            "raw_mae_rmse": False,
            "direction_and_evidence_scope": True,
            "rule": "See methodology doc SS10 - cross-dataset raw-metric comparison is prohibited.",
        },
    }


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_fault_robustness_unavailable() -> dict:
    """Represent a current missing dependency without rewriting its history."""
    return {
        "record_id": "ppg_dalia_fault_robustness",
        "evidence_axis": "robustness_and_pipeline_availability",
        "status": "CURRENT_INTEGRATION_SOURCE_UNAVAILABLE",
        "source_artifact": "results/ppg_dalia_fault_robustness.json",
        "note": (
            "The isolated Ismet Day 5 working context could not resolve this source. The "
            "current builder also cannot read it, so no robustness numbers are emitted."
        ),
        "action_required": "Restore the accepted frozen source and rerun this builder.",
    }


def build_fault_robustness_record(robustness: dict, audit_text: str, source_sha256: str) -> dict:
    """Build a separate robustness axis solely from the frozen source and audit."""
    required_audit_statements = (
        "first affected S14 replay batch",
        "fail-closed pipeline availability",
        "must not be described as robustness to universally severe IMU noise",
        "automatic neural-network fault detection",
        "fault tolerance",
    )
    missing = [statement for statement in required_audit_statements if statement not in audit_text]
    if missing:
        raise ValueError(f"Mandatory robustness audit semantics are missing: {missing}")

    execution = robustness["execution"]
    dataset = robustness["dataset"]
    clean = robustness["clean_baseline"]
    boundary = robustness["interpretation_boundary"]
    condition_ids = [condition["condition_id"] for condition in robustness["conditions"]]
    if len(condition_ids) != execution["condition_count"]:
        raise ValueError("Robustness source condition_count does not match the condition records")

    return {
        "record_id": "ppg_dalia_fault_robustness",
        "evidence_axis": "robustness_and_pipeline_availability",
        "status": "RESOLVED_FROM_INTEGRATION_SOURCE",
        "source_artifact": "results/ppg_dalia_fault_robustness.json",
        "source_sha256": source_sha256,
        "source_experiment_id": robustness["experiment_id"],
        "audit_addendum": "docs/PHASE5_ROBUSTNESS_AUDIT_ADDENDUM.md",
        "historical_provenance": {
            "isolated_day5_context": "Source was unavailable in the isolated Ismet Day 5 working context, so that historical branch emitted an unavailable placeholder.",
            "integrated_resolution": "The accepted Phase 5 artifact became resolvable after integration; current values are parsed from that frozen source without rewriting the historical commit.",
        },
        "scope": {
            "characterization": robustness["scope"],
            "dataset": dataset["name"],
            "subject_id": dataset["subject_id"],
            "subject_role": dataset["subject_role"],
            "single_subject": len(dataset["available_verified_subjects_used"]) == 1,
        },
        "execution": {
            "condition_count": execution["condition_count"],
            "eligible_windows_per_condition": execution["eligible_windows_per_condition"],
            "total_condition_windows": execution["total_condition_windows"],
            "no_fallback_prediction": execution["no_fallback_prediction"],
            "condition_ids": condition_ids,
        },
        "metric_semantics": {
            "accuracy_population": "valid_predictions_only",
            "accuracy_fields": ["mae_bpm_valid_only", "rmse_bpm_valid_only"],
            "prediction_availability_field": "prediction_availability_rate",
            "availability_is_separate_from_accuracy": True,
            "zero_survivor_accuracy": None,
        },
        "clean_baseline": {
            "eligible_window_count": clean["eligible_window_count"],
            "valid_prediction_count": clean["valid_prediction_count"],
            "prediction_availability_rate": clean["prediction_availability_rate"],
            "mae_bpm_valid_only": clean["mae_bpm_valid_only"],
            "rmse_bpm_valid_only": clean["rmse_bpm_valid_only"],
        },
        "interpretive_context": {
            "packet_loss": "Independent loss of a required native-rate sample primarily triggered fail-closed input rejection, so packet-loss results characterize prediction availability rather than continuous error degradation.",
            "imu_fault_calibration": "IMU noise and saturation scales came from the first affected S14 batch, whose motion variance was much lower than typical later windows; the tested grid is not proof of robustness to severe corruption.",
            "fault_detection": "Continued or rejected output is not evidence of automatic fault detection or fault tolerance.",
        },
        "claim_boundaries": {
            "supported": boundary["supported"],
            "not_supported": list(dict.fromkeys([
                *boundary["not_supported"],
                "robustness to universally severe IMU corruption",
                "automatic neural-network fault detection",
                "fault tolerance",
            ])),
        },
        "separation_rule": "This record is not marginal sensor value and is never folded into MAE benefit, a robustness-adjusted score, or a sensor ranking.",
    }


def main() -> None:
    ppg = json.loads(PPG_DALIA_SOURCE.read_text())
    ptt = json.loads(PTT_SOURCE.read_text())
    if FAULT_ROBUSTNESS_SOURCE.is_file():
        source_sha256 = _sha256(FAULT_ROBUSTNESS_SOURCE)
        if source_sha256 != FROZEN_FAULT_ROBUSTNESS_SHA256:
            raise ValueError(
                "Frozen robustness source SHA256 changed; investigate instead of regenerating the contract"
            )
        robustness = json.loads(FAULT_ROBUSTNESS_SOURCE.read_text())
        audit_text = FAULT_ROBUSTNESS_AUDIT.read_text()
        robustness_record = build_fault_robustness_record(robustness, audit_text, source_sha256)
    else:
        robustness_record = build_fault_robustness_unavailable()

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
            "ppg_dalia_imu_hr": build_ppg_dalia_experiment(ppg),
            "ptt_second_ppg_site_hr": build_ptt_experiment(ptt),
        },
        "robustness_records": {"ppg_dalia_fault_robustness": robustness_record},
        "evidence_matrix": {
            "heart_rate_bpm": {
                "wrist_imu_accelerometer": {"status": "POSITIVE", "experiment_id": "ppg_dalia_imu_hr"},
                "second_physical_ppg_site_proximal_phalanx": {"status": "NEGATIVE", "experiment_id": "ptt_second_ppg_site_hr"},
            },
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
