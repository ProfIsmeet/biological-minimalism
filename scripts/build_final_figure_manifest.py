"""Stage 5 Final Synthesis: final figure-data export catalog (master prompt
Part IV, Sections 23-25).

Catalogs the 9 existing Stage-4 figure-data exports (results/figure_sources/
figure_A..I) verbatim and adds 5 NEW figure-data exports for figure types the
master prompt lists that have no existing export yet: GalaxyPPG external
replication (J), negative/mixed modality summary (K), science-vs-burden
architecture comparison (L), Pareto map (M), and final architecture diagram
data (N). Every field is read programmatically from already-accepted source
artifacts - no hand-edited plot values, no new numbers.

Writes results/final_figure_manifest.json (catalog + provenance) and new
per-figure JSON files alongside the existing ones in results/figure_sources/.
"""

from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
FIGURE_DIR = REPO_ROOT / "results" / "figure_sources"
MANIFEST_PATH = REPO_ROOT / "results" / "final_figure_manifest.json"

EXISTING_FIGURES = [
    ("figure_A_ppg_capacity_control.json", "PPG-DaLiA controlled IMU result"),
    ("figure_B_ppg_subject_activity_heterogeneity.json", "PPG-DaLiA controlled IMU result (subject/activity heterogeneity)"),
    ("figure_C_ptt_subject_heterogeneity.json", "Negative/mixed modality evidence (second-site PPG)"),
    ("figure_D_sleep_primary_abc.json", "Sleep/EOG result"),
    ("figure_E_sleep_secondary_abc.json", "Sleep/EOG result (secondary holdout)"),
    ("figure_F_sleep_subject_level_b_minus_a.json", "Sleep/EOG result (subject-level)"),
    ("figure_G_sleep_class_level_b_minus_a.json", "Sleep/EOG result (class-level)"),
    ("figure_H_robustness.json", "Robustness/fault-injection summary"),
    ("figure_I_interaction.json", "Negative/mixed modality evidence (EEG-EOG-respiration interaction)"),
]


def _load(rel: str) -> dict:
    return json.loads((REPO_ROOT / rel).read_text(encoding="utf-8"))


def _write_figure(name: str, payload: dict) -> None:
    path = FIGURE_DIR / name
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {path}")


def build_figure_j_galaxyppg() -> dict:
    galaxy = _load("results/galaxyppg_corrected_full_cv_result.json")
    return {
        "title": "GalaxyPPG (corrected cohort): external replication of wrist PPG+IMU HR benefit",
        "metric": "delta MAE (bpm), positive = candidate (B) better",
        "sample_unit": "participant (n=18 eligible of 24; 6 excluded for a reference-ECG signal-quality defect)",
        "uncertainty_meaning": "sd_sample_ddof1 across the 18-participant aggregate; per-participant values also shown to disclose heterogeneity",
        "claim_boundary": "This is external-dataset replication support with real participant heterogeneity (6/18 subjects disfavor B on A_to_B) - never present as uniform or as 24/24 subject cohort.",
        "series": {
            "per_subject_A_to_B": galaxy["heterogeneity_and_sensitivity"]["per_subject_A_to_B_sorted"],
            "per_subject_C_to_B": galaxy["heterogeneity_and_sensitivity"]["per_subject_C_to_B_sorted"],
        },
        "aggregate": galaxy["aggregate_across_all_18_eligible_subjects"],
        "provenance": ["results/galaxyppg_corrected_full_cv_result.json"],
    }


def build_figure_k_negative_mixed_summary() -> dict:
    table_d = _load("results/final_tables/table_d_negative_mixed_results.json")
    return {
        "title": "Negative / mixed modality evidence summary",
        "metric": "qualitative classification per modality (see numeric_support for governing numbers)",
        "sample_unit": "modality (n=4: second-site PPG, leg BioZ, thoracic EIS, EEG-EOG-respiration interaction)",
        "uncertainty_meaning": "each modality's own numeric_support field carries its governing sd/n; no cross-modality aggregation is performed",
        "claim_boundary": "These results must remain visible in any final presentation - never omitted to present a cleaner minimalism story.",
        "series": {row["claim_id"]: {"finding": row["finding"], "numeric_support": row["numeric_support"]} for row in table_d["rows"]},
        "provenance": ["results/final_tables/table_d_negative_mixed_results.json"],
    }


def build_figure_l_science_vs_burden() -> dict:
    burden_matrix = _load("results/stage4_candidate_burden_matrix.json")
    pareto = _load("results/stage4_formal_pareto_analysis.json")
    series = {}
    for cls in burden_matrix["classes"]:
        power = cls["power_range_mw"]
        battery_side = (
            power["per_module_mcu_radio"]["battery_side"]
            if "per_module_mcu_radio" in power
            else power["single_shared_mcu_radio"]["battery_side"]
        )
        series[cls["class_id"]] = {
            "module_count": cls["module_count"],
            "total_contacts_most_likely": cls["total_contacts"]["most_likely"],
            "battery_side_power_mw": battery_side,
            "is_pareto_relevant": cls["class_id"] in pareto["pareto_relevant_set"],
        }
    return {
        "title": "Science-vs-burden architecture comparison across 4 candidate classes",
        "metric": "module count / contacts / battery-side power (mW) per candidate class",
        "sample_unit": "candidate architecture class (n=4: MINIMAL_CORE, CORE_PLUS_CONTEXT, EVIDENCE_EXTENDED, EXPERIMENTAL_EXTENDED)",
        "uncertainty_meaning": "each class's figures are bounded engineering estimates from results/stage4_candidate_burden_matrix.json, not measured",
        "claim_boundary": "Burden strictly increases class-to-class; do not visually imply this ordering also ranks scientific value - see figure_M_pareto_map for the Pareto relationship.",
        "series": series,
        "provenance": ["results/stage4_candidate_burden_matrix.json", "results/stage4_formal_pareto_analysis.json"],
    }


