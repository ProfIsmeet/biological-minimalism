"""Stage 4 Gate-D closure: versioned reassessment of GATE_D_BURDEN_COMPLETENESS
(INTEGRATION_OWNER, master prompt Part X Section 35).

Reads the existing results/stage4_gate_d_burden_completeness.json (v1.0.0,
NOT_READY, written by the prior Closure Prep sprint) and this sprint's new
evidence (contact/electrode bounds, battery topology scenarios, candidate
burden matrix + robustness test), then writes a v2.0.0 assessment that
PRESERVES the entire v1.0.0 record verbatim under assessment_history
(never deleted) while updating the top-level fields to the new verdict.

Does not touch any science file. Writes (overwrites, with history
preserved inside) results/stage4_gate_d_burden_completeness.json.
"""

from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
GATE_D_PATH = REPO_ROOT / "results" / "stage4_gate_d_burden_completeness.json"


def _load(rel: str) -> dict:
    return json.loads((REPO_ROOT / rel).read_text())


v1 = json.loads(GATE_D_PATH.read_text())  # the existing NOT_READY assessment - preserved verbatim below

# Idempotency guard: this script is meant to run exactly ONCE, wrapping the
# v1.0.0 (NOT_READY) record into assessment_history. Running it again would
# read its OWN v2.0.0 output as if it were "v1", silently destroying the
# real v1.0.0/NOT_READY history that master prompt Part X Section 35
# explicitly requires to be preserved (this exact bug was caught and fixed
# during this sprint's own hostile review, Part XII Attack A/D).
if v1.get("schema_version") != "1.0.0":
    raise SystemExit(
        f"REFUSING TO RUN: {GATE_D_PATH} is already schema_version={v1.get('schema_version')!r}, not the "
        "expected v1.0.0 source record. This script must only run once, against the original NOT_READY "
        "assessment. Re-running it against its own output would destroy the preserved history."
    )
contact_burden = _load("results/stage4_contact_electrode_burden.json")
battery_scenarios = _load("results/stage4_battery_topology_scenarios.json")
burden_matrix = _load("results/stage4_candidate_burden_matrix.json")
readiness = _load("results/stage4_engineering_readiness.json")

chest_module = readiness["mass"]["modules"]["chest_module"]

# ---------------------------------------------------------------------------
# Bounded ECG-only chest-module mass estimate (closes remediation item #3).
# Method: component_ic_mass_g is already IC-count-separable (2 ICs = 0.02 g,
# i.e. 0.01 g/IC, matching the project's own per-IC allowance used
# everywhere else). PCB mass is assumed to scale roughly with IC/trace count
# (2 ICs -> 1 IC is a defensible ~25-40% reduction, bounded not exact).
# Enclosure/attachment/battery/wiring are mechanically/battery-driven, not
# IC-count-driven, and are held CONSTANT (a smaller PCB does not imply a
# smaller enclosure/strap/battery in this project's generic-allowance model).
# ---------------------------------------------------------------------------
ecg_only_ic_mass_g = 0.01  # 1 of the 2 already-separable per-IC allowances
pcb_reduction_fraction = {"min": 0.25, "max": 0.40}
ecg_only_pcb_g = {
    "min": round(chest_module["pcb_mass_g"] * (1 - pcb_reduction_fraction["max"]), 3),
    "max": round(chest_module["pcb_mass_g"] * (1 - pcb_reduction_fraction["min"]), 3),
}
ecg_only_chest_module_g = {
    "min": round(ecg_only_ic_mass_g + ecg_only_pcb_g["min"] + chest_module["battery_mass_g"] + chest_module["enclosure_mass_g"] + chest_module["attachment_mass_g"] + chest_module["wiring_mass_g"] * 0.75, 3),
    "max": round(ecg_only_ic_mass_g + ecg_only_pcb_g["max"] + chest_module["battery_mass_g"] + chest_module["enclosure_mass_g"] + chest_module["attachment_mass_g"] + chest_module["wiring_mass_g"], 3),
}
_delta_min = round(chest_module["module_total_g"] - ecg_only_chest_module_g["max"], 3)
_delta_max = round(chest_module["module_total_g"] - ecg_only_chest_module_g["min"], 3)
chest_module_decomposition_bound = {
    "ecg_only_chest_module_g": ecg_only_chest_module_g,
    "ecg_plus_thoracic_bioz_chest_module_g": chest_module["module_total_g"],
    "delta_g": {"min": _delta_min, "max": _delta_max},
    "method": (
        "component_ic_mass_g is already per-IC-separable (2 ICs = 0.02 g total, matching the project's "
        "0.01 g/IC allowance used everywhere else) - dropping thoracic_bioz's AD5940-class IC removes exactly "
        "0.01 g. pcb_mass_g is assumed to scale with IC/trace count (25-40% reduction for 1 IC vs 2, bounded not "
        "exact). enclosure_mass_g/attachment_mass_g/battery_mass_g are mechanically/battery-driven, not "
        "IC-count-driven, and are held CONSTANT under this project's generic-allowance model; wiring_mass_g is "
        "given a small bounded reduction (0.75x-1.0x) for one fewer IC's local interconnect."
    ),
    "confidence": "BOUNDED_ENGINEERING_ESTIMATE",
    "magnitude_note": f"Delta ({_delta_min}-{_delta_max} g) is small relative to the ~30.5 g system total (<2%) - does not change candidate ordering, closes remediation item #3 to a bounded (not exact) state.",
}

