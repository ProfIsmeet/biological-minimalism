"""Build the target-specific evidence matrix (§18) from frozen artifacts.

Populates ONLY current real, committed evidence:
  - HR / PPG-DaLiA, candidate = synchronized IMU (positive, capacity-confounded)
  - HR / PTT, candidate = second PPG site (heterogeneous negative aggregate)

Does NOT fabricate Sleep-EDF / EOG evidence — that target is listed under `awaiting`.
Raw metric magnitudes across different targets/datasets are non-comparable and are
never ranked. Run with PYTHONPATH=backend:

    PYTHONPATH=backend python ml/build_target_evidence_matrix.py
"""

from __future__ import annotations

import json
from pathlib import Path

from app.schemas.research import (
    CapacityMatchStatus,
    EvidenceStrength,
    MarginalDirection,
    MetricDirectionality,
    MetricKind,
    ResearchResultClass,
    SensitivityStatus,
    TargetEvidenceMatrix,
    TargetEvidenceMatrixEntry,
)

REPO = Path(__file__).resolve().parents[1]
RESULTS = REPO / "results"
OUT_PATH = RESULTS / "target_evidence_matrix.json"


def _load(name: str) -> dict:
    return json.loads((RESULTS / name).read_text(encoding="utf-8"))


def build() -> TargetEvidenceMatrix:
    multiseed = _load("ppg_dalia_imu_multiseed_replication.json")
    agg = multiseed["aggregate"]
    a = agg["model_a"]["mean_mae"]
    b = agg["model_b"]["mean_mae"]
    rel = agg["relative_improvement_B_over_A"]["mean"] * 100

    ppg_dalia = TargetEvidenceMatrixEntry(
        experiment_id="ppg-dalia-imu-ablation",
        target="heart_rate_bpm",
        dataset="PPG-DaLiA",
        candidate="synchronized wrist IMU",
        metric="MAE (bpm)",
        metric_kind=MetricKind.REGRESSION,
        metric_directionality=MetricDirectionality.LOWER_IS_BETTER,
        baseline_configuration_id="model_a_ppg_only",
        candidate_configuration_id="model_b_ppg_plus_imu",
        direction=MarginalDirection.IMPROVED,
        result_class=ResearchResultClass.POSITIVE_MARGINAL_VALUE,
        evidence_strength=EvidenceStrength.STRONGLY_REPLICATED,
        capacity_match_status=CapacityMatchStatus.CONFOUNDED,
        subject_heterogeneity=(
            "Benefit held for all three held-out subjects (S2, S9, S14); "
            "motion-quartile benefit was positive but non-monotonic."
        ),
        class_heterogeneity=None,
        sensitivity_status=SensitivityStatus.AVAILABLE,
        operational_cost_linkage_status="linked (component wrist_imu in pareto_decision_inputs)",
        supported_claim=(
            f"On PPG-DaLiA held-out subjects under the frozen 8s/2s protocol, adding synchronized "
            f"wrist IMU reduced HR MAE {a:.3f}->{b:.3f} bpm (~{rel:.1f}% relative), replicated 5/5 seeds. "
            "The capacity-matched C->B increment (0.776 bpm) is the cleanest comparison."
        ),
        prohibited_claims=[
            "The full A->B benefit is pure IMU sensor value (A->B and A->C are capacity-confounded, ~8k vs ~29k params).",
            "IMU is universally required for heart rate or any other target.",
            "The evaluated sensor set is globally optimal.",
            "Generalizes to astronauts / microgravity or beyond PPG-DaLiA's population.",
        ],
    )

    ptt = TargetEvidenceMatrixEntry(
        experiment_id="ptt-ppg-site-ablation",
        target="heart_rate_bpm",
        dataset="PTT-PPG",
        candidate="second physical PPG site",
        metric="MAE (bpm)",
        metric_kind=MetricKind.REGRESSION,
        metric_directionality=MetricDirectionality.LOWER_IS_BETTER,
        baseline_configuration_id="single_ppg_site",
        candidate_configuration_id="two_ppg_site",
        direction=MarginalDirection.WORSENED,
        result_class=ResearchResultClass.HETEROGENEOUS_MARGINAL_RESULT,
        evidence_strength=EvidenceStrength.REPLICATED_BUT_VARIABLE,
        capacity_match_status=CapacityMatchStatus.UNKNOWN,
        subject_heterogeneity=(
            "Subject behavior is heterogeneous: subject s2 strongly dominates the aggregate "
            "negative direction and descriptively removing s2 reverses the aggregate. The 5 seeds "
            "are optimization replications, NOT five independent populations."
        ),
        class_heterogeneity=None,
        sensitivity_status=SensitivityStatus.PENDING,
        operational_cost_linkage_status="linked (component second_ppg_site in pareto_decision_inputs)",
        supported_claim=(
            "Under the frozen PTT protocol, the single-site PPG baseline beat the two-site candidate "
            "in aggregate HR MAE across 5 optimization seeds — bounded, heterogeneous negative evidence."
        ),
        prohibited_claims=[
            "The second PPG site is universally harmful or useless.",
            "This proves the second PPG site should be removed.",
            "s2 should be removed from the analysis.",
            "PTT and PPG-DaLiA magnitudes are comparable or rankable.",
        ],
    )

    return TargetEvidenceMatrix(
        matrix_id="biological-minimalism-target-evidence-matrix-v1",
        statement=(
            "Target-specific marginal-value evidence for each completed experiment. Only frozen, "
            "committed evidence is included; empty targets are listed under 'awaiting' and are not "
            "fabricated."
        ),
        cross_target_comparability=(
            "PROHIBITED: raw metric magnitudes across different targets/datasets/model families are "
            "not comparable and must never be ranked against each other."
        ),
        entries=[ppg_dalia, ptt],
        awaiting=[
            "Sleep stage / Sleep-EDF, candidate = EOG (classification target) — not yet produced by the ML track.",
            "PPG-DaLiA capacity-matched PPG-only control (A_cap) — required before A->B can be attributed to IMU alone.",
            "PTT leave-one-subject-out sensitivity artifact — required to characterize the s2-dominated heterogeneity.",
        ],
    )


if __name__ == "__main__":
    matrix = build()
    OUT_PATH.write_text(json.dumps(matrix.model_dump(mode="json"), indent=2) + "\n", encoding="utf-8")
    print("Wrote", OUT_PATH.relative_to(REPO))
    print("entries:", len(matrix.entries), "| awaiting:", len(matrix.awaiting))
