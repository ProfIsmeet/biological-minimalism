"""Stage 5 Final Synthesis: the final project claim ledger (master prompt
Part II, Sections 13-16).

Merges the Stage-4 Science Owner claim ledger (results/stage4_science_claim_ledger.json,
14 claims) with the Integration Owner's closure claim updates
(results/stage4_final_closure_claim_updates.json, which supersedes ONLY the
`final_architecture` and `pareto` claim_ids) and adds three claim areas that
were governed by prose docs rather than a formal claim_id
(sensor_minimalism_framing, engineering_burden, robustness_fault_injection),
synthesized strictly from existing accepted evidence - no new science, no new
numbers not already present in the cited source artifacts.

Adds three fields the base ledger does not carry per claim: population_scope,
replication_status, architecture_relevance - and jury_safe_wording /
paper_safe_wording, which this project keeps IDENTICAL to exact_safe_wording
(the ledger wording is already dual-purpose safe; no separate loosened
variant is manufactured for either audience).
"""

from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PATH = REPO_ROOT / "results" / "final_claim_ledger.json"

SCIENCE_LEDGER_PATH = "results/stage4_science_claim_ledger.json"
CLOSURE_UPDATES_PATH = "results/stage4_final_closure_claim_updates.json"


def _load(rel: str) -> dict:
    return json.loads((REPO_ROOT / rel).read_text(encoding="utf-8"))


# Additional per-claim metadata not present in the base ledger, grounded in
# the same governing evidence artifacts already cited by that claim.
ADDITIONAL_METADATA: dict[str, dict[str, str]] = {
    "ppg_plus_imu": {
        "population_scope": "PPG-DaLiA n=15 subjects (5/5 seeds) + GalaxyPPG corrected cohort n=18/24 eligible participants.",
        "replication_status": "EXTERNALLY_REPLICATED_SUPPORTIVE_WITH_HETEROGENEITY",
        "architecture_relevance": "INCLUDED_MODALITY_WRIST_PPG_PLUS_IMU",
    },
    "old_ppg_imu_headline_20_6_23_percent": {
        "population_scope": "PPG-DaLiA n=15, single uncontrolled comparison (Model A 8,065 params vs Model B 28,865-29,089 params).",
        "replication_status": "HISTORICAL_ONLY_NOT_CURRENT_GOVERNING_EVIDENCE",
        "architecture_relevance": "NOT_USED_CAPACITY_CONFOUNDED_SUPERSEDED_BY_ppg_plus_imu",
    },
    "galaxy_replication": {
        "population_scope": "GalaxyPPG corrected cohort: 18/24 eligible participants (6 excluded for a reference-ECG signal-quality defect).",
        "replication_status": "EXTERNAL_REPLICATION_SUPPORTIVE_CORRECTED_COHORT_PLUS_BOUNDED_SINGLE_FOLD_DIAGNOSTIC",
        "architecture_relevance": "SUPPORTS_INCLUSION_OF_WRIST_IMU",
    },
    "eog_incremental_value": {
        "population_scope": "Sleep-EDF primary + shuffled-EOG control (5 seeds) + secondary holdout n=8 prospective, zero retraining.",
        "replication_status": "SAME_DATASET_CONTROLLED_SUPPORT_PLUS_BOUNDED_SECONDARY_HOLDOUT_NOT_AN_EXTERNAL_COHORT",
        "architecture_relevance": "INCLUDED_MODALITY_HEAD_EOG_GATE_E_CONDITIONAL_FREEZE",
    },
    "sleep_interaction": {
        "population_scope": "Sleep-EDF EEG+EOG+Respiration factorial interaction experiment, same cohort as the primary Sleep-EDF result.",
        "replication_status": "PENDING_SINGLE_RUN_MIXED_SIGN_NOT_STABLE",
        "architecture_relevance": "NOT_USED_FOR_ARCHITECTURE_DECISION_INSUFFICIENT_TO_JUSTIFY_A_JOINT_EOG_RESPIRATION_MODULE",
    },
    "second_site_ppg": {
        "population_scope": "n=4 held-out test subjects.",
        "replication_status": "NOT_REPLICATED_SINGLE_DATASET_NEGATIVE_AND_SUBJECT_FRAGILE",
        "architecture_relevance": "EXCLUDED_MODALITY_SECOND_SITE_PPG",
    },
    "leg_bioz": {
        "population_scope": "QDE V2 n=10 subjects.",
        "replication_status": "NOT_REPLICATED_SINGLE_DATASET_HETEROGENEOUS",
        "architecture_relevance": "EXCLUDED_MODALITY_LEG_BIOZ",
    },
    "thoracic_eis": {
        "population_scope": "LBNP corrected protocol-compliant cohort: n=12/16 eligible subjects.",
        "replication_status": "NOT_REPLICATED_SINGLE_PROTOCOL_MIXED_SIGN_SUBJECT_9_REVERSES_AGGREGATE",
        "architecture_relevance": "EXCLUDED_MODALITY_THORACIC_BIOZ_EIS",
    },
    "hmc": {
        "population_scope": "Bounded n=7 diagnostic subset (59 EDF downloaded, 52 SHA256-verified, 1 partial); full cohort is 151 subjects, not yet trained.",
        "replication_status": "BOUNDED_DIAGNOSTIC_PENDING_FULL_COHORT",
        "architecture_relevance": "GATE_E_REVISION_TRIGGER_FOR_EOG_INCLUSION",
    },
    "ds003838": {
        "population_scope": "Bounded n=3 diagnostic subset (sub-032/033/034); full cohort requires ~93GB additional download, not attempted.",
        "replication_status": "BOUNDED_DIAGNOSTIC_PENDING_FULL_COHORT",
        "architecture_relevance": "GATE_E_REVISION_TRIGGER_FOR_SPARSE_EEG_CHANNEL_COUNT",
    },
    "digital_twin": {
        "population_scope": "N/A - architecture-only proposal, not trained on any subject data.",
        "replication_status": "NOT_APPLICABLE_UNTRAINED_UNVALIDATED",
        "architecture_relevance": "ARCHITECTURE_DECISION_IS_INDEPENDENT_OF_AND_DOES_NOT_IMPLY_DIGITAL_TWIN_VALIDATION",
    },
    "final_architecture": {
        "population_scope": "Aggregates all governing per-modality evidence populations listed under each modality's own claim area above.",
        "replication_status": "MIXED_PER_MODALITY_SEE_INDIVIDUAL_MODALITY_CLAIMS",
        "architecture_relevance": "IS_THE_ARCHITECTURE_DECISION_OF_RECORD",
    },
    "pareto": {
        "population_scope": "N/A - burden/evidence axes compared across 4 candidate architecture classes, not a subject population.",
        "replication_status": "NOT_APPLICABLE_ANALYTICAL_METHOD",
        "architecture_relevance": "GOVERNS_THE_ARCHITECTURE_SELECTION_METHODOLOGY",
    },
    "astronaut_microgravity_applicability": {
        "population_scope": "All governing datasets are terrestrial (healthy or patient populations); LBNP is a terrestrial hypovolemia protocol-analog, not spaceflight data.",
        "replication_status": "NOT_APPLICABLE_NO_SPACEFLIGHT_DATA_EXISTS_IN_THIS_PROJECT",
        "architecture_relevance": "CONTEXTUAL_LIMITATION_APPLIES_TO_THE_ENTIRE_ARCHITECTURE_AND_EVERY_CLAIM_ABOVE",
    },
}

