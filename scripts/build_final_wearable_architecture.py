"""Stage 4 Final Architecture Closure: the ONE canonical final architecture
artifact (INTEGRATION_OWNER, master prompt Part II Sections 13-14).

Aggregates the Coordinator's final decisions (selected class, module
topology, Gate D acceptance, Gate E freezes, formal Pareto result) into a
single authoritative results/final_wearable_architecture.json. Every number
here is read/derived from already-frozen upstream artifacts - nothing is
invented. This artifact is what changes `final_architecture_status` from
UNRESOLVED to CORE_PLUS_CONTEXT for the FIRST time in this project;
upstream per-sprint artifacts (gate_d_burden_completeness, candidate
classes, burden matrix, etc.) intentionally retain their own UNRESOLVED/
NOT_READY fields, since their scope is burden/science analysis inputs, not
the final decision itself - only this artifact (and the formal Pareto
analysis / closure manifest that reference it) records the resolved state.
"""

from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PATH = REPO_ROOT / "results" / "final_wearable_architecture.json"


def _load(rel: str) -> dict:
    return json.loads((REPO_ROOT / rel).read_text())


candidate_classes = _load("results/stage4_architecture_candidate_classes.json")
burden_matrix = _load("results/stage4_candidate_burden_matrix.json")
contact_burden = _load("results/stage4_contact_electrode_burden.json")
battery_scenarios = _load("results/stage4_battery_topology_scenarios.json")
gate_d = _load("results/stage4_gate_d_burden_completeness.json")
gate_e_decisions = _load("results/stage4_gate_e_coordinator_decisions.json")
pareto = _load("results/stage4_formal_pareto_analysis.json")

SELECTED_CLASS = "CORE_PLUS_CONTEXT"

# ---------------------------------------------------------------------------
# Hard-fail guards: the selection must be internally consistent with every
# upstream artifact it cites before this script will write anything.
# ---------------------------------------------------------------------------
if gate_d.get("schema_version") != "3.0.0" or "coordinator_acceptance" not in gate_d:
    raise SystemExit(
        "REFUSING TO RUN: results/stage4_gate_d_burden_completeness.json is not the v3.0.0 "
        "coordinator_acceptance record - run scripts/build_stage4_gate_d_coordinator_acceptance.py first."
    )
if gate_d["gate_d_burden_completeness"] not in ("CONDITIONALLY_READY", "READY"):
    raise SystemExit(f"REFUSING TO RUN: Gate D is {gate_d['gate_d_burden_completeness']!r}, not accepted.")
if gate_e_decisions.get("no_option_selected") is not False or gate_e_decisions.get("gate_e_pending_science_sensitivity") != "CLOSED_BY_COORDINATOR_DECISION":
    raise SystemExit("REFUSING TO RUN: Gate E coordinator decisions are not recorded as closed.")
if SELECTED_CLASS not in pareto.get("pareto_relevant_set", []):
    raise SystemExit(
        f"REFUSING TO RUN: {SELECTED_CLASS!r} is not in the formal Pareto analysis's pareto_relevant_set "
        f"{pareto.get('pareto_relevant_set')!r} - a final architecture must be selected from within the "
        "Pareto-relevant set."
    )

science_class = next(c for c in candidate_classes["classes"] if c["class_id"] == SELECTED_CLASS)
burden_class = next(c for c in burden_matrix["classes"] if c["class_id"] == SELECTED_CLASS)
battery_class = next(c for c in battery_scenarios["candidate_class_comparison"] if c["class_id"] == SELECTED_CLASS)
contacts_by_modality = {m["modality"]: m for m in contact_burden["modalities"]}

