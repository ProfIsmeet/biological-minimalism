"""Stage 4 closure-prep: Gate E (PENDING_SCIENCE_SENSITIVITY) Coordinator options
(master prompt Part V, INTEGRATION_OWNER prepares - does NOT choose).

For each HIGH-decision-sensitivity item in
results/stage4_sensor_decision_sensitivity.json (currently: EOG/HMC,
sparse-vs-full EEG/ds003838), prepares the three explicit options the
gate requires (results/stage4_architecture_acceptance_gates.json
GATE_E_PENDING_SCIENCE_SENSITIVITY): WAIT / FREEZE_CONDITIONALLY /
FREEZE_DESPITE_UNCERTAINTY_WITH_DISCLOSURE. No option is selected here -
that is explicitly Emir/Project Coordinator's call. Decision-flip
scenarios are cited verbatim from the Science Owner artifact, never
reinterpreted. Writes results/stage4_gate_e_coordinator_options.json.
"""

from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
OUT_PATH = REPO_ROOT / "results" / "stage4_gate_e_coordinator_options.json"

sensitivity = json.loads((REPO_ROOT / "results/stage4_sensor_decision_sensitivity.json").read_text())
by_modality = {s["modality"]: s for s in sensitivity["sensors"]}
consumption_manifest = json.loads((REPO_ROOT / "results/stage4_science_consumption_manifest.json").read_text())
by_family = {f["family_id"]: f for f in consumption_manifest["families"]}

hmc = by_modality["EOG (with EEG)"]
ds = by_modality["sparse vs. full-montage EEG (ds003838-adjacent)"]
hmc_limitation = by_family["hmc_bounded_diagnostic"]["unresolved_limitation"]
ds_limitation = by_family["ds003838_bounded_diagnostic"]["unresolved_limitation"]

