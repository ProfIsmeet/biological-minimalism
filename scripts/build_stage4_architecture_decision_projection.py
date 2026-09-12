"""Stage 4 closure-prep: ONE authoritative architecture-decision projection
(master prompt Part II, INTEGRATION_OWNER deliverable).

Joins two Science Owner artifacts that use DIFFERENT, non-identical
groupings and DIFFERENT confidence vocabularies - deliberately not merged
into a single reinterpreted taxonomy:

  - results/stage4_scientific_sensor_value_matrix.json (per-MODALITY,
    HIGH/MEDIUM/LOW/NONE confidence_tier, from stage4-science-handoff)
  - results/stage4_sensor_decision_sensitivity.json (per-DECISION-UNIT,
    TIER_A..TIER_P confidence tiers, HIGH/MEDIUM/LOW decision_sensitivity,
    from stage4-architecture-decision-framework)

The decision-sensitivity artifact's grouping (e.g. "wrist PPG + wrist IMU"
as one unit, "wrist temperature / wrist light" as one unit) is the
decision-relevant level, so this projection is organized around it; each
unit cites its corresponding sensor-value-matrix modality entries verbatim
(1 or 2 per unit) rather than forcing a false 1:1 rename. Burden state is
joined from results/stage4_engineering_readiness.json (component-level,
already-published values only - no new numbers). No tier/sensitivity value
is altered from its source. Writes
results/stage4_architecture_decision_projection.json.
"""

from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
OUT_PATH = REPO_ROOT / "results" / "stage4_architecture_decision_projection.json"

sensor_value_matrix = json.loads((REPO_ROOT / "results/stage4_scientific_sensor_value_matrix.json").read_text())
sensitivity = json.loads((REPO_ROOT / "results/stage4_sensor_decision_sensitivity.json").read_text())
readiness = json.loads((REPO_ROOT / "results/stage4_engineering_readiness.json").read_text())

by_modality = {m["modality"]: m for m in sensor_value_matrix["modalities"]}
contributors_mw = readiness["power"]["system_average_power"]["contributors_mw"]
excluded_mw = readiness["power"]["system_average_power"]["excluded_from_base_total"]

# Explicit, disclosed join map from decision-unit -> sensor-value-matrix
# modality key(s). "sparse vs. full-montage EEG" has no sensor-value-matrix
# counterpart (it is a within-EEG channel-count question, not a modality
# inclusion question) - left empty rather than force-matched.
UNIT_TO_MODALITIES = {
    "wrist PPG + wrist IMU": ["wrist PPG", "wrist IMU"],
    "EOG (with EEG)": ["EOG", "frontal EEG"],
    "sparse vs. full-montage EEG (ds003838-adjacent)": [],
    "second-site PPG": ["second-site PPG"],
    "leg BioZ": ["leg BioZ"],
    "thoracic BioZ/EIS": ["thoracic BioZ/EIS"],
    "sleep interaction (EOG x respiration)": ["respiration (derived, EEG-adjacent)"],
    "wrist temperature / wrist light": ["wrist temperature", "wrist light (ambient/optical)"],
}

BURDEN_STATE = {
    "wrist PPG + wrist IMU": {
        "power_mw": {"wrist_ppg_incl_led": contributors_mw["wrist_ppg_total_incl_led"], "wrist_imu": contributors_mw["wrist_imu"]},
        "shared_module": "wrist_module (shared enclosure/battery/strap; no incremental module for IMU)",
        "evidence_class": "ENGINEERING_ASSUMPTION / ENGINEERING_ALLOWANCE_MECHANICAL_ESTIMATE",
    },
    "EOG (with EEG)": {
        "power_mw": {"eog_incremental_over_eeg_only": readiness["power"]["head_afe_eeg_eog"]["eog_incremental_power_mw"]["value"]},
        "mass_g": {"eog_incremental": readiness["mass"]["eog_incremental_mass_g"]["value"]},
        "shared_module": "head_module (shared AFE/reference/battery; EOG's isolated incremental cost only)",
        "evidence_class": "ENGINEERING_ASSUMPTION",
        "caveat": "Shared-AFE co-location feasibility is asserted, not yet Integration-Owner-confirmed (candidate_classes.json).",
    },
    "sparse vs. full-montage EEG (ds003838-adjacent)": {
        "power_mw": None,
        "note": "Not a modality-inclusion burden question; channel-count-within-EEG burden (electrode montage size) is separately MISSING per results/stage4_gate_d_burden_completeness.json (electrode/contact count dimension).",
    },
    "second-site PPG": {
        "power_mw": {"second_ppg_site_incl_led": excluded_mw["second_ppg_site_incl_led_mw"]},
        "shared_module": "optical_site_evaluation_branch (OPEN_BOUNDARY - shared/tethered/standalone unresolved)",
        "evidence_class": "ENGINEERING_ASSUMPTION",
    },
    "leg BioZ": {
        "power_mw": {"leg_bioz": excluded_mw["leg_bioz_mw"]},
        "mass_g": {"leg_module_total": readiness["mass"]["modules"]["leg_module"]["module_total_g"]},
        "shared_module": "leg_module (new body region, not shared with any other module)",
        "evidence_class": "ENGINEERING_ASSUMPTION / ENGINEERING_ALLOWANCE_MECHANICAL_ESTIMATE",
    },
    "thoracic BioZ/EIS": {
        "power_mw": {"thoracic_bioz": contributors_mw["thoracic_bioz"]},
        "shared_module": "chest_module (shared with ECG; electrode/contact sharing NOT assumed)",
        "evidence_class": "ENGINEERING_ASSUMPTION",
        "caveat": "Chest-module mass cannot be decomposed into ECG-only vs ECG+BioZ submasses (see results/stage4_gate_d_burden_completeness.json).",
    },
    "sleep interaction (EOG x respiration)": {
        "power_mw": None,
        "note": "No dedicated hardware burden beyond EOG/EEG already-accounted infrastructure; respiration here is model-derived, not a separate sensor.",
    },
    "wrist temperature / wrist light": {
        "power_mw": {"skin_temperature": contributors_mw["skin_temperature"], "light_sensor": contributors_mw["light_sensor"]},
        "shared_module": "wrist_module (shared; light_sensor's wrist placement itself is LOCATION_UNRESOLVED per hardware_topology_contract.json)",
        "evidence_class": "DATASHEET_CALCULATED",
    },
}