# ---------------------------------------------------------------------------
# Module topology: DISTRIBUTED_BODY_MODULE_TOPOLOGY (Coordinator selection,
# master prompt Part I Section 7). Each module keeps its own local battery +
# MCU/radio domain - this corresponds to the DISTRIBUTED_PER_MODULE battery
# scenario (no cross-body wiring harness) AND the per_module_mcu_radio power
# interpretation (each module's electronics domain is independent, not a
# single shared system-wide MCU/radio). The higher per-module power cost is
# accepted and disclosed here, not hidden behind the cheaper single-shared
# figure.
# ---------------------------------------------------------------------------
selected_power_mw = burden_class["power_range_mw"]["per_module_mcu_radio"]
alternative_power_mw = burden_class["power_range_mw"]["single_shared_mcu_radio"]

MODULE_TOPOLOGY = {
    "topology_class": "DISTRIBUTED_BODY_MODULE_TOPOLOGY",
    "rationale": (
        "Independent body-worn modules for wrist, chest, and head, each maintaining its own local "
        "electronics/power/MCU-radio domain. Avoids cross-body shared-hub wiring/harness; maintains modular "
        "wearable topology; final candidate ordering (results/stage4_candidate_burden_matrix.json "
        "robustness_analysis) is robust to this topology choice; higher distributed power burden is accepted "
        "and disclosed below rather than hidden behind the cheaper single-shared-MCU/radio figure."
    ),
    "modules": science_class.get("anatomical_regions", []),
    "module_ids": ["wrist_module", "chest_module", "head_module"],
    "battery_topology_selected": "DISTRIBUTED_PER_MODULE",
    "battery_topology_rationale": (
        f"Battery-cell mass is scenario-neutral ({battery_class['distributed_per_module_total_battery_g']} g "
        "either way per results/stage4_battery_topology_scenarios.json) - DISTRIBUTED_PER_MODULE additionally "
        "avoids the cross-body wiring-harness mass penalty SHARED_HUB would add "
        f"({battery_class['shared_hub_additional_wiring_g']['min']}-{battery_class['shared_hub_additional_wiring_g']['max']} g, "
        f"most likely {battery_class['shared_hub_additional_wiring_g']['most_likely']} g) and keeps the "
        "already-frozen single-stage 0.85 regulator efficiency (no added regulation-stage risk)."
    ),
    "mcu_radio_topology_selected": "PER_MODULE",
    "mcu_radio_topology_rationale": (
        "Consistent with results/hardware_topology_contract.json's literal per-module 'host MCU'/'wireless "
        "radio' shared_resources listing for each independent body-worn module. This is the HIGHER-power "
        "interpretation and is accepted/disclosed as such: "
        f"{selected_power_mw['battery_side']} mW battery-side (selected, per-module) vs. "
        f"{alternative_power_mw['battery_side']} mW battery-side (alternative, single-shared system-wide MCU/"
        "radio - NOT selected). Source power assumptions are unchanged from "
        "results/stage4_engineering_readiness.json; only the topology interpretation differs."
    ),
}

# ---------------------------------------------------------------------------
# Contact model: ~9 total contacts (most_likely), from the already-bounded
# per-modality contact/electrode burden. EOG contributes only its
# incremental ocular contacts, sharing EEG reference/ground.
# ---------------------------------------------------------------------------
selected_modality_keys = ["wrist_ppg_plus_imu", "ecg_chest", "frontal_eeg", "eog"]
per_modality_contacts = {k: contacts_by_modality[k]["total_contacts"] for k in selected_modality_keys}
_sum_most_likely = sum(v["most_likely"] for v in per_modality_contacts.values())

CONTACT_MODEL = {
    "total_contacts": burden_class["total_contacts"],
    "per_modality_breakdown": per_modality_contacts,
    "sum_check": {
        "sum_of_most_likely_per_modality": _sum_most_likely,
        "matches_burden_matrix_most_likely": _sum_most_likely == burden_class["total_contacts"]["most_likely"],
    },
    "eog_shared_infrastructure_note": (
        "EOG contributes only its incremental ocular contacts (2, CLOSED confidence) and shares frontal EEG's "
        "reference/ground/AFE infrastructure - not double-counted. See "
        "results/stage4_contact_electrode_burden.json modalities[eog].shared_with and "
        "results/stage4_gate_d_burden_completeness.json eeg_eog_shared_afe_confirmation."
    ),
    "exact_anatomical_positions_not_specified": (
        "Bounded engineering estimates only (BOUNDED_ENGINEERING_ESTIMATE / PHYSICALLY_CONSTRAINED_BY_FROZEN_"
        "METHOD per modality) - no exact anatomical electrode montage positions are invented beyond what "
        "results/stage4_contact_electrode_burden.json already specifies."
    ),
}

