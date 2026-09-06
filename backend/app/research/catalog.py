"""Adapt immutable committed result artifacts into the canonical schema."""

from __future__ import annotations

import json
import statistics
from collections.abc import Callable
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from app.schemas.research import (
    MarginalDirection,
    ResearchAvailability,
    ResearchBreakdown,
    ResearchBreakdownEntry,
    ResearchCheckpointIdentity,
    ResearchClaimBoundaries,
    ResearchConfiguration,
    ResearchEnvironmentScope,
    ResearchExperiment,
    ResearchExperimentEnvelope,
    ResearchExperimentSummary,
    ResearchExperimentSummaryEnvelope,
    ResearchMarginalResult,
    ResearchMetricEstimate,
    ResearchProjectSummary,
    ResearchProvenance,
    ResearchResultClass,
    ResearchScope,
    ResearchStatus,
)

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]

PPG_DALIA_ABLATION_ID = "ppg-dalia-imu-ablation"
PPG_DALIA_ROBUSTNESS_ID = "ppg-dalia-s14-fault-robustness"
PTT_SITE_ABLATION_ID = "ptt-ppg-site-ablation"


class ResearchArtifactError(RuntimeError):
    """A committed scientific artifact is absent, malformed, or contradictory."""


def _metric(
    mean: float | int | None,
    unit: str,
    *,
    sd: float | int | None = None,
    n: int | None = None,
) -> ResearchMetricEstimate:
    return ResearchMetricEstimate(
        mean=None if mean is None else float(mean),
        sd=None if sd is None else float(sd),
        n=n,
        unit=unit,
    )


def _require(mapping: dict[str, Any], key: str, context: str) -> Any:
    if key not in mapping:
        raise ResearchArtifactError(f"{context} is missing required field {key!r}.")
    return mapping[key]


def _read_json(repository_root: Path, relative_path: str) -> dict[str, Any]:
    path = repository_root / relative_path
    if not path.is_file():
        raise ResearchArtifactError(f"Research artifact unavailable: {relative_path}")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ResearchArtifactError(f"Research artifact {relative_path} could not be read: {exc}") from exc
    if not isinstance(value, dict):
        raise ResearchArtifactError(f"Research artifact {relative_path} must contain a JSON object.")
    return value


def _summary(experiment: ResearchExperiment) -> ResearchExperimentSummary:
    return ResearchExperimentSummary(
        experiment_id=experiment.experiment_id,
        title=experiment.title,
        research_question=experiment.research_question,
        dataset=experiment.dataset,
        target=experiment.target,
        status=experiment.status,
        result_class=experiment.result_class,
        outcome_summary=experiment.outcome_summary,
        held_out_subject_count=len(experiment.scope.held_out_subjects),
        source_artifact=experiment.provenance.source_artifact,
    )


def _metric_map(raw: dict[str, Any]) -> dict[str, ResearchMetricEstimate]:
    n = int(_require(raw, "n_windows", "metric record"))
    return {
        "mae": _metric(_require(raw, "mae", "metric record"), "bpm", n=n),
        "rmse": _metric(_require(raw, "rmse", "metric record"), "bpm", n=n),
    }


def _ppg_breakdown(
    result: dict[str, Any],
    source_key: str,
    breakdown_id: str,
    title: str,
) -> ResearchBreakdown:
    source = _require(result, source_key, "PPG-DaLiA ablation")
    configuration_ids = (
        "model_a_ppg_only",
        "model_b_ppg_plus_imu",
        "model_c_ppg_plus_shuffled_imu",
    )
    labels = sorted(source[configuration_ids[0]])
    entries: list[ResearchBreakdownEntry] = []
    for label in labels:
        configuration_metrics = {
            configuration_id: _metric_map(source[configuration_id][label])
            for configuration_id in configuration_ids
        }
        baseline = configuration_metrics["model_a_ppg_only"]["mae"].mean
        candidate = configuration_metrics["model_b_ppg_plus_imu"]["mae"].mean
        assert baseline is not None and candidate is not None
        entries.append(
            ResearchBreakdownEntry(
                entry_id=f"{breakdown_id}-{label.lower()}",
                label=label,
                dimensions={"category": label},
                configuration_metrics=configuration_metrics,
                delta=_metric(candidate - baseline, "bpm"),
            )
        )
    return ResearchBreakdown(
        breakdown_id=breakdown_id,
        kind=breakdown_id,
        title=title,
        entries=entries,
    )


