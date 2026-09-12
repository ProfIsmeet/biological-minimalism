"""Stage 5 Final Synthesis: Tables A-F (master prompt Part III, Sections 17-22).

Consolidates ALREADY-ACCEPTED Stage-3/Stage-4 evidence into six final,
machine-readable synthesis tables. Reuses existing artifacts as the source of
truth (results/sensor_value_master_matrix_stage3_complete.json,
results/paper_tables/table2_main_marginal_value_results.json,
results/final_wearable_architecture.json, results/final_claim_ledger.json,
results/stage4_candidate_burden_matrix.json) rather than re-deriving numbers
by hand. No new science; every row cites its governing source artifact.

Writes to results/final_tables/.
"""

from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = REPO_ROOT / "results" / "final_tables"


def _load(rel: str) -> dict:
    return json.loads((REPO_ROOT / rel).read_text(encoding="utf-8"))


def _write(name: str, payload: dict) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUT_DIR / name
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {path}")


# Maps each sensor_value_master_matrix "experiment" row to the final
# architecture decision it corresponds to, citing final_wearable_architecture.json.
ARCHITECTURE_DECISION_BY_EXPERIMENT = {
    "PPG-DaLiA PPG -> +IMU": ("INCLUDED", "wrist_ppg_plus_imu", "Foundational MINIMAL_CORE sensor; governs wrist IMU inclusion."),
    "GalaxyPPG PPG -> +IMU": ("INCLUDED", "wrist_ppg_plus_imu", "External corroboration for wrist IMU inclusion (corrected cohort)."),
    "Sleep-EDF EEG -> +EOG (historical + H1-corrected)": ("INCLUDED", "eog", "Included via Gate E FREEZE_CONDITIONALLY; shares EEG AFE/reference infrastructure."),
    "HMC bounded n=7 EEG -> +EOG (diagnostic only)": ("REVISION_TRIGGER_ONLY", "eog", "Bounded diagnostic feeding EOG's Gate E revision trigger; not itself an inclusion/exclusion test."),
    "ds003838 sparse EEG (AF7/AF8/TP9/TP10) -> full 63ch": ("REVISION_TRIGGER_ONLY", "frontal_eeg", "Bounded diagnostic feeding sparse-EEG Gate E revision trigger; sparse channel count retained conditionally."),
    "PTT one PPG -> second PPG": ("EXCLUDED", "second_site_ppg", "Negative/deprioritized; largest single sensor power contributor (9.018 mW)."),
    "QDE V2 upper-body BioZ -> +leg BioZ": ("EXCLUDED", "leg_bioz", "Aggregate-negative and sensitivity-fragile (7/10 subjects individually favor candidate despite negative aggregate)."),
    "LBNP ECG+pleth -> +thoracic EIS": ("EXCLUDED", "thoracic_bioz_eis", "COMPLETE_MIXED, negative-leaning, sign-reverses without subject 9."),
}


def build_table_a() -> dict:
    """Table A - modality evidence (Part 17)."""
    source = _load("results/sensor_value_master_matrix_stage3_complete.json")
    rows = []
    for row in source["rows"]:
        decision, modality_key, decision_note = ARCHITECTURE_DECISION_BY_EXPERIMENT[row["experiment"]]
        rows.append(
            {
                "modality": row["experiment"],
                "target": row["target"],
                "biological_n_subjects": row["n_subjects"],
                "seeds": row["seeds"],
                "metric": row["metric"],
                "sign_convention": row["sign_convention"],
                "primary_effect": row["exact_result"],
                "heterogeneity_or_sensitivity": row["sensitivity"],
                "negative_finding": row["negative_finding"],
                "replication_state": row["replication_state"],
                "burden_relevance": row["burden_relevance"],
                "safe_claim": row["safe_claim"],
                "architecture_decision": decision,
                "architecture_decision_modality_key": modality_key,
                "architecture_decision_note": decision_note,
            }
        )
    return {
        "table_id": "TABLE_A_MODALITY_EVIDENCE",
        "purpose": "Every governing modality-level experiment: dataset, biological n, controls, primary effect, heterogeneity, classification, replication, and the final architecture decision it maps to.",
        "cross_row_comparability_prohibition": "PROHIBITED: raw metric magnitudes across different targets/datasets/model families are not comparable and must never be ranked against each other (results/target_evidence_matrix.json).",
        "rows": rows,
        "row_count": len(rows),
        "provenance": {
            "source": "results/sensor_value_master_matrix_stage3_complete.json",
            "architecture_decision_source": "results/final_wearable_architecture.json",
        },
    }


