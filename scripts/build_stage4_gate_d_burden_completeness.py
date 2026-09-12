"""Stage 4 closure-prep: Gate D (BURDEN_COMPLETENESS) honest readiness assessment
(INTEGRATION_OWNER deliverable, per results/stage4_architecture_acceptance_gates.json
gate_id=GATE_D_BURDEN_COMPLETENESS, what_closes_it).

Answers "is the engineering burden model sufficiently complete to support a
final architecture decision?" - NOT "are the arithmetic sums correct?" (they
already are; see results/stage4_engineering_readiness.json and
results/independent_engineering_arithmetic_check_day12.json). This script
recomputes nothing: every number cited here is read from already-frozen
artifacts. Writes results/stage4_gate_d_burden_completeness.json.
"""

from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
OUT_PATH = REPO_ROOT / "results" / "stage4_gate_d_burden_completeness.json"

ENGINEERING_READINESS_PATH = "results/stage4_engineering_readiness.json"
TOPOLOGY_PATH = "results/hardware_topology_contract.json"

readiness = json.loads((REPO_ROOT / ENGINEERING_READINESS_PATH).read_text())
_topology = json.loads((REPO_ROOT / TOPOLOGY_PATH).read_text())  # validated present; referenced by path below

power = readiness["power"]["system_average_power"]
mass = readiness["mass"]
data_rate = readiness["data_rate"]
bom = readiness["bom"]