def adapt_ppg_dalia_ablation(repository_root: Path) -> ResearchExperiment:
    artifact = "results/ppg_dalia_imu_ablation.json"
    result = _read_json(repository_root, artifact)
    if _require(result, "dataset", artifact) != "PPG-DaLiA":
        raise ResearchArtifactError("PPG-DaLiA ablation dataset identity changed.")
    if _require(result, "target", artifact) != "heart_rate_bpm":
        raise ResearchArtifactError("PPG-DaLiA ablation target identity changed.")
    overall = _require(result, "overall_metrics", artifact)
    model_specs = [
        (
            "model_a_ppg_only",
            "PPG only",
            "Wrist PPG without motion input.",
            ["wrist PPG"],
        ),
        (
            "model_b_ppg_plus_imu",
            "PPG + synchronized IMU",
            "Wrist PPG with its synchronized wrist accelerometer input.",
            ["wrist PPG", "synchronized wrist IMU"],
        ),
        (
            "model_c_ppg_plus_shuffled_imu",
            "PPG + shuffled IMU",
            "Negative control with within-subject IMU windows temporally shuffled.",
            ["wrist PPG", "temporally shuffled wrist IMU"],
        ),
    ]
    configurations = [
        ResearchConfiguration(
            configuration_id=configuration_id,
            label=label,
            description=description,
            sensing=sensing,
            metrics=_metric_map(_require(overall, configuration_id, artifact)),
        )
        for configuration_id, label, description, sensing in model_specs
    ]
    baseline_mae = configurations[0].metrics["mae"].mean
    candidate_mae = configurations[1].metrics["mae"].mean
    assert baseline_mae is not None and candidate_mae is not None
    test_subjects = list(_require(result, "test_subjects", artifact))
    all_subjects = [
        *list(_require(result, "train_subjects", artifact)),
        *list(_require(result, "validation_subjects", artifact)),
        *test_subjects,
    ]
    per_activity = result.get("per_activity_metrics", {})
    activities = sorted(per_activity.get("model_a_ppg_only", {}).keys())
    breakdowns = [
        _ppg_breakdown(result, "per_subject_metrics", "per_subject", "Held-out subjects"),
        _ppg_breakdown(result, "motion_quartile_metrics", "motion_quartile", "Motion quartiles"),
    ]
    if activities:
        breakdowns.append(_ppg_breakdown(result, "per_activity_metrics", "per_activity", "Activities"))

    # Day-6 multi-seed replication is layered on as ADDITIONAL evidence; the
    # single-seed artifact above remains the frozen headline point estimate.
    multiseed_path = repository_root / "results" / "ppg_dalia_imu_multiseed_replication.json"
    marginal_notes = [
        "Improvement was present for all three held-out subjects and all four motion quartiles.",
        "The benefit did not increase monotonically with motion.",
        "The shuffled-IMU negative control also improved over PPG-only.",
    ]
    paired_replicates: int | None = None
    candidate_improved_count: int | None = None
    candidate_worsened_count: int | None = None
    if multiseed_path.is_file():
        multiseed = json.loads(multiseed_path.read_text(encoding="utf-8"))
        agg = multiseed["aggregate"]
        total = agg["total_sync_imu_benefit_mae_A_minus_B"]
        ctx = agg["shuffled_context_like_benefit_mae_A_minus_C"]
        inc = agg["synchronization_increment_mae_C_minus_B"]
        paired_replicates = total["n_seeds_total"]
        candidate_improved_count = total["n_seeds_favor_B"]
        candidate_worsened_count = total["n_seeds_total"] - total["n_seeds_favor_B"]
        never_favor = sorted(
            act for act, rec in multiseed["activity_level_consistency"].items()
            if rec["n_seeds_favor_B"] == 0
        )
        marginal_notes = [
            f"Multi-seed replication ({multiseed['replication_status']}, seeds "
            f"{multiseed['frozen_protocol']['training_seeds']}): B beats A in "
            f"{total['n_seeds_favor_B']}/{total['n_seeds_total']} seeds, C beats A in "
            f"{ctx['n_seeds_favor_C']}/{ctx['n_seeds_total']}, B beats C in "
            f"{inc['n_seeds_favor_B_over_C']}/{inc['n_seeds_total']}.",
            f"Across-seed MAE mean±SD (bpm): A {agg['model_a']['mean_mae']:.3f}±{agg['model_a']['sd_mae']:.3f}, "
            f"B {agg['model_b']['mean_mae']:.3f}±{agg['model_b']['sd_mae']:.3f}, "
            f"C {agg['model_c']['mean_mae']:.3f}±{agg['model_c']['sd_mae']:.3f}.",
            f"Decomposition (descriptive, not a causal split): total IMU benefit A−B "
            f"{total['mean']:.3f}±{total['sd']:.3f}; retained under shuffle A−C "
            f"{ctx['mean']:.3f}±{ctx['sd']:.3f}; additional synchronized increment C−B "
            f"{inc['mean']:.3f}±{inc['sd']:.3f} bpm.",
            "All three held-out subjects and all four motion quartiles favor synchronized IMU in 5/5 seeds; "
            f"activities never favoring the candidate across seeds: {', '.join(never_favor) if never_favor else 'none'}.",
        ]

    return ResearchExperiment(
        experiment_id=PPG_DALIA_ABLATION_ID,
        title="PPG-DaLiA — Marginal value of synchronized IMU",
        research_question=str(_require(result, "research_question", artifact)),
        dataset="PPG-DaLiA",
        target="Heart rate",
        status=ResearchStatus.COMPLETE,
        result_class=ResearchResultClass.POSITIVE_MARGINAL_VALUE,
        outcome_summary=(
            "Synchronized IMU improved held-out PPG-based HR estimation in this frozen experiment; "
            "shuffled IMU also improved over PPG-only, so synchronization explains only part of the gain."
        ),
        scope=ResearchScope(
            subjects=sorted(set(all_subjects)),
            held_out_subjects=test_subjects,
            evaluation_windows=int(configurations[0].metrics["mae"].n or 0),
            activities=activities,
            environment_scope=ResearchEnvironmentScope.TERRESTRIAL_FREE_LIVING,
            cohort_note="Three subject-disjoint held-out PPG-DaLiA participants.",
        ),
        configurations=configurations,
        marginal_result=ResearchMarginalResult(
            baseline_configuration_id="model_a_ppg_only",
            candidate_configuration_id="model_b_ppg_plus_imu",
            added_sensing="synchronized wrist IMU",
            metric="mae",
            delta=_metric(candidate_mae - baseline_mae, "bpm"),
            direction=MarginalDirection.IMPROVED,
            paired_replicates=paired_replicates,
            candidate_improved_count=candidate_improved_count,
            candidate_worsened_count=candidate_worsened_count,
            notes=marginal_notes,
        ),
        breakdowns=breakdowns,
        provenance=ResearchProvenance(
            source_artifact=artifact,
            supporting_artifacts=[
                "ml/experiments/ppg_dalia_imu_ablation/subject_split.json",
                "docs/MODEL_CONTRACT_PPG_DALIA_HR.md",
            ],
            dataset_version=result.get("dataset_version"),
            split_identity="subject-wise train/validation/test split stored in the source result",
            model_identity=[item[0] for item in model_specs],
            experiment_version=result.get("commit_hash"),
        ),
        claim_boundaries=ResearchClaimBoundaries(
            supported=[
                "On the frozen PPG-DaLiA split, synchronized PPG+IMU reduced held-out HR MAE relative to PPG-only.",
                "The result demonstrates positive target- and dataset-specific marginal sensor value.",
            ],
            unsupported=[
                "IMU is universally required for heart-rate estimation or every health target.",
                "The evaluated sensor set is globally optimal.",
                "The result generalizes to astronauts or microgravity.",
            ],
            limitations=[
                "Only three held-out subjects were evaluated.",
                "The data are terrestrial and free-living.",
                "Shuffled IMU also helped, so synchronization explains only part of Model B's gain.",
                "Motion-quartile benefit was not monotonic.",
            ],
        ),
    )


