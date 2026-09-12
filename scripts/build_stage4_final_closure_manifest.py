"""Stage 4 Final Architecture Closure: the final closure manifest
(INTEGRATION_OWNER, master prompt Part IX Section 25).

Aggregates every authoritative Stage-4 artifact path + content hash, the
final architecture decision, formal Pareto status, acceptance gates A-H
(original severity, evidence, closure mechanism, final state), pending
science, and Coordinator decisions into one manifest. Run this LAST, after
every other Stage-4 closure artifact/script in this sprint.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PATH = REPO_ROOT / "results" / "stage4_final_closure_manifest.json"


def _load(rel: str) -> dict:
    return json.loads((REPO_ROOT / rel).read_text())


def _sha256(rel: str) -> str:
    return hashlib.sha256((REPO_ROOT / rel).read_bytes()).hexdigest()


acceptance_gates = _load("results/stage4_architecture_acceptance_gates.json")
gate_d = _load("results/stage4_gate_d_burden_completeness.json")
gate_e_decisions = _load("results/stage4_gate_e_coordinator_decisions.json")
final_arch = _load("results/final_wearable_architecture.json")
pareto = _load("results/stage4_formal_pareto_analysis.json")

if gate_d.get("schema_version") != "3.0.0" or "coordinator_acceptance" not in gate_d:
    raise SystemExit("REFUSING TO RUN: Gate D is not the v3.0.0 coordinator_acceptance record - run its build script first.")
if final_arch.get("selected_class") != "CORE_PLUS_CONTEXT":
    raise SystemExit("REFUSING TO RUN: final_wearable_architecture.json selected_class is not CORE_PLUS_CONTEXT.")

AUTHORITATIVE_ARTIFACT_PATHS = [
    ("results/stage4_architecture_acceptance_gates.json", "Acceptance gates A-H (Science Owner authored, severity/evidence/owner)"),
    ("results/stage4_architecture_candidate_classes.json", "4 candidate architecture classes (Science Owner authored)"),
    ("results/stage4_architecture_decision_projection.json", "Per-decision-unit science+burden join (pre-closure input)"),
    ("results/stage4_gate_d_burden_completeness.json", "Gate D burden-completeness assessment, v3.0.0, CONDITIONALLY_READY + coordinator_acceptance"),
    ("results/stage4_gate_e_coordinator_options.json", "Gate E options prepared (historical, no_option_selected=true - superseded by decisions below)"),
    ("results/stage4_gate_e_coordinator_decisions.json", "Gate E Coordinator decisions - FREEZE_CONDITIONALLY x2, with revision triggers"),
    ("results/stage4_candidate_burden_matrix.json", "Configuration-level burden matrix, 4 classes, computed robustness"),
    ("results/stage4_contact_electrode_burden.json", "Bounded contact/electrode topology, 7 modalities"),
    ("results/stage4_battery_topology_scenarios.json", "Battery/electronics topology scenarios (shared-hub vs distributed)"),
    ("results/stage4_candidate_class_burden_comparison.json", "Per-class burden comparison, dominance flags"),
    ("results/stage4_scientific_pareto_inputs.json", "Science-only Pareto axes (Science Owner authored)"),
    ("results/stage4_formal_pareto_analysis.json", "Formal multi-objective Pareto dominance analysis - COMPLETE"),
    ("results/final_wearable_architecture.json", "THE canonical final architecture decision - CORE_PLUS_CONTEXT"),
    ("results/stage4_final_architecture_decision_packet.json", "Pre-closure decision packet (historical aggregation input, superseded by final_wearable_architecture.json as the decision-of-record)"),
    ("results/stage4_science_claim_ledger.json", "Science Owner claim ledger - exact safe wording per claim area"),
    ("results/stage4_final_closure_claim_updates.json", "Integration Owner claim-update - supersedes final_architecture/pareto claim wording only"),
]

authoritative_artifacts = [
    {"path": path, "sha256": _sha256(path), "description": description}
    for path, description in AUTHORITATIVE_ARTIFACT_PATHS
]

GATE_FINAL_STATES = {
    "GATE_A_SCIENTIFIC_PROVENANCE": "PASS - every included sensor traces to results/stage4_science_consumption_manifest.json / results/stage4_science_claim_ledger.json (cited in final_wearable_architecture.json science_rationale).",
    "GATE_B_EXCLUDED_SENSOR_RATIONALE": "PASS - every excluded sensor (thoracic BioZ, leg BioZ, second-site PPG, wrist temp/light) has documented evidence-based rationale in final_wearable_architecture.json exclusion_rationale.",
    "GATE_C_EVIDENCE_STATUS_HONESTY": "PASS - EOG/sparse-EEG wording remains bounded/conditional per results/stage4_gate_e_coordinator_decisions.json claim_limitations; validated by ml/validate_stage4_final_architecture_closure.py.",
    "GATE_D_BURDEN_COMPLETENESS": "CONDITIONALLY_READY, CLOSED_FOR_STAGE4_BY_COORDINATOR_ACCEPTANCE_OF_BOUNDED_ENGINEERING_UNCERTAINTY (results/stage4_gate_d_burden_completeness.json coordinator_acceptance) - NOT silently relabeled READY.",
    "GATE_E_PENDING_SCIENCE_SENSITIVITY": "CLOSED_BY_COORDINATOR_DECISION - both HIGH-sensitivity items (EOG/HMC, sparse-vs-full EEG/ds003838) FREEZE_CONDITIONALLY with explicit revision triggers (results/stage4_gate_e_coordinator_decisions.json).",
    "GATE_F_NEGATIVE_RESULT_PRESERVATION": "PASS - thoracic BioZ COMPLETE_MIXED, leg BioZ aggregate-negative, second-site PPG negative all preserved verbatim in final_wearable_architecture.json exclusion_rationale, never rewritten as clean negatives or erased.",
    "GATE_G_CLAIM_CONSISTENCY": "PASS - validated by ml/validate_stage4_science_claim_consistency.py (18 pre-closure artifacts remain UNRESOLVED/NOT_READY) and ml/validate_stage4_final_architecture_closure.py (4 new closure artifacts internally consistent, no false dominance, no premature HMC/ds003838 completion).",
    "GATE_H_DIGITAL_TWIN_SEPARATION": "PASS - Digital Twin not mentioned in any new closure artifact; results/digital_twin_architecture_footprint.json's ARCHITECTURE_ONLY_UNTRAINED_UNVALIDATED status is untouched and unreferenced by the wearable architecture decision.",
}

acceptance_gate_closures = []
for gate in acceptance_gates["gates"]:
    acceptance_gate_closures.append(
        {
            "gate_id": gate["gate_id"],
            "original_severity": gate["severity"],
            "original_requirement": gate["requirement"],
            "evidence": gate["evidence_needed"],
            "closure_mechanism": gate["what_closes_it"],
            "final_state": GATE_FINAL_STATES[gate["gate_id"]],
        }
    )

pending_science = {
    "hmc_full_cohort": "LOWER_PRIORITY_EXTERNAL_WORK_PENDING - not run, not marked complete, not required for Stage-4 closure under FREEZE_CONDITIONALLY.",
    "ds003838_full_cohort": "LOWER_PRIORITY_EXTERNAL_WORK_PENDING - not run, not marked complete, not required for Stage-4 closure under FREEZE_CONDITIONALLY.",
    "digital_twin": "ARCHITECTURE_ONLY_UNTRAINED_UNVALIDATED (results/digital_twin_architecture_footprint.json) - unaffected by, and not implied by, this architecture closure.",
}

coordinator_decisions = {
    "final_architecture_class": final_arch["selected_class"],
    "module_topology": final_arch["module_topology"]["topology_class"],
    "battery_topology": final_arch["module_topology"]["battery_topology_selected"],
    "mcu_radio_topology": final_arch["module_topology"]["mcu_radio_topology_selected"],
    "gate_d_acceptance": gate_d["coordinator_acceptance"]["status"],
    "gate_e_decisions": [{"item": d["item"], "decision": d["decision"]} for d in gate_e_decisions["decisions"]],
    "formal_pareto_status": pareto["formal_pareto_status"],
    "pareto_relevant_set": pareto["pareto_relevant_set"],
    "coordinator_selection_rationale": pareto["coordinator_selection_rationale"],
}

try:
    repository_sha_after_closure = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=REPO_ROOT, capture_output=True, text=True, check=True
    ).stdout.strip()
except (subprocess.CalledProcessError, FileNotFoundError):
    repository_sha_after_closure = "UNKNOWN_GIT_UNAVAILABLE"

output = {
    "artifact_id": "biological-minimalism-stage4-final-closure-manifest-v1",
    "schema_version": "1.0.0",
    "sprint": "STAGE4_FINAL_ARCHITECTURE_CLOSURE",
    "generated_role": "INTEGRATION_OWNER",
    "purpose": (
        "The Stage-4 final closure manifest: every authoritative artifact path/hash, the final architecture "
        "decision, formal Pareto status, acceptance gates A-H closure record, pending science, and Coordinator "
        "decisions, for independent audit."
    ),
    "authoritative_artifacts": authoritative_artifacts,
    "final_architecture": final_arch["selected_class"],
    "formal_pareto_status": pareto["formal_pareto_status"],
    "acceptance_gates": acceptance_gate_closures,
    "pending_science": pending_science,
    "coordinator_decisions": coordinator_decisions,
    "repository_sha_after_closure": repository_sha_after_closure,
    "repository_sha_note": (
        "This is the repository HEAD SHA at manifest-generation time (the parent of this sprint's closure "
        "commit(s) - a file cannot embed its own resulting commit hash without amending, which this project's "
        "git discipline avoids). The actual final closure commit SHA is reported in the branch push report/PR, "
        "not embedded here."
    ),
    "accepted_stage3_sha": "5c381014af61e5d10d41223963831b25b9ff23e6",
    "status": "STAGE4_FINAL_CLOSURE_CANDIDATE_REPORTED_COMPLETE_PENDING_INDEPENDENT_AUDIT",
}

OUTPUT_PATH.write_text(json.dumps(output, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(f"Wrote {OUTPUT_PATH}")