# New claim areas required by master prompt Part 14 that were governed by
# prose docs rather than a formal Stage-4 claim_id. Synthesized strictly from
# the cited governing_evidence artifacts.
NEW_CLAIM_AREAS: list[dict] = [
    {
        "claim_id": "sensor_minimalism_framing",
        "exact_safe_wording": (
            "Biological Minimalism evaluates whether sensing modalities provide measurable incremental value "
            "after controlling for model capacity, temporal correspondence, subject separation, heterogeneity, "
            "and physical burden. Some modalities retain value under stronger controls and external replication, "
            "while others become mixed, negative, fragile, or deprioritized."
        ),
        "strength": "SAFE_FRAMING_PRINCIPLE",
        "governing_evidence": [
            "results/sensor_value_master_matrix_stage3_complete.json",
            "results/target_evidence_matrix.json",
            "docs/SENSOR_MARGINAL_VALUE_METHODOLOGY.md",
        ],
        "relevant_numeric_result": "N/A - methodological framing statement, not a numeric result.",
        "scope_limitation": "Applies across the modalities tested in this project; not a universal claim about sensing minimalism in general. No cross-row scoring or aggregation across targets/datasets is performed (each row uses its own metric/sign convention).",
        "prohibited_stronger_wording": "'We proved four sensors are enough.'; any wording asserting a single minimal sufficient sensor set exists universally.",
        "population_scope": "N/A - framing principle governing interpretation of all experiments in this project.",
        "replication_status": "N/A - framing principle, not itself a replicated result.",
        "architecture_relevance": "GOVERNS_ENTIRE_PROJECT_INTERPRETATION_AND_MUST_NOT_BE_REPLACED_BY_A_STRONGER_CLAIM",
    },
    {
        "claim_id": "engineering_burden",
        "exact_safe_wording": (
            "Reference engineering burden estimates (power, mass, data rate, contact/electrode count) for the "
            "final architecture are bounded engineering estimates (component-datasheet or class-level, Tier 0-2), "
            "not measured, vendor-sourced, or flight-qualified figures. Ranges reflect explicit topology and "
            "assumption uncertainty and are not yet collapsed to point estimates."
        ),
        "strength": "SAFE_WITH_LIMITATION",
        "governing_evidence": [
            "results/final_wearable_architecture.json",
            "results/stage4_candidate_burden_matrix.json",
            "results/reference_power_budget_day11_part2.json",
            "results/reference_mass_readiness_day11_part2.json",
            "results/reference_bom_readiness_day11_part2.json",
            "results/reference_data_rate_budget_day11.json",
            "docs/STAGE4_ENGINEERING_SAFE_UNSAFE_CLAIMS.md",
        ],
        "relevant_numeric_result": (
            "Selected (per-module) topology battery-side power 9.937201 mW vs alternative single-shared "
            "battery-side 5.644949 mW (not selected); battery-only mass 8.763 g (3 x 2.921 g); contacts 9 "
            "most-likely (range 9-14); base-topology raw data rate ~19.6 kbps excluding the excluded second-PPG-site branch."
        ),
        "scope_limitation": (
            "Excludes PCB/enclosure/attachment/wiring mass beyond battery cells (module-level total mass is "
            "SYSTEM_MASS_NOT_READY); no vendor-specific parts selected (class-level components only, e.g. "
            "'Cortex-M4F BLE SoC class'); no target operating duration exists in the project so battery capacity "
            "is held at a frozen 150 mAh/module reference rather than duration-derived."
        ),
        "prohibited_stronger_wording": "'This BOM is final/flight-ready'; 'the final wearable weighs 30.5 g'; presenting any burden figure as measured, guaranteed, or vendor-sourced.",
        "population_scope": "N/A - engineering estimate, not a subject population.",
        "replication_status": "NOT_APPLICABLE_ENGINEERING_ESTIMATE_NOT_A_SCIENTIFIC_REPLICATION_CLAIM",
        "architecture_relevance": "QUANTIFIES_THE_BURDEN_AXIS_USED_IN_THE_PARETO_ANALYSIS_AND_GATE_D",
    },
    {
        "claim_id": "robustness_fault_injection",
        "exact_safe_wording": (
            "Under the implemented first-batch-calibrated IMU perturbation, aggregate held-out subject HR error "
            "changed very little; zero/frozen IMU diagnostics confirm the model depends on IMU input; and "
            "independent native-sample loss primarily caused the current contiguous-window pipeline to fail closed."
        ),
        "strength": "SAFE_WITH_LIMITATION",
        "governing_evidence": [
            "results/ppg_dalia_fault_robustness.json",
            "results/day10_ppg_dalia_fault_robustness_reproduction.json",
            "docs/PHASE5_ROBUSTNESS_AUDIT_ADDENDUM.md",
        ],
        "relevant_numeric_result": (
            "Zero/frozen IMU diagnostic: +0.95 bpm MAE vs clean baseline; 114/114 fault-injection conditions "
            "reproduced within 1e-4 bpm tolerance from the frozen checkpoint (max observed difference 7.6e-6 bpm, "
            "float32 rounding)."
        ),
        "scope_limitation": (
            "Single held-out subject (S14) across 114 fault-injection conditions; this is a re-evaluation from a "
            "frozen checkpoint on the same dataset, not independent-dataset replication. Undefined MAE/RMSE for "
            "zero-survivor packet-loss conditions is kept N/A, never fabricated."
        ),
        "prohibited_stronger_wording": (
            "'robustness to universally severe IMU corruption'; 'generic IMU irrelevance'; 'automatic neural-"
            "network fault detection'; 'predictive confidence or calibrated uncertainty'; 'fault tolerance'; "
            "'population-level robustness'; 'astronaut or microgravity robustness'."
        ),
        "population_scope": "n=1 held-out subject (S14), 114 fault-injection conditions.",
        "replication_status": "REPRODUCED_FROM_FROZEN_CHECKPOINT_114_OF_114_WITHIN_TOLERANCE_NOT_INDEPENDENT_DATASET_REPLICATION",
        "architecture_relevance": "INFORMS_CONFIDENCE_IN_THE_WRIST_PPG_PLUS_IMU_MODEL_UNDER_SENSOR_FAULTS_NOT_ITSELF_AN_ARCHITECTURE_INCLUSION_CRITERION",
    },
]