def _fault_metrics(condition: dict[str, Any]) -> dict[str, ResearchMetricEstimate]:
    eligible = int(_require(condition, "eligible_window_count", "fault condition"))
    valid = int(_require(condition, "valid_prediction_count", "fault condition"))
    return {
        "mae": _metric(condition.get("mae_bpm_valid_only"), "bpm", n=valid),
        "rmse": _metric(condition.get("rmse_bpm_valid_only"), "bpm", n=valid),
        "availability": _metric(
            _require(condition, "prediction_availability_rate", "fault condition"),
            "fraction",
            n=eligible,
        ),
        "valid_predictions": _metric(valid, "windows", n=eligible),
    }


def adapt_ppg_dalia_robustness(repository_root: Path) -> ResearchExperiment:
    artifact = "results/ppg_dalia_fault_robustness.json"
    result = _read_json(repository_root, artifact)
    if _require(result, "experiment_id", artifact) != "ppg_dalia_s14_fault_robustness_v1":
        raise ResearchArtifactError("Phase 5 experiment identity changed.")
    dataset = _require(result, "dataset", artifact)
    if _require(dataset, "name", artifact) != "PPG-DaLiA" or dataset.get("subject_id") != "S14":
        raise ResearchArtifactError("Phase 5 dataset/subject identity changed.")
    clean = _require(result, "clean_baseline", artifact)
    if _require(clean, "eligible_window_count", artifact) != 4476:
        raise ResearchArtifactError("Phase 5 clean eligible-window count changed.")
    conditions = list(_require(result, "conditions", artifact))
    if len(conditions) != 114:
        raise ResearchArtifactError(f"Phase 5 expected 114 conditions, found {len(conditions)}.")
    condition_entries = []
    for condition in conditions:
        dimensions: dict[str, str | float | int | bool | None] = {
            "fault_type": condition.get("fault_type"),
            "target": condition.get("target"),
            "severity": condition.get("severity"),
            "seed": condition.get("seed"),
            "stochastic": bool(condition.get("stochastic", False)),
            "input_unavailable": int(condition["failure_counts"]["input_unavailable"]),
            "canonical_invalid_input": int(condition["failure_counts"]["canonical_invalid_input"]),
            "inference_error": int(condition["failure_counts"]["inference_error"]),
        }
        condition_entries.append(
            ResearchBreakdownEntry(
                entry_id=str(_require(condition, "condition_id", "fault condition")),
                label=str(_require(condition, "condition_id", "fault condition")),
                dimensions=dimensions,
                configuration_metrics={"canonical_pipeline": _fault_metrics(condition)},
                delta=(
                    None
                    if condition.get("delta_from_clean", {}).get("mae_bpm") is None
                    else _metric(condition["delta_from_clean"]["mae_bpm"], "bpm")
                ),
            )
        )
    aggregate_entries = []
    for aggregate in _require(result, "stochastic_aggregates", artifact):
        metrics: dict[str, ResearchMetricEstimate] = {}
        for source_key, output_key, unit in (
            ("mae_bpm_valid_only", "mae", "bpm"),
            ("rmse_bpm_valid_only", "rmse", "bpm"),
            ("prediction_availability_rate", "availability", "fraction"),
            ("valid_prediction_count", "valid_predictions", "windows"),
        ):
            source = aggregate[source_key]
            metrics[output_key] = _metric(source.get("mean"), unit, sd=source.get("population_std"))
        aggregate_entries.append(
            ResearchBreakdownEntry(
                entry_id=str(aggregate["group_id"]),
                label=str(aggregate["group_id"]),
                dimensions={
                    "fault_type": aggregate["fault_type"],
                    "target": aggregate["target"],
                    "severity": aggregate["severity"],
                    "replicates": len(aggregate["seeds"]),
                },
                configuration_metrics={"canonical_pipeline": metrics},
                delta=(
                    None
                    if aggregate["delta_from_clean"]["mae_bpm"].get("mean") is None
                    else _metric(
                        aggregate["delta_from_clean"]["mae_bpm"]["mean"],
                        "bpm",
                        sd=aggregate["delta_from_clean"]["mae_bpm"].get("population_std"),
                    )
                ),
            )
        )
    model = _require(result, "model", artifact)
    execution = _require(result, "execution", artifact)
    return ResearchExperiment(
        experiment_id=PPG_DALIA_ROBUSTNESS_ID,
        title="PPG-DaLiA S14 — Controlled sensor-fault characterization",
        research_question=(
            "How do predefined replay sensor faults change valid-prediction accuracy and pipeline availability "
            "relative to the clean canonical HR path?"
        ),
        dataset="PPG-DaLiA",
        target="Heart rate",
        status=ResearchStatus.COMPLETE,
        result_class=ResearchResultClass.ROBUSTNESS_CHARACTERIZATION,
        outcome_summary=(
            "PPG noise degraded accuracy while predictions remained available; dropout, flat PPG, and native "
            "sample loss primarily reduced explicit pipeline availability."
        ),
        scope=ResearchScope(
            subjects=["S14"],
            held_out_subjects=["S14"],
            evaluation_windows=int(execution["total_condition_windows"]),
            environment_scope=ResearchEnvironmentScope.TERRESTRIAL_FREE_LIVING,
            cohort_note="Controlled single-subject characterization across 114 pre-registered conditions.",
        ),
        configurations=[
            ResearchConfiguration(
                configuration_id="canonical_pipeline",
                label="Canonical PPG + synchronized IMU HR pipeline",
                description="Frozen Model B evaluated under clean and injected replay conditions.",
                sensing=["wrist PPG", "synchronized wrist IMU"],
                metrics=_fault_metrics(clean),
            )
        ],
        breakdowns=[
            ResearchBreakdown(
                breakdown_id="fault_conditions",
                kind="fault_condition",
                title="All concrete fault conditions",
                entries=condition_entries,
            ),
            ResearchBreakdown(
                breakdown_id="stochastic_fault_aggregates",
                kind="fault_aggregate",
                title="Five-seed stochastic fault aggregates",
                entries=aggregate_entries,
            ),
        ],
        provenance=ResearchProvenance(
            source_artifact=artifact,
            supporting_artifacts=[
                "ml/experiments/ppg_dalia_fault_robustness/REPORT.md",
                "docs/PHASE5_ROBUSTNESS_AUDIT_ADDENDUM.md",
                "ml/experiments/ppg_dalia_fault_robustness/config.json",
            ],
            dataset_version="Official UCI PPG-DaLiA S14 payload",
            split_identity="S14 held-out test subject from the frozen PPG-DaLiA split",
            model_identity=[str(model["model_id"])],
            checkpoints=[
                ResearchCheckpointIdentity(
                    run_id="canonical_model_b",
                    model_id=str(model["model_id"]),
                    sha256=str(model["checkpoint_sha256"]),
                    size_bytes=int(model["checkpoint_size_bytes"]),
                )
            ],
            experiment_version=str(result["protocol"]["sha256"]),
        ),
        claim_boundaries=ResearchClaimBoundaries(
            supported=[
                "Under the implemented S14 corruptions, PPG noise changed valid-prediction error while several missing/flat input faults collapsed availability.",
                "The current contiguous-window pipeline fails closed under independent native-sample loss.",
                "Under first-batch-calibrated IMU noise, aggregate S14 HR error changed very little.",
            ],
            unsupported=[
                "The model is robust to universally severe IMU noise.",
                "IMU is irrelevant to the model.",
                "The neural network detects faults or knows when it is wrong.",
                "The system is fault tolerant or has predictive uncertainty.",
                "S14 establishes population, astronaut, or microgravity robustness.",
            ],
            limitations=[
                "Only one held-out subject was characterized.",
                "IMU noise/saturation calibration used the low-motion first S14 batch; its per-axis standard deviation was about 0.0075, 0.0093, and 0.0080 versus typical median-window values near 0.122, 0.144, and 0.101.",
                "Per-window z-scoring may attenuate part of the tested present-but-noisy IMU perturbation.",
                "Zero/frozen IMU increased MAE, so near-zero additive-noise change is not evidence that the model ignores IMU.",
                "Packet-loss results primarily characterize fail-closed availability; surviving-window MAE is based on small, selected subsets.",
            ],
        ),
    )


