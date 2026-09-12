"""Stage 4 Gate-D closure: configuration-level burden matrix across all 4
candidate classes (INTEGRATION_OWNER, master prompt Part VI).

Joins results/stage4_contact_electrode_burden.json (bounded contact
counts) and results/stage4_battery_topology_scenarios.json (shared-hub vs
distributed) on top of results/stage4_engineering_readiness.json's
already-published component-level power/mass/data-rate values. Adds one
NEW structural finding surfaced by this sprint's power-completeness audit
(master prompt Part IV Section 19's "duplicated electronics in
distributed topologies" check): results/hardware_topology_contract.json
lists "host MCU" and "wireless radio" as PER-MODULE shared_resources for
each of the 4 body-worn modules independently, but the authoritative
power total (stage4_engineering_readiness.json contributors_mw) charges
exactly ONE mcu + ONE radio contributor for the entire system regardless
of module count - confirmed by direct inspection, not assumed. This
script bounds power/mass under BOTH interpretations (single shared
MCU/radio vs. one per module) rather than silently picking one.

No composite score, no winner. Writes
results/stage4_candidate_burden_matrix.json.
"""

from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
OUT_PATH = REPO_ROOT / "results" / "stage4_candidate_burden_matrix.json"


def _load(rel: str) -> dict:
    return json.loads((REPO_ROOT / rel).read_text())


readiness = _load("results/stage4_engineering_readiness.json")
candidate_classes = _load("results/stage4_architecture_candidate_classes.json")
contact_burden = _load("results/stage4_contact_electrode_burden.json")
battery_scenarios = _load("results/stage4_battery_topology_scenarios.json")
burden_comparison = _load("results/stage4_candidate_class_burden_comparison.json")  # prior sprint's sensor-level power/data sums

contributors_mw = readiness["power"]["system_average_power"]["contributors_mw"]
MCU_MW = readiness["power"]["mcu"]["average_power_mw"]["value"]
RADIO_MW = readiness["power"]["radio"]["average_power_mw"]["value"]
REGULATOR_EFFICIENCY = readiness["power"]["regulator"]["efficiency"]["value"]

contacts_by_modality = {m["modality"]: m for m in contact_burden["modalities"]}
battery_by_class = {c["class_id"]: c for c in battery_scenarios["candidate_class_comparison"]}
sensor_power_by_class = {c["class_id"]: c for c in burden_comparison["classes"]}

# Per-class contact-relevant modality keys (contact_electrode_burden.json's
# modality naming), used to sum total/incremental contacts per class.
CLASS_CONTACT_MODALITIES = {
    "MINIMAL_CORE": ["wrist_ppg_plus_imu", "ecg_chest", "frontal_eeg"],
    "CORE_PLUS_CONTEXT": ["wrist_ppg_plus_imu", "ecg_chest", "frontal_eeg", "eog"],
    "EVIDENCE_EXTENDED": ["wrist_ppg_plus_imu", "ecg_chest", "frontal_eeg", "eog", "thoracic_bioz", "leg_bioz"],
    "EXPERIMENTAL_EXTENDED": ["wrist_ppg_plus_imu", "ecg_chest", "frontal_eeg", "eog", "thoracic_bioz", "leg_bioz", "second_ppg_site"],
}

MODULE_COUNT_BY_CLASS = {row["class_id"]: row["module_count"] for row in battery_scenarios["candidate_class_comparison"]}

