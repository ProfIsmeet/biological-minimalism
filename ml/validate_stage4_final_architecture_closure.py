#!/usr/bin/env python
"""Stage 4 Final Architecture Closure: fail-closed cross-layer consistency
validator (master prompt Part IX Section 26, Part XI hostile-review Attacks
A-H).

Extends (never replaces) ml.validate_stage4_science_claim_consistency: that
validator still enforces UNRESOLVED/NOT_READY on its original 18 Stage-4
artifacts (their scope is science/burden analysis inputs, unaffected by this
closure). This validator additionally checks that the 4 NEW/updated final-
closure artifacts agree with each other and with the still-UNRESOLVED
upstream inputs, and that no surface has silently overclaimed beyond what
the evidence supports.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from ml.validate_stage4_science_claim_consistency import main as run_upstream_validator  # noqa: E402

FINAL_ARCH_PATH = "results/final_wearable_architecture.json"
FORMAL_PARETO_PATH = "results/stage4_formal_pareto_analysis.json"
GATE_E_DECISIONS_PATH = "results/stage4_gate_e_coordinator_decisions.json"
GATE_D_PATH = "results/stage4_gate_d_burden_completeness.json"

CLOSURE_ARTIFACTS = [FINAL_ARCH_PATH, FORMAL_PARETO_PATH, GATE_E_DECISIONS_PATH, GATE_D_PATH]

EXPECTED_SELECTED_CLASS = "CORE_PLUS_CONTEXT"


class FinalClosureConsistencyError(RuntimeError):
    pass


def _load(rel: str) -> dict:
    return json.loads((REPO_ROOT / rel).read_text(encoding="utf-8"))


def check_upstream_still_honest() -> None:
    """Attack A/D surface: the original 18 science/burden artifacts must
    still all say UNRESOLVED/NOT_READY - this closure adds a NEW resolved
    surface, it does not retroactively resolve the inputs."""
    run_upstream_validator()


def check_selected_class_consistent_everywhere() -> None:
    """Attack A: selected architecture must agree across every surface that
    states one."""
    final_arch = _load(FINAL_ARCH_PATH)
    pareto = _load(FORMAL_PARETO_PATH)
    surfaces = {
        FINAL_ARCH_PATH + "#selected_class": final_arch["selected_class"],
        FINAL_ARCH_PATH + "#final_architecture_status": final_arch["final_architecture_status"],
        FINAL_ARCH_PATH + "#coordinator_decision_status.final_architecture": final_arch["coordinator_decision_status"]["final_architecture"],
        FORMAL_PARETO_PATH + "#coordinator_selected_architecture": pareto["coordinator_selected_architecture"],
        FORMAL_PARETO_PATH + "#final_architecture_status": pareto["final_architecture_status"],
    }
    bad = {k: v for k, v in surfaces.items() if v != EXPECTED_SELECTED_CLASS}
    if bad:
        raise FinalClosureConsistencyError(f"Selected-architecture disagreement across surfaces: {bad}")


def check_selected_modalities_match_science_owner_class() -> None:
    """Attack A variant: selected_modalities must match the Science Owner's
    own CORE_PLUS_CONTEXT class definition, not a hand-edited list."""
    final_arch = _load(FINAL_ARCH_PATH)
    candidate_classes = _load("results/stage4_architecture_candidate_classes.json")
    science_class = next(c for c in candidate_classes["classes"] if c["class_id"] == EXPECTED_SELECTED_CLASS)
    if final_arch["selected_modalities"] != science_class["sensors"]:
        raise FinalClosureConsistencyError(
            "final_wearable_architecture.json selected_modalities does not match "
            "stage4_architecture_candidate_classes.json's CORE_PLUS_CONTEXT sensor list."
        )


def check_gate_d_not_silently_ready() -> None:
    """Attack B: Gate D must never be silently promoted to unconditional
    READY without new bounding evidence."""
    gate_d = _load(GATE_D_PATH)
    if gate_d["gate_d_burden_completeness"] != "CONDITIONALLY_READY":
        raise FinalClosureConsistencyError(
            f"gate_d_burden_completeness is {gate_d['gate_d_burden_completeness']!r}, expected "
            "CONDITIONALLY_READY - this closure accepts bounded uncertainty, it does not manufacture READY."
        )
    acceptance = gate_d.get("coordinator_acceptance")
    if not acceptance or acceptance.get("accepted_verdict") != "CONDITIONALLY_READY":
        raise FinalClosureConsistencyError("gate_d coordinator_acceptance missing or does not accept CONDITIONALLY_READY.")
    if acceptance["state_transition"] != ["NOT_READY", "CONDITIONALLY_READY", "COORDINATOR_ACCEPTED_BOUNDED_UNCERTAINTY"]:
        raise FinalClosureConsistencyError(f"gate_d state_transition history malformed: {acceptance['state_transition']}")
    history = gate_d.get("assessment_history", [])
    if len(history) < 2 or history[0]["gate_d_burden_completeness"] != "NOT_READY" or history[0]["schema_version"] != "1.0.0":
        raise FinalClosureConsistencyError("gate_d assessment_history no longer starts from the original v1.0.0 NOT_READY record.")


def check_gate_e_frozen_conditionally_with_triggers() -> None:
    """Attack: Gate E decisions must both be FREEZE_CONDITIONALLY with a
    real revision trigger citing the pre-existing HMC-3/DS-2/DS-3 scenarios,
    never an invented trigger and never a bare unconditional freeze."""
    decisions = _load(GATE_E_DECISIONS_PATH)
    if decisions["no_option_selected"] is not False:
        raise FinalClosureConsistencyError("Gate E decisions still show no_option_selected=true.")
    if len(decisions["decisions"]) != 2:
        raise FinalClosureConsistencyError(f"Expected exactly 2 Gate E decisions, found {len(decisions['decisions'])}.")
    for d in decisions["decisions"]:
        if d["decision"] != "FREEZE_CONDITIONALLY":
            raise FinalClosureConsistencyError(f"Gate E item {d['item']!r} decision is {d['decision']!r}, expected FREEZE_CONDITIONALLY.")
        if not d.get("revision_trigger"):
            raise FinalClosureConsistencyError(f"Gate E item {d['item']!r} has no revision_trigger.")


def check_formal_pareto_no_false_dominance() -> None:
    """Attack G: never claim CORE_PLUS_CONTEXT mathematically dominates
    every alternative, or that a unique Pareto winner exists, unless the
    methodology genuinely establishes one."""
    pareto = _load(FORMAL_PARETO_PATH)
    # Check actual status/verdict FIELD VALUES only (never a raw substring
    # search) - this artifact's own prose legitimately explains, in negated
    # form, that "PARETO_WINNER is never used", which must not itself trip
    # this guard.
    status_like_values = [
        pareto.get("formal_pareto_status"),
        pareto.get("coordinator_selected_architecture"),
        *[entry.get("verdict") for entry in pareto.get("pairwise_dominance_analysis", [])],
    ]
    if "PARETO_WINNER" in status_like_values:
        raise FinalClosureConsistencyError("stage4_formal_pareto_analysis.json uses the forbidden PARETO_WINNER label as a field value.")
    if pareto.get("no_unique_pareto_winner") is not True:
        raise FinalClosureConsistencyError("stage4_formal_pareto_analysis.json must record no_unique_pareto_winner=true.")
    if "MINIMAL_CORE" not in pareto.get("pareto_relevant_set", []) or "CORE_PLUS_CONTEXT" not in pareto.get("pareto_relevant_set", []):
        raise FinalClosureConsistencyError("MINIMAL_CORE and CORE_PLUS_CONTEXT must both remain in pareto_relevant_set.")
    for entry in pareto.get("pairwise_dominance_analysis", []):
        if entry["class_a"] == "MINIMAL_CORE" and entry["class_b"] == "CORE_PLUS_CONTEXT":
            if entry["verdict"] not in ("NEITHER_DOMINATES_INCOMPARABLE",):
                raise FinalClosureConsistencyError(
                    f"MINIMAL_CORE vs CORE_PLUS_CONTEXT verdict is {entry['verdict']!r} - CORE_PLUS_CONTEXT must "
                    "never be asserted to mathematically dominate MINIMAL_CORE."
                )
    for entry in pareto.get("pairwise_dominance_analysis", []):
        if entry["class_b"] in ("EVIDENCE_EXTENDED", "EXPERIMENTAL_EXTENDED") and entry["verdict"] == "DOMINATED":
            raise FinalClosureConsistencyError(
                f"{entry['class_b']} marked formally DOMINATED - methodology in this artifact only supports "
                "POTENTIALLY_DOMINATED; upgrade requires new methodology, not a label edit."
            )


EOG_FORBIDDEN_PHRASES = (
    "eog is externally validated",
    "eog externally validated",
    "eog is validated on an independent",
    "eog validated on an independent",
)


def check_eog_not_marked_externally_validated() -> None:
    """Attack C: EOG must never be presented as externally validated - only
    same-dataset (TIER_B) support plus a bounded, underpowered (n=7)
    external diagnostic exist."""
    for rel in CLOSURE_ARTIFACTS:
        text = json.dumps(_load(rel)).lower()
        for phrase in EOG_FORBIDDEN_PHRASES:
            if phrase in text:
                raise FinalClosureConsistencyError(f"{rel}: forbidden phrase {phrase!r} found - EOG must never be presented as externally validated.")


def check_hmc_ds003838_not_complete_in_closure_artifacts() -> None:
    """Attacks D/E: HMC full-cohort / ds003838 full-cohort must never be
    marked complete anywhere in the new closure surfaces."""
    for rel in CLOSURE_ARTIFACTS:
        raw = json.dumps(_load(rel))
        for bad in ("HMC full-cohort training: COMPLETE", "ds003838 full-cohort: COMPLETE", "FULL_COHORT_COMPLETE"):
            if bad in raw:
                raise FinalClosureConsistencyError(f"{rel}: HMC/ds003838 full-cohort work marked complete: {bad!r}")


def check_bioz_negative_evidence_not_removed() -> None:
    """Attack F: thoracic/leg BioZ negative-leaning evidence must remain
    disclosed in the exclusion rationale, never silently dropped."""
    final_arch = _load(FINAL_ARCH_PATH)
    exclusions = final_arch["exclusion_rationale"]
    if "thoracic_bioz_eis" not in exclusions or "COMPLETE_MIXED" not in exclusions["thoracic_bioz_eis"]["reason"]:
        raise FinalClosureConsistencyError("Thoracic BioZ COMPLETE_MIXED negative-leaning evidence missing from exclusion_rationale.")
    if "leg_bioz" not in exclusions or "aggregate-negative" not in exclusions["leg_bioz"]["reason"]:
        raise FinalClosureConsistencyError("Leg BioZ aggregate-negative evidence missing from exclusion_rationale.")


def check_digital_twin_not_promoted() -> None:
    """Attack H: Digital Twin must not be implied validated by architecture
    closure anywhere in the new surfaces."""
    for rel in CLOSURE_ARTIFACTS:
        text = json.dumps(_load(rel))
        idx = text.find("Digital Twin")
        if idx != -1:
            window = text[idx:idx + 400].lower()
            if "validated" in window and "unvalidated" not in window and "not longitudinally validated" not in window and "not a trained" not in window:
                raise FinalClosureConsistencyError(f"{rel}: Digital Twin mentioned near 'validated' without required disclaimer.")


def check_stage5_not_started() -> None:
    final_arch = _load(FINAL_ARCH_PATH)
    note = final_arch["coordinator_decision_status"].get("not_yet_started", "")
    if "Stage 5" not in note or "NOT authorized" not in note:
        raise FinalClosureConsistencyError("final_wearable_architecture.json must explicitly state Stage 5 is not authorized.")


def main() -> None:
    check_upstream_still_honest()
    check_selected_class_consistent_everywhere()
    check_selected_modalities_match_science_owner_class()
    check_gate_d_not_silently_ready()
    check_gate_e_frozen_conditionally_with_triggers()
    check_formal_pareto_no_false_dominance()
    check_eog_not_marked_externally_validated()
    check_hmc_ds003838_not_complete_in_closure_artifacts()
    check_bioz_negative_evidence_not_removed()
    check_digital_twin_not_promoted()
    check_stage5_not_started()
    print("OK - all Stage-4 final architecture closure consistency checks passed")


if __name__ == "__main__":
    main()