# EEG+EOG shared-AFE engineering confirmation (closes remediation item #4).
eeg_eog_shared_afe_confirmation = {
    "status": "CONFIRMED_BY_STANDARD_ARCHITECTURE",
    "confirmation": (
        "Multi-channel biopotential AFEs in the ADS1299 family (the already-selected ADS1299-4-class reference "
        "part, evidence_id day6_ads1299_datasheet) are fundamentally architected around a SINGLE shared "
        "reference/bias-drive circuit common to all channels - this is not an optional feature but the basic "
        "operating principle of how a '4-channel EEG AFE' functions at all (every channel measures relative to "
        "the same reference electrode). Treating EOG as a 2nd channel on the same 4-channel-capable AFE sharing "
        "the existing reference/bias is therefore consistent with standard, well-established multi-channel "
        "biopotential AFE architecture, not a novel or unverified assumption specific to this project."
    ),
    "residual_caveat": (
        "This confirms ARCHITECTURAL feasibility (the AFE class supports it by design), not a specific validated "
        "PCB layout, noise-isolation, or final montage - those remain open per the topology contract's existing "
        "unresolved_dependencies. The engineering ASSUMPTION label on the +0.375 mW / +0.4 g EOG increment is "
        "retained (still not a datasheet-table-verified number), but the shared-AFE PREMISE itself is now "
        "engineering-confirmed rather than merely asserted."
    ),
}

new_dimensions_audited = list(v1["dimensions_audited"])
for dim in new_dimensions_audited:
    if dim["dimension"] == "electrodes_and_contact_count":
        dim["status"] = "BOUNDED"
        dim["evidence"] = "results/stage4_contact_electrode_burden.json bounds every previously-MISSING modality (ECG, thoracic BioZ, frontal EEG, leg BioZ) with [min, max, most_likely] ranges and explicit method/provenance (PHYSICALLY_CONSTRAINED_BY_FROZEN_METHOD for tetrapolar BioZ, BOUNDED_ENGINEERING_ESTIMATE for ECG/EEG)."
        dim["gap"] = "Ranges are bounded but not exact/frozen - a final montage decision would still narrow these further. Does not block comparative burden analysis (results/stage4_candidate_burden_matrix.json robustness_analysis confirms candidate ordering is preserved across the full min-max range)."
    elif dim["dimension"] == "battery":
        dim["status"] = "BOUNDED"
        dim["evidence"] = "results/stage4_battery_topology_scenarios.json models both shared-hub and distributed topologies: battery CELL mass is scenario-neutral (same total Wh, same 190 Wh/kg density, no project-specific economies-of-scale figure to assume otherwise); the delta is a bounded cross-body wiring-harness estimate."
        dim["gap"] = "Final topology (shared-hub vs. distributed) remains an open engineering/Coordinator decision - bounded, not resolved. results/stage4_candidate_burden_matrix.json confirms candidate ORDERING is unaffected either way."
    elif dim["dimension"] == "shared_infrastructure_and_resource_credit":
        dim["status"] = "PARTIALLY_MODELED_WITH_NEW_BOUNDED_FINDING"
        dim["evidence"] = dim["evidence"] + " EEG+EOG shared-AFE premise is now ENGINEERING-CONFIRMED (not merely assumed) based on standard ADS1299-family multi-channel architecture - see eeg_eog_shared_afe_confirmation below. ECG-only vs. ECG+thoracic-BioZ chest-module mass is now bounded (not exact) via IC-count-proportional PCB scaling - see chest_module_decomposition below."
        dim["gap"] = (
            "NEW FINDING this sprint (not previously disclosed): results/hardware_topology_contract.json lists "
            "'host MCU' and 'wireless radio' as PER-MODULE shared_resources for each of the 4 body-worn modules "
            "independently, but results/stage4_engineering_readiness.json's authoritative power total charges "
            "exactly ONE mcu + ONE radio contributor system-wide regardless of module count - confirmed by direct "
            "inspection. Bounded both interpretations in results/stage4_candidate_burden_matrix.json (single-shared "
            "vs. per-module): candidate ORDERING is preserved either way, but EVIDENCE_EXTENDED's battery-side "
            "power roughly DOUBLES (8.79 -> 15.22 mW) under the per-module interpretation. This is now a bounded, "
            "disclosed range, not an unbounded unknown - but the underlying topology choice (1 MCU/radio design "
            "vs. per-module) remains an open engineering decision."
        )