# ---------------------------------------------------------------------------
# Dimension-by-dimension audit (closure-prep master prompt Sections 16-20:
# body region, module, battery, enclosure, strap/mounting, electrodes,
# contact count, wiring/cabling, connector, data rate, compute, power,
# shared infrastructure, additional body-site burden).
# ---------------------------------------------------------------------------
dimensions_audited = [
    {
        "dimension": "body_region_and_module_count",
        "status": "AVAILABLE",
        "evidence": "results/hardware_topology_contract.json defines 4 FROZEN_REFERENCE modules (wrist, chest, head, leg) + 1 OPEN_BOUNDARY module (optical_site_evaluation_branch/second_ppg_site).",
        "gap": None,
    },
    {
        "dimension": "battery",
        "status": "ENGINEERING_ASSUMPTION",
        "evidence": "150 mAh / 3.7 V Li-Po reference class, 190 Wh/kg -> 2.921 g/module, applied per-module (conservative 'each module self-powered' assumption).",
        "gap": "Shared-hub-vs-per-module battery boundary is explicitly OPEN (hardware_topology_contract.json optical_site_evaluation_branch note; mass report 'Unresolved mechanical items'). A shared-hub design could materially reduce total battery mass for multi-module configurations (EVIDENCE_EXTENDED, EXPERIMENTAL_EXTENDED) relative to the per-module assumption used here - not bounded either direction.",
    },
    {
        "dimension": "enclosure_and_attachment_strap",
        "status": "ENGINEERING_ALLOWANCE_MECHANICAL_ESTIMATE",
        "evidence": "Generic per-module polymer-shell (1.5-3.0 g) and strap/patch/headband (3.0-4.0 g) allowances, Tier2 (electronics-subassembly estimate).",
        "gap": "No CAD/geometry (Tier3) or measured (Tier4) evidence anywhere; generic allowance only.",
    },
    {
        "dimension": "electrodes_and_contact_count",
        "status": "MISSING",
        "evidence": "hardware_topology_contract.json components[*].contact_burden.dry_electrodes/adhesive_or_wet_electrodes/physical_sensing_sites is None (unresolved) for ecg_chest, thoracic_bioz, frontal_eeg, and leg_bioz. Only the +2 ocular electrodes for EOG (0.4 g incremental) is a defensible, closed count.",
        "gap": "ECG montage electrode count, EEG montage electrode count, and thoracic/leg BioZ electrode count/material are all genuinely unresolved (None, not a bounded range) - not merely imprecise, but absent.",
    },
    {
        "dimension": "wiring_and_cabling",
        "status": "ENGINEERING_ALLOWANCE_MECHANICAL_ESTIMATE",
        "evidence": "Generic per-module interconnect allowance (0.2-0.8 g) included in every module total.",
        "gap": "Inter-module wiring harness / external cabling to a shared hub (if that topology were selected) is explicitly not modeled (mass report 'not_included').",
    },
    {
        "dimension": "connector_burden",
        "status": "MISSING",
        "evidence": "No connector-level BOM line exists anywhere in reference_bom_readiness_day11_part2.json or stage4_engineering_readiness.json.",
        "gap": "Not modeled at all; folded implicitly (if at all) into the generic wiring allowance.",
    },
    {
        "dimension": "power",
        "status": "PARTIAL_READY",
        "evidence": f"Battery-side system total {power['base_topology_battery_side_mw']['value']} mW covers every base-topology sensor rail, MCU, radio, and a single regulator-efficiency boundary; every previously-open blocker (LED, head AFE, BioZ, MCU/radio numeric points, duty cycle) now has an explicit value.",
        "gap": "Every closed value is ENGINEERING_ASSUMPTION, not measured/vendor-verified; enclosure/thermal effects, battery self-discharge, and charging-circuit power are explicitly excluded from every total.",
    },
    {
        "dimension": "data_rate",
        "status": "PARTIAL_READY_RAW_ONLY",
        "evidence": f"Raw acquisition ({data_rate['system_raw_total_bps']['value']} bps) and transmitted-with-overhead ({data_rate['system_transmitted_bps']['value']} bps) are closed for the base topology.",
        "gap": f"Processed/on-device data rate: {data_rate['processed_data_rate_status']} - {data_rate['processed_data_rate_reason']}",
    },
    {
        "dimension": "compute_burden",
        "status": "ENGINEERING_ASSUMPTION",
        "evidence": "MCU duty-cycle scenario (10% active, feature-extraction/fusion burst) folded into the 1.65594 mW MCU contributor.",
        "gap": "No actual on-device model/feature-extraction implementation exists to verify this duty-cycle assumption against; it is not tied to the processed-data-rate unknown above.",
    },
    {
        "dimension": "shared_infrastructure_and_resource_credit",
        "status": "PARTIALLY_MODELED",
        "evidence": "Wrist PPG+IMU share one wrist_module (no separate module charged twice). EOG's incremental cost over EEG-alone is isolated and small (+0.375 mW, +0.4 g) because it shares the head module's AFE/battery/enclosure. ECG+thoracic BioZ share one chest_module (hardware_topology_contract.json component_ids=[ecg_chest, thoracic_bioz]).",
        "gap": "The chest_module's mass total (9.541 g) was estimated as one combined ECG+thoracic-BioZ allowance, not built bottom-up per sub-component - there is no artifact that isolates 'ECG-only chest module mass' from 'ECG+BioZ chest module mass'. A candidate class that drops thoracic BioZ (e.g. MINIMAL_CORE, CORE_PLUS_CONTEXT) therefore cannot be assigned a precise reduced chest-module mass; only the qualitative direction (smaller) is known. Whether EOG's shared-AFE assumption is engineering-confirmed (vs. merely asserted) also remains an open determination per results/stage4_architecture_candidate_classes.json's own text.",
    },
]

