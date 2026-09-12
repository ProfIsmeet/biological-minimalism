"""Stage 4 closure-prep: the Coordinator decision packet (master prompt Part VII).

Pure aggregation of this sprint's already-frozen artifacts - NOT the final
architecture, NOT a new analysis. No new numbers, no reinterpretation, no
winner. Writes results/stage4_final_architecture_decision_packet.json.
"""

from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
OUT_PATH = REPO_ROOT / "results" / "stage4_final_architecture_decision_packet.json"


def _load(rel: str) -> dict:
    return json.loads((REPO_ROOT / rel).read_text())


gates = _load("results/stage4_architecture_acceptance_gates.json")
gate_d = _load("results/stage4_gate_d_burden_completeness.json")
gate_e = _load("results/stage4_gate_e_coordinator_options.json")
burden_comparison = _load("results/stage4_candidate_class_burden_comparison.json")
decision_projection = _load("results/stage4_architecture_decision_projection.json")

# Merge Gate D's own INTEGRATION_OWNER verdict into the Science-Owner-authored
# gate list's current_readiness field for GATE_D only (that field was
# explicitly left for Integration Owner to fill; every other gate's
# current_readiness is cited verbatim, unmodified).
acceptance_gate_readiness = []
for g in gates["gates"]:
    entry = dict(g)
    if g["gate_id"] == "GATE_D_BURDEN_COMPLETENESS":
        entry["current_readiness"] = (
            f"{gate_d['gate_d_burden_completeness']} (Integration Owner assessment, "
            f"see results/stage4_gate_d_burden_completeness.json) - {g['current_readiness']}"
        )
    elif g["gate_id"] == "GATE_E_PENDING_SCIENCE_SENSITIVITY":
        entry["current_readiness"] = (
            f"{g['current_readiness']} Coordinator options prepared: "
            f"see results/stage4_gate_e_coordinator_options.json ({len(gate_e['high_sensitivity_items'])} HIGH-sensitivity items)."
        )
    acceptance_gate_readiness.append(entry)

decision_blockers = [
    {
        "blocker": "GATE_D_BURDEN_COMPLETENESS is NOT_READY",
        "detail": gate_d["rationale"],
        "what_closes_it": gate_d["what_would_close_it"],
    },
    {
        "blocker": "GATE_E_PENDING_SCIENCE_SENSITIVITY requires an explicit Coordinator choice per HIGH-sensitivity item",
        "detail": "No WAIT / FREEZE_CONDITIONALLY / FREEZE_DESPITE_UNCERTAINTY_WITH_DISCLOSURE decision has been recorded for EOG/HMC or sparse-vs-full-EEG/ds003838.",
        "what_closes_it": ["Coordinator records one option per item in results/stage4_gate_e_coordinator_options.json."],
    },
]

coordinator_choices_required = [
    "Gate E: EOG/HMC - choose WAIT / FREEZE_CONDITIONALLY / FREEZE_DESPITE_UNCERTAINTY_WITH_DISCLOSURE.",
    "Gate E: sparse-vs-full EEG/ds003838 - choose WAIT / FREEZE_CONDITIONALLY / FREEZE_DESPITE_UNCERTAINTY_WITH_DISCLOSURE.",
    "Whether to resume HMC full-cohort and/or ds003838 full-cohort work before Stage 5 (explicitly Emir's call, unchanged from the Stage-3 handoff).",
    "Gate D remediation priority: which of the 4 items in results/stage4_gate_d_burden_completeness.json#what_would_close_it to pursue before a final architecture freeze.",
    "The final architecture selection itself - this packet provides inputs only, never a selection.",
]

output = {
    "artifact_id": "biological-minimalism-stage4-final-architecture-decision-packet-v1",
    "schema_version": "1.0.0",
    "sprint": "STAGE4_CLOSURE_PREP",
    "generated_role": "INTEGRATION_OWNER",
    "purpose": "The Coordinator-facing decision packet for the Stage-4 final architecture decision. This is NOT the final architecture - it aggregates candidate configurations, evidence, burden, uncertainty, gate readiness, and required Coordinator choices so Emir/Project Coordinator can make that decision.",
    "statement": "Pure aggregation of already-frozen Stage-4 closure-prep artifacts produced in this sprint. No new science, no new engineering numbers, no reinterpretation, no winner selected.",
    "candidate_configurations": burden_comparison["classes"],
    "scientific_evidence_summary": {
        "source": "results/stage4_architecture_decision_projection.json",
        "units": decision_projection["units"],
    },
    "burden_evidence_summary": {
        "source": "results/stage4_gate_d_burden_completeness.json",
        "dimensions_audited": gate_d["dimensions_audited"],
        "shared_resource_accounting": gate_d["shared_resource_accounting"],
    },
    "uncertainties": {
        "engineering_known_unknowns": gate_d["known_unknowns"],
        "pending_science_high_sensitivity": [
            {"item": item["item"], "current_confidence_tier": item["current_confidence_tier"], "pending_evidence": item["pending_evidence"]}
            for item in gate_e["high_sensitivity_items"]
        ],
    },
    "pending_science_sensitivity": gate_e["high_sensitivity_items"],
    "potential_dominance": [
        {"class_id": c["class_id"], "dominance_flag": c["dominance_flag"], "dominance_reason": c["dominance_reason"]}
        for c in burden_comparison["classes"]
    ],
    "acceptance_gate_readiness": acceptance_gate_readiness,
    "decision_blockers": decision_blockers,
    "coordinator_choices_required": coordinator_choices_required,
    "final_architecture_status": "UNRESOLVED",
    "formal_pareto_status": "NOT_READY",
}

OUT_PATH.write_text(json.dumps(output, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(f"Wrote {OUT_PATH}")