def _aggregate_ptt_breakdown(
    result: dict[str, Any],
    source_key: str,
    breakdown_id: str,
    title: str,
) -> ResearchBreakdown:
    runs = _require(result, "runs", "PTT result")
    model_runs: dict[str, dict[str, Any]] = {"model_a": runs["a"], "model_b": runs["b"]}
    labels = sorted(next(iter(model_runs["model_a"].values()))[source_key])
    entries: list[ResearchBreakdownEntry] = []
    for label in labels:
        metrics_by_model: dict[str, dict[str, ResearchMetricEstimate]] = {}
        for model_id, reports in model_runs.items():
            records = [report[source_key][label] for report in reports.values()]
            mae_values = [float(record["mae"]) for record in records]
            rmse_values = [float(record["rmse"]) for record in records]
            metrics_by_model[model_id] = {
                "mae": _metric(
                    statistics.fmean(mae_values),
                    "bpm",
                    sd=statistics.pstdev(mae_values),
                    n=int(records[0]["n_windows"]),
                ),
                "rmse": _metric(
                    statistics.fmean(rmse_values),
                    "bpm",
                    sd=statistics.pstdev(rmse_values),
                    n=int(records[0]["n_windows"]),
                ),
            }
        a_mae = metrics_by_model["model_a"]["mae"].mean
        b_mae = metrics_by_model["model_b"]["mae"].mean
        assert a_mae is not None and b_mae is not None
        entries.append(
            ResearchBreakdownEntry(
                entry_id=f"{breakdown_id}-{label}",
                label=label,
                dimensions={"category": label, "replicates": 5},
                configuration_metrics=metrics_by_model,
                delta=_metric(b_mae - a_mae, "bpm"),
            )
        )
    return ResearchBreakdown(
        breakdown_id=breakdown_id,
        kind=breakdown_id,
        title=title,
        entries=entries,
    )