shared_resource_accounting = {
    "wrist_ppg_plus_imu": {
        "claim": "Same body region, same module (wrist_module), no new electrodes - IMU adds zero incremental module/enclosure/battery/strap burden.",
        "evidence_class": "ENGINEERING_ALLOWANCE_MECHANICAL_ESTIMATE",
        "status": "CONFIRMED_IN_TOPOLOGY_CONTRACT",
        "source": "results/hardware_topology_contract.json wrist_module.component_ids includes both wrist_ppg and wrist_imu.",
    },
    "eeg_plus_eog": {
        "claim": "Shared AFE/reference/ground/head infrastructure; EOG's entire incremental burden is +0.375 mW (2nd-channel current) and +0.4 g (2 ocular electrodes + leads only).",
        "evidence_class": "ENGINEERING_ASSUMPTION / ENGINEERING_ALLOWANCE_MECHANICAL_ESTIMATE",
        "status": "MODELED_BUT_NOT_ENGINEERING_CONFIRMED",
        "source": "results/stage4_engineering_readiness.json power.head_afe_eeg_eog.eog_incremental_power_mw, mass.eog_incremental_mass_g.",
        "caveat": "results/stage4_architecture_candidate_classes.json (Science Owner) itself states shared-AFE co-location feasibility is 'Integration Owner's determination, not yet made' - this report treats it as an engineering assumption, not a confirmed determination.",
    },
    "ecg_plus_thoracic_bioz": {
        "claim": "Share one chest_module (enclosure/battery/host MCU/radio/clock), but electrode/contact sharing is explicitly NOT assumed.",
        "evidence_class": "ENGINEERING_ALLOWANCE_MECHANICAL_ESTIMATE",
        "status": "MODULE_SHARED_BUT_SUBMASS_NOT_DECOMPOSABLE",
        "source": "results/hardware_topology_contract.json chest_module notes: 'ECG/BioZ electrode sharing is not assumed until a montage is validated.'",
    },
    "trunk_plus_leg_bioz": {
        "claim": "Leg BioZ is a genuinely separate module (leg_module): new body region, new attachment, its own battery/enclosure/wiring allowance.",
        "evidence_class": "ENGINEERING_ALLOWANCE_MECHANICAL_ESTIMATE",
        "status": "CORRECTLY_MODELED_AS_ADDITIONAL_BURDEN",
        "source": "results/stage4_engineering_readiness.json mass.modules.leg_module (8.431 g, excluded from every system total per rule 47).",
    },
}

known_unknowns = [
    {
        "item": "Shared-hub vs. per-module battery/electronics boundary",
        "why_it_matters": "Determines whether multi-module configurations (EVIDENCE_EXTENDED, EXPERIMENTAL_EXTENDED) pay a full battery+enclosure+MCU+radio cost per module or a shared cost - a potentially multi-gram, multi-mW swing.",
        "bounded": False,
        "could_be_decision_changing": True,
    },
    {
        "item": "ECG / EEG-main / thoracic-BioZ / leg-BioZ electrode and contact counts",
        "why_it_matters": "Contact/electrode count is one of the four HARD_BLOCK burden dimensions per GATE_D_BURDEN_COMPLETENESS's own requirement text (body region, contact/electrode count, module count, attachment/strap burden) - three of four sensing modalities have no count at all (None), not merely an estimate.",
        "bounded": False,
        "could_be_decision_changing": True,
    },
    {
        "item": "Processed/on-device data rate",
        "why_it_matters": "Raw and transmitted rates are known; processed rate depends on a feature-extraction/compression pipeline that does not exist yet. Affects storage/compute burden comparisons, not the current power total (MCU duty-cycle is an independent assumption).",
        "bounded": False,
        "could_be_decision_changing": False,
    },
    {
        "item": "Vendor-specific part selection (MCU, radio, regulator, battery, all sensing ICs)",
        "why_it_matters": "Every number is class-level (e.g. 'Cortex-M4F BLE SoC class') with an engineering-assumption operating point, not a specific datasheet-verified part.",
        "bounded": True,
        "could_be_decision_changing": False,
    },
]

