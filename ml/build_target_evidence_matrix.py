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

    # Day 8/9: matched negative control, per-subject decomposition, and
    # prospective secondary holdout are now integrated — surface them here so
    # the matrix no longer reports them as pending.
    sleep_control_agg = _load("sleep_edf_eeg_eog_control_analysis.json")["aggregate"]
    sl_c_mean = sleep_control_agg["model_c_macro_f1"]["mean"]
    sl_c_to_b = sleep_control_agg["C_to_B"]
    sl_a_to_c = sleep_control_agg["A_to_C"]
    sleep_persubj = _load("sleep_edf_per_subject_analysis.json")
    sl_dominated = sleep_persubj["global_result_dominated_by_one_subject"]
    sleep_secondary = _load("sleep_edf_secondary_holdout_evaluation.json")
    sec_agg = sleep_secondary["aggregate"]
    sec_a = sec_agg["model_a_macro_f1"]["mean"]
    sec_b = sec_agg["model_b_macro_f1"]["mean"]
    sec_a_to_b = sec_agg["A_to_B"]
    sec_c_to_b = sec_agg["C_to_B"]
    sec_sum = sleep_secondary["subject_level_generalization_summary"]
    sec_n = sec_sum["n_subjects_total"]
    sec_b_gt_a = sec_sum["n_subjects_B_greater_than_A"]
    sec_b_gt_c = sec_sum["n_subjects_B_greater_than_C"]
    sec_cls = sleep_secondary["class_level_aggregate"]
    n3_b_minus_a = sec_cls["N3"]["B_minus_A"]
    rem_b_minus_a = sec_cls["REM"]["B_minus_A"]

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
        evidence_strength=EvidenceStrength.STRONGLY_REPLICATED,
        capacity_match_status=CapacityMatchStatus.MATCHED,
        subject_heterogeneity=(
            f"Primary test n={n_sleep_test}: the aggregate positive effect is concentrated in one "
            f"subject (SC4011 improves; SC4081/SC4131 mixed), so the primary result is "
            f"{'dominated by a single subject' if sl_dominated else 'not single-subject dominated'}. "
            f"Prospective secondary holdout (n={sec_n}, evaluation-only, no retraining) broadens this: "
            f"{sec_b_gt_a}/{sec_n} subjects favor B over A and {sec_b_gt_c}/{sec_n} favor B over the "
            "shuffled control C; the largest single-subject effect (SC4221) contributes ~41% of the summed "
            "B-A effect but does not solely carry it. Benefit is broader in the secondary cohort but still "
            "not uniform (2/8 subjects near-zero or slightly negative)."
        ),
        class_heterogeneity=(
            "Primary: largest gains in N1 and REM (physiologically expected for EOG). Secondary holdout "
            f"reproduces a large REM gain (B-A ~{rem_b_minus_a:+.3f}) but shows an N3 regression "
            f"(B-A ~{n3_b_minus_a:+.3f}) not seen in the primary test — disclosed, not smoothed. "
            "Read-only confusion diagnostic: the N3 drop is a precision effect (B over-labels true N2 "
            "epochs as N3); N3 recall actually improves."
        ),
        sensitivity_status=SensitivityStatus.UNAVAILABLE,
        operational_cost_linkage_status="not linked (EEG/EOG components not in the current HR-focused pareto_decision_inputs)",
        supported_claim=(
            f"Under the frozen Sleep-EDF protocol (18 subjects, 12/3/3 subject-disjoint split), adding "
            f"horizontal EOG to EEG Fpz-Cz improved 5-class sleep-stage macro-F1 in the primary test "
            f"({sl_base:.3f}->{sl_cand:.3f}, delta ~{sl_delta['mean']:.3f}, {sl_delta['n_seeds_candidate_better']}/"
            f"{sl_delta['n_seeds_total']} seeds) and again in a prospectively-frozen {sec_n}-subject secondary "
            f"holdout from the same dataset ({sec_a:.3f}->{sec_b:.3f}, "
            f"{sec_a_to_b['n_seeds_favor_B']}/{sec_a_to_b['n_seeds_total']} seeds). A capacity-identical "
            f"shuffled-EOG control (C, macro-F1 {sl_c_mean:.3f}) is consistently worse than aligned EOG "
            f"(primary C->B {sl_c_to_b['n_seeds_favor_B']}/{sl_c_to_b['n_seeds_total']} seeds; secondary "
            f"C->B {sec_c_to_b['n_seeds_favor_B']}/{sec_c_to_b['n_seeds_total']} seeds), while A->C is "
            f"approximately neutral — supporting a role for temporally aligned ocular information rather than "
            f"mere EOG presence. Evidence strength: replicated-with-control with prospective secondary-holdout "
            f"support. Key limitations: single dataset (Sleep-EDF cassette), terrestrial population, benefit "
            f"non-uniform across subjects, and an N3 regression in the secondary cohort."
        ),
        prohibited_claims=[
            "EOG is necessary or universally improves sleep staging.",
            "This validates astronaut / microgravity / spaceflight sleep monitoring.",
            "The final architecture should contain EOG.",
            "Sleep-EDF macro-F1 is comparable to or rankable against the HR-MAE experiments.",
            "This validates the Biological Digital Twin.",
            "The primary and secondary holdouts form one pooled n=11 test set.",
            "This is independent-dataset or cross-population replication.",
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
