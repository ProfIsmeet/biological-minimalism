"""Stage 4 Gate-D closure: explicit contact/electrode topology model
(INTEGRATION_OWNER, master prompt Part I).

Extends results/hardware_topology_contract.json (which left electrode
counts as None/unresolved for ECG, thoracic BioZ, frontal EEG, leg BioZ)
with BOUNDED ranges [min, max] plus a most_likely point estimate and
explicit reasoning/provenance for each - never an invented single exact
number, never an unbounded UNKNOWN where a physical bound exists.

Distinguishes TOTAL_CONTACTS from INCREMENTAL_CONTACTS_ADDED per modality
so shared reference/ground electrodes (EEG+EOG) are never double-counted,
while explicitly NOT crediting sharing that the topology contract itself
says is unvalidated (ECG+thoracic BioZ).

New finding surfaced here (not previously disclosed in any Stage-4
artifact): the Science Owner's own results/stage4_architecture_candidate_classes.json
scopes leg BioZ as "legs (bilateral)" for EVIDENCE_EXTENDED, but
results/stage4_engineering_readiness.json's leg_module models only ONE
module instance with no statement of whether it represents one leg or
both - a genuine, currently-unbounded topology question (single
multiplexed module vs two independent modules) that could materially
change leg BioZ's mass/power burden. Flagged explicitly below and again
as a known_unknown in the Gate-D reassessment.

Writes results/stage4_contact_electrode_burden.json.
"""

from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
OUT_PATH = REPO_ROOT / "results" / "stage4_contact_electrode_burden.json"

topology = json.loads((REPO_ROOT / "results/hardware_topology_contract.json").read_text())
readiness = json.loads((REPO_ROOT / "results/stage4_engineering_readiness.json").read_text())
candidate_classes = json.loads((REPO_ROOT / "results/stage4_architecture_candidate_classes.json").read_text())

_components = {c["component_id"]: c for c in topology["components"]}

# EOG's own count is already CLOSED (not open) per the prior sprint's Gate D
# work - carried forward unchanged, not re-derived here.
EOG_INCREMENTAL_ELECTRODES = 2
EOG_MASS_NOTE = readiness["mass"]["eog_incremental_mass_g"]["note"]

