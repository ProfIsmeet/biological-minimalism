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

    capacity = _load("ppg_dalia_capacity_control.json")
    cap_cmp = capacity["primary_comparisons"]
    a_minus_acap = cap_cmp["baseline_A_candidate_Acap"]["mean"]
    acap_minus_b = cap_cmp["baseline_Acap_candidate_B"]["mean"]
    c_minus_b = cap_cmp["baseline_C_candidate_B"]["mean"]
    fraction_capacity = a_minus_acap / (a_minus_acap + acap_minus_b) * 100

    ptt_sens = _load("ptt_sensitivity_analysis.json")
    n_ptt_subjects = len(ptt_sens["held_out_subjects"])
    s2_delta = ptt_sens["s2_dependence"]["magnitude_of_s2_influence_on_delta"]

    sleep = _load("sleep_edf_eeg_eog_ablation.json")
    sleep_agg = sleep["aggregate"]
    sl_base = sleep_agg["baseline_macro_f1"]["mean"]
    sl_cand = sleep_agg["candidate_macro_f1"]["mean"]
    sl_delta = sleep_agg["delta_candidate_minus_baseline"]
    n_sleep_test = len(sleep["frozen_protocol"]["subject_split"]["test"])

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
            f"wrist IMU reduced HR MAE {a:.3f}->{b:.3f} bpm (~{rel:.1f}% relative), replicated 5/5 seeds "
            "(original protocol). A supplemental capacity-matched PPG-only control (A_cap) is now "
            f"available: ~{fraction_capacity:.0f}% of the original A->B gap was recovered by capacity/"
            f"architecture alone, leaving a smaller capacity-controlled IMU-information benefit "
            f"(A_cap->B ~{acap_minus_b:.3f} bpm, 5/5 seeds). The already-capacity-matched C->B increment "
            f"(~{c_minus_b:.3f} bpm, 5/5 seeds) remains the cleanest comparison. Key limitation: the "
            "effect is substantially smaller after architecture/capacity control."
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
            f"Subject behavior is heterogeneous across only n={n_ptt_subjects} held-out subjects "
            "(2 of 4 favor the candidate): subject s2 strongly dominates the aggregate negative "
            f"direction and descriptively excluding s2 flips the aggregate direction (delta shift "
            f"~{s2_delta:.2f} bpm). The 5 seeds are optimization replications, NOT five independent "
            "populations. s2 is never removed from the frozen primary result."
        ),
        class_heterogeneity=None,
        sensitivity_status=SensitivityStatus.AVAILABLE,
        operational_cost_linkage_status="linked (component second_ppg_site in pareto_decision_inputs)",
        supported_claim=(
            "Under the frozen PTT protocol, the single-site PPG baseline beat the two-site candidate "
            "in aggregate HR MAE across 5 optimization seeds — bounded, heterogeneous negative evidence. "
            f"Key limitation: n={n_ptt_subjects} held-out subjects, and the aggregate direction is "
            "s2-sensitive."
        ),
        prohibited_claims=[
            "The second PPG site is universally harmful or useless.",
            "This proves the second PPG site should be removed.",
            "s2 should be removed from the analysis.",
            "PTT and PPG-DaLiA magnitudes are comparable or rankable.",
        ],
    )

    sleep_edf = TargetEvidenceMatrixEntry(
        experiment_id="sleep-edf-eeg-eog-ablation",
        target="sleep_stage_5class",
        dataset="Sleep-EDF",
        candidate="horizontal EOG added to EEG",
        metric="macro-F1",
        metric_kind=MetricKind.CLASSIFICATION,
        metric_directionality=MetricDirectionality.HIGHER_IS_BETTER,
        baseline_configuration_id="eeg_fpz_cz_only",
        candidate_configuration_id="eeg_fpz_cz_plus_eog_horizontal",
        direction=MarginalDirection.IMPROVED,
        result_class=ResearchResultClass.POSITIVE_MARGINAL_VALUE,
        evidence_strength=EvidenceStrength.REPLICATED_BUT_VARIABLE,
        capacity_match_status=CapacityMatchStatus.MATCHED,
        subject_heterogeneity=(
            f"Only {n_sleep_test} held-out test subjects; per-subject decomposition not yet computed."
        ),
        class_heterogeneity=(
            "Largest gains in N1 and REM (physiologically expected for EOG); no class regresses "
            "(N2/N3 approximately flat). Balanced accuracy improved in 5/5 seeds."
        ),
        sensitivity_status=SensitivityStatus.UNAVAILABLE,
        operational_cost_linkage_status="not linked (EEG/EOG components not in the current HR-focused pareto_decision_inputs)",
        supported_claim=(
            f"Under the frozen Sleep-EDF protocol (18 subjects, 12/3/3 subject-disjoint split), adding "
            f"horizontal EOG to EEG Fpz-Cz produced a modest positive result: macro-F1 "
            f"{sl_base:.3f}->{sl_cand:.3f} (delta ~{sl_delta['mean']:.3f}), with the candidate better in "
            f"{sl_delta['n_seeds_candidate_better']}/{sl_delta['n_seeds_total']} training seeds. Preliminary "
            f"evidence (mean effect comparable to its seed-to-seed SD). Key limitations: only {n_sleep_test} "
            "held-out test subjects, no shuffled-EOG negative control, no per-subject breakdown yet, single "
            "dataset, terrestrial population."
        ),
        prohibited_claims=[
            "EOG is necessary or universally improves sleep staging.",
            "This validates astronaut / microgravity / spaceflight sleep monitoring.",
            "The final architecture should contain EOG.",
            "Sleep-EDF macro-F1 is comparable to or rankable against the HR-MAE experiments.",
            "This validates the Biological Digital Twin.",
        ],
    )

    return TargetEvidenceMatrix(
        matrix_id="biological-minimalism-target-evidence-matrix-v1",
        statement=(
            "Target-specific marginal-value evidence for each completed experiment. Only frozen, "
            "committed evidence is included; the three entries span distinct targets/datasets/metrics "
            "and are NOT ranked against one another."
        ),
        cross_target_comparability=(
            "PROHIBITED: raw metric magnitudes across different targets/datasets/model families are "
            "not comparable and must never be ranked against each other (e.g. MAE vs macro-F1)."
        ),
        entries=[ppg_dalia, ptt, sleep_edf],
        awaiting=[],
    )


if __name__ == "__main__":
    matrix = build()
    OUT_PATH.write_text(json.dumps(matrix.model_dump(mode="json"), indent=2) + "\n", encoding="utf-8")
    print("Wrote", OUT_PATH.relative_to(REPO))
    print("entries:", len(matrix.entries), "| awaiting:", len(matrix.awaiting))