GATE_D_STATUS = "NOT_READY"
RATIONALE = (
    "Arithmetic is independently verified correct (results/independent_engineering_arithmetic_check_day12.json) "
    "and every previously-open power/mass/data-rate blocker now has an explicit, separately-labeled value - this is genuine "
    "progress over Day-11 Part-2's NOT_READY baseline. However, GATE_D_BURDEN_COMPLETENESS requires burden accounting across "
    "body region, contact/electrode count, module count, and attachment/strap burden (not chip/component count alone). Two of "
    "the known_unknowns above are NOT bounded (electrode/contact counts are literally absent - None - for 3 of 4 electrode-bearing "
    "modalities; the shared-hub-vs-per-module battery boundary is a completely open topology choice with no stated interval either "
    "direction) and both could plausibly change how burden compares across candidate classes (e.g. how much leg BioZ or the second "
    "PPG site actually cost once module-sharing is resolved; how much any electrode-heavy configuration weighs once montages are "
    "frozen). Per the closure-prep master prompt's own Gate D closure logic, CONDITIONALLY_READY requires 'uncertainties are "
    "explicitly bounded' - that is not yet true here. NOT_READY is the honest classification; CONDITIONALLY_READY would require "
    "converting the electrode-count and module-boundary unknowns into stated bounded ranges first."
)

WHAT_WOULD_CLOSE_IT = [
    "Freeze the module-boundary decision (shared hub vs. per-module electronics/battery) so battery/enclosure/wiring mass and MCU/radio power can be apportioned once per system rather than once per module - OR, short of freezing it, publish a bounded interval (best case shared-hub / worst case per-module) for every multi-module candidate class.",
    "Freeze electrode/contact counts for ECG, EEG main montage, and thoracic/leg BioZ (or publish an explicit bounded range with a stated worst case), matching the precedent already set for EOG's +2-electrode count.",
    "Decompose (or explicitly bound) the chest_module's combined ECG+thoracic-BioZ mass into per-sensor contributions, or accept and disclose that MINIMAL_CORE/CORE_PLUS_CONTEXT's chest-module mass is only qualitatively (not quantitatively) lower than EVIDENCE_EXTENDED's.",
    "Obtain Integration Owner engineering confirmation (not assumption) that EEG+EOG shared-AFE co-location is feasible on the selected AFE part, since results/stage4_architecture_candidate_classes.json itself flags this as an unmade determination.",
]

output = {
    "artifact_id": "biological-minimalism-stage4-gate-d-burden-completeness-v1",
    "schema_version": "1.0.0",
    "sprint": "STAGE4_CLOSURE_PREP",
    "generated_role": "INTEGRATION_OWNER",
    "gate_reference": "results/stage4_architecture_acceptance_gates.json#GATE_D_BURDEN_COMPLETENESS",
    "primary_question": "Is the engineering burden model sufficiently complete to support a final architecture decision? (NOT: are the arithmetic sums correct - they already are.)",
    "source_artifacts": [
        ENGINEERING_READINESS_PATH,
        TOPOLOGY_PATH,
        "results/independent_engineering_arithmetic_check_day12.json",
        "results/reference_bom_readiness_day11_part2.json",
        "results/reference_mass_readiness_day11_part2.json",
        "results/reference_power_budget_day11_part2.json",
        "results/reference_data_rate_budget_day11.json",
    ],
    "dimensions_audited": dimensions_audited,
    "shared_resource_accounting": shared_resource_accounting,
    "known_unknowns": known_unknowns,
    "bom_final": bom["final"],
    "bom_still_missing": bom["still_missing"],
    "gate_d_burden_completeness": GATE_D_STATUS,
    "rationale": RATIONALE,
    "what_would_close_it": WHAT_WOULD_CLOSE_IT,
    "final_architecture_status": "UNRESOLVED",
    "formal_pareto_status": "NOT_READY",
}

if mass["system_mass_status"] != "PARTIAL":
    raise SystemExit(f"Unexpected upstream mass status {mass['system_mass_status']!r}; re-check this script's claims.")

OUT_PATH.write_text(json.dumps(output, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(f"Wrote {OUT_PATH}")