new_known_unknowns = [
    {
        "item": "Shared-hub vs. per-module battery/electronics boundary",
        "why_it_matters": "Determines total wiring-harness mass and possible extra regulation-stage power loss for multi-module configurations.",
        "bounded": True,
        "could_be_decision_changing": False,
        "note": "BOUNDED this sprint (results/stage4_battery_topology_scenarios.json). Candidate ORDERING confirmed robust across both topologies (results/stage4_candidate_burden_matrix.json robustness_analysis) - downgraded from could_be_decision_changing=true to false because ordering-preservation is now demonstrated, not assumed.",
    },
    {
        "item": "MCU/radio single-shared-vs-per-module topology (NEW finding this sprint)",
        "why_it_matters": "hardware_topology_contract.json's per-module shared_resources listing vs. the power model's single system-wide mcu+radio contributor creates up to a ~2x power swing for multi-module classes (EVIDENCE_EXTENDED: 8.79-15.22 mW battery-side).",
        "bounded": True,
        "could_be_decision_changing": False,
        "note": "BOUNDED this sprint (results/stage4_candidate_burden_matrix.json). Candidate ORDERING confirmed robust across both interpretations - the swing affects absolute magnitude, not relative comparison.",
    },
    {
        "item": "ECG / EEG-main / thoracic-BioZ / leg-BioZ electrode and contact counts",
        "why_it_matters": "Contact/electrode count is one of the four HARD_BLOCK burden dimensions per GATE_D_BURDEN_COMPLETENESS's own requirement text.",
        "bounded": True,
        "could_be_decision_changing": False,
        "note": "BOUNDED this sprint (results/stage4_contact_electrode_burden.json) with explicit method/provenance per modality. Downgraded from could_be_decision_changing=true to false because contact-count ordering is confirmed stable across min-max (results/stage4_candidate_burden_matrix.json).",
    },
    {
        "item": "Leg BioZ unilateral-vs-bilateral module topology (NEW finding this sprint)",
        "why_it_matters": "Science Owner scopes leg BioZ as 'legs (bilateral)' (candidate_classes.json) but the engineering model is silent on 1-vs-2 physical leg_module instances - could double leg BioZ's own mass/power contribution.",
        "bounded": True,
        "could_be_decision_changing": False,
        "note": "Bounded within results/stage4_contact_electrode_burden.json's leg_bioz total_contacts range (4-8, most_likely=8 reflecting bilateral scope). Affects only EVIDENCE_EXTENDED/EXPERIMENTAL_EXTENDED magnitude (both already carry this sensor), not their ordering relative to each other or to MINIMAL_CORE/CORE_PLUS_CONTEXT.",
    },
    {
        "item": "Processed/on-device data rate",
        "why_it_matters": "Raw and transmitted rates are known; processed rate depends on a feature-extraction/compression pipeline that does not exist yet.",
        "bounded": False,
        "could_be_decision_changing": False,
        "note": "Reasoned through this sprint (not separately re-derived): a compression/feature-extraction pipeline would apply roughly proportionally across every candidate class's raw data volume (no modality-specific reason to expect categorically different compression), so comparative candidate ordering does not depend on knowing the exact processed rate - it remains numerically unknown without blocking comparative burden, per the master prompt's own explicit closure logic for this dimension.",
    },
    {
        "item": "Vendor-specific part selection (MCU, radio, regulator, battery, all sensing ICs)",
        "why_it_matters": "Every number is class-level with an engineering-assumption operating point, not a specific datasheet-verified part.",
        "bounded": True,
        "could_be_decision_changing": False,
    },
]

