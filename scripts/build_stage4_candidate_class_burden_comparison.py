"""Stage 4 closure-prep: per-candidate-class burden comparison (INTEGRATION_OWNER).

Joins the Science Owner's 4 candidate architecture classes
(results/stage4_architecture_candidate_classes.json - no winner selected
there, none selected here) against the already-frozen engineering numbers in
results/stage4_engineering_readiness.json. No new physics/arithmetic is
invented: component-level power and data-rate contributors are additive and
are summed per class from already-published per-component values (one
subtraction is used to isolate the EEG-only baseline from the published
head_afe_eeg_eog total and its already-published eog_incremental_power_mw -
shown explicitly, not hidden). Mass is reported at MODULE granularity only,
because results/hardware_topology_contract.json's chest_module bundles
ECG+thoracic-BioZ as one estimate that cannot be decomposed per sensor
(see results/stage4_gate_d_burden_completeness.json shared_resource_accounting).
No arbitrary composite score is computed (rule: multi-objective only).
Writes results/stage4_candidate_class_burden_comparison.json.
"""

from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
OUT_PATH = REPO_ROOT / "results" / "stage4_candidate_class_burden_comparison.json"

readiness = json.loads((REPO_ROOT / "results/stage4_engineering_readiness.json").read_text())
candidate_classes = json.loads((REPO_ROOT / "results/stage4_architecture_candidate_classes.json").read_text())
_pareto_inputs = json.loads((REPO_ROOT / "results/stage4_scientific_pareto_inputs.json").read_text())

contributors_mw = readiness["power"]["system_average_power"]["contributors_mw"]
data_rate_bps = readiness["data_rate"]["base_topology_raw_bps"]
eog_incremental_mw = readiness["power"]["head_afe_eeg_eog"]["eog_incremental_power_mw"]["value"]
head_afe_total_mw = readiness["power"]["head_afe_eeg_eog"]["average_power_mw"]["value"]
eeg_only_baseline_mw = round(head_afe_total_mw - eog_incremental_mw, 6)  # 1.5 - 0.375 = 1.125, shown not hidden
thoracic_bioz_mw = contributors_mw["thoracic_bioz"]
thoracic_bioz_bps = data_rate_bps["thoracic_bioz"]
leg_bioz_mw = readiness["power"]["system_average_power"]["excluded_from_base_total"]["leg_bioz_mw"]
leg_bioz_bps = readiness["data_rate"]["excluded_from_base_total_bps"]["leg_bioz"]
leg_module_mass_g = readiness["mass"]["modules"]["leg_module"]["module_total_g"]
second_ppg_mw = readiness["power"]["system_average_power"]["excluded_from_base_total"]["second_ppg_site_incl_led_mw"]
second_ppg_bps = readiness["data_rate"]["excluded_from_base_total_bps"]["second_ppg_site"]

SHARED_INFRA_MW = round(contributors_mw["mcu"] + contributors_mw["radio"], 6)  # required by every class, applied once

DECOMPOSITION_LIMITATION = (
    "Module mass (wrist_module/chest_module/head_module/leg_module) is reported as a single per-module "
    "allowance in results/stage4_engineering_readiness.json and cannot be decomposed per sensor within a shared "
    "module (see results/stage4_gate_d_burden_completeness.json shared_resource_accounting.ecg_plus_thoracic_bioz). "
    "Where a class excludes a sensor that shares a module with an included sensor (e.g. MINIMAL_CORE excludes "
    "thoracic BioZ but includes ECG, both in chest_module), this comparison reports the FULL published module mass "
    "for every class that includes at least one sensor from that module, and flags the resulting mass figure "
    "BURDEN_DATA_INCOMPLETE for classes that would, in reality, have a smaller (but currently unquantifiable) module."
)