modalities = [
    {
        "modality": "wrist_ppg_plus_imu",
        "anatomical_region": "wrist",
        "module_id": "wrist_module",
        "components": ["wrist_ppg", "wrist_imu"],
        "sensing_contacts": {"type": "optical_interface", "count": 1, "confidence": "CLOSED"},
        "reference_electrodes": {"count": 0},
        "ground_bias_electrodes": {"count": 0},
        "shared_with": [],
        "total_contacts": {"min": 1, "max": 1, "most_likely": 1, "unit": "optical_sites"},
        "incremental_contacts_if_added": {"wrist_ppg": 1, "wrist_imu": 0},
        "electrode_type": "reflective_optical (no electrode)",
        "disposable_or_reusable": "UNKNOWN - not specified in any project artifact",
        "attachment_type": "elastomer strap (wrist_module, shared)",
        "external_cable_required": False,
        "source": "results/hardware_topology_contract.json wrist_ppg/wrist_imu contact_burden (already fully resolved, no bounding needed).",
        "confidence": "CLOSED",
    },
    {
        "modality": "ecg_chest",
        "anatomical_region": "thorax",
        "module_id": "chest_module",
        "components": ["ecg_chest"],
        "sensing_contacts": {"type": "wet_or_adhesive_electrode", "min": 2, "max": 4, "most_likely": 2},
        "reference_electrodes": {"min": 1, "max": 1, "most_likely": 1, "note": "right-leg-drive-class reference/ground, standard for ADS1292R-class single-vector wearable ECG"},
        "ground_bias_electrodes": {"count": 0, "note": "folded into the single reference/RLD electrode above for a minimal single-vector design"},
        "shared_with": [],
        "total_contacts": {
            "min": 3,
            "max": 5,
            "most_likely": 3,
            "unit": "electrodes",
            "reasoning": (
                "ADS1292R is a 2-channel biopotential AFE (results/hardware_topology_contract.json evidence_id "
                "day6_ads1292r_datasheet). A minimal single-vector wearable ECG (the project's stated HR/HRV "
                "reference-signal use case, not diagnostic multi-lead ECG) needs 2 sensing electrodes + 1 "
                "reference/right-leg-drive electrode = 3 (most_likely, matching the project's HR-reference scope). "
                "A dual-vector 2-channel configuration (e.g. adding a respiration-impedance-style second derivation) "
                "would need up to 3 sensing + 1-2 reference/ground = 5 (max). dry_electrodes=0 is already confirmed "
                "in the topology contract, so wet/adhesive is the constrained electrode type, not an open question."
            ),
        },
        "incremental_contacts_if_added": {"min": 3, "max": 5, "most_likely": 3},
        "electrode_type": "wet_or_adhesive (dry_electrodes=0 confirmed in hardware_topology_contract.json)",
        "disposable_or_reusable": "UNKNOWN - not specified in any project artifact",
        "attachment_type": "adhesive patch set (chest_module, shared enclosure)",
        "external_cable_required": "UNKNOWN (hardware_topology_contract.json: null)",
        "source": "Bounded engineering estimate from ADS1292R-class 2-channel AFE + project's stated HR/HRV reference-signal scope. NOT a validated montage - this is the single most defensible bound available without a frozen electrode-count decision.",
        "confidence": "BOUNDED_ENGINEERING_ESTIMATE",
    },
    {
        "modality": "thoracic_bioz",
        "anatomical_region": "thorax",
        "module_id": "chest_module",
        "components": ["thoracic_bioz"],
        "sensing_contacts": {"type": "wet_or_adhesive_electrode", "min": 4, "max": 8, "most_likely": 4},
        "reference_electrodes": {"count": 0, "note": "tetrapolar method has no separate reference electrode - the 4 electrodes are 2 current-drive + 2 voltage-sense pairs"},
        "ground_bias_electrodes": {"count": 0},
        "shared_with": [],
        "total_contacts": {
            "min": 4,
            "max": 8,
            "most_likely": 4,
            "unit": "electrodes",
            "reasoning": (
                "The excitation scenario is already frozen as '50 kHz tetrapolar excitation' "
                "(results/stage4_engineering_readiness.json power.thoracic_bioz.scenario) - tetrapolar bioimpedance "
                "is a physically defined method requiring exactly 4 electrodes (2 current-injection + 2 "
                "voltage-sensing) as a hard minimum, not a guess. 8 (max) reflects clinical dual-band ICG designs "
                "using paired spot electrodes for improved signal quality; the frozen scenario says 'tetrapolar' "
                "(singular), not 'dual-band' or 'segmental', so 4 (most_likely) matches the already-frozen design intent."
            ),
        },
        "incremental_contacts_if_added": {
            "min": 4,
            "max": 8,
            "most_likely": 4,
            "note": "FULL count, no sharing credit taken - hardware_topology_contract.json chest_module explicitly states 'ECG/BioZ electrode sharing is not assumed until a montage is validated'. Shares the chest_module ENCLOSURE/battery/MCU/radio, but not contacts.",
        },
        "electrode_type": "wet_or_adhesive (dry_electrodes=0 confirmed)",
        "disposable_or_reusable": "UNKNOWN - not specified in any project artifact",
        "attachment_type": "adhesive patch set (chest_module, shared enclosure only, not contacts)",
        "external_cable_required": "UNKNOWN (hardware_topology_contract.json: null)",
        "source": "Tetrapolar electrode count is a physical constraint of the already-frozen excitation method, not an invented number. Upper bound is a clinical-practice reference range, not a project-specific decision.",
        "confidence": "PHYSICALLY_CONSTRAINED_BY_FROZEN_METHOD",
    },
    {
        "modality": "frontal_eeg",
        "anatomical_region": "head/forehead",
        "module_id": "head_module",
        "components": ["frontal_eeg"],
        "sensing_contacts": {"type": "dry_or_wet_electrode (type itself unresolved)", "min": 1, "max": 4, "most_likely": 1},
        "reference_electrodes": {"min": 1, "max": 1, "most_likely": 1},
        "ground_bias_electrodes": {"min": 1, "max": 1, "most_likely": 1},
        "shared_with": ["eog (reference + ground/bias)"],
        "total_contacts": {
            "min": 3,
            "max": 6,
            "most_likely": 3,
            "unit": "electrodes",
            "reasoning": (
                "results/stage4_engineering_readiness.json's already-frozen power scenario "
                "(power.head_afe_eeg_eog.scenario) models exactly '2 active_channels (1 EEG + 1 shared EOG)' - "
                "i.e. the frozen DESIGN INTENT is 1 EEG signal channel, not the full 4-channel capacity of the "
                "ADS1299-4-class AFE (evidence_id day6_ads1299_datasheet). A minimal single-derivation montage is "
                "1 signal + 1 reference + 1 ground/bias = 3 (most_likely, matches the frozen 1-channel power "
                "design point). Using the AFE's full 4-channel capacity would need up to 4 signal + reference + "
                "ground = 6 (max) - not the currently-modeled scenario, but physically available on the selected "
                "AFE class. Unlike ECG/thoracic-BioZ/leg-BioZ, dry_electrodes is None (not 0) in "
                "hardware_topology_contract.json - the electrode TYPE itself remains genuinely open, not just the count."
            ),
        },
        "incremental_contacts_if_added": {"min": 3, "max": 6, "most_likely": 3},
        "electrode_type": "UNRESOLVED (dry vs wet) - hardware_topology_contract.json frontal_eeg.contact_burden.dry_electrodes=null, unlike ECG/BioZ/leg where dry=0 is already confirmed",
        "disposable_or_reusable": "UNKNOWN - not specified in any project artifact",
        "attachment_type": "headband (head_module, shared)",
        "external_cable_required": False,
        "source": "Bounded engineering estimate derived from the already-frozen 1-active-EEG-channel power design point, cross-referenced with the ADS1299-4-class AFE's channel capacity. NOT a validated montage.",
        "confidence": "BOUNDED_ENGINEERING_ESTIMATE",
    },
    {
        "modality": "eog",
        "anatomical_region": "head/peri-ocular",
        "module_id": "head_module",
        "components": ["eog (not a separate hardware_topology_contract.json component_id - modeled only as an incremental line item in stage4_engineering_readiness.json)"],
        "sensing_contacts": {"type": "wet_or_adhesive_electrode", "count": EOG_INCREMENTAL_ELECTRODES, "confidence": "CLOSED"},
        "reference_electrodes": {"count": 0, "note": "shares frontal_eeg's reference electrode - not additive"},
        "ground_bias_electrodes": {"count": 0, "note": "shares frontal_eeg's ground/bias electrode - not additive"},
        "shared_with": ["frontal_eeg (reference + ground/bias, per already-frozen 'shares reference/bias, adds no new module' power-model note)"],
        "total_contacts": {
            "min": EOG_INCREMENTAL_ELECTRODES,
            "max": EOG_INCREMENTAL_ELECTRODES,
            "most_likely": EOG_INCREMENTAL_ELECTRODES,
            "unit": "electrodes",
            "reasoning": f"Already closed by the prior Closure Prep sprint: {EOG_MASS_NOTE}",
        },
        "incremental_contacts_if_added": {
            "min": EOG_INCREMENTAL_ELECTRODES,
            "max": EOG_INCREMENTAL_ELECTRODES,
            "most_likely": EOG_INCREMENTAL_ELECTRODES,
            "note": "This IS the total for EOG - it adds no reference/ground of its own, sharing frontal_eeg's entirely (rule: never double-count a shared electrode).",
        },
        "electrode_type": "wet_or_adhesive (ocular)",
        "disposable_or_reusable": "UNKNOWN - not specified in any project artifact",
        "attachment_type": "peri-ocular extension of head_module headband",
        "external_cable_required": False,
        "source": "results/stage4_engineering_readiness.json mass.eog_incremental_mass_g (already CLOSED in the prior Closure Prep sprint) - carried forward unchanged, not re-derived.",
        "confidence": "CLOSED",
    },
    {
        "modality": "leg_bioz",
        "anatomical_region": "lower leg(s)",
        "module_id": "leg_module",
        "components": ["leg_bioz"],
        "sensing_contacts": {"type": "wet_or_adhesive_electrode", "min": 4, "max": 8, "most_likely": 8},
        "reference_electrodes": {"count": 0, "note": "tetrapolar method, same as thoracic BioZ"},
        "ground_bias_electrodes": {"count": 0},
        "shared_with": [],
        "total_contacts": {
            "min": 4,
            "max": 8,
            "most_likely": 8,
            "unit": "electrodes",
            "reasoning": (
                "results/stage4_engineering_readiness.json power.leg_bioz explicitly uses 'Same AD5940-class "
                "engineering assumption as thoracic_bioz' - i.e. the same frozen tetrapolar method, 4 electrodes "
                "PER LEG SEGMENT minimum. NEW FINDING (not previously disclosed in any Stage-4 artifact): "
                "results/stage4_architecture_candidate_classes.json (Science Owner) explicitly scopes EVIDENCE_EXTENDED's "
                "anatomical_regions as 'legs (bilateral)' - both legs, not one - but results/stage4_engineering_readiness.json's "
                "leg_module is silent on whether it represents one leg or both. Taking the Science Owner's explicit "
                "bilateral scope at face value (most_likely=8, 4 electrodes/leg x 2 legs) rather than the engineering "
                "model's silent single-instance treatment (min=4, unilateral, which would CONTRADICT the Science "
                "Owner's stated scope) is the more defensible reading; the 4-electrode unilateral figure is kept "
                "as the physical floor, not the recommended value."
            ),
        },
        "incremental_contacts_if_added": {
            "min": 4,
            "max": 8,
            "most_likely": 8,
            "note": "New body region, no sharing possible with any other modality.",
        },
        "electrode_type": "wet_or_adhesive (dry_electrodes=0 confirmed)",
        "disposable_or_reusable": "UNKNOWN - not specified in any project artifact",
        "attachment_type": "strap (leg_module)",
        "external_cable_required": "UNKNOWN (hardware_topology_contract.json: null)",
        "source": "Tetrapolar-per-leg count is physically constrained by the already-frozen method; bilateral scoping is Science-Owner-stated (candidate_classes.json), not Integration-Owner-invented.",
        "confidence": "PHYSICALLY_CONSTRAINED_BY_FROZEN_METHOD_PLUS_SCIENCE_OWNER_SCOPE",
        "unresolved_topology_question": {
            "question": "Does bilateral leg BioZ require ONE shared/multiplexed leg_module (single battery/enclosure/MCU, AD5940-class chips are datasheet-capable of sequenced multi-channel switching per hardware_topology_contract.json's own AD5940 rationale) or TWO independent leg_module instances (one per leg, doubling battery/enclosure/PCB/wiring mass and power)?",
            "why_it_matters": "results/stage4_engineering_readiness.json currently models exactly ONE leg_module instance (8.431 g, 1.33485 mW). If two independent modules are actually required, leg BioZ's mass/power burden for EVIDENCE_EXTENDED and EXPERIMENTAL_EXTENDED roughly DOUBLES (to ~16.86 g / ~2.67 mW) - a materially decision-relevant swing given the system's base-topology totals are only ~30.5 g / ~7.24 mW.",
            "bounded": False,
            "could_be_decision_changing": True,
        },
    },
    {
        "modality": "second_ppg_site",
        "anatomical_region": "finger/phalanx",
        "module_id": "optical_site_evaluation_branch",
        "components": ["second_ppg_site"],
        "sensing_contacts": {"type": "optical_interface", "count": 1, "confidence": "CLOSED"},
        "reference_electrodes": {"count": 0},
        "ground_bias_electrodes": {"count": 0},
        "shared_with": [],
        "total_contacts": {"min": 1, "max": 1, "most_likely": 1, "unit": "optical_sites"},
        "incremental_contacts_if_added": {"min": 1, "max": 1, "most_likely": 1},
        "electrode_type": "reflective_optical (no electrode)",
        "disposable_or_reusable": "UNKNOWN - not specified in any project artifact",
        "attachment_type": "UNKNOWN (hardware_topology_contract.json optical_site_evaluation_branch: OPEN_BOUNDARY, shared/tethered/standalone unresolved)",
        "external_cable_required": "UNKNOWN (hardware_topology_contract.json: null)",
        "source": "results/hardware_topology_contract.json second_ppg_site contact_burden (electrode count already resolved; module BOUNDARY, not contact count, is what remains open). Already excluded from every base-system total per rule 48 - not a Gate-D blocker.",
        "confidence": "CLOSED_FOR_CONTACTS_OPEN_FOR_MODULE_BOUNDARY",
    },
]

