"""Stage 4 Final Architecture Closure: claim ledger migration
(INTEGRATION_OWNER, master prompt Part V Section 19).

results/stage4_science_claim_ledger.json is Science-Owner-authored and tied
to the accepted Stage-4 science package SHA (5730efd2...) - it is NOT
edited here (per master prompt Section 2, "Do not reopen accepted science").
Instead, this script writes a small Integration-Owner claim-UPDATE artifact
that explicitly supersedes only the `final_architecture` and `pareto` claims
(the two claims whose PENDING/UNRESOLVED wording is now stale given the
Coordinator's actual decision), citing what it supersedes rather than
silently overwriting the original ledger.
"""

from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PATH = REPO_ROOT / "results" / "stage4_final_closure_claim_updates.json"


def _load(rel: str) -> dict:
    return json.loads((REPO_ROOT / rel).read_text())


ledger = _load("results/stage4_science_claim_ledger.json")
final_arch = _load("results/final_wearable_architecture.json")
pareto = _load("results/stage4_formal_pareto_analysis.json")

claims_by_id = {c["claim_id"]: c for c in ledger["claims"]}
for required in ("final_architecture", "pareto"):
    if required not in claims_by_id:
        raise SystemExit(f"REFUSING TO RUN: claim_id {required!r} not found in results/stage4_science_claim_ledger.json")

UPDATED_CLAIMS = [
    {
        "claim_id": "final_architecture",
        "supersedes": {
            "artifact": "results/stage4_science_claim_ledger.json",
            "original_exact_safe_wording": claims_by_id["final_architecture"]["exact_safe_wording"],
            "original_strength": claims_by_id["final_architecture"]["strength"],
        },
        "exact_safe_wording": (
            f"A final Stage-4 wearable architecture has been selected: {final_arch['selected_class']}. Selection "
            "is evidence-driven and burden-aware (Gate D CONDITIONALLY_READY, coordinator-accepted bounded "
            "engineering uncertainty). EOG inclusion is conditional on pending external replication (HMC "
            "full-cohort); sparse EEG channel choice is conditional on pending full-cohort evidence (ds003838)."
        ),
        "strength": "SAFE_WITH_LIMITATION",
        "governing_evidence": ["results/final_wearable_architecture.json", "results/stage4_gate_e_coordinator_decisions.json"],
        "scope_limitation": (
            "Both HIGH-sensitivity conditional freezes (EOG/HMC, sparse-EEG/ds003838) remain subject to explicit "
            "revision triggers - this is a conditional, disclosed final decision, not an unconditional one."
        ),
        "prohibited_stronger_wording": (
            "'Four sensors are proven sufficient'; 'EOG is externally validated'; 'sparse EEG is population "
            "validated'; 'the architecture is immutable/unconditionally final'; any claim omitting the "
            "conditional-freeze/revision-trigger scope above."
        ),
        "stage4_consumer_guidance": "Cite results/final_wearable_architecture.json and docs/STAGE4_FINAL_ARCHITECTURE_CLOSURE.md for this claim; never the pre-closure PENDING wording in results/stage4_science_claim_ledger.json alone.",
    },
    {
        "claim_id": "pareto",
        "supersedes": {
            "artifact": "results/stage4_science_claim_ledger.json",
            "original_exact_safe_wording": claims_by_id["pareto"]["exact_safe_wording"],
            "original_strength": claims_by_id["pareto"]["strength"],
        },
        "exact_safe_wording": (
            "A formal multi-objective Pareto dominance analysis has been completed (no single collapsed score). "
            f"Pareto-relevant set: {', '.join(pareto['pareto_relevant_set'])}. Coordinator selected "
            f"{pareto['coordinator_selected_architecture']} from within that set on evidence-driven, burden-aware "
            "judgment, not because it mathematically dominates every alternative."
        ),
        "strength": "SAFE_WITH_LIMITATION",
        "governing_evidence": ["results/stage4_formal_pareto_analysis.json"],
        "scope_limitation": (
            "MINIMAL_CORE remains Pareto-relevant (non-dominated) alongside CORE_PLUS_CONTEXT - this is not a "
            "unique mathematical winner. EVIDENCE_EXTENDED/EXPERIMENTAL_EXTENDED remain POTENTIALLY_DOMINATED, "
            "not formally DOMINATED."
        ),
        "prohibited_stronger_wording": (
            "'CORE_PLUS_CONTEXT mathematically dominates every architecture'; 'Pareto winner'; presenting any "
            "ranked sensor list as establishing a unique optimum."
        ),
        "stage4_consumer_guidance": "Cite results/stage4_formal_pareto_analysis.json; never present potential_dominance as confirmed mathematical dominance.",
    },
]

output = {
    "artifact_id": "biological-minimalism-stage4-final-closure-claim-updates-v1",
    "schema_version": "1.0.0",
    "sprint": "STAGE4_FINAL_ARCHITECTURE_CLOSURE",
    "generated_role": "INTEGRATION_OWNER",
    "purpose": (
        "Supersedes only the `final_architecture` and `pareto` claims in the Science-Owner-authored "
        "results/stage4_science_claim_ledger.json (left otherwise untouched) with new safe wording reflecting "
        "the Coordinator's actual final decision."
    ),
    "updated_claims": UPDATED_CLAIMS,
}

OUTPUT_PATH.write_text(json.dumps(output, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(f"Wrote {OUTPUT_PATH}")