def adapt_ptt_site_ablation(repository_root: Path) -> ResearchExperiment:
    artifact = "results/ptt_ppg_site_ablation.json"
    result = _read_json(repository_root, artifact)
    config = _require(result, "config", artifact)
    dataset_name = str(_require(config, "dataset", artifact))
    if dataset_name != "PhysioNet Pulse Transit Time PPG Dataset v1.1.0":
        raise ResearchArtifactError("PTT dataset identity changed.")
    if bool(config.get("imu_included_in_primary_comparison")):
        raise ResearchArtifactError("PTT primary comparison unexpectedly includes IMU.")
    split = _require(result, "subject_split", artifact)
    if [len(split[key]) for key in ("train", "val", "test")] != [15, 3, 4]:
        raise ResearchArtifactError("PTT frozen subject split changed.")
    aggregate = _require(result, "aggregate", artifact)
    a = _require(aggregate, "model_a", artifact)
    b = _require(aggregate, "model_b", artifact)
    delta = _require(aggregate, "paired_delta_mae_b_minus_a", artifact)
    per_seed = _require(delta, "per_seed", artifact)
    b_worse_count = sum(float(value) > 0 for value in per_seed.values())
    if len(per_seed) != 5 or b_worse_count != 5:
        raise ResearchArtifactError("PTT paired seed direction contradicts the accepted frozen result.")
    test_windows = int(_require(result, "window_counts", artifact)["test"])
    configurations = [
        ResearchConfiguration(
            configuration_id="model_a",
            label="Model A — one physical PPG site",
            description="Distal phalanx site with red, infrared, and green PPG wavelengths.",
            sensing=["PPG site 1: red", "PPG site 1: infrared", "PPG site 1: green"],
            metrics={
                "mae": _metric(a["mean_mae"], "bpm", sd=a["sd_mae"], n=test_windows),
                "rmse": _metric(a["mean_rmse"], "bpm", sd=a["sd_rmse"], n=test_windows),
            },
        ),
        ResearchConfiguration(
            configuration_id="model_b",
            label="Model B — two physical PPG sites",
            description="The same three wavelengths at distal and proximal phalanx sites.",
            sensing=[
                "PPG site 1: red/infrared/green",
                "PPG site 2: red/infrared/green",
            ],
            metrics={
                "mae": _metric(b["mean_mae"], "bpm", sd=b["sd_mae"], n=test_windows),
                "rmse": _metric(b["mean_rmse"], "bpm", sd=b["sd_rmse"], n=test_windows),
            },
        ),
    ]
    seed_entries = []
    for seed_key in sorted(per_seed, key=lambda value: int(value.removeprefix("seed"))):
        report_a = result["runs"]["a"][seed_key]["overall"]
        report_b = result["runs"]["b"][seed_key]["overall"]
        seed_entries.append(
            ResearchBreakdownEntry(
                entry_id=f"paired-{seed_key}",
                label=seed_key,
                dimensions={"seed": int(seed_key.removeprefix("seed"))},
                configuration_metrics={
                    "model_a": _metric_map(report_a),
                    "model_b": _metric_map(report_b),
                },
                delta=_metric(per_seed[seed_key], "bpm"),
            )
        )
    checkpoints = [
        ResearchCheckpointIdentity(
            run_id=str(item["run_id"]),
            model_id=f"model_{item['model']}",
            sha256=str(item["sha256"]),
            size_bytes=int(item["size_bytes"]),
        )
        for item in _require(result, "checkpoint_manifest", artifact)
    ]
    return ResearchExperiment(
        experiment_id=PTT_SITE_ABLATION_ID,
        title="PTT Dataset — Marginal value of a second PPG site",
        research_question=(
            "Does adding a second physical PPG site improve ECG-referenced heart-rate estimation "
            "under the frozen subject-disjoint experiment?"
        ),
        dataset=dataset_name,
        target="ECG-referenced heart rate",
        status=ResearchStatus.COMPLETE,
        result_class=ResearchResultClass.NEGATIVE_MARGINAL_RESULT,
        outcome_summary=(
            "Adding the second PPG site did not improve overall held-out HR estimation in the evaluated "
            "model family; the two-site model was worse in all five paired training seeds."
        ),
        scope=ResearchScope(
            subjects=[f"s{index}" for index in range(1, 23)],
            held_out_subjects=list(split["test"]),
            evaluation_windows=test_windows,
            activities=["sit", "walk", "run"],
            environment_scope=ResearchEnvironmentScope.TERRESTRIAL_CONTROLLED,
            cohort_note="22 terrestrial participants; 15 train, 3 validation, and 4 held-out test subjects.",
        ),
        configurations=configurations,
        marginal_result=ResearchMarginalResult(
            baseline_configuration_id="model_a",
            candidate_configuration_id="model_b",
            added_sensing="second physical red/infrared/green PPG site",
            metric="mae",
            delta=_metric(delta["mean"], "bpm", sd=delta["sd"]),
            direction=MarginalDirection.WORSENED,
            paired_replicates=5,
            candidate_improved_count=0,
            candidate_worsened_count=5,
            notes=[
                "The two-site model was worse in 5/5 paired training seeds.",
                "Across held-out subjects, the second site improved s9 and s20 but worsened s2 and s14.",
                "Walking MAE was approximately equal/slightly better for Model B; sitting and running were worse.",
            ],
        ),
        breakdowns=[
            _aggregate_ptt_breakdown(result, "per_subject", "per_subject", "Held-out subjects"),
            _aggregate_ptt_breakdown(result, "per_activity", "per_activity", "Activities"),
            ResearchBreakdown(
                breakdown_id="paired_seeds",
                kind="seed",
                title="Paired training seeds",
                entries=seed_entries,
            ),
        ],
        provenance=ResearchProvenance(
            source_artifact=artifact,
            supporting_artifacts=[
                "results/ptt_ppg_site_ablation_reproducibility.json",
                "ml/experiments/ptt_ppg_site_ablation/REPORT.md",
                "ml/experiments/ptt_ppg_site_ablation/config.json",
                "ml/experiments/ptt_ppg_site_ablation/subject_split.json",
                "datasets/PTT_DATASET_AUDIT_DAY3.md",
                "docs/MODEL_CONTRACT_PTT_HR.md",
            ],
            dataset_version="v1.1.0",
            split_identity="ml/experiments/ptt_ppg_site_ablation/subject_split.json",
            model_identity=["PPGSiteHRModel model_a (3 channels)", "PPGSiteHRModel model_b (6 channels)"],
            checkpoints=checkpoints,
            experiment_version="a18068440319786c6921e8b8914420eeb731b350",
        ),
        claim_boundaries=ResearchClaimBoundaries(
            supported=[
                "Under this frozen split and model family, the second PPG site did not improve overall ECG-referenced HR estimation.",
                "The negative marginal result is stable in direction across all five paired training seeds.",
            ],
            unsupported=[
                "The second physical site contains no useful physiology or is universally useless.",
                "More sensors are always worse or fewer sensors are always better.",
                "This result selects a globally optimal wearable architecture.",
                "The result validates cuffless blood pressure, astronauts, or microgravity use.",
            ],
            limitations=[
                "Only four held-out subjects were evaluated; two improved and two worsened with Model B.",
                "Model B has more input channels, so site and channel-count effects are not fully separable.",
                "Held-out s2 is an important high-HR out-of-distribution-like case and is retained in all aggregates.",
                "Windows within a subject/activity are not independent; no window-level significance test was used.",
                "The cohort is terrestrial and healthy.",
            ],
        ),
    )