output = {
    "artifact_id": "biological-minimalism-stage4-contact-electrode-burden-v1",
    "schema_version": "1.0.0",
    "sprint": "STAGE4_GATE_D_BURDEN_CLOSURE",
    "generated_role": "INTEGRATION_OWNER",
    "purpose": (
        "Bounded contact/electrode topology model for every architecture-relevant electrophysiological/impedance "
        "modality, closing (with explicit ranges, never fabricated exact numbers) the electrode/contact-count gap "
        "identified as one of Gate D's 4 governing remediation items in results/stage4_gate_d_burden_completeness.json."
    ),
    "method": (
        "Every bound is either (a) CLOSED - already established and unchanged from the prior Closure Prep sprint "
        "(EOG's +2 electrodes), (b) PHYSICALLY_CONSTRAINED_BY_FROZEN_METHOD - a hard minimum implied by an "
        "already-frozen measurement method (tetrapolar bioimpedance = 4 electrodes), or (c) BOUNDED_ENGINEERING_ESTIMATE "
        "- derived from an already-frozen AFE channel-count/power design point plus standard wearable-sensor "
        "engineering practice, explicitly NOT a validated montage. No count is invented without one of these three bases."
    ),
    "source_artifacts": [
        "results/hardware_topology_contract.json",
        "results/stage4_engineering_readiness.json",
        "results/stage4_architecture_candidate_classes.json",
        "results/stage4_gate_d_burden_completeness.json",
    ],
    "modalities": modalities,
    "new_findings_not_previously_disclosed": [
        {
            "finding": "leg_bioz_bilateral_module_topology_ambiguity",
            "summary": "Science Owner scopes leg BioZ as bilateral (candidate_classes.json); engineering model is silent on unilateral-vs-bilateral module count, creating a potential ~2x understatement of leg BioZ mass/power if two independent modules are actually required.",
        },
        {
            "finding": "eog_not_a_hardware_topology_contract_component",
            "summary": "results/hardware_topology_contract.json's stable_component_ids list has no 'eog' entry at all - EOG exists only as an incremental power/mass line item in results/stage4_engineering_readiness.json, predating that artifact. Not a blocking gap (EOG's incremental burden is already closed), but noted for completeness/traceability.",
        },
    ],
    "final_architecture_status": "UNRESOLVED",
    "formal_pareto_status": "NOT_READY",
}

OUT_PATH.write_text(json.dumps(output, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(f"Wrote {OUT_PATH}")