def _finalize_claim(claim: dict, supersedes_note: dict | None = None) -> dict:
    meta = ADDITIONAL_METADATA.get(claim["claim_id"])
    if meta is None:
        # New claim areas already carry the extra fields directly.
        meta = {
            "population_scope": claim.pop("population_scope"),
            "replication_status": claim.pop("replication_status"),
            "architecture_relevance": claim.pop("architecture_relevance"),
        }
    entry = {
        "claim_id": claim["claim_id"],
        "exact_final_safe_wording": claim["exact_safe_wording"],
        "evidence_strength": claim["strength"],
        "governing_evidence": claim["governing_evidence"],
        "numeric_support": claim.get(
            "relevant_numeric_result",
            "N/A - this claim is a decision/methodology synthesis, not a single numeric result; see governing_evidence.",
        ),
        "limitation": claim["scope_limitation"],
        "population_scope": meta["population_scope"],
        "replication_status": meta["replication_status"],
        "architecture_relevance": meta["architecture_relevance"],
        "jury_safe_wording": claim["exact_safe_wording"],
        "paper_safe_wording": claim["exact_safe_wording"],
        "prohibited_stronger_wording": claim["prohibited_stronger_wording"],
        "wording_identical_across_audiences_note": (
            "jury_safe_wording and paper_safe_wording are intentionally identical to exact_final_safe_wording: "
            "the ledger wording is already dual-purpose safe; no separate loosened variant is manufactured for "
            "either audience."
        ),
    }
    if supersedes_note is not None:
        entry["supersedes"] = supersedes_note
    return entry