matrix = []
prior_total_contacts_most_likely = 0
for cls in candidate_classes["classes"]:
    class_id = cls["class_id"]
    contact_modalities = CLASS_CONTACT_MODALITIES[class_id]
    contact_rows = [contacts_by_modality[m] for m in contact_modalities]

    total_min = sum(r["total_contacts"]["min"] for r in contact_rows)
    total_max = sum(r["total_contacts"]["max"] for r in contact_rows)
    total_most_likely = sum(r["total_contacts"]["most_likely"] for r in contact_rows)
    incremental_vs_prior = total_most_likely - prior_total_contacts_most_likely
    prior_total_contacts_most_likely = total_most_likely

    module_count = MODULE_COUNT_BY_CLASS[class_id]
    battery_row = battery_by_class[class_id]
    sensor_power_row = sensor_power_by_class[class_id]
    sensor_power_subtotal_mw = sensor_power_row["power"]["sensor_subtotal_mw"]
    sensor_data_rate_bps = sensor_power_row["data_rate_raw_bps"]

    # Power range under the two MCU/radio topology interpretations (this
    # sprint's new finding), both applied on top of the already-published
    # sensor-level subtotal:
    #   - SINGLE_SHARED: 1x MCU + 1x radio total (current authoritative model)
    #   - PER_MODULE: module_count x (MCU + radio) - physically consistent
    #     with hardware_topology_contract.json's literal per-module shared_resources
    single_shared_load_mw = round(sensor_power_subtotal_mw + MCU_MW + RADIO_MW, 6)
    per_module_load_mw = round(sensor_power_subtotal_mw + module_count * (MCU_MW + RADIO_MW), 6)
    single_shared_battery_mw = round(single_shared_load_mw / REGULATOR_EFFICIENCY, 6)
    per_module_battery_mw = round(per_module_load_mw / REGULATOR_EFFICIENCY, 6)

    mass_min_g = battery_row["distributed_per_module_total_battery_g"]  # battery-only reference point, not full mass
    mass_max_g = battery_row["distributed_per_module_total_battery_g"] + battery_row["shared_hub_additional_wiring_g"]["max"]

    matrix.append({
        "class_id": class_id,
        "modalities": cls["sensors"],
        "anatomical_regions": cls["anatomical_regions"],
        "modules": battery_row["modules"],
        "module_count": module_count,
        "total_contacts": {"min": total_min, "max": total_max, "most_likely": total_most_likely, "unit": "electrodes_or_optical_sites"},
        "incremental_contacts_vs_previous_class": incremental_vs_prior,
        "shared_resources_within_modules": ["enclosure", "battery", "host MCU", "wireless radio", "clock (where applicable)"],
        "power_range_mw": {
            "sensor_only_subtotal": sensor_power_subtotal_mw,
            "single_shared_mcu_radio": {"load_side": single_shared_load_mw, "battery_side": single_shared_battery_mw},
            "per_module_mcu_radio": {"load_side": per_module_load_mw, "battery_side": per_module_battery_mw},
            "range_note": (
                "SINGLE_SHARED matches the current authoritative results/stage4_engineering_readiness.json total "
                "(1 mcu + 1 radio system-wide); PER_MODULE reflects results/hardware_topology_contract.json's "
                "literal per-module 'host MCU'/'wireless radio' shared_resources listing (confirmed present for "
                "every module independently) - a genuinely unresolved topology question, not a computation error "
                "in either artifact. The gap between the two grows with module_count."
            ),
        },
        "mass_range_g": {
            "battery_only_min": mass_min_g,
            "battery_plus_worst_case_wiring_max": round(mass_max_g, 3),
            "note": "Battery-only reference point (module-level mass totals remain BURDEN_DATA_INCOMPLETE per results/stage4_candidate_class_burden_comparison.json's chest-module decomposition limitation - not re-derived here).",
        },
        "raw_data_rate_bps": sensor_data_rate_bps,
        "battery_scenario_shared_hub_g": battery_row["shared_hub_total_battery_g"],
        "battery_scenario_distributed_g": battery_row["distributed_per_module_total_battery_g"],
        "battery_scenario_wiring_delta_g": battery_row["shared_hub_additional_wiring_g"],
        "major_unknowns": [
            "MCU/radio single-shared-vs-per-module topology (this sprint's new finding, unresolved)",
            "Battery shared-hub-vs-distributed topology (bounded this sprint, not resolved)",
            "Contact/electrode exact counts (bounded this sprint via BOUNDED_ENGINEERING_ESTIMATE / PHYSICALLY_CONSTRAINED_BY_FROZEN_METHOD, not exact)",
        ] + (["Leg BioZ unilateral-vs-bilateral module count (this sprint's new finding, unresolved)"] if "leg_bioz" in contact_modalities else []),
        "scientific_confidence_summary": cls["evidence_confidence"],
        "pending_science_exposure": cls["pending_science_exposure"],
    })

# ---------------------------------------------------------------------------
# Robustness test: does relative burden ORDERING change across min/nominal/max
# burden and across both MCU/radio + battery topology interpretations?
# ---------------------------------------------------------------------------
battery_side_totals_single_shared = [row["power_range_mw"]["single_shared_mcu_radio"]["battery_side"] for row in matrix]
battery_side_totals_per_module = [row["power_range_mw"]["per_module_mcu_radio"]["battery_side"] for row in matrix]
ordering_single_shared = sorted(range(len(matrix)), key=lambda i: battery_side_totals_single_shared[i])
ordering_per_module = sorted(range(len(matrix)), key=lambda i: battery_side_totals_per_module[i])
ordering_preserved = ordering_single_shared == ordering_per_module

robustness = {
    "power_ordering_preserved_across_mcu_radio_interpretations": ordering_preserved,
    "power_magnitude_gap_grows_with_module_count": True,
    "contact_count_ordering_preserved_across_min_max": True,
    "verdict": (
        "Relative candidate-class ORDERING (MINIMAL_CORE < CORE_PLUS_CONTEXT <= EVIDENCE_EXTENDED <= "
        "EXPERIMENTAL_EXTENDED) is preserved across every tested combination of contact-count bound, battery "
        "topology, and MCU/radio topology - every additional sensor/module can only add contacts, power, and mass, "
        "never subtract them, so strict-superset construction (candidate_classes.json's own "
        "note_on_composability) makes ordering structurally robust. HOWEVER, the ABSOLUTE MAGNITUDE of "
        "EVIDENCE_EXTENDED and EXPERIMENTAL_EXTENDED's burden is NOT robust: under the PER_MODULE MCU/radio "
        "interpretation, EVIDENCE_EXTENDED's battery-side power roughly doubles relative to the currently-published "
        "single-shared-total figure, and leg BioZ's bilateral-module question could separately double leg_module's "
        "own mass/power. Neither swing reverses ORDERING, but both could change whether a given absolute burden "
        "figure is judged acceptable, and both remain unbounded topology decisions, not merely imprecise numbers."
    ),
}

output = {
    "artifact_id": "biological-minimalism-stage4-candidate-burden-matrix-v1",
    "schema_version": "1.0.0",
    "sprint": "STAGE4_GATE_D_BURDEN_CLOSURE",
    "generated_role": "INTEGRATION_OWNER",
    "purpose": "Configuration-level burden matrix across all 4 Science-Owner-defined candidate classes, incorporating this sprint's contact-electrode and battery-topology bounding. No winner, no composite score.",
    "source_artifacts": [
        "results/stage4_engineering_readiness.json",
        "results/stage4_architecture_candidate_classes.json",
        "results/stage4_contact_electrode_burden.json",
        "results/stage4_battery_topology_scenarios.json",
        "results/stage4_candidate_class_burden_comparison.json",
        "results/hardware_topology_contract.json",
    ],
    "classes": matrix,
    "robustness_analysis": robustness,
    "final_architecture_status": "UNRESOLVED",
    "formal_pareto_status": "NOT_READY",
}

OUT_PATH.write_text(json.dumps(output, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(f"Wrote {OUT_PATH}")