classes_out = []
for cls in candidate_classes["classes"]:
    cid = cls["class_id"]
    sensors = cls["sensors"]

    if cid == "MINIMAL_CORE":
        power_components = {
            "wrist_ppg_incl_led": contributors_mw["wrist_ppg_total_incl_led"],
            "wrist_imu": contributors_mw["wrist_imu"],
            "ecg_chest_afe": contributors_mw["ecg_chest_afe"],
            "frontal_eeg_only_derived": eeg_only_baseline_mw,
        }
        modules_required = ["wrist_module", "chest_module (shares thoracic BioZ circuitry - see limitation)", "head_module"]
        data_rate_components = {"wrist_ppg": data_rate_bps["wrist_ppg"], "wrist_imu": data_rate_bps["wrist_imu"], "ecg_chest": data_rate_bps["ecg_chest"]}
        dominance_flag = "PARETO_RELEVANT"
        dominance_reason = "Tier-A evidence only; no HIGH-decision-sensitivity dependency; lowest sensor count."
    elif cid == "CORE_PLUS_CONTEXT":
        power_components = {
            "wrist_ppg_incl_led": contributors_mw["wrist_ppg_total_incl_led"],
            "wrist_imu": contributors_mw["wrist_imu"],
            "ecg_chest_afe": contributors_mw["ecg_chest_afe"],
            "head_afe_eeg_plus_eog": head_afe_total_mw,
        }
        modules_required = ["wrist_module", "chest_module (shares thoracic BioZ circuitry - see limitation)", "head_module"]
        data_rate_components = {"wrist_ppg": data_rate_bps["wrist_ppg"], "wrist_imu": data_rate_bps["wrist_imu"], "ecg_chest": data_rate_bps["ecg_chest"], "head_eeg_eog_scientific": data_rate_bps["head_eeg_eog_scientific"]}
        dominance_flag = "PARETO_RELEVANT"
        dominance_reason = "EOG's isolated incremental burden (+0.375 mW, +0.4 g) is small; HIGH decision sensitivity to pending HMC full-cohort result (Gate E), not a burden concern."
    elif cid == "EVIDENCE_EXTENDED":
        power_components = {
            "wrist_ppg_incl_led": contributors_mw["wrist_ppg_total_incl_led"],
            "wrist_imu": contributors_mw["wrist_imu"],
            "ecg_chest_afe": contributors_mw["ecg_chest_afe"],
            "head_afe_eeg_plus_eog": head_afe_total_mw,
            "thoracic_bioz": thoracic_bioz_mw,
            "leg_bioz": leg_bioz_mw,
        }
        modules_required = ["wrist_module", "chest_module", "head_module", "leg_module (new body region)"]
        data_rate_components = {"wrist_ppg": data_rate_bps["wrist_ppg"], "wrist_imu": data_rate_bps["wrist_imu"], "ecg_chest": data_rate_bps["ecg_chest"], "head_eeg_eog_scientific": data_rate_bps["head_eeg_eog_scientific"], "thoracic_bioz": thoracic_bioz_bps, "leg_bioz": leg_bioz_bps}
        dominance_flag = "POTENTIALLY_DOMINATED"
        dominance_reason = (
            "leg BioZ adds a genuinely new body region + attachment/contact burden (leg_module, "
            f"{leg_module_mass_g} g, excluded from every base total) for TIER_D_MIXED_OR_FRAGILE evidence "
            "(pareto_inputs incremental_value=MIXED, decision_fragility=HIGH); thoracic BioZ adds real, non-trivial "
            f"power ({thoracic_bioz_mw} mW - one of the largest single contributors) for MIXED/negative-leaning "
            "evidence with no new body region. Per the Science Owner's own governing rule "
            "('low burden does not transform weak evidence into strong evidence'), both warrant scrutiny; "
            "confirmed DOMINATED status requires Integration Owner's engineering burden confirmation (module-boundary, "
            "electrode counts) that Gate D has not yet closed."
        )
    else:  # EXPERIMENTAL_EXTENDED
        power_components = {
            "wrist_ppg_incl_led": contributors_mw["wrist_ppg_total_incl_led"],
            "wrist_imu": contributors_mw["wrist_imu"],
            "ecg_chest_afe": contributors_mw["ecg_chest_afe"],
            "head_afe_eeg_plus_eog": head_afe_total_mw,
            "thoracic_bioz": thoracic_bioz_mw,
            "leg_bioz": leg_bioz_mw,
            "second_ppg_site_incl_led": second_ppg_mw,
            "skin_temperature": contributors_mw["skin_temperature"],
            "light_sensor": contributors_mw["light_sensor"],
        }
        modules_required = ["wrist_module", "chest_module", "head_module", "leg_module (new body region)", "optical_site_evaluation_branch (OPEN_BOUNDARY - module boundary unresolved)"]
        data_rate_components = {"wrist_ppg": data_rate_bps["wrist_ppg"], "wrist_imu": data_rate_bps["wrist_imu"], "ecg_chest": data_rate_bps["ecg_chest"], "head_eeg_eog_scientific": data_rate_bps["head_eeg_eog_scientific"], "thoracic_bioz": thoracic_bioz_bps, "leg_bioz": leg_bioz_bps, "second_ppg_site": second_ppg_bps, "skin_temperature": data_rate_bps["skin_temperature"], "light_sensor": data_rate_bps["light_sensor"]}
        dominance_flag = "POTENTIALLY_DOMINATED"
        dominance_reason = (
            f"second-site PPG adds a new physical/optical sensing site with real burden ({second_ppg_mw} mW, "
            f"{second_ppg_bps} bps - both larger than several already-included modalities) for a "
            "TIER_E_NEGATIVE_OR_DEPRIORITIZED, consistently-negative result (pareto_inputs incremental_value=NEGATIVE). "
            "Wrist temperature/light are TIER_P_PENDING with no governing experiment at all. This class is explicitly "
            "exploratory per the Science Owner's own candidate_classes.json, never evidence-supported."
        )

    sensor_power_subtotal_mw = round(sum(power_components.values()), 6)

    classes_out.append({
        "class_id": cid,
        "description": cls["description"],
        "sensors": sensors,
        "evidence_confidence": cls["evidence_confidence"],
        "pending_science_exposure": cls["pending_science_exposure"],
        "power": {
            "sensor_components_mw": power_components,
            "sensor_subtotal_mw": sensor_power_subtotal_mw,
            "shared_infrastructure_mcu_radio_mw": SHARED_INFRA_MW,
            "note": "Regulator efficiency (0.85) not applied here at the per-class level; see results/stage4_engineering_readiness.json for the system-level battery-side conversion. shared_infrastructure applies once regardless of class (every configuration needs one MCU+radio).",
        },
        "data_rate_raw_bps": data_rate_components,
        "mass": {
            "modules_required": modules_required,
            "status": "BURDEN_DATA_INCOMPLETE",
            "limitation": DECOMPOSITION_LIMITATION,
        },
        "dominance_flag": dominance_flag,
        "dominance_reason": dominance_reason,
    })