def build_table_b() -> dict:
    """Table B - controlled ablations (Part 18). Reuses the existing paper
    table verbatim; this is the same governing data, not a re-derivation."""
    source = _load("results/paper_tables/table2_main_marginal_value_results.json")
    return {
        "table_id": "TABLE_B_CONTROLLED_ABLATIONS",
        "purpose": "Accepted controlled ablation experiments (PPG-DaLiA capacity control, PTT, Sleep-EDF A/B/C, robustness, interaction), including negative results, preserved verbatim.",
        "header": source["header"],
        "rows": source["rows"],
        "provenance": {"source": "results/paper_tables/table2_main_marginal_value_results.json", "upstream": source["provenance"]["source"]},
    }


def build_table_c() -> dict:
    """Table C - external replication (Part 19), explicitly distinguishing
    full external replication / bounded external diagnostic / pending."""
    ledger = _load("results/final_claim_ledger.json")
    claims_by_id = {c["claim_id"]: c for c in ledger["claims"]}
    rows = [
        {
            "modality": "Wrist PPG + IMU -> HR",
            "external_dataset": "GalaxyPPG (corrected cohort)",
            "replication_class": "EXTERNAL_REPLICATION_SUPPORTIVE_WITH_HETEROGENEITY",
            "numeric_support": claims_by_id["galaxy_replication"]["numeric_support"],
            "limitation": claims_by_id["galaxy_replication"]["limitation"],
            "governing_evidence": claims_by_id["galaxy_replication"]["governing_evidence"],
        },
        {
            "modality": "Frontal EEG + EOG -> sleep stage",
            "external_dataset": "HMC (bounded n=7 subset of 151-subject cohort)",
            "replication_class": "BOUNDED_EXTERNAL_DIAGNOSTIC_NOT_A_FULL_REPLICATION",
            "numeric_support": claims_by_id["hmc"]["numeric_support"],
            "limitation": claims_by_id["hmc"]["limitation"],
            "governing_evidence": claims_by_id["hmc"]["governing_evidence"],
        },
        {
            "modality": "Sparse vs full-montage frontal EEG -> sleep stage",
            "external_dataset": "ds003838 (bounded n=3 subset)",
            "replication_class": "BOUNDED_EXTERNAL_DIAGNOSTIC_NOT_A_FULL_REPLICATION",
            "numeric_support": claims_by_id["ds003838"]["numeric_support"],
            "limitation": claims_by_id["ds003838"]["limitation"],
            "governing_evidence": claims_by_id["ds003838"]["governing_evidence"],
        },
        {
            "modality": "HMC full cohort (151 subjects)",
            "external_dataset": "HMC",
            "replication_class": "PENDING_EXTERNAL_REPLICATION_LOWER_PRIORITY_NOT_A_RELEASE_BLOCKER",
            "numeric_support": "N/A - not run.",
            "limitation": "Access working (59/151 downloaded); compute/time-budget limited, not an access blocker.",
            "governing_evidence": ["results/hmc_current_download_inventory.json"],
        },
        {
            "modality": "ds003838 full cohort",
            "external_dataset": "ds003838",
            "replication_class": "PENDING_EXTERNAL_REPLICATION_LOWER_PRIORITY_NOT_A_RELEASE_BLOCKER",
            "numeric_support": "N/A - not run.",
            "limitation": "Requires ~93GB / ~9.4h additional download, not attempted.",
            "governing_evidence": ["results/ds003838_eeg_minimalism_stage3_bounded_diagnostic.json"],
        },
    ]
    return {
        "table_id": "TABLE_C_EXTERNAL_REPLICATION",
        "purpose": "Every external-dataset validity check in this project, explicitly classed as full replication, bounded diagnostic, or pending - never conflated.",
        "rows": rows,
        "provenance": {"source": "results/final_claim_ledger.json"},
    }


