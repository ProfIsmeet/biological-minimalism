"""Stage 4 Final Architecture Closure: Gate E Coordinator decisions
(INTEGRATION_OWNER, master prompt Part I Sections 10-12 / Part IV Section 18).

results/stage4_gate_e_coordinator_options.json (prior sprint) prepared three
options per HIGH-sensitivity pending-science item (WAIT / FREEZE_CONDITIONALLY
/ FREEZE_DESPITE_UNCERTAINTY_WITH_DISCLOSURE) with no_option_selected=true.
This script records the Project Coordinator's actual, explicit decisions -
FREEZE_CONDITIONALLY for both current HIGH-sensitivity items - deriving the
revision-trigger wording directly from the already-frozen decision_flip_scenarios
in results/stage4_gate_e_coordinator_options.json (never inventing new
trigger conditions).

Does not touch any science file or the options artifact itself (which
remains a valid historical record of what was PREPARED before the decision).
Writes results/stage4_gate_e_coordinator_decisions.json.
"""

from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
GATE_E_OPTIONS_PATH = REPO_ROOT / "results" / "stage4_gate_e_coordinator_options.json"
OUTPUT_PATH = REPO_ROOT / "results" / "stage4_gate_e_coordinator_decisions.json"


def _load(rel: str) -> dict:
    return json.loads((REPO_ROOT / rel).read_text())


options = _load("results/stage4_gate_e_coordinator_options.json")

if not options.get("no_option_selected"):
    raise SystemExit(
        f"REFUSING TO RUN: {GATE_E_OPTIONS_PATH} no longer has no_option_selected=true - a decision may "
        "already have been recorded elsewhere. Verify before overwriting."
    )

items_by_name = {item["item"]: item for item in options["high_sensitivity_items"]}

EOG_ITEM = "EOG external validity (HMC full-cohort)"
EEG_ITEM = "Sparse-vs-full EEG electrode-count minimization (ds003838 full cohort)"

if EOG_ITEM not in items_by_name or EEG_ITEM not in items_by_name:
    raise SystemExit(
        f"REFUSING TO RUN: expected high_sensitivity_items {[EOG_ITEM, EEG_ITEM]!r} not found in "
        f"{GATE_E_OPTIONS_PATH} - actual items: {list(items_by_name)!r}"
    )

eog_flip = items_by_name[EOG_ITEM]["decision_flip_scenarios"]
eeg_flip = items_by_name[EEG_ITEM]["decision_flip_scenarios"]

# Hostile-review guard: the revision-trigger condition text quoted below must
# be copied verbatim from the already-frozen decision_flip_scenarios, never
# invented - this assertion fails loudly if that source ever drifts.
if "HMC-3_external_negative_result" not in eog_flip:
    raise SystemExit("REFUSING TO WRITE: HMC-3_external_negative_result scenario missing from source options artifact.")
if "DS-2_sparse_materially_worse" not in eeg_flip or "DS-3_strong_subject_heterogeneity" not in eeg_flip:
    raise SystemExit("REFUSING TO WRITE: DS-2/DS-3 scenarios missing from source options artifact.")