output = {
    "artifact_id": "biological-minimalism-stage4-candidate-class-burden-comparison-v1",
    "schema_version": "1.0.0",
    "sprint": "STAGE4_CLOSURE_PREP",
    "generated_role": "INTEGRATION_OWNER",
    "purpose": (
        "Multi-objective burden comparison across the Science Owner's 4 candidate architecture classes "
        "(results/stage4_architecture_candidate_classes.json). No winner selected, no composite score computed."
    ),
    "explicit_non_goal": "Does NOT compute TOTAL_SCORE = SCIENCE - MASS - POWER or any weighted composite. Does NOT select a final architecture.",
    "derivation_note": (
        f"frontal_eeg_only_derived ({eeg_only_baseline_mw} mW) = head_afe_eeg_eog.average_power_mw "
        f"({head_afe_total_mw}) - eog_incremental_power_mw ({eog_incremental_mw}), both already-published "
        "ENGINEERING_ASSUMPTION values in results/stage4_engineering_readiness.json - a single disclosed "
        "subtraction, not a new measurement or a re-labeled datasheet fact."
    ),
    "source_artifacts": [
        "results/stage4_engineering_readiness.json",
        "results/stage4_architecture_candidate_classes.json",
        "results/stage4_scientific_pareto_inputs.json",
        "results/stage4_gate_d_burden_completeness.json",
    ],
    "classes": classes_out,
    "allowed_dominance_flags": ["PARETO_RELEVANT", "POTENTIALLY_DOMINATED", "BURDEN_DATA_INCOMPLETE"],
    "note_on_dominance": "PARETO_RELEVANT/POTENTIALLY_DOMINATED here are flags for further analysis, not final dominance rulings - GATE_D_BURDEN_COMPLETENESS is NOT_READY (results/stage4_gate_d_burden_completeness.json), so no configuration is confirmed DOMINATED.",
    "final_architecture_status": "UNRESOLVED",
    "formal_pareto_status": "NOT_READY",
}

OUT_PATH.write_text(json.dumps(output, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(f"Wrote {OUT_PATH}")
