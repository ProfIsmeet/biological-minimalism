"""Stage 4 Final Architecture Closure: Coordinator acceptance of Gate D
(INTEGRATION_OWNER, master prompt Part I Section 6 / Part IV Section 18).

The Project Coordinator has explicitly reviewed the v2.0.0 CONDITIONALLY_READY
Gate-D assessment (results/stage4_gate_d_burden_completeness.json) and
accepted it as sufficient for the final Stage-4 architecture decision,
because: (1) all material burden uncertainties are now bounded, (2)
candidate ordering is stable across every tested contact/battery/MCU-radio
bound, (3) remaining uncertainty affects absolute burden magnitude only,
not the selected architecture-class ordering.

This script writes a v3.0.0 record that PRESERVES the entire v2.0.0 record
verbatim under assessment_history (which itself already carries v1.0.0
verbatim) and adds an explicit `coordinator_acceptance` field recording the
NOT_READY -> CONDITIONALLY_READY -> COORDINATOR_ACCEPTED_BOUNDED_UNCERTAINTY
state transition. The top-level `gate_d_burden_completeness` verdict is left
UNCHANGED at "CONDITIONALLY_READY" - the Coordinator is accepting this level
as sufficient, NOT silently relabeling it READY (master prompt Part I
Section 6 / Part IV Section 18: "Do NOT silently relabel it fully READY").
`final_architecture_status`/`formal_pareto_status` inside THIS artifact are
also left UNCHANGED (UNRESOLVED/NOT_READY) - this artifact's scope is burden
completeness only; the actual final-architecture decision is recorded
separately in results/final_wearable_architecture.json.
"""

from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
GATE_D_PATH = REPO_ROOT / "results" / "stage4_gate_d_burden_completeness.json"

v2 = json.loads(GATE_D_PATH.read_text())  # the existing CONDITIONALLY_READY v2.0.0 assessment - preserved verbatim below

# Idempotency guard, same discipline as build_stage4_gate_d_reassessment.py's
# own hostile-review-derived guard: this script must run exactly once against
# the v2.0.0 record, wrapping it into assessment_history. Re-running it
# against its own v3.0.0 output would read v3 as if it were v2 and silently
# double-wrap history.
if v2.get("schema_version") != "2.0.0":
    raise SystemExit(
        f"REFUSING TO RUN: {GATE_D_PATH} is already schema_version={v2.get('schema_version')!r}, not the "
        "expected v2.0.0 source record. This script must only run once, against the CONDITIONALLY_READY "
        "v2.0.0 assessment produced by scripts/build_stage4_gate_d_reassessment.py."
    )

if v2["gate_d_burden_completeness"] != "CONDITIONALLY_READY":
    raise SystemExit(
        f"REFUSING TO RUN: v2 gate_d_burden_completeness is {v2['gate_d_burden_completeness']!r}, expected "
        "CONDITIONALLY_READY - coordinator acceptance of bounded uncertainty is only meaningful applied to "
        "a CONDITIONALLY_READY verdict, never to NOT_READY."
    )

# Hostile-review guard (same invariant as the v2 reassessment script): a
# COORDINATOR_ACCEPTED_BOUNDED_UNCERTAINTY closure must be impossible to
# write while any known_unknown is both unbounded AND could_be_decision_changing.
_unsafe_unknowns = [u for u in v2["known_unknowns"] if u["could_be_decision_changing"] and not u["bounded"]]
if _unsafe_unknowns:
    raise SystemExit(
        f"REFUSING TO WRITE: {len(_unsafe_unknowns)} known_unknown(s) are unbounded AND decision-changing: "
        f"{[u['item'] for u in _unsafe_unknowns]}. Coordinator acceptance requires every decision-changing "
        "unknown to already be bounded."
    )

COORDINATOR_ACCEPTANCE = {
    "status": "CLOSED_FOR_STAGE4_BY_COORDINATOR_ACCEPTANCE_OF_BOUNDED_ENGINEERING_UNCERTAINTY",
    "accepted_verdict": "CONDITIONALLY_READY",
    "decided_by": "PROJECT_COORDINATOR (Emir)",
    "sprint": "STAGE4_FINAL_ARCHITECTURE_CLOSURE",
    "rationale": (
        "The Coordinator explicitly accepts CONDITIONALLY_READY as sufficient for the final Stage-4 "
        "architecture decision because: (1) all material burden uncertainties are now bounded "
        "(results/stage4_gate_d_burden_completeness.json known_unknowns - every item with "
        "could_be_decision_changing=true also has bounded=true); (2) candidate ordering is stable across "
        "every tested contact-count bound, battery topology, and MCU/radio topology "
        "(results/stage4_candidate_burden_matrix.json robustness_analysis); (3) remaining uncertainty "
        "affects absolute burden magnitude only, never the selected architecture-class ordering."
    ),
    "state_transition": ["NOT_READY", "CONDITIONALLY_READY", "COORDINATOR_ACCEPTED_BOUNDED_UNCERTAINTY"],
    "does_not_imply": (
        "This acceptance does NOT retroactively make Gate D READY, and does NOT imply the underlying bounds "
        "have narrowed to exact values - gate_d_burden_completeness remains CONDITIONALLY_READY verbatim. "
        "what_would_close_it (below) remains a real, disclosed list of what a future unconditional READY "
        "verdict would still require."
    ),
    "residual_disclosure_required_at_freeze": list(v2["what_would_close_it"]),
}

output = dict(v2)  # start from the full v2 record, then layer v3 on top - nothing dropped
output["schema_version"] = "3.0.0"
output["assessment_history"] = list(v2["assessment_history"]) + [
    {k: v for k, v in v2.items() if k != "assessment_history"}
]
output["coordinator_acceptance"] = COORDINATOR_ACCEPTANCE
# gate_d_burden_completeness, final_architecture_status, formal_pareto_status
# are intentionally left unchanged from v2 (CONDITIONALLY_READY / UNRESOLVED / NOT_READY).

GATE_D_PATH.write_text(json.dumps(output, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(f"Wrote {GATE_D_PATH} (v2 preserved in assessment_history, coordinator_acceptance added)")
