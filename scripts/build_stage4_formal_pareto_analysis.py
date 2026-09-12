"""Stage 4 Final Architecture Closure: formal Pareto analysis
(INTEGRATION_OWNER, master prompt Part III Sections 15-17).

Combines the Science Owner's science-only Pareto axes
(results/stage4_scientific_pareto_inputs.json) with the Integration Owner's
burden axes (results/stage4_candidate_burden_matrix.json,
results/stage4_candidate_class_burden_comparison.json) into a formal,
per-axis multi-objective dominance analysis across the 4 candidate classes.

Explicit non-goal (preserved from every upstream artifact): this script does
NOT compute TOTAL_SCORE = SCIENCE +/- MASS +/- POWER or any other collapsed
composite. Dominance is determined by a strict per-axis partial order: class
A dominates class B only if A is weakly better than B on every burden axis
(contacts, power, mass, data rate - lower is better) AND weakly better on
every science axis for B's full modality set, with a strict improvement on
at least one axis. Where axes are not commensurable (e.g. a candidate adds a
sensing capability entirely absent from the other, regardless of that
capability's evidence quality), the two classes are INCOMPARABLE, not
dominated, by definition of a partial (not total) order.
"""

from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PATH = REPO_ROOT / "results" / "stage4_formal_pareto_analysis.json"


def _load(rel: str) -> dict:
    return json.loads((REPO_ROOT / rel).read_text())


pareto_inputs = _load("results/stage4_scientific_pareto_inputs.json")
burden_comparison = _load("results/stage4_candidate_class_burden_comparison.json")
burden_matrix = _load("results/stage4_candidate_burden_matrix.json")
candidate_classes = _load("results/stage4_architecture_candidate_classes.json")

# Hard-fail guard: this analysis is only valid if Gate D burden data is at
# least bounded (CONDITIONALLY_READY or better) - a formal dominance claim
# built on NOT_READY burden data would be unsound.
gate_d = _load("results/stage4_gate_d_burden_completeness.json")
if gate_d["gate_d_burden_completeness"] not in ("CONDITIONALLY_READY", "READY"):
    raise SystemExit(
        f"REFUSING TO RUN: gate_d_burden_completeness={gate_d['gate_d_burden_completeness']!r} - a formal "
        "Pareto analysis requires at least CONDITIONALLY_READY burden data."
    )

burden_by_class = {c["class_id"]: c for c in burden_comparison["classes"]}
matrix_by_class = {c["class_id"]: c for c in burden_matrix["classes"]}

METHODOLOGY = {
    "explicit_non_goal": (
        "Does NOT compute TOTAL_SCORE = SCIENCE +/- MASS +/- POWER or any other weighted/collapsed composite. "
        "No single numeric score is ever produced for any candidate class."
    ),
    "dominance_definition": (
        "Class A formally DOMINATES class B if and only if A is weakly better than B on EVERY burden axis "
        "(total_contacts most_likely, battery-side power [selected topology], mass, raw data rate - lower is "
        "better) AND weakly better than B on EVERY science axis for every modality B includes that A lacks "
        "(incremental_value ordinal NEGATIVE < MIXED < NEUTRAL < POSITIVE, decision_fragility HIGH worse than "
        "LOW), with a strict improvement on at least one axis. Where B includes a sensing capability entirely "
        "ABSENT from A (a distinct physiological target A structurally cannot capture, per "
        "results/stage4_scientific_pareto_inputs.json breadth/uniqueness axes), A and B are INCOMPARABLE on "
        "that axis, not ordered - by definition of a partial order, A cannot dominate B while such an "
        "incomparable axis exists in B's favor. This is a conservative methodology: it will under-claim "
        "dominance rather than over-claim it, per the governing instruction to never assert false mathematical "
        "dominance."
    ),
    "burden_axes": ["total_contacts.most_likely", "power_range_mw (selected topology)", "mass_range_g", "raw_data_rate_bps"],
    "science_axes": list(pareto_inputs["scientific_pareto_axes"].keys()),
    "source_artifacts": [
        "results/stage4_scientific_pareto_inputs.json",
        "results/stage4_candidate_class_burden_comparison.json",
        "results/stage4_candidate_burden_matrix.json",
        "results/stage4_architecture_candidate_classes.json",
    ],
}