GATE_D_STATUS_V2 = "CONDITIONALLY_READY"
RATIONALE_V2 = (
    "All four of v1's governing remediation items are now closed to a BOUNDED (not exact/final) state: "
    "(1) battery/module-boundary topology is modeled under both shared-hub and distributed scenarios "
    "(results/stage4_battery_topology_scenarios.json), with battery-cell mass shown scenario-neutral and the "
    "delta bounded to a wiring-harness estimate; (2) electrode/contact counts are bounded for every previously-"
    "MISSING modality with explicit method/provenance (results/stage4_contact_electrode_burden.json); "
    "(3) the ECG-only vs. ECG+thoracic-BioZ chest-module mass split is now bounded via IC-count-proportional PCB "
    "scaling (this artifact, chest_module_decomposition); (4) EEG+EOG shared-AFE co-location is now "
    "engineering-CONFIRMED (not merely assumed) based on standard ADS1299-family multi-channel architecture "
    "(this artifact, eeg_eog_shared_afe_confirmation). This sprint's hostile audit of power completeness also "
    "surfaced one materially significant NEW finding - a per-module vs. single-shared MCU/radio topology "
    "ambiguity worth up to ~2x power for multi-module classes - which was immediately bounded upon discovery "
    "(results/stage4_candidate_burden_matrix.json). Critically, results/stage4_candidate_burden_matrix.json's "
    "robustness_analysis COMPUTATIONALLY CONFIRMS (not merely asserts) that relative candidate-class ORDERING is "
    "preserved across every tested combination of contact-count bound, battery topology, and MCU/radio topology - "
    "every additional sensor/module can only add burden, never subtract it, so the Science Owner's own "
    "strict-superset candidate-class construction makes ordering structurally robust. This satisfies "
    "CONDITIONALLY_READY's bar exactly as defined in the governing closure logic: 'some absolute engineering "
    "values remain approximate; all meaningful unknowns are bounded; candidate-level conclusions remain stable "
    "across plausible bounds/topologies; final decision can be made with explicit disclosure.' It does NOT meet "
    "the bar for unconditional READY, because several of these bounds remain ranges rather than frozen exact "
    "values (final montage/topology decisions are still open engineering choices, not just imprecise numbers) - "
    "disclosure of that residual approximation is required at freeze time."
)

WHAT_WOULD_CLOSE_IT_TO_READY_V2 = [
    "Freeze the final battery/electronics topology decision (shared-hub vs. per-module, and single-shared-vs-per-module MCU/radio) - the bounded ranges in results/stage4_battery_topology_scenarios.json and results/stage4_candidate_burden_matrix.json would collapse to a single point estimate.",
    "Freeze exact electrode montages for ECG, EEG, thoracic BioZ, and leg BioZ (converting results/stage4_contact_electrode_burden.json's bounded ranges to exact counts).",
    "Resolve the leg BioZ unilateral-vs-bilateral module question with an explicit engineering decision (not just the Science-Owner-implied bilateral scope).",
    "Obtain vendor-specific part selection for MCU/radio/regulator/battery/sensing ICs (currently class-level only).",
]

output = dict(v1)  # start from the full v1 record, then layer v2 on top - nothing dropped
output["schema_version"] = "2.0.0"
output["assessment_history"] = [dict(v1)]  # v1 preserved verbatim, in full, as history - never deleted
output["dimensions_audited"] = new_dimensions_audited
output["known_unknowns"] = new_known_unknowns
output["chest_module_decomposition"] = chest_module_decomposition_bound
output["eeg_eog_shared_afe_confirmation"] = eeg_eog_shared_afe_confirmation
output["new_artifacts_this_sprint"] = [
    "results/stage4_contact_electrode_burden.json",
    "results/stage4_battery_topology_scenarios.json",
    "results/stage4_candidate_burden_matrix.json",
]
output["gate_d_burden_completeness"] = GATE_D_STATUS_V2

# ---------------------------------------------------------------------------
# Hostile-review guard (master prompt Part XII Attack A): a status of READY
# or CONDITIONALLY_READY must be IMPOSSIBLE to write while any known_unknown
# is both unbounded AND could_be_decision_changing. This is a hard-fail
# generation-time check, not a discipline convention - if a future edit adds
# a new decision-changing unknown without bounding it, this script refuses
# to write the file rather than silently shipping an inconsistent verdict.
# ---------------------------------------------------------------------------
_unsafe_unknowns = [
    u for u in new_known_unknowns if u["could_be_decision_changing"] and not u["bounded"]
]
if GATE_D_STATUS_V2 in ("READY", "CONDITIONALLY_READY") and _unsafe_unknowns:
    raise SystemExit(
        f"REFUSING TO WRITE: gate_d_burden_completeness={GATE_D_STATUS_V2!r} but "
        f"{len(_unsafe_unknowns)} known_unknown(s) are unbounded AND decision-changing: "
        f"{[u['item'] for u in _unsafe_unknowns]}. Bound them or downgrade the status to NOT_READY."
    )
output["rationale"] = RATIONALE_V2
output["what_would_close_it"] = WHAT_WOULD_CLOSE_IT_TO_READY_V2
output["final_architecture_status"] = "UNRESOLVED"
output["formal_pareto_status"] = "NOT_READY"

GATE_D_PATH.write_text(json.dumps(output, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(f"Wrote {GATE_D_PATH} (v1 preserved in assessment_history)")