def build_figure_m_pareto_map() -> dict:
    pareto = _load("results/stage4_formal_pareto_analysis.json")
    return {
        "title": "Formal Pareto dominance map",
        "metric": "pairwise dominance verdict (categorical, not a score)",
        "sample_unit": "candidate architecture class pair",
        "uncertainty_meaning": "not applicable - this is a categorical dominance analysis, no single collapsed score exists",
        "claim_boundary": "MUST NOT be rendered as a ranked list or single axis implying a unique winner. MINIMAL_CORE and CORE_PLUS_CONTEXT are both Pareto-relevant (non-dominated); Coordinator selection of CORE_PLUS_CONTEXT is a judgment call within that set, not a mathematical result.",
        "pareto_relevant_set": pareto["pareto_relevant_set"],
        "potentially_dominated_set": pareto["potentially_dominated_set"],
        "pairwise_dominance_analysis": pareto["pairwise_dominance_analysis"],
        "coordinator_selected_architecture": pareto["coordinator_selected_architecture"],
        "coordinator_selection_is_not_mathematical_dominance": pareto["coordinator_selection_is_not_mathematical_dominance"],
        "no_unique_pareto_winner": pareto["no_unique_pareto_winner"],
        "provenance": ["results/stage4_formal_pareto_analysis.json"],
    }


def build_figure_n_final_architecture() -> dict:
    final_arch = _load("results/final_wearable_architecture.json")
    return {
        "title": "Final wearable architecture: CORE_PLUS_CONTEXT",
        "metric": "structural diagram data (body regions, modules, modalities, contacts) - not a statistical figure",
        "sample_unit": "not applicable",
        "uncertainty_meaning": "burden figures shown are bounded engineering estimates (results/final_wearable_architecture.json burden_ranges), not measured",
        "claim_boundary": "Must display the conditional-freeze disclosures for EOG and sparse EEG (Gate E) alongside the diagram - never render as an unconditionally final architecture.",
        "selected_class": final_arch["selected_class"],
        "selected_body_regions": final_arch["selected_body_regions"],
        "module_topology": final_arch["module_topology"],
        "contact_model": final_arch["contact_model"],
        "burden_ranges": final_arch["burden_ranges"],
        "gate_d_status": final_arch["gate_d_status"]["gate_d_burden_completeness"],
        "gate_e_decisions": final_arch["gate_e_decisions"],
        "provenance": ["results/final_wearable_architecture.json"],
    }


def main() -> None:
    new_figures = {
        "figure_J_galaxyppg_external_replication.json": build_figure_j_galaxyppg(),
        "figure_K_negative_mixed_summary.json": build_figure_k_negative_mixed_summary(),
        "figure_L_science_vs_burden_comparison.json": build_figure_l_science_vs_burden(),
        "figure_M_pareto_map.json": build_figure_m_pareto_map(),
        "figure_N_final_architecture_diagram.json": build_figure_n_final_architecture(),
    }
    for name, payload in new_figures.items():
        _write_figure(name, payload)

    catalog = []
    for name, figure_type in EXISTING_FIGURES:
        data = _load(f"results/figure_sources/{name}")
        catalog.append(
            {
                "figure_file": f"results/figure_sources/{name}",
                "figure_type": figure_type,
                "title": data["title"],
                "status": "EXISTING_STAGE4_FIGURE_REUSED_VERBATIM",
                "provenance": data["provenance"],
            }
        )
    figure_type_map = {
        "figure_J_galaxyppg_external_replication.json": "GalaxyPPG external replication",
        "figure_K_negative_mixed_summary.json": "Negative/mixed modality evidence",
        "figure_L_science_vs_burden_comparison.json": "Science-vs-burden architecture comparison",
        "figure_M_pareto_map.json": "Pareto map / candidate comparison",
        "figure_N_final_architecture_diagram.json": "Final wearable architecture",
    }
    for name, payload in new_figures.items():
        catalog.append(
            {
                "figure_file": f"results/figure_sources/{name}",
                "figure_type": figure_type_map[name],
                "title": payload["title"],
                "status": "NEW_STAGE5_FIGURE_DERIVED_FROM_ACCEPTED_DATA",
                "provenance": payload["provenance"],
            }
        )

    manifest = {
        "artifact_id": "biological-minimalism-stage5-final-figure-manifest-v1",
        "schema_version": "1.0.0",
        "sprint": "STAGE5_FINAL_SYNTHESIS_AND_RELEASE",
        "generated_role": "FINAL_SYNTHESIS_AND_RELEASE_OWNER",
        "purpose": (
            "Catalog of every reproducible figure-data export for the final paper/presentation, each identifying "
            "its source artifact(s), exact fields, transformation, units, and claim boundary. 9 figures (A-I) are "
            "existing Stage-4 exports reused verbatim; 5 figures (J-N) are new Stage-5 exports derived strictly "
            "from already-accepted data (no new science, no hand-edited plot values)."
        ),
        "no_visual_overclaim_policy": (
            "No figure may imply tiny differences are huge, mixed results are decisive, pending evidence is "
            "final, or that the Coordinator's architecture choice equals mathematical Pareto dominance."
        ),
        "figures": catalog,
        "figure_count": len(catalog),
        "status": "STAGE5_FIGURE_MANIFEST_REPORTED_COMPLETE_PENDING_INDEPENDENT_AUDIT",
    }
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {MANIFEST_PATH} ({len(catalog)} figures)")


if __name__ == "__main__":
    main()