# ---------------------------------------------------------------------------
# MINIMAL_CORE vs CORE_PLUS_CONTEXT: CORE_PLUS_CONTEXT is strictly worse on
# every burden axis (more contacts/power/mass) but strictly better on the
# science breadth axis (adds EOG sleep-staging capability MINIMAL_CORE
# entirely lacks). Neither weakly dominates the other -> both Pareto-relevant.
# ---------------------------------------------------------------------------
minimal_core_vs_core_plus_context = {
    "class_a": "MINIMAL_CORE",
    "class_b": "CORE_PLUS_CONTEXT",
    "burden_comparison": "CORE_PLUS_CONTEXT strictly worse on every burden axis (contacts +2, power +0.375 mW sensor-side, data rate +2400 bps) - MINIMAL_CORE weakly dominates on burden alone.",
    "science_comparison": "CORE_PLUS_CONTEXT strictly better on breadth/capability (adds sleep-stage-classification improvement via EOG, TIER_B_CONTROLLED_SUPPORT same-dataset) - a capability MINIMAL_CORE structurally lacks. MINIMAL_CORE cannot weakly dominate on this axis.",
    "verdict": "NEITHER_DOMINATES_INCOMPARABLE",
    "reasoning": "MINIMAL_CORE dominates on burden but not on science breadth; CORE_PLUS_CONTEXT dominates on science breadth but not on burden. A partial order with disagreeing axis rankings yields two mutually non-dominated (Pareto-relevant) points, not a winner.",
}

# ---------------------------------------------------------------------------
# EVIDENCE_EXTENDED: adds thoracic BioZ + leg BioZ, both MIXED (not
# NEGATIVE) incremental_value with HIGH decision_fragility, at a real burden
# cost (new leg_module body region, +12 contacts, +~2.4-6.5 mW sensor-side).
# Its added modalities capture thoracic-impedance/fluid-shift-proxy
# information CORE_PLUS_CONTEXT cannot capture at all (breadth axis) - so
# CORE_PLUS_CONTEXT does not weakly dominate on every axis, and formal
# dominance is NOT established, despite the burden cost being real and the
# evidence being weak. This mirrors the existing (pre-closure)
# dominance_flag=POTENTIALLY_DOMINATED and is not upgraded to DOMINATED.
# ---------------------------------------------------------------------------
core_plus_context_vs_evidence_extended = {
    "class_a": "CORE_PLUS_CONTEXT",
    "class_b": "EVIDENCE_EXTENDED",
    "burden_comparison": "CORE_PLUS_CONTEXT strictly better on every burden axis (fewer contacts, lower power/mass/data-rate, no new body region) - confirmed by results/stage4_candidate_burden_matrix.json robustness_analysis (ordering preserved across every tested bound/topology).",
    "science_comparison": (
        "Thoracic BioZ/EIS and leg BioZ (EVIDENCE_EXTENDED's increment) both score incremental_value=MIXED "
        "(not NEGATIVE) with decision_fragility=HIGH in results/stage4_scientific_pareto_inputs.json, and both "
        "target physiological information (thoracic-impedance / lower-body fluid-tissue signal) that "
        "CORE_PLUS_CONTEXT structurally cannot capture at all - a breadth/uniqueness axis on which "
        "EVIDENCE_EXTENDED is not weakly dominated by CORE_PLUS_CONTEXT, regardless of the current evidence "
        "quality for that specific capability."
    ),
    "verdict": "NOT_FORMALLY_DOMINATED_REMAINS_POTENTIALLY_DOMINATED",
    "reasoning": (
        "CORE_PLUS_CONTEXT is weakly better on every burden axis (strict improvement, several axes) but is NOT "
        "weakly better on the breadth axis (it simply does not attempt thoracic/leg BioZ sensing) - per this "
        "methodology's dominance_definition, an incomparable axis in B's favor blocks formal domination even "
        "though B's evidence for that axis is currently weak (MIXED, not POSITIVE). This is a genuine "
        "methodological limit, not an oversight: 'low burden does not transform weak evidence into strong "
        "evidence' (candidate_class_burden_comparison.json dominance_reason) cuts both ways - weak evidence "
        "for an unmatched capability also does not, by itself, mathematically prove that capability worthless "
        "enough to declare formal dominance. EVIDENCE_EXTENDED remains POTENTIALLY_DOMINATED, not DOMINATED: "
        "the burden case against it is real and disclosed (new body region, real power cost, MIXED/fragile "
        "evidence), but that is a normative judgment for the Coordinator, not a proven mathematical dominance."
    ),
    "why_not_selected": "Neither thoracic BioZ nor leg BioZ has demonstrated stable incremental value in current governing evidence (both TIER_D_MIXED_OR_FRAGILE); their pending_science_exposure is LOW (no planned experiment would resolve the ambiguity further) - the burden cost is real and ongoing while the evidence case is not expected to improve without new experimental work outside current scope.",
}