DECISIONS = [
    {
        "item": EOG_ITEM,
        "decision": "FREEZE_CONDITIONALLY",
        "architecture_disposition": (
            "EOG is INCLUDED in the final Stage-4 architecture (CORE_PLUS_CONTEXT), on the basis of "
            "TIER_B_CONTROLLED_SUPPORT same-dataset evidence and TIER_C_BOUNDED_SUPPORT (bounded, "
            "underpowered n=7) external evidence, sharing the head_module's EEG AFE/reference/ground "
            "infrastructure per results/stage4_gate_d_burden_completeness.json eeg_eog_shared_afe_confirmation."
        ),
        "claim_limitations": items_by_name[EOG_ITEM]["options"]["FREEZE_CONDITIONALLY"]["claim_limitations"],
        "what_could_trigger_revision": items_by_name[EOG_ITEM]["options"]["FREEZE_CONDITIONALLY"]["what_could_trigger_revision"],
        "revision_trigger": {
            "condition": eog_flip["HMC-3_external_negative_result"]["condition"],
            "action_if_triggered": (
                "Reopen EOG architecture inclusion for re-evaluation (per HMC-3's own "
                f"implication_if_observed: {eog_flip['HMC-3_external_negative_result']['implication_if_observed']})"
            ),
            "source_scenario": "results/stage4_gate_e_coordinator_options.json high_sensitivity_items[EOG].decision_flip_scenarios.HMC-3_external_negative_result",
        },
        "near_zero_result_note": (
            "A near-zero/inconclusive HMC-2 result may trigger Coordinator review but is NOT an automatic "
            "removal condition - only a stable, majority-consistent HMC-3-equivalent negative result reopens "
            "inclusion, per this decision's own governing scope."
        ),
        "decided_by": "PROJECT_COORDINATOR (Emir)",
    },
    {
        "item": EEG_ITEM,
        "decision": "FREEZE_CONDITIONALLY",
        "architecture_disposition": (
            "The current sparse/minimal frontal EEG architecture (1 active EEG signal channel + shared "
            "reference/ground, per results/stage4_contact_electrode_burden.json frontal_eeg most_likely=3 "
            "total contacts) is retained as-is. This is NOT presented as a population-validated minimization "
            "result - it is the already-frozen engineering design point, continued under explicit condition."
        ),
        "claim_limitations": items_by_name[EEG_ITEM]["options"]["FREEZE_CONDITIONALLY"]["claim_limitations"],
        "what_could_trigger_revision": items_by_name[EEG_ITEM]["options"]["FREEZE_CONDITIONALLY"]["what_could_trigger_revision"],
        "revision_trigger": {
            "condition_ds2": eeg_flip["DS-2_sparse_materially_worse"]["condition"],
            "condition_ds3": eeg_flip["DS-3_strong_subject_heterogeneity"]["condition"],
            "action_if_triggered": (
                "Reopen EEG channel-count architecture for re-evaluation (per DS-2's implication: "
                f"{eeg_flip['DS-2_sparse_materially_worse']['implication_if_observed']} — or per DS-3's "
                f"implication: {eeg_flip['DS-3_strong_subject_heterogeneity']['implication_if_observed']})"
            ),
            "source_scenario": "results/stage4_gate_e_coordinator_options.json high_sensitivity_items[EEG].decision_flip_scenarios.{DS-2,DS-3}",
        },
        "decided_by": "PROJECT_COORDINATOR (Emir)",
    },
]

output = {
    "artifact_id": "biological-minimalism-stage4-gate-e-coordinator-decisions-v1",
    "schema_version": "1.0.0",
    "sprint": "STAGE4_FINAL_ARCHITECTURE_CLOSURE",
    "generated_role": "INTEGRATION_OWNER",
    "purpose": (
        "Records the Project Coordinator's explicit decisions for every current HIGH-decision-sensitivity "
        "pending-science item, closing GATE_E_PENDING_SCIENCE_SENSITIVITY. Supersedes the no_option_selected "
        "state in results/stage4_gate_e_coordinator_options.json (which remains a valid historical record of "
        "what was prepared) with actual recorded decisions."
    ),
    "gate_reference": "results/stage4_architecture_acceptance_gates.json#GATE_E_PENDING_SCIENCE_SENSITIVITY",
    "source_artifacts": [
        "results/stage4_gate_e_coordinator_options.json",
        "results/stage4_sensor_decision_sensitivity.json",
    ],
    "decisions": DECISIONS,
    "no_option_selected": False,
    "gate_e_pending_science_sensitivity": "CLOSED_BY_COORDINATOR_DECISION",
    "pending_science_still_pending": (
        "HMC full-cohort and ds003838 full-cohort training remain LOWER_PRIORITY_EXTERNAL_WORK_PENDING and "
        "are explicitly NOT run, NOT marked complete, and NOT required for Stage-4 closure under this "
        "conditional-freeze decision."
    ),
}

OUTPUT_PATH.write_text(json.dumps(output, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(f"Wrote {OUTPUT_PATH}")