def build() -> dict:
    science_ledger = _load(SCIENCE_LEDGER_PATH)
    closure_updates = _load(CLOSURE_UPDATES_PATH)

    updates_by_id = {c["claim_id"]: c for c in closure_updates["updated_claims"]}

    final_claims = []
    for claim in science_ledger["claims"]:
        claim_id = claim["claim_id"]
        if claim_id in updates_by_id:
            updated = updates_by_id[claim_id]
            final_claims.append(_finalize_claim(updated, supersedes_note=updated["supersedes"]))
        else:
            final_claims.append(_finalize_claim(claim))

    for new_claim in NEW_CLAIM_AREAS:
        final_claims.append(_finalize_claim(dict(new_claim)))

    required_claim_ids = {
        "sensor_minimalism_framing", "ppg_plus_imu", "galaxy_replication", "eog_incremental_value",
        "hmc", "ds003838", "second_site_ppg", "leg_bioz", "thoracic_eis", "final_architecture",
        "pareto", "engineering_burden", "robustness_fault_injection", "digital_twin",
        "astronaut_microgravity_applicability",
    }
    present_ids = {c["claim_id"] for c in final_claims}
    missing = required_claim_ids - present_ids
    if missing:
        raise SystemExit(f"REFUSING TO WRITE: master-prompt-required claim areas missing: {missing}")

    return {
        "artifact_id": "biological-minimalism-stage5-final-claim-ledger-v1",
        "schema_version": "1.0.0",
        "sprint": "STAGE5_FINAL_SYNTHESIS_AND_RELEASE",
        "generated_role": "FINAL_SYNTHESIS_AND_RELEASE_OWNER",
        "purpose": (
            "The Stage-5 final project claim contract: every claim area required by the Stage-5 master prompt "
            "Part 14, with exact final safe wording, evidence strength, governing evidence, numeric support, "
            "limitation, population scope, replication status, architecture relevance, jury-safe wording, "
            "paper-safe wording, and prohibited stronger wording. Merged from "
            f"{SCIENCE_LEDGER_PATH} (base, 14 claims) with {CLOSURE_UPDATES_PATH} (supersedes final_architecture "
            "and pareto only) plus 3 new claim areas synthesized strictly from existing accepted evidence docs "
            "(sensor_minimalism_framing, engineering_burden, robustness_fault_injection). No new science; no "
            "claim strengthened beyond what its governing_evidence supports."
        ),
        "central_scientific_message": (
            "Biological Minimalism evaluates whether sensing modalities provide measurable incremental value "
            "after controlling for model capacity, temporal correspondence, subject separation, heterogeneity, "
            "and physical burden. Some modalities retain value under stronger controls and external replication, "
            "while others become mixed, negative, fragile, or deprioritized."
        ),
        "central_scientific_message_prohibited_replacement": "'We proved four sensors are enough.'",
        "claims": final_claims,
        "source_artifacts": {
            "base_science_ledger": SCIENCE_LEDGER_PATH,
            "closure_updates": CLOSURE_UPDATES_PATH,
        },
        "status": "STAGE5_FINAL_CLAIM_LEDGER_REPORTED_COMPLETE_PENDING_INDEPENDENT_AUDIT",
    }


if __name__ == "__main__":
    output = build()
    OUTPUT_PATH.write_text(json.dumps(output, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {OUTPUT_PATH} ({len(output['claims'])} claim areas)")