Adapter = Callable[[Path], ResearchExperiment]


class ResearchCatalog:
    """Read-through catalog; artifacts remain the immutable source of truth."""

    ADAPTERS: dict[str, Adapter] = {
        PPG_DALIA_ABLATION_ID: adapt_ppg_dalia_ablation,
        PPG_DALIA_ROBUSTNESS_ID: adapt_ppg_dalia_robustness,
        PTT_SITE_ABLATION_ID: adapt_ptt_site_ablation,
    }

    def __init__(self, repository_root: str | Path = REPOSITORY_ROOT) -> None:
        self.repository_root = Path(repository_root).resolve()

    @property
    def experiment_ids(self) -> tuple[str, ...]:
        return tuple(self.ADAPTERS)

    def get(self, experiment_id: str) -> ResearchExperimentEnvelope:
        adapter = self.ADAPTERS.get(experiment_id)
        if adapter is None:
            raise KeyError(experiment_id)
        try:
            experiment = adapter(self.repository_root)
        except (ResearchArtifactError, KeyError, TypeError, ValueError, ValidationError) as exc:
            return ResearchExperimentEnvelope(
                experiment_id=experiment_id,
                availability=ResearchAvailability.UNAVAILABLE,
                error=str(exc),
            )
        return ResearchExperimentEnvelope(
            experiment_id=experiment_id,
            availability=ResearchAvailability.AVAILABLE,
            experiment=experiment,
        )

    def list(self) -> list[ResearchExperimentSummaryEnvelope]:
        responses: list[ResearchExperimentSummaryEnvelope] = []
        for experiment_id in self.experiment_ids:
            envelope = self.get(experiment_id)
            responses.append(
                ResearchExperimentSummaryEnvelope(
                    experiment_id=experiment_id,
                    availability=envelope.availability,
                    summary=None if envelope.experiment is None else _summary(envelope.experiment),
                    error=envelope.error,
                )
            )
        return responses

    def summary(self) -> ResearchProjectSummary:
        experiments = self.list()
        available = sum(item.availability == ResearchAvailability.AVAILABLE for item in experiments)
        return ResearchProjectSummary(
            experiment_count=len(experiments),
            available_count=available,
            unavailable_count=len(experiments) - available,
            experiments=experiments,
            statement=(
                "Biological Minimalism evaluates added sensing by target- and dataset-specific measured "
                "marginal value; these completed experiments demonstrate the method, not a globally optimal sensor suite."
            ),
        )


research_catalog = ResearchCatalog()
