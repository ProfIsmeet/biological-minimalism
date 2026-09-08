"""Adapt immutable committed result artifacts into the canonical schema."""

from __future__ import annotations

import json
import statistics
from collections.abc import Callable
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from app.schemas.research import (
    CapacityMatchStatus,
    ComparisonRole,
    ControlledComparison,
    EvidenceStrength,
    MarginalDirection,
    MetricDirectionality,
    MetricKind,
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
    ReproComponent,
    ReproComponentStatus,
    ReproducibilityInteraction,
    ReproducibilitySummary,
    ResearchProjectSummary,
    ResearchProvenance,
    ResearchResultClass,
    ResearchScope,
    ResearchStatus,
    SensitivityStatus,
    TargetEvidenceMatrix,
    TargetEvidenceMatrixEnvelope,
)

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]

PPG_DALIA_ABLATION_ID = "ppg-dalia-imu-ablation"
PPG_DALIA_ROBUSTNESS_ID = "ppg-dalia-s14-fault-robustness"
PTT_SITE_ABLATION_ID = "ptt-ppg-site-ablation"
SLEEP_EDF_ABLATION_ID = "sleep-edf-eeg-eog-ablation"


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


def _ppg_controlled_comparisons(
    repository_root: Path,
) -> tuple[list[ControlledComparison], ResearchConfiguration | None, ControlledComparison | None]:
    """Build the capacity-controlled PPG comparisons from the canonical source
    (audit H5/M15). Returns (comparisons, model_a_cap configuration, primary).

    Each comparison reads its OWN mean/SD/seed-sign-count from
    results/ppg_dalia_capacity_control.json::primary_comparisons — no blending of
    a single-run magnitude with another comparison's replication metadata. If the
    artifact is absent the headline degrades to None and the caller falls back to
    the historical framing (clearly labelled) rather than fabricating values."""
    cc = _optional_json(repository_root, "results/ppg_dalia_capacity_control.json")
    if cc is None:
        return [], None, None
    pcs = cc.get("primary_comparisons", {})
    agg = cc.get("aggregate", {})

    def _cmp(key: str, cid: str, label: str, role: ComparisonRole, baseline: str,
             candidate: str, interpretation: str) -> ControlledComparison | None:
        block = pcs.get(key)
        if not isinstance(block, dict) or not isinstance(block.get("mean"), (int, float)):
            return None
        return ControlledComparison(
            comparison_id=cid, label=label, role=role,
            baseline_id=baseline, candidate_id=candidate,
            delta_definition="baseline_MAE - candidate_MAE (positive = candidate lower MAE = better)",
            delta=_metric(block["mean"], "bpm", sd=block.get("sd_sample_ddof1"),
                          n=block.get("n_seeds_total")),
            n_seeds=block.get("n_seeds_total"),
            n_seeds_favor_candidate=block.get("n_seeds_candidate_better"),
            interpretation=interpretation,
        )

    primary = _cmp(
        "baseline_Acap_candidate_B", "capacity_controlled_Acap_to_B",
        "Capacity-controlled IMU-information benefit (A_cap -> B)",
        ComparisonRole.PRIMARY_CONTROLLED, "model_a_cap", "model_b_ppg_plus_imu",
        "After matching PPG-only capacity to Model B, synchronized IMU still lowers MAE in every seed; "
        "this is the cleanest current estimate of IMU sensor-information value.",
    )
    shuffled = _cmp(
        "baseline_C_candidate_B", "matched_shuffled_control_C_to_B",
        "Matched shuffled control (C -> B, synchronization increment)",
        ComparisonRole.MATCHED_SHUFFLED_CONTROL, "model_c_ppg_plus_shuffled_imu",
        "model_b_ppg_plus_imu",
        "Against a same-capacity shuffled-IMU control, synchronized IMU still helps in every seed, "
        "so the benefit is not merely extra parameters or a shuffled context signal.",
    )
    comparisons = [c for c in (primary, shuffled) if c is not None]

    # Historical uncontrolled A->B, DEMOTED and clearly labelled (never the headline).
    ms = _optional_json(repository_root, "results/ppg_dalia_imu_multiseed_replication.json")
    if ms is not None:
        tot = ms.get("aggregate", {}).get("total_sync_imu_benefit_mae_A_minus_B", {})
        if isinstance(tot.get("mean"), (int, float)):
            comparisons.append(ControlledComparison(
                comparison_id="historical_uncontrolled_A_to_B",
                label="Historical uncontrolled A -> B (capacity-confounded)",
                role=ComparisonRole.HISTORICAL_CAPACITY_CONFOUNDED_RESULT,
                baseline_id="model_a_ppg_only", candidate_id="model_b_ppg_plus_imu",
                delta_definition="baseline_MAE - candidate_MAE (positive = candidate better)",
                delta=_metric(tot["mean"], "bpm", sd=tot.get("sd"), n=tot.get("n_seeds_total")),
                n_seeds=tot.get("n_seeds_total"), n_seeds_favor_candidate=tot.get("n_seeds_favor_B"),
                interpretation=(
                    "Original architecture differed (baseline A ~8k params vs candidate ~29k). This "
                    "magnitude CANNOT be interpreted as pure IMU value; capacity control (A_cap->B) "
                    "substantially reduced the apparent effect. Shown for history only."
                ),
            ))

    # Capacity-matched PPG-only (A_cap) as a real configuration for referential integrity.
    a_cap = agg.get("model_a_cap")
    b_recomp = agg.get("model_b_original_recomputed_from_multiseed")
    a_cap_config = None
    if isinstance(a_cap, dict) and isinstance(a_cap.get("mean"), (int, float)):
        a_cap_config = ResearchConfiguration(
            configuration_id="model_a_cap",
            label="PPG only (capacity-matched, A_cap)",
            description="Capacity-matched PPG-only baseline (~29k params) for a fair A_cap->B comparison.",
            sensing=["wrist PPG"],
            metrics={"mae": _metric(a_cap["mean"], "bpm", sd=a_cap.get("sd_sample_ddof1"))},
        )
        if isinstance(b_recomp, dict) and isinstance(b_recomp.get("mean"), (int, float)):
            a_cap_config.metrics["mae_reference_model_b"] = _metric(
                b_recomp["mean"], "bpm", sd=b_recomp.get("sd_sample_ddof1")
            )
    return comparisons, a_cap_config, primary


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
    # Capacity-controlled headline (audit H5): the marginal_result.delta must be
    # the capacity-controlled A_cap->B, NOT the uncontrolled single-seed A->B.
    controlled_comparisons, a_cap_config, primary_cmp = _ppg_controlled_comparisons(repository_root)
    if a_cap_config is not None:
        configurations.append(a_cap_config)
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
            "Under capacity control, synchronized IMU still lowers held-out PPG HR MAE by "
            "~0.605 bpm (A_cap->B, 5/5 seeds); a same-capacity shuffled-IMU control (C->B) improves "
            "~0.776 bpm (5/5). The original uncontrolled A->B magnitude was largely capacity, not IMU "
            "information, and is retained only as a historical, capacity-confounded result."
            if primary_cmp is not None else
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
            # Headline is the CAPACITY-CONTROLLED A_cap->B when available (audit H5);
            # only if the capacity-control artifact is absent do we fall back to the
            # uncontrolled A->B point estimate (older deployments).
            baseline_configuration_id="model_a_cap" if primary_cmp is not None else "model_a_ppg_only",
            candidate_configuration_id="model_b_ppg_plus_imu",
            added_sensing="synchronized wrist IMU",
            metric="mae",
            # Headline delta kept in the codebase-wide candidate-baseline convention
            # (MAE: negative = improvement), so it reads consistently against PTT/others.
            # The +0.605 baseline-candidate value lives in the self-documenting
            # controlled_comparisons entry with its explicit delta_definition (audit M1).
            delta=(
                _metric(-primary_cmp.delta.mean, "bpm", sd=primary_cmp.delta.sd, n=primary_cmp.delta.n)
                if primary_cmp is not None and primary_cmp.delta.mean is not None
                else _metric(candidate_mae - baseline_mae, "bpm")
            ),
            direction=MarginalDirection.IMPROVED,
            paired_replicates=primary_cmp.n_seeds if primary_cmp is not None else paired_replicates,
            candidate_improved_count=(
                primary_cmp.n_seeds_favor_candidate if primary_cmp is not None else candidate_improved_count
            ),
            candidate_worsened_count=(
                (primary_cmp.n_seeds - primary_cmp.n_seeds_favor_candidate)
                if primary_cmp is not None and primary_cmp.n_seeds is not None
                and primary_cmp.n_seeds_favor_candidate is not None
                else candidate_worsened_count
            ),
            metric_kind=MetricKind.REGRESSION,
            metric_directionality=MetricDirectionality.LOWER_IS_BETTER,
            capacity_match_status=(
                CapacityMatchStatus.MATCHED if primary_cmp is not None else CapacityMatchStatus.CONFOUNDED
            ),
            controlled_comparisons=controlled_comparisons,
            headline_comparison_id=primary_cmp.comparison_id if primary_cmp is not None else None,
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
                (
                    "A->B and A->C are capacity-confounded (baseline A ~8k params vs candidate "
                    "B/C ~29k params); the capacity-matched C->B comparison is the cleanest "
                    "current evidence. A supplemental capacity-matched PPG-only control (A_cap, "
                    "~29k params) now exists (results/ppg_dalia_capacity_control.json): a large "
                    "majority of the original A->B gap was recovered by architecture/capacity "
                    "alone, leaving a smaller but still 5/5-seed-consistent capacity-controlled "
                    "IMU-information benefit (A_cap->B). The original A->B magnitude must not be "
                    "read as pure IMU sensor value."
                ),
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
            metric_kind=MetricKind.REGRESSION,
            metric_directionality=MetricDirectionality.LOWER_IS_BETTER,
            capacity_match_status=CapacityMatchStatus.UNKNOWN,
            evidence_strength=EvidenceStrength.REPLICATED_BUT_VARIABLE,
            subject_heterogeneity=(
                "Heterogeneous across only 4 held-out subjects (2 of 4 favor the candidate). The "
                "aggregate negative direction is dominated by subject s2; descriptively excluding s2 "
                "flips the aggregate direction. s2 is never removed from the frozen primary result. "
                "The 5/5 seed agreement is optimization replication, not 5 independent populations."
            ),
            sensitivity_status=SensitivityStatus.AVAILABLE,
            notes=[
                "The two-site model was worse in 5/5 paired training seeds (optimization replication).",
                "Across held-out subjects, the second site improved s9 and s20 but worsened s2 and s14.",
                "Walking MAE was approximately equal/slightly better for Model B; sitting and running were worse.",
                "See results/ptt_sensitivity_analysis.json for the descriptive s2/LOSO sensitivity analysis.",
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


def _optional_json(repository_root: Path, relative_path: str) -> dict[str, Any] | None:
    """Load a research artifact if present; return None if it is absent (so the
    adapter degrades gracefully when a supplementary Sleep-EDF artifact has not
    been integrated yet)."""
    try:
        return _read_json(repository_root, relative_path)
    except ResearchArtifactError:
        return None


# --- Reproducibility panel helpers (audit H3 §3-§7) --------------------------
# Each helper validates one subcomponent and returns a typed ReproComponent.
# Rules enforced: (a) a subcomponent missing from the artifact is UNAVAILABLE,
# never PASS; (b) a present-but-wrong-typed field is MALFORMED, never PASS;
# (c) an explicit failure flag is FAIL; (d) every displayed number is read from
# the artifact, never hardcoded. The overall verdict is computed worst-of over
# the reproduction components (interaction is informational and excluded).

_REPRO_SEVERITY = {
    ReproComponentStatus.PASS: 0,
    ReproComponentStatus.PARTIAL: 1,
    ReproComponentStatus.UNAVAILABLE: 2,
    ReproComponentStatus.MALFORMED: 3,
    ReproComponentStatus.FAIL: 4,
}


def _as_number(value: Any) -> float | None:
    """Return value as float only if it is a real number (bool excluded)."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return float(value)


def _subdict(repro: dict[str, Any], key: str) -> tuple[dict[str, Any] | None, ReproComponentStatus | None]:
    """Fetch a subcomponent dict, classifying absence vs. wrong-type."""
    if key not in repro:
        return None, ReproComponentStatus.UNAVAILABLE
    value = repro[key]
    if not isinstance(value, dict):
        return None, ReproComponentStatus.MALFORMED
    return value, None


def _repro_environment(repro: dict[str, Any], provenance: str) -> ReproComponent:
    env, missing = _subdict(repro, "environment")
    label = "Environment verification"
    if missing is not None:
        return ReproComponent(
            key="environment", label=label, status=missing,
            detail="Frozen-environment sub-artifact absent or malformed.",
            provenance=provenance,
            reason_if_unavailable="environment block missing from reproduction artifact",
        )
    verified = env.get("frozen_stack_verified")
    src = env.get("source") if isinstance(env.get("source"), str) else provenance
    if verified is True:
        return ReproComponent(
            key="environment", label=label, status=ReproComponentStatus.PASS,
            detail=(
                "Recorded interpreter/backend versions and deterministic thread settings match for the "
                "checked fields (python, os, torch, numpy, scipy, scikit-learn, thread count). Scope is "
                "RECORDED_ENVIRONMENT_MATCH_FOR_CHECKED_FIELDS, not full CPU/env-var capture."
            ),
            value_display="checked fields match", provenance=src,
        )
    if verified is False:
        return ReproComponent(
            key="environment", label=label, status=ReproComponentStatus.FAIL,
            detail="Frozen-stack verification reported a mismatch.",
            value_display="stack mismatch", provenance=src,
        )
    return ReproComponent(
        key="environment", label=label, status=ReproComponentStatus.MALFORMED,
        detail="`frozen_stack_verified` is missing or not a boolean.",
        provenance=src,
    )


def _repro_datasets(repro: dict[str, Any], provenance: str) -> ReproComponent:
    ds, missing = _subdict(repro, "dataset_fingerprints")
    label = "Dataset fingerprints"
    if missing is not None:
        return ReproComponent(
            key="datasets", label=label, status=missing,
            detail="Dataset-fingerprint sub-artifact absent or malformed.",
            provenance=provenance,
            reason_if_unavailable="dataset_fingerprints block missing",
        )
    total = _as_number(ds.get("n_records_total"))
    present = _as_number(ds.get("n_present"))
    missing_n = _as_number(ds.get("n_missing"))
    if total is None or present is None or missing_n is None:
        return ReproComponent(
            key="datasets", label=label, status=ReproComponentStatus.MALFORMED,
            detail="Fingerprint counts missing or non-numeric.", provenance=provenance,
        )
    disp = f"{int(present)}/{int(total)} records fingerprinted"
    if total > 0 and present == total and missing_n == 0:
        status = ReproComponentStatus.PASS
        detail = "Every record present and fingerprinted; none missing."
    else:
        status = ReproComponentStatus.PARTIAL
        detail = f"{int(missing_n)} record(s) missing; fingerprint coverage incomplete."
    return ReproComponent(
        key="datasets", label=label, status=status, detail=detail,
        value_display=disp, provenance=provenance,
    )


def _repro_checkpoint_durability(repository_root: Path) -> ReproComponent:
    """Derived from the integrated 60-checkpoint inventory (Day-14 support),
    NOT a hardcoded '50 checkpoints' string."""
    label = "Checkpoint durability"
    inv = _optional_json(repository_root, "results/final_checkpoint_inventory_day14.json")
    prov = "results/final_checkpoint_inventory_day14.json"
    if inv is None:
        return ReproComponent(
            key="checkpoint_durability", label=label, status=ReproComponentStatus.UNAVAILABLE,
            detail="Checkpoint inventory not integrated in this deployment.",
            reason_if_unavailable="final_checkpoint_inventory_day14.json absent",
        )
    summary = inv.get("summary")
    if not isinstance(summary, dict):
        return ReproComponent(
            key="checkpoint_durability", label=label, status=ReproComponentStatus.MALFORMED,
            detail="Inventory present but `summary` missing or malformed.", provenance=prov,
        )
    total = _as_number(summary.get("n_total_referenced"))
    archived = _as_number(summary.get("n_with_external_archival"))
    if total is None or archived is None:
        return ReproComponent(
            key="checkpoint_durability", label=label, status=ReproComponentStatus.MALFORMED,
            detail="Inventory counts missing or non-numeric.", provenance=prov,
        )
    disp = f"{int(archived)}/{int(total)} externally archived"
    if total > 0 and archived == total:
        return ReproComponent(
            key="checkpoint_durability", label=label, status=ReproComponentStatus.PASS,
            detail="All referenced checkpoints have an external archival location (GitHub Release tags).",
            value_display=disp, provenance=prov,
        )
    return ReproComponent(
        key="checkpoint_durability", label=label, status=ReproComponentStatus.PARTIAL,
        detail="Some referenced checkpoints lack an external archival location.",
        value_display=disp, provenance=prov,
    )


def _repro_canonical(repro: dict[str, Any], provenance: str) -> ReproComponent:
    ppg, missing = _subdict(repro, "ppg_dalia")
    label = "Canonical experiment reproduction"
    if missing is not None:
        return ReproComponent(
            key="canonical", label=label, status=missing,
            detail="Canonical reproduction sub-artifact absent or malformed.",
            provenance=provenance, reason_if_unavailable="ppg_dalia block missing",
        )
    match = ppg.get("all_metrics_match")
    n_ckpt = _as_number(ppg.get("checkpoints_verified"))
    max_diff = _as_number(ppg.get("max_abs_difference"))
    if match is None or n_ckpt is None or max_diff is None:
        return ReproComponent(
            key="canonical", label=label, status=ReproComponentStatus.MALFORMED,
            detail="Reproduction match flag or counts missing/non-numeric.", provenance=provenance,
        )
    disp = f"{int(n_ckpt)} checkpoints re-evaluated, max abs diff {max_diff:g}"
    if match is True:
        return ReproComponent(
            key="canonical", label=label, status=ReproComponentStatus.PASS,
            detail="All metrics matched on re-evaluation from frozen checkpoints (max abs diff as shown).",
            value_display=disp, provenance=provenance,
        )
    return ReproComponent(
        key="canonical", label=label, status=ReproComponentStatus.FAIL,
        detail="At least one metric did not match on re-evaluation.",
        value_display=disp, provenance=provenance,
    )


def _repro_robustness(repro: dict[str, Any], provenance: str) -> ReproComponent:
    rob, missing = _subdict(repro, "robustness")
    label = "Robustness reproduction"
    if missing is not None:
        return ReproComponent(
            key="robustness", label=label, status=missing,
            detail="Robustness sub-artifact absent or malformed.",
            provenance=provenance, reason_if_unavailable="robustness block missing",
        )
    n_can = _as_number(rob.get("n_conditions_canonical"))
    n_rep = _as_number(rob.get("n_conditions_reproduced"))
    match = rob.get("all_metrics_match")
    max_diff = _as_number(rob.get("max_abs_difference_bpm"))
    tol = _as_number(rob.get("tolerance_bpm"))
    mismatches = _as_number(rob.get("n_mismatches_beyond_tolerance"))
    if None in (n_can, n_rep, max_diff, tol) or match is None or mismatches is None:
        return ReproComponent(
            key="robustness", label=label, status=ReproComponentStatus.MALFORMED,
            detail="Robustness counts/flags missing or non-numeric.", provenance=provenance,
        )
    disp = f"{int(n_rep)}/{int(n_can)} conditions, max diff {max_diff:g} bpm (tol {tol:g})"
    if match is True and mismatches == 0 and n_rep == n_can and n_can > 0:
        return ReproComponent(
            key="robustness", label=label, status=ReproComponentStatus.PASS,
            detail="Full condition sweep reproduced within the documented tolerance; no mismatches.",
            value_display=disp, provenance=provenance,
        )
    if mismatches and mismatches > 0 or match is False:
        return ReproComponent(
            key="robustness", label=label, status=ReproComponentStatus.FAIL,
            detail=f"{int(mismatches)} condition(s) exceeded tolerance.",
            value_display=disp, provenance=provenance,
        )
    return ReproComponent(
        key="robustness", label=label, status=ReproComponentStatus.PARTIAL,
        detail="Only part of the condition sweep was reproduced.",
        value_display=disp, provenance=provenance,
    )


def _repro_n3(repro: dict[str, Any], provenance: str) -> ReproComponent:
    n3, missing = _subdict(repro, "n3_diagnostic")
    label = "N3 diagnostic verification"
    if missing is not None:
        return ReproComponent(
            key="n3", label=label, status=missing,
            detail="N3 diagnostic sub-artifact absent or malformed.",
            provenance=provenance, reason_if_unavailable="n3_diagnostic block missing",
        )
    verified = n3.get("verified")
    if verified is True:
        return ReproComponent(
            key="n3", label=label, status=ReproComponentStatus.PASS,
            detail="N3 recall up / precision down recomputed and matched the canonical Day-9 figures "
                   "(disclosed regression, not smoothed).",
            value_display="matches canonical", provenance=provenance,
        )
    if verified is False:
        return ReproComponent(
            key="n3", label=label, status=ReproComponentStatus.FAIL,
            detail="N3 diagnostic recomputation did not match the canonical figures.",
            provenance=provenance,
        )
    return ReproComponent(
        key="n3", label=label, status=ReproComponentStatus.MALFORMED,
        detail="`verified` flag missing or not a boolean.", provenance=provenance,
    )


def _repro_interaction(
    repro: dict[str, Any], provenance: str
) -> tuple[ReproComponent, ReproducibilityInteraction | None]:
    """Interaction is NEW evidence, not a reproduction of a prior claim, so its
    component is informational and excluded from the overall verdict. Numeric
    values are derived from the artifact (audit H3 §6), never hardcoded."""
    label = "Interaction experiment"
    inter, missing = _subdict(repro, "interaction_experiment")
    if missing is not None:
        return (
            ReproComponent(
                key="interaction", label=label, status=missing,
                detail="Interaction experiment sub-artifact absent or malformed.",
                provenance=provenance, reason_if_unavailable="interaction_experiment block missing",
            ),
            None,
        )
    if inter.get("status") != "RUN":
        return (
            ReproComponent(
                key="interaction", label=label, status=ReproComponentStatus.UNAVAILABLE,
                detail="Interaction experiment not marked RUN.",
                provenance=provenance, reason_if_unavailable="status is not RUN",
            ),
            None,
        )
    mean = _as_number(inter.get("interaction_term_mean"))
    sd = _as_number(inter.get("interaction_term_sd_sample_ddof1"))
    if mean is None or sd is None:
        return (
            ReproComponent(
                key="interaction", label=label, status=ReproComponentStatus.MALFORMED,
                detail="Interaction term mean/SD missing or non-numeric.", provenance=provenance,
            ),
            None,
        )
    estimate = f"{mean:+.4f} macro-F1"
    uncertainty = f"sample SD {sd:.4f}"
    classification = inter.get("classification")
    interpretation = (
        "approximately additive / unresolved"
        if not isinstance(classification, str)
        else classification.replace("_", " ")
    )
    interaction = ReproducibilityInteraction(
        tested=True,
        configs="M0 EEG / M_A EEG+EOG / M_B EEG+Resp / M_AB EEG+EOG+Resp (5 seeds)",
        interaction_estimate=estimate,
        uncertainty=uncertainty,
        interpretation=interpretation,
        plain_language=(
            "Adding both EOG and respiration did not show a stable extra benefit beyond "
            "their individual effects under this model and dataset."
        ),
        boundary="This does not prove that sensor interactions are absent in general; not a synergy claim.",
    )
    component = ReproComponent(
        key="interaction", label=label, status=ReproComponentStatus.PASS,
        detail="One controlled pair tested and honestly analyzed; global interaction coverage is partial.",
        value_display=f"{estimate} ({uncertainty})", provenance=provenance,
    )
    return component, interaction


def _overall_from_components(components: list[ReproComponent]) -> str:
    """Compute the overall verdict worst-of over the REPRODUCTION components
    (interaction excluded). Never defaults to PASS: an empty artifact whose
    every component is UNAVAILABLE yields PARTIAL, not PASS."""
    core = [c for c in components if c.key != "interaction"]
    worst = max(
        (_REPRO_SEVERITY[c.status] for c in core),
        default=_REPRO_SEVERITY[ReproComponentStatus.UNAVAILABLE],
    )
    if worst == _REPRO_SEVERITY[ReproComponentStatus.PASS]:
        return "SCIENTIFIC_REPRODUCTION_PASS"
    if worst == _REPRO_SEVERITY[ReproComponentStatus.FAIL]:
        return "SCIENTIFIC_REPRODUCTION_FAIL"
    if worst == _REPRO_SEVERITY[ReproComponentStatus.MALFORMED]:
        return "SCIENTIFIC_REPRODUCTION_MALFORMED"
    return "SCIENTIFIC_REPRODUCTION_PARTIAL"


def _malformed_repro_summary(reason: str) -> ReproducibilitySummary:
    return ReproducibilitySummary(
        overall_status="SCIENTIFIC_REPRODUCTION_MALFORMED",
        overall_declared=None,
        overall_matches_declared=False,
        environment_scope="UNKNOWN",
        independence_caveat="reproduction artifact could not be parsed",
        components=[
            ReproComponent(
                key="artifact", label="Reproduction artifact",
                status=ReproComponentStatus.MALFORMED, detail=reason,
            )
        ],
        interaction=None,
    )


def _build_sleep_supplementary_breakdowns(
    control: dict[str, Any] | None,
    persubj: dict[str, Any] | None,
    secondary: dict[str, Any] | None,
) -> list[ResearchBreakdown]:
    """Day 8/9: matched shuffled-EOG control, primary per-subject decomposition,
    and the prospective secondary holdout, as separate breakdowns. Primary (n=3)
    and secondary (n=8) are kept strictly separate — never pooled."""
    breakdowns: list[ResearchBreakdown] = []

    if control is not None:
        agg = control.get("aggregate", {})
        a = agg.get("model_a_macro_f1", {})
        b = agg.get("model_b_macro_f1", {})
        c = agg.get("model_c_macro_f1", {})
        ctb = agg.get("C_to_B", {})
        breakdowns.append(
            ResearchBreakdown(
                breakdown_id="negative_control_shuffled_eog",
                kind="negative_control",
                title="Matched negative control — aligned vs shuffled EOG (primary n=3)",
                entries=[
                    ResearchBreakdownEntry(
                        entry_id="control-aggregate",
                        label="Aligned (B) vs shuffled (C) EOG",
                        dimensions={
                            "b_beats_c_seeds": f"{ctb.get('n_seeds_favor_B')}/{ctb.get('n_seeds_total')}",
                            "control_note": "shuffled-EOG C is capacity-identical to B; A->C is ~neutral, so the benefit depends on temporal alignment, not EOG presence",
                        },
                        configuration_metrics={
                            "baseline_eeg_only": {"macro_f1": _metric(a.get("mean"), "macro-F1", sd=a.get("sd_sample_ddof1"))},
                            "candidate_eeg_plus_eog": {"macro_f1": _metric(b.get("mean"), "macro-F1", sd=b.get("sd_sample_ddof1"))},
                            "control_eeg_plus_shuffled_eog": {"macro_f1": _metric(c.get("mean"), "macro-F1", sd=c.get("sd_sample_ddof1"))},
                        },
                        delta=_metric(ctb.get("mean"), "macro-F1", sd=ctb.get("sd_sample_ddof1")),
                    )
                ],
            )
        )

    if persubj is not None:
        summary = persubj.get("subject_summary", {})
        entries = []
        for subj, rec in summary.items():
            base_m = rec.get("baseline_macro_f1", {})
            cand_m = rec.get("candidate_macro_f1", {})
            delta_m = rec.get("delta_candidate_minus_baseline", {})
            entries.append(
                ResearchBreakdownEntry(
                    entry_id=f"primary-subject-{subj}",
                    label=subj,
                    dimensions={"n_epochs": rec.get("n_epochs")},
                    configuration_metrics={
                        "baseline_eeg_only": {"macro_f1": _metric(base_m.get("mean"), "macro-F1", sd=base_m.get("sd_sample_ddof1"))},
                        "candidate_eeg_plus_eog": {"macro_f1": _metric(cand_m.get("mean"), "macro-F1", sd=cand_m.get("sd_sample_ddof1"))},
                    },
                    delta=_metric(delta_m.get("mean"), "macro-F1", sd=delta_m.get("sd_sample_ddof1")),
                )
            )
        breakdowns.append(
            ResearchBreakdown(
                breakdown_id="primary_per_subject",
                kind="per_subject_primary",
                title="Primary per-subject decomposition (n=3) — effect concentrated in SC4011",
                entries=entries,
            )
        )

    if secondary is not None:
        sagg = secondary.get("aggregate", {})
        sa = sagg.get("model_a_macro_f1", {})
        sb = sagg.get("model_b_macro_f1", {})
        sc = sagg.get("model_c_macro_f1", {})
        satb = sagg.get("A_to_B", {})
        ssum = secondary.get("subject_level_generalization_summary", {})
        breakdowns.append(
            ResearchBreakdown(
                breakdown_id="secondary_holdout_aggregate",
                kind="secondary_holdout",
                title=f"Prospective secondary holdout (n={secondary.get('cohort_size')}) — aggregate A/B/C, zero retraining",
                entries=[
                    ResearchBreakdownEntry(
                        entry_id="secondary-aggregate",
                        label="Secondary aggregate (evaluation-only)",
                        dimensions={
                            "b_beats_a_seeds": f"{satb.get('n_seeds_favor_B')}/{satb.get('n_seeds_total')}",
                            "subjects_B_gt_A": f"{ssum.get('n_subjects_B_greater_than_A')}/{ssum.get('n_subjects_total')}",
                            "subjects_B_gt_C": f"{ssum.get('n_subjects_B_greater_than_C')}/{ssum.get('n_subjects_total')}",
                            "no_retraining": secondary.get("no_retraining"),
                            "pooling_note": "primary n=3 and secondary n=8 are reported separately; never pooled into an n=11 test",
                        },
                        configuration_metrics={
                            "baseline_eeg_only": {"macro_f1": _metric(sa.get("mean"), "macro-F1", sd=sa.get("sd_sample_ddof1"))},
                            "candidate_eeg_plus_eog": {"macro_f1": _metric(sb.get("mean"), "macro-F1", sd=sb.get("sd_sample_ddof1"))},
                            "control_eeg_plus_shuffled_eog": {"macro_f1": _metric(sc.get("mean"), "macro-F1", sd=sc.get("sd_sample_ddof1"))},
                        },
                        delta=_metric(satb.get("mean"), "macro-F1", sd=satb.get("sd_sample_ddof1")),
                    )
                ],
            )
        )

        cls = secondary.get("class_level_aggregate", {})
        class_entries = []
        for cname in ("Wake", "N1", "N2", "N3", "REM"):
            rec = cls.get(cname, {})
            class_entries.append(
                ResearchBreakdownEntry(
                    entry_id=f"secondary-class-{cname}",
                    label=cname,
                    dimensions={"b_minus_a": rec.get("B_minus_A"), "regresses": (rec.get("B_minus_A") or 0) < 0},
                    configuration_metrics={
                        "baseline_eeg_only": {"macro_f1": _metric(rec.get("A_mean_f1"), "F1")},
                        "candidate_eeg_plus_eog": {"macro_f1": _metric(rec.get("B_mean_f1"), "F1")},
                        "control_eeg_plus_shuffled_eog": {"macro_f1": _metric(rec.get("C_mean_f1"), "F1")},
                    },
                    delta=_metric(rec.get("B_minus_A"), "F1"),
                )
            )
        breakdowns.append(
            ResearchBreakdown(
                breakdown_id="secondary_class_level",
                kind="secondary_class_level",
                title="Secondary holdout class-level F1 (B-A) — large REM gain, N3 regression",
                entries=class_entries,
            )
        )

    return breakdowns


def adapt_sleep_edf_ablation(repository_root: Path) -> ResearchExperiment:
    artifact = "results/sleep_edf_eeg_eog_ablation.json"
    result = _read_json(repository_root, artifact)
    if _require(result, "experiment_id", artifact) != "sleep_edf_eeg_eog_ablation":
        raise ResearchArtifactError("Sleep-EDF experiment identity changed.")
    protocol = _require(result, "frozen_protocol", artifact)
    split = _require(protocol, "subject_split", artifact)
    if [len(split[key]) for key in ("train", "val", "test")] != [12, 3, 3]:
        raise ResearchArtifactError("Sleep-EDF frozen subject split changed.")
    channels = _require(protocol, "channels", artifact)
    params = _require(result, "parameter_counts", artifact)
    aggregate = _require(result, "aggregate", artifact)
    base = _require(aggregate, "baseline_macro_f1", artifact)
    cand = _require(aggregate, "candidate_macro_f1", artifact)
    delta = _require(aggregate, "delta_candidate_minus_baseline", artifact)
    per_seed = _require(delta, "per_seed", artifact)
    better = int(_require(delta, "n_seeds_candidate_better", artifact))
    total = int(_require(delta, "n_seeds_total", artifact))
    if len(per_seed) != total or better != 4:
        raise ResearchArtifactError("Sleep-EDF seed direction contradicts the accepted frozen result.")
    test_windows = int(_require(_require(result, "window_counts", artifact), "candidate_eeg_plus_eog", artifact)["test"])

    # Day 8/9: matched shuffled-EOG control, per-subject decomposition, and the
    # prospective secondary holdout are now integrated. Surface them as separate
    # breakdowns (never pooled into the primary marginal result).
    control_full = _optional_json(repository_root, "results/sleep_edf_eeg_eog_control_analysis.json")
    persubj_full = _optional_json(repository_root, "results/sleep_edf_per_subject_analysis.json")
    secondary_full = _optional_json(repository_root, "results/sleep_edf_secondary_holdout_evaluation.json")
    extra_breakdowns = _build_sleep_supplementary_breakdowns(control_full, persubj_full, secondary_full)

    configurations = [
        ResearchConfiguration(
            configuration_id="baseline_eeg_only",
            label="Baseline — EEG Fpz-Cz only",
            description="Single-channel EEG (Fpz-Cz), 30s epochs, 5-class sleep staging.",
            sensing=list(channels["baseline_eeg_only"]),
            metrics={
                "macro_f1": _metric(base["mean"], "macro-F1", sd=base["sd_sample_ddof1"], n=test_windows),
            },
        ),
        ResearchConfiguration(
            configuration_id="candidate_eeg_plus_eog",
            label="Candidate — EEG Fpz-Cz + aligned EOG",
            description="EEG Fpz-Cz plus one horizontal EOG channel; capacity-fair (shared encoder, differs only in in_channels).",
            sensing=list(channels["candidate_eeg_plus_eog"]),
            metrics={
                "macro_f1": _metric(cand["mean"], "macro-F1", sd=cand["sd_sample_ddof1"], n=test_windows),
            },
        ),
    ]
    if control_full is not None:
        _c_agg = control_full.get("aggregate", {}).get("model_c_macro_f1", {})
        configurations.append(
            ResearchConfiguration(
                configuration_id="control_eeg_plus_shuffled_eog",
                label="Control — EEG Fpz-Cz + shuffled EOG",
                description="Capacity-identical negative control: EOG epochs shuffled within-subject/within-partition (temporal alignment destroyed, signal distribution preserved).",
                sensing=list(channels["candidate_eeg_plus_eog"]),
                metrics={
                    "macro_f1": _metric(_c_agg.get("mean"), "macro-F1", sd=_c_agg.get("sd_sample_ddof1"), n=test_windows),
                },
            )
        )

    seed_entries = []
    for seed_key in sorted(per_seed, key=lambda value: int(value.removeprefix("seed"))):
        b_f1 = base["per_seed"][seed_key]
        c_f1 = cand["per_seed"][seed_key]
        seed_entries.append(
            ResearchBreakdownEntry(
                entry_id=f"paired-{seed_key}",
                label=seed_key,
                dimensions={"seed": int(seed_key.removeprefix("seed"))},
                configuration_metrics={
                    "baseline_eeg_only": {"macro_f1": _metric(b_f1, "macro-F1")},
                    "candidate_eeg_plus_eog": {"macro_f1": _metric(c_f1, "macro-F1")},
                },
                delta=_metric(per_seed[seed_key], "macro-F1"),
            )
        )

    checkpoints = [
        ResearchCheckpointIdentity(
            run_id=str(item["run_id"]),
            model_id=str(item["config"]),
            sha256=str(item["sha256"]),
            size_bytes=int(item["size_bytes"]),
        )
        for item in _require(result, "checkpoint_manifest", artifact)
    ]

    return ResearchExperiment(
        experiment_id=SLEEP_EDF_ABLATION_ID,
        title="Sleep-EDF — Marginal value of horizontal EOG added to EEG",
        research_question=(
            "Does adding one horizontal EOG channel to single-channel EEG improve 5-class sleep-stage "
            "classification under a frozen, subject-disjoint Sleep-EDF protocol?"
        ),
        dataset="PhysioNet Sleep-EDF (sleep-cassette)",
        target="5-class sleep stage (Wake/N1/N2/N3/REM)",
        status=ResearchStatus.COMPLETE,
        result_class=ResearchResultClass.POSITIVE_MARGINAL_VALUE,
        outcome_summary=(
            "Adding horizontal EOG to EEG improved 5-class sleep-stage macro-F1 in the primary test "
            f"({better}/{total} training seeds; balanced accuracy 5/5), and again in a prospectively-frozen "
            "8-subject secondary holdout from the same dataset (A->B 5/5 seeds, zero retraining). A matched "
            "shuffled-EOG control is consistently worse than aligned EOG in both evaluations (C->B 5/5 each), "
            "supporting a role for temporally aligned ocular information. Same-dataset evidence with a matched "
            "control and prospective secondary-holdout support; largest class gains in N1/REM, with an N3 "
            "regression disclosed in the secondary cohort."
        ),
        scope=ResearchScope(
            subjects=sorted(list(split["train"]) + list(split["val"]) + list(split["test"])),
            held_out_subjects=list(split["test"]),
            evaluation_windows=test_windows,
            activities=[],
            environment_scope=ResearchEnvironmentScope.TERRESTRIAL_CONTROLLED,
            cohort_note=(
                "18 real Sleep-EDF subjects (one night each), 12 train / 3 validation / 3 held-out "
                "test, subject-disjoint. Selected from 153 recording files in the PhysioNet "
                "sleep-cassette directory (recordings/files are not subjects)."
            ),
        ),
        configurations=configurations,
        marginal_result=ResearchMarginalResult(
            baseline_configuration_id="baseline_eeg_only",
            candidate_configuration_id="candidate_eeg_plus_eog",
            added_sensing="one horizontal EOG channel",
            metric="macro_f1",
            delta=_metric(delta["mean"], "macro-F1", sd=delta["sd_sample_ddof1"]),
            direction=MarginalDirection.IMPROVED,
            paired_replicates=total,
            candidate_improved_count=better,
            candidate_worsened_count=total - better,
            metric_kind=MetricKind.CLASSIFICATION,
            metric_directionality=MetricDirectionality.HIGHER_IS_BETTER,
            capacity_match_status=CapacityMatchStatus.MATCHED,
            evidence_strength=EvidenceStrength.STRONGLY_REPLICATED,
            subject_heterogeneity=(
                "Primary n=3: the positive effect is concentrated in one subject (SC4011 improves; "
                "SC4081/SC4131 mixed; global result dominated by one subject). The prospective secondary "
                "holdout (n=8) broadens support to 6/8 subjects B>A and 7/8 B>C, with the largest single "
                "subject (SC4221) ~41% of the summed effect — no longer single-subject-dominated, but still "
                "not uniform (2/8 near-zero or slightly negative)."
            ),
            class_heterogeneity=(
                "Largest gains in N1 and REM. The secondary holdout reproduces a large REM gain but shows "
                "an N3 regression (B-A ~-0.043) not seen in the primary test — disclosed. Read-only "
                "confusion diagnostic: N3 recall improves but N3 precision drops because B over-labels true "
                "N2 epochs as N3."
            ),
            sensitivity_status=SensitivityStatus.UNAVAILABLE,
            notes=[
                f"Baseline {params['baseline_eeg_only']} params vs candidate {params['candidate_eeg_plus_eog']} params (capacity-fair by design).",
                "Primary metric is macro-F1 (classification); it must never be compared against the HR-MAE experiments.",
                "Evidence strength: replicated-with-control + prospective_secondary_holdout_supported. This is same-dataset evidence, NOT independent-dataset or cross-population replication.",
                "Primary (n=3) and secondary (n=8) holdouts are reported separately and must never be pooled into one n=11 test.",
            ],
        ),
        breakdowns=[
            ResearchBreakdown(
                breakdown_id="paired_seeds",
                kind="seed",
                title="Paired training seeds (macro-F1)",
                entries=seed_entries,
            ),
            *extra_breakdowns,
        ],
        provenance=ResearchProvenance(
            source_artifact=artifact,
            supporting_artifacts=[
                "results/sleep_edf_eeg_eog_ablation_reproducibility.json",
                "docs/SLEEP_EDF_EEG_EOG_PREDECLARATION_DAY7.md",
                "docs/SLEEP_EDF_EEG_EOG_RESULTS.md",
                "ml/experiments/sleep_edf_eeg_eog_ablation/subject_split.json",
            ],
            split_identity="ml/experiments/sleep_edf_eeg_eog_ablation/subject_split.json",
            model_identity=[
                f"Conv1DEncoder baseline ({params['baseline_eeg_only']} params)",
                f"Conv1DEncoder candidate ({params['candidate_eeg_plus_eog']} params)",
            ],
            checkpoints=checkpoints,
        ),
        claim_boundaries=ResearchClaimBoundaries(
            supported=[
                "Under a frozen, capacity-matched protocol, adding a synchronized EOG channel to "
                "single-channel EEG improved 5-class Sleep-EDF macro-F1 in the primary 3-subject test and "
                "again in a prospectively-frozen 8-subject secondary holdout from the same dataset.",
                "A capacity-identical shuffled-EOG negative control was consistently worse than aligned EOG "
                "in both evaluations (C->B 5/5 seeds each), supporting a role for temporally aligned ocular "
                "information rather than the mere presence of an EOG-shaped input.",
                "This demonstrates the marginal-value methodology transfers to a classification target and a "
                "different modality family (EEG/EOG).",
            ],
            unsupported=[
                "EOG is necessary or universally improves sleep staging.",
                "Independent-dataset or cross-population replication (this is still one Sleep-EDF cassette protocol).",
                "The primary (n=3) and secondary (n=8) holdouts form a single pooled n=11 test set.",
                "Uniform per-subject benefit (2/8 secondary subjects near-zero/negative; N3 regresses in the secondary cohort).",
                "This validates astronaut, microgravity, or spaceflight sleep monitoring.",
                "The final architecture should contain EOG.",
                "Sleep-EDF macro-F1 is comparable to or rankable against the HR-MAE experiments.",
                "This result validates the (untrained) Biological Digital Twin.",
            ],
            limitations=[
                "Primary test is only 3 held-out subjects and is dominated by one subject (SC4011).",
                "Single dataset (Sleep-EDF cassette); terrestrial population.",
                "Secondary-holdout benefit is broader (6/8 B>A) but not uniform.",
                "N3 per-class F1 regresses in the secondary cohort (precision effect; disclosed).",
                "Evidence is replicated-with-control, NOT independent-dataset replication.",
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
        SLEEP_EDF_ABLATION_ID: adapt_sleep_edf_ablation,
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

    def target_evidence_matrix(self) -> TargetEvidenceMatrixEnvelope:
        """Read-through the committed target-specific evidence matrix (§18)."""
        try:
            raw = _read_json(self.repository_root, "results/target_evidence_matrix.json")
            matrix = TargetEvidenceMatrix.model_validate(raw)
        except (ResearchArtifactError, ValidationError, KeyError, TypeError, ValueError) as exc:
            return TargetEvidenceMatrixEnvelope(
                availability=ResearchAvailability.UNAVAILABLE, error=str(exc)
            )
        return TargetEvidenceMatrixEnvelope(
            availability=ResearchAvailability.AVAILABLE, matrix=matrix
        )

    def _reproducibility(self) -> ReproducibilitySummary | None:
        """Concise reproducibility panel, fully DERIVED from frozen artifacts
        (audit H3 §3-§7).

        Returns None (panel omitted, no claim made) only when the reproduction
        artifact is entirely absent. When the artifact is PRESENT but empty,
        malformed, partial, or failed, this emits typed component statuses and a
        computed overall verdict that can never be PASS on missing/bad evidence.
        No scientific number is hardcoded: every value_display is read from the
        artifact, and `overall_status` is computed worst-of over the components,
        not defaulted."""
        repro = _optional_json(self.repository_root, "results/day10_scientific_reproduction.json")
        if repro is None:
            return None
        if not isinstance(repro, dict):
            # File present but not an object: report malformed, never PASS.
            return _malformed_repro_summary("reproduction artifact is not a JSON object")

        provenance = "results/day10_scientific_reproduction.json"
        components: list[ReproComponent] = [
            _repro_environment(repro, provenance),
            _repro_datasets(repro, provenance),
            _repro_checkpoint_durability(self.repository_root),
            _repro_canonical(repro, provenance),
            _repro_robustness(repro, provenance),
            _repro_n3(repro, provenance),
        ]
        interaction_component, interaction = _repro_interaction(repro, provenance)
        components.append(interaction_component)

        overall_status = _overall_from_components(components)
        declared = repro.get("overall")
        declared_str = declared if isinstance(declared, str) else None
        matches = declared_str == overall_status

        return ReproducibilitySummary(
            overall_status=overall_status,
            overall_declared=declared_str,
            overall_matches_declared=matches,
            environment_scope="RECORDED_ENVIRONMENT_MATCH_FOR_CHECKED_FIELDS",
            independence_caveat=(
                "independent re-evaluation from frozen artifacts on the same recorded stack; "
                "NOT independent-dataset replication"
            ),
            components=components,
            interaction=interaction,
        )

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
            reproducibility=self._reproducibility(),
        )


research_catalog = ResearchCatalog()