def build_table_d() -> dict:
    """Table D - negative / mixed results (Part 20). Preserved, never hidden."""
    ledger = _load("results/final_claim_ledger.json")
    claims_by_id = {c["claim_id"]: c for c in ledger["claims"]}
    negative_mixed_ids = ["second_site_ppg", "leg_bioz", "thoracic_eis", "sleep_interaction"]
    rows = []
    for cid in negative_mixed_ids:
        c = claims_by_id[cid]
        rows.append(
            {
                "claim_id": cid,
                "finding": c["exact_final_safe_wording"],
                "numeric_support": c["numeric_support"],
                "population_scope": c["population_scope"],
                "limitation": c["limitation"],
                "architecture_relevance": c["architecture_relevance"],
                "governing_evidence": c["governing_evidence"],
            }
        )
    return {
        "table_id": "TABLE_D_NEGATIVE_MIXED_RESULTS",
        "purpose": "Negative/mixed/fragile results (second-site PPG, leg BioZ, thoracic EIS, EEG-EOG-respiration interaction), explicitly preserved as scientifically important - never hidden from final presentation.",
        "rows": rows,
        "row_count": len(rows),
        "provenance": {"source": "results/final_claim_ledger.json"},
    }


def build_table_e() -> dict:
    """Table E - final architecture rationale (Part 21), for every
    included/excluded modality."""
    final_arch = _load("results/final_wearable_architecture.json")
    sr = final_arch["science_rationale"]
    rows = []
    for included in sr["included_modalities"]:
        rows.append(
            {
                "modality": included,
                "decision": "INCLUDE",
                "evidence_confidence": sr["evidence_confidence"],
                "rationale": sr["class_description"],
            }
        )
    rows.append(
        {
            "modality": "eog",
            "decision": "INCLUDE",
            "evidence_confidence": sr["evidence_confidence"],
            "rationale": sr["eog_specific_rationale"],
        }
    )
    for key, exclusion in final_arch["exclusion_rationale"].items():
        rows.append(
            {
                "modality": key,
                "decision": "EXCLUDE",
                "reason": exclusion["reason"],
                "prohibited_claim": exclusion["prohibited_claim"],
            }
        )
    return {
        "table_id": "TABLE_E_FINAL_ARCHITECTURE_RATIONALE",
        "purpose": "For every included/excluded modality in the final CORE_PLUS_CONTEXT architecture: evidence, burden, replication, decision, and rationale.",
        "final_architecture": final_arch["selected_class"],
        "rows": rows,
        "provenance": {"source": "results/final_wearable_architecture.json"},
    }


def build_table_f() -> dict:
    """Table F - engineering burden (Part 22), using honest ranges."""
    final_arch = _load("results/final_wearable_architecture.json")
    burden = final_arch["burden_ranges"]
    contact = final_arch["contact_model"]
    return {
        "table_id": "TABLE_F_ENGINEERING_BURDEN",
        "purpose": "Body regions, modules, contacts, power, mass, data rate, topology, and uncertainty for the final CORE_PLUS_CONTEXT architecture. Bounded engineering estimates, not measured/vendor-sourced figures.",
        "body_regions": final_arch["selected_body_regions"],
        "module_topology": final_arch["module_topology"]["topology_class"],
        "modules": final_arch["module_topology"]["module_ids"],
        "battery_topology_selected": final_arch["module_topology"]["battery_topology_selected"],
        "mcu_radio_topology_selected": final_arch["module_topology"]["mcu_radio_topology_selected"],
        "contacts": {
            "total": contact["total_contacts"],
            "per_modality": contact["per_modality_breakdown"],
        },
        "power_mw": burden["power_mw"],
        "mass_g": burden["mass_g"],
        "raw_data_rate_bps": burden["raw_data_rate_bps"],
        "bounded_not_exact_disclosure": burden["bounded_not_exact"],
        "gate_d_status": final_arch["gate_d_status"]["gate_d_burden_completeness"],
        "residual_disclosure_required_at_freeze": final_arch["gate_d_status"]["coordinator_acceptance"]["residual_disclosure_required_at_freeze"],
        "provenance": {"source": "results/final_wearable_architecture.json", "burden_matrix": "results/stage4_candidate_burden_matrix.json"},
    }


def main() -> None:
    _write("table_a_modality_evidence.json", build_table_a())
    _write("table_b_controlled_ablations.json", build_table_b())
    _write("table_c_external_replication.json", build_table_c())
    _write("table_d_negative_mixed_results.json", build_table_d())
    _write("table_e_final_architecture_rationale.json", build_table_e())
    _write("table_f_engineering_burden.json", build_table_f())


if __name__ == "__main__":
    main()