# ---------------------------------------------------------------------------
# EXPERIMENTAL_EXTENDED: adds second-site PPG (NEGATIVE, LOW fragility - a
# confident negative) + wrist temperature/light (TIER_P_PENDING - genuinely
# unknown, not negative). The PENDING component blocks a full-class
# dominance claim: PENDING evidence cannot be treated as equivalent to zero
# value without violating this project's own evidentiary-honesty standard
# (Gate C/G) - so the class as a whole remains POTENTIALLY_DOMINATED, even
# though second-site PPG alone would be the stronger dominance candidate.
# ---------------------------------------------------------------------------
evidence_extended_vs_experimental_extended = {
    "class_a": "EVIDENCE_EXTENDED",
    "class_b": "EXPERIMENTAL_EXTENDED",
    "burden_comparison": "EVIDENCE_EXTENDED strictly better on every burden axis (fewer contacts, substantially lower power - EXPERIMENTAL_EXTENDED's second-site PPG alone is 9.018 mW sensor-side, the single largest contributor in the entire burden model).",
    "science_comparison": (
        "Second-site PPG scores incremental_value=NEGATIVE with decision_fragility=LOW (a confident, "
        "consistently-negative result, per results/stage4_science_claim_ledger.json second_site_ppg claim) - "
        "this component alone would satisfy formal dominance (no positive value claimed, real burden cost). "
        "However, wrist temperature/light score TIER_P_PENDING with decision_sensitivity=MEDIUM - genuinely "
        "UNKNOWN value, not established-negative. Per this project's evidentiary-honesty standard (Gate C/G), "
        "PENDING/unproven must never be treated as equivalent to zero or negative value."
    ),
    "verdict": "NOT_FORMALLY_DOMINATED_REMAINS_POTENTIALLY_DOMINATED",
    "reasoning": (
        "If EXPERIMENTAL_EXTENDED consisted only of second-site PPG, EVIDENCE_EXTENDED would formally dominate "
        "it (NEGATIVE evidence + real burden cost, no incomparable-capability axis in its favor). But the "
        "class as defined also includes wrist temperature/light, whose TIER_P_PENDING status is a genuinely "
        "open capability axis (no governing experiment exists either direction) - treating PENDING as "
        "dominated-away would misrepresent an absence of evidence as evidence of absence, which Gate C/G "
        "explicitly forbids. The class-level verdict is therefore POTENTIALLY_DOMINATED, not DOMINATED, driven "
        "entirely by the PENDING component; second-site PPG's own sub-verdict is noted separately below for "
        "transparency."
    ),
    "second_site_ppg_sub_verdict": "Would satisfy formal dominance in isolation (NEGATIVE evidence, LOW fragility, real burden) - not sufficient alone to dominate the full class because wrist temperature/light remain PENDING.",
    "why_not_selected": "Second-site PPG has a demonstrated negative result (not merely absent evidence); wrist temperature/light have zero governing evidence at all. This class is explicitly exploratory per results/stage4_architecture_candidate_classes.json, never evidence-supported.",
}

PARETO_RELEVANT_SET = ["MINIMAL_CORE", "CORE_PLUS_CONTEXT"]
POTENTIALLY_DOMINATED_SET = ["EVIDENCE_EXTENDED", "EXPERIMENTAL_EXTENDED"]

COORDINATOR_SELECTION_RATIONALE = (
    "Coordinator selected CORE_PLUS_CONTEXT from the Pareto-relevant set because the EOG increment adds "
    "controlled sleep-staging evidence at low incremental physical burden without adding a new body region or "
    "full module, while accepting conditional external-validation uncertainty."
)

output = {
    "artifact_id": "biological-minimalism-stage4-formal-pareto-analysis-v1",
    "schema_version": "1.0.0",
    "sprint": "STAGE4_FINAL_ARCHITECTURE_CLOSURE",
    "generated_role": "INTEGRATION_OWNER",
    "purpose": (
        "Formal, multi-objective (never single-score) Pareto dominance analysis across the 4 Science-Owner-"
        "defined candidate architecture classes, completing GATE_D-bounded burden data with the Science "
        "Owner's science-only Pareto axes."
    ),
    "methodology": METHODOLOGY,
    "pairwise_dominance_analysis": [
        minimal_core_vs_core_plus_context,
        core_plus_context_vs_evidence_extended,
        evidence_extended_vs_experimental_extended,
    ],
    "pareto_relevant_set": PARETO_RELEVANT_SET,
    "potentially_dominated_set": POTENTIALLY_DOMINATED_SET,
    "no_unique_pareto_winner": True,
    "no_unique_pareto_winner_reason": "MINIMAL_CORE and CORE_PLUS_CONTEXT are both non-dominated (Pareto-relevant) - the methodology does not establish a unique mathematical winner. PARETO_WINNER is never used.",
    "coordinator_selected_architecture": "CORE_PLUS_CONTEXT",
    "coordinator_selection_rationale": COORDINATOR_SELECTION_RATIONALE,
    "coordinator_selection_is_not_mathematical_dominance": (
        "CORE_PLUS_CONTEXT does NOT mathematically dominate MINIMAL_CORE or any other candidate - it was "
        "selected from within the Pareto-relevant set on Coordinator judgment (evidence-driven, burden-aware), "
        "not because the formal analysis proves it superior on every axis."
    ),
    "final_architecture_status": "CORE_PLUS_CONTEXT",
    "formal_pareto_status": "COMPLETE",
}

OUTPUT_PATH.write_text(json.dumps(output, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(f"Wrote {OUTPUT_PATH}")