high_sensitivity_items = [
    {
        "item": "EOG external validity (HMC full-cohort)",
        "current_science_state": hmc["current_science_state"],
        "current_confidence_tier": hmc["current_confidence_tier"],
        "pending_evidence": hmc["pending_evidence"],
        "decision_flip_scenarios": hmc["decision_flip_scenarios"],
        "options": {
            "WAIT": {
                "description": "Delay final architecture freeze on the EOG/EEG head module until HMC full-cohort (151-recording) training completes.",
                "benefit": "Directly resolves which of the three decision-flip scenarios (HMC-1 strong replication / HMC-2 near-zero / HMC-3 negative) actually occurred, removing the single largest open external-validity question for the head module.",
                "cost": f"results/stage4_science_consumption_manifest.json marks this as: {hmc_limitation!r} - full-cohort training is LOWER_PRIORITY_EXTERNAL_WORK_PENDING per the accepted Stage-3 verdict, with no guaranteed completion date from this sprint.",
                "what_uncertainty_is_removed": "External replication status for EOG moves from 'underpowered n=7, 1 test recording' to a real full-cohort read (majority-recording direction, control-superiority check).",
            },
            "FREEZE_CONDITIONALLY": {
                "description": "Select an architecture now that includes (or excludes) EOG, with an explicit written condition that the HMC full-cohort result may trigger revision.",
                "what_could_trigger_revision": "A stable, majority-consistent NEGATIVE HMC full-cohort result (scenario HMC-3) if EOG was included; OR a strong external-replication result (scenario HMC-1) if EOG was excluded pending more evidence.",
                "claim_limitations": "Any public/jury-facing claim about EOG must cite TIER_B_CONTROLLED_SUPPORT (same-dataset) / TIER_C_BOUNDED_SUPPORT (external) exactly as the claim ledger requires (GATE_C/GATE_G) - never presented as externally validated pending the full-cohort result.",
            },
            "FREEZE_DESPITE_UNCERTAINTY_WITH_DISCLOSURE": {
                "description": "Freeze the architecture decision on EOG now, without waiting for or conditioning on HMC full-cohort results.",
                "residual_uncertainty": "HMC bounded n=7 (1 held-out test recording) is explicitly underpowered to distinguish any of the three decision-flip scenarios - the true external-validity direction for EOG remains genuinely unknown at freeze time.",
                "disclosure_language": "EOG is included/excluded on the basis of same-dataset (Sleep-EDF) controlled evidence only; independent external validation (HMC) remains a bounded, underpowered diagnostic (n=7) and does not constitute external replication.",
                "scientific_risk": "If HMC full-cohort later shows a stable external-negative result (HMC-3), a frozen 'EOG included' architecture would have been decided against the eventual weight of evidence; the inverse risk applies if EOG was excluded and HMC-1 later occurs.",
            },
        },
    },
    {
        "item": "Sparse-vs-full EEG electrode-count minimization (ds003838 full cohort)",
        "current_science_state": ds["current_science_state"],
        "current_confidence_tier": ds["current_confidence_tier"],
        "pending_evidence": ds["pending_evidence"],
        "decision_flip_scenarios": ds["decision_flip_scenarios"],
        "options": {
            "WAIT": {
                "description": "Delay the EEG channel-count decision until the full ~65-subject ds003838 cohort comparison completes.",
                "benefit": "Distinguishes between the three decision-flip scenarios (DS-1 approximate equality supports minimization, DS-2 materially worse weakens it, DS-3 heterogeneity may justify a conditional/adaptive architecture class) - n=3 cannot currently distinguish any of these.",
                "cost": f"results/stage4_science_consumption_manifest.json marks this as: {ds_limitation!r} - plus full-cohort training time on top of that download.",
                "what_uncertainty_is_removed": "Whether aggressive EEG electrode minimization is scientifically supported at the population level, or whether a subject-adaptive channel-count architecture class is warranted instead.",
            },
            "FREEZE_CONDITIONALLY": {
                "description": "Select a specific EEG channel count now (sparse or full montage), with an explicit condition that the ds003838 full-cohort result may trigger revision.",
                "what_could_trigger_revision": "A materially-worse sparse-EEG result at full cohort (DS-2) if a sparse montage was selected; or strong subject heterogeneity (DS-3) surfacing a need for a conditional/adaptive channel-count class regardless of which fixed count was initially selected.",
                "claim_limitations": "Any claim about electrode-count sufficiency must be scoped to 'n=3 bounded diagnostic, inconclusive by design' (TIER_C_BOUNDED_SUPPORT) - never presented as population-validated minimization.",
            },
            "FREEZE_DESPITE_UNCERTAINTY_WITH_DISCLOSURE": {
                "description": "Freeze the EEG channel-count decision now, without waiting for or conditioning on the ds003838 full-cohort result.",
                "residual_uncertainty": "n=3 is explicitly too small to distinguish approximate equality, material worsening, or strong subject heterogeneity - the population-level electrode-minimization question remains genuinely open at freeze time.",
                "disclosure_language": "The selected EEG channel count reflects an n=3 bounded diagnostic only (TIER_C_BOUNDED_SUPPORT), not a population-validated minimization result; full-cohort evidence that could materially change this conclusion has not been obtained.",
                "scientific_risk": "If the full cohort later shows DS-2 (materially worse) or DS-3 (strong heterogeneity), a frozen fixed-channel-count architecture may need later revision or may have foreclosed a conditional/adaptive design that the evidence would have supported.",
            },
        },
    },
]

output = {
    "artifact_id": "biological-minimalism-stage4-gate-e-coordinator-options-v1",
    "schema_version": "1.0.0",
    "sprint": "STAGE4_CLOSURE_PREP",
    "generated_role": "INTEGRATION_OWNER",
    "purpose": "Coordinator-facing options for every current HIGH-decision-sensitivity pending-science item, per GATE_E_PENDING_SCIENCE_SENSITIVITY. No option is selected.",
    "gate_reference": "results/stage4_architecture_acceptance_gates.json#GATE_E_PENDING_SCIENCE_SENSITIVITY",
    "source_artifacts": [
        "results/stage4_sensor_decision_sensitivity.json",
        "results/stage4_science_consumption_manifest.json",
    ],
    "high_sensitivity_items": high_sensitivity_items,
    "no_option_selected": True,
    "coordinator_action_required": "For each item above, Emir/Project Coordinator must explicitly record one of WAIT / FREEZE_CONDITIONALLY / FREEZE_DESPITE_UNCERTAINTY_WITH_DISCLOSURE before Gate E can close.",
    "final_architecture_status": "UNRESOLVED",
    "formal_pareto_status": "NOT_READY",
}

if len(high_sensitivity_items) != sum(1 for s in sensitivity["sensors"] if s.get("decision_sensitivity") == "HIGH"):
    raise SystemExit("HIGH-sensitivity item count in source drifted from this script's assumptions - update before writing.")

OUT_PATH.write_text(json.dumps(output, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(f"Wrote {OUT_PATH}")