units_out = []
for unit in sensitivity["sensors"]:
    unit_id = unit["modality"]
    matrix_entries = [by_modality[m] for m in UNIT_TO_MODALITIES.get(unit_id, []) if m in by_modality]
    coordinator_decision_requirement = (
        "GATE_E_COORDINATOR_DECISION_REQUIRED (WAIT / FREEZE_CONDITIONALLY / FREEZE_DESPITE_UNCERTAINTY_WITH_DISCLOSURE)"
        if unit.get("decision_sensitivity") == "HIGH"
        else "NONE_CURRENTLY - no HIGH-sensitivity pending science identified for this unit"
    )
    units_out.append({
        "decision_unit": unit_id,
        "related_sensor_value_matrix_modalities": [
            {
                "modality": e["modality"],
                "anatomical_site": e["anatomical_site"],
                "confidence_tier_science_handoff": e["confidence_tier"],
                "external_replication_status": e["external_replication_status"],
                "heterogeneity": e["heterogeneity"],
                "architecture_implication": e["architecture_implication"],
                "unresolved_evidence": e["unresolved_evidence"],
            }
            for e in matrix_entries
        ],
        "confidence_tier_decision_framework": unit["current_confidence_tier"],
        "decision_sensitivity": unit["decision_sensitivity"],
        "pending_evidence": unit.get("pending_evidence"),
        "decision_flip_condition": unit.get("decision_flip_condition") or unit.get("decision_flip_scenarios"),
        "burden_state": BURDEN_STATE.get(unit_id),
        "unresolved_science": unit.get("pending_evidence"),
        "unresolved_engineering": (
            "See results/stage4_gate_d_burden_completeness.json known_unknowns"
            + (" (module-boundary + shared-AFE confirmation apply to this unit)" if unit_id == "EOG (with EEG)" else "")
        ),
        "coordinator_decision_requirement": coordinator_decision_requirement,
    })

output = {
    "artifact_id": "biological-minimalism-stage4-architecture-decision-projection-v1",
    "schema_version": "1.0.0",
    "sprint": "STAGE4_CLOSURE_PREP",
    "generated_role": "INTEGRATION_OWNER",
    "purpose": "The single authoritative architecture-decision projection joining Science Owner evidence (2 artifacts, 2 vocabularies, not conflated) with Integration Owner burden state, per decision unit.",
    "join_note": "Organized around results/stage4_sensor_decision_sensitivity.json's decision-unit grouping (the decision-relevant level); each unit cites its corresponding results/stage4_scientific_sensor_value_matrix.json modality entries verbatim (0-2 per unit, disclosed join map in this script) rather than forcing a false 1:1 rename between the two Science Owner artifacts' different groupings.",
    "source_artifacts": [
        "results/stage4_scientific_sensor_value_matrix.json",
        "results/stage4_sensor_decision_sensitivity.json",
        "results/stage4_engineering_readiness.json",
        "results/hardware_topology_contract.json",
        "results/stage4_gate_d_burden_completeness.json",
    ],
    "units": units_out,
    "final_architecture_status": "UNRESOLVED",
    "formal_pareto_status": "NOT_READY",
}

OUT_PATH.write_text(json.dumps(output, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(f"Wrote {OUT_PATH}")