BURDEN_RANGES = {
    "power_mw": {
        "selected_topology_battery_side": selected_power_mw["battery_side"],
        "selected_topology_load_side": selected_power_mw["load_side"],
        "alternative_single_shared_battery_side_not_selected": alternative_power_mw["battery_side"],
        "sensor_only_subtotal": burden_class["power_range_mw"]["sensor_only_subtotal"],
    },
    "mass_g": {
        "battery_only": battery_class["distributed_per_module_total_battery_g"],
        "shared_hub_wiring_avoided_g": battery_class["shared_hub_additional_wiring_g"],
        "note": burden_class["mass_range_g"]["note"],
    },
    "raw_data_rate_bps": burden_class["raw_data_rate_bps"],
    "contacts": burden_class["total_contacts"],
    "bounded_not_exact": (
        "Every figure above is a bounded engineering estimate carried forward from "
        "results/stage4_gate_d_burden_completeness.json (CONDITIONALLY_READY, coordinator-accepted) - not a "
        "final/exact BOM. bom_final remains false."
    ),
}

SCIENCE_RATIONALE = {
    "class_description": science_class["description"],
    "evidence_confidence": science_class["evidence_confidence"],
    "included_modalities": science_class["sensors"],
    "eog_specific_rationale": (
        "Aligned EOG provides bounded same-dataset incremental sleep-staging value beyond EEG-only and "
        "shuffled/control conditions under the tested protocol (TIER_B_CONTROLLED_SUPPORT same-dataset; "
        "TIER_C_BOUNDED_SUPPORT external, via HMC bounded n=7 - NOT externally replicated). Included at low "
        "incremental physical burden (+0.375 mW, +0.4 g, +2 contacts) via shared EEG AFE/reference "
        "infrastructure, without adding a new body region or full module."
    ),
    "pareto_context": pareto["coordinator_selection_rationale"],
}

EXCLUSION_RATIONALE = {
    "thoracic_bioz_eis": {
        "excluded_from_final_architecture": True,
        "reason": (
            "Corrected protocol-compliant LBNP evidence is COMPLETE_MIXED, negative-leaning and heterogeneous "
            "(results/lbnp_thoracic_eis_stage3_v2_protocol_compliant.json). Does not demonstrate stable "
            "incremental value sufficient to justify final architecture inclusion."
        ),
        "prohibited_claim": "BioZ is useless - NOT the finding. Preserved in scientific history/evidence, excluded from hardware architecture only.",
    },
    "leg_bioz": {
        "excluded_from_final_architecture": True,
        "reason": (
            "QDE V2 is aggregate-negative, heterogeneous, and sensitivity-fragile (7/10 subjects individually "
            "favor B despite a negative aggregate mean), while leg BioZ adds a new body region, electrode/"
            "contact burden, and attachment/module burden."
        ),
        "prohibited_claim": "Generalization beyond the tested terrestrial endpoint is not supported.",
    },
    "second_site_ppg": {
        "excluded_from_final_architecture": True,
        "reason": (
            "Current PTT evidence is negative/deprioritized (B_minus_A=+1.462 MAE, worse; n=4 held-out test "
            "subjects) and it adds substantial sensor power (9.018 mW, the single largest sensor contributor "
            "in the entire burden model), data rate (28500 bps), and a new sensing location."
        ),
        "prohibited_claim": "'Second PPG never helps' as an absolute/permanent claim - NOT supported; only this tested implementation is deprioritized.",
    },
    "wrist_temperature_light": {
        "excluded_from_final_architecture": True,
        "reason": (
            "No governing scientific experiment currently establishes incremental value (TIER_P_PENDING - "
            "complete absence of governing evidence, not a negative result)."
        ),
        "prohibited_claim": "Labeling these modalities negative - NOT supported. Correct status is insufficient/pending evidence.",
    },
}

GATE_D_STATUS = {
    "gate_d_burden_completeness": gate_d["gate_d_burden_completeness"],
    "coordinator_acceptance": gate_d["coordinator_acceptance"],
    "state_transition_history": gate_d["coordinator_acceptance"]["state_transition"],
}

GATE_E_DECISIONS = {
    "gate_e_pending_science_sensitivity": gate_e_decisions["gate_e_pending_science_sensitivity"],
    "decisions": gate_e_decisions["decisions"],
}

REVISION_TRIGGERS = [
    {
        "item": d["item"],
        "revision_trigger": d["revision_trigger"],
    }
    for d in gate_e_decisions["decisions"]
]

PROVENANCE = {
    "accepted_stage3_sha": "5c381014af61e5d10d41223963831b25b9ff23e6",
    "stage4_science_owner_package_sha": "5730efd246df8a898d77ea60a32d04235078c215",
    "stage4_architecture_decision_framework_sha": "fa71eec8a870e4d0d87d5f541344d4d9c299dc23",
    "stage4_controlled_integration_sha": "05c0ff8cd1b8b815e26188c25b62007b0d03f284",
    "stage4_gate_d_burden_closure_branch_head_sha": "51a644e0a797ba65b4b3f38acb3c8ee25f1dd95d",
    "source_artifacts": [
        "results/stage4_architecture_candidate_classes.json",
        "results/stage4_candidate_burden_matrix.json",
        "results/stage4_contact_electrode_burden.json",
        "results/stage4_battery_topology_scenarios.json",
        "results/stage4_gate_d_burden_completeness.json",
        "results/stage4_gate_e_coordinator_decisions.json",
        "results/stage4_formal_pareto_analysis.json",
    ],
}

COORDINATOR_DECISION_STATUS = {
    "final_architecture": SELECTED_CLASS,
    "formal_pareto_status": pareto["formal_pareto_status"],
    "gate_d": GATE_D_STATUS["coordinator_acceptance"]["status"],
    "gate_e": GATE_E_DECISIONS["gate_e_pending_science_sensitivity"],
    "not_yet_started": "Stage 5 (paper/jury writing) is explicitly NOT authorized by this closure.",
}

output = {
    "artifact_id": "biological-minimalism-final-wearable-architecture-v1",
    "schema_version": "1.0.0",
    "sprint": "STAGE4_FINAL_ARCHITECTURE_CLOSURE",
    "generated_role": "INTEGRATION_OWNER",
    "purpose": (
        "The ONE canonical final Stage-4 wearable architecture artifact. Records the Project Coordinator's "
        "selection of CORE_PLUS_CONTEXT, closing the architecture decision that every upstream Stage-4 "
        "artifact deliberately left UNRESOLVED."
    ),
    "selected_class": SELECTED_CLASS,
    "selected_modalities": science_class["sensors"],
    "selected_body_regions": science_class["anatomical_regions"],
    "module_topology": MODULE_TOPOLOGY,
    "contact_model": CONTACT_MODEL,
    "burden_ranges": BURDEN_RANGES,
    "science_rationale": SCIENCE_RATIONALE,
    "exclusion_rationale": EXCLUSION_RATIONALE,
    "gate_d_status": GATE_D_STATUS,
    "gate_e_decisions": GATE_E_DECISIONS,
    "revision_triggers": REVISION_TRIGGERS,
    "provenance": PROVENANCE,
    "coordinator_decision_status": COORDINATOR_DECISION_STATUS,
    "final_architecture_status": SELECTED_CLASS,
    "formal_pareto_status": pareto["formal_pareto_status"],
}

OUTPUT_PATH.write_text(json.dumps(output, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(f"Wrote {OUTPUT_PATH}")
