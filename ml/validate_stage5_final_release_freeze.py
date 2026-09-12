#!/usr/bin/env python
"""Stage 5 Final Synthesis & Freeze: fail-closed cross-layer consistency
validator (master prompt Part X Section 44, Part XII hostile-review Attacks
A-J).

Extends (never replaces) ml.validate_stage4_final_architecture_closure: that
validator still enforces Stage-4 closure consistency (final architecture,
Gate D/E, formal Pareto, Digital Twin separation) on its original scope.
This validator additionally checks that every NEW Stage-5 synthesis artifact
(claim ledger, tables A-F, figure manifest, jury evidence pack, abstract fact
sheet, reproduction manifest, project manifest) agrees with the Stage-4
closure it derives from, and that no Stage-5 surface has silently
overclaimed beyond what the evidence supports.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from ml.validate_stage4_final_architecture_closure import main as run_stage4_closure_validator  # noqa: E402

CLAIM_LEDGER_PATH = "results/final_claim_ledger.json"
PROJECT_MANIFEST_PATH = "results/final_project_manifest.json"
TABLE_D_PATH = "results/final_tables/table_d_negative_mixed_results.json"
TABLE_E_PATH = "results/final_tables/table_e_final_architecture_rationale.json"
FIGURE_MANIFEST_PATH = "results/final_figure_manifest.json"
JURY_PACK_PATH = "presentation/final_jury_evidence_pack.json"
ABSTRACT_FACT_SHEET_PATH = "paper/final/abstract_fact_sheet.json"
REPRODUCTION_MANIFEST_PATH = "results/final_reproduction_manifest.json"
FINAL_ARCH_PATH = "results/final_wearable_architecture.json"
FORMAL_PARETO_PATH = "results/stage4_formal_pareto_analysis.json"
GATE_D_PATH = "results/stage4_gate_d_burden_completeness.json"

STAGE5_JSON_ARTIFACTS = [
    CLAIM_LEDGER_PATH, PROJECT_MANIFEST_PATH, TABLE_D_PATH, TABLE_E_PATH,
    FIGURE_MANIFEST_PATH, JURY_PACK_PATH, ABSTRACT_FACT_SHEET_PATH, REPRODUCTION_MANIFEST_PATH,
]

EXPECTED_SELECTED_CLASS = "CORE_PLUS_CONTEXT"


class Stage5FreezeConsistencyError(RuntimeError):
    pass


def _load(rel: str) -> dict:
    return json.loads((REPO_ROOT / rel).read_text(encoding="utf-8"))


def _canonical_text_sha256(rel: str) -> str:
    raw = (REPO_ROOT / rel).read_bytes()
    return hashlib.sha256(raw.replace(b"\r\n", b"\n")).hexdigest()


# Keys that legitimately document FORBIDDEN wording (i.e. contain the exact
# phrase as an example of what NOT to say) - must be excluded from positive-
# assertion phrase scans, or every prohibition list would trip its own guard.
PROHIBITION_DOCUMENTING_KEYS = {"prohibited_stronger_wording", "forbidden_overclaim", "prohibited_claim"}


def _dump_excluding_prohibition_fields(obj) -> str:
    """Serializes obj to text for forbidden-phrase scanning, omitting the
    values of any key that documents prohibited wording (those legitimately
    contain the exact phrases being guarded against)."""

    def _strip(node):
        if isinstance(node, dict):
            return {k: ("<<PROHIBITION_TEXT_OMITTED>>" if k in PROHIBITION_DOCUMENTING_KEYS else _strip(v)) for k, v in node.items()}
        if isinstance(node, list):
            return [_strip(v) for v in node]
        return node

    return json.dumps(_strip(obj))


def check_stage4_closure_still_honest() -> None:
    """Baseline: the Stage-4 closure validator (and everything it chains to)
    must still pass - Stage 5 adds a synthesis layer, it does not
    retroactively change Stage-4 facts."""
    run_stage4_closure_validator()


def check_galaxy_numbers_consistent_across_surfaces() -> None:
    """Attack A: the GalaxyPPG numeric_support string must agree across
    every Stage-5 surface that cites it."""
    ledger = _load(CLAIM_LEDGER_PATH)
    ledger_value = next(c for c in ledger["claims"] if c["claim_id"] == "galaxy_replication")["numeric_support"]

    table_c = _load("results/final_tables/table_c_external_replication.json")
    table_c_value = next(r for r in table_c["rows"] if r["modality"] == "Wrist PPG + IMU -> HR")["numeric_support"]

    abstract = _load(ABSTRACT_FACT_SHEET_PATH)
    abstract_value = next(s for s in abstract["statements"] if s["claim_id"] == "galaxy_replication")["numeric_support"]

    surfaces = {
        f"{CLAIM_LEDGER_PATH}#galaxy_replication": ledger_value,
        "results/final_tables/table_c_external_replication.json#galaxy_row": table_c_value,
        f"{ABSTRACT_FACT_SHEET_PATH}#galaxy_replication": abstract_value,
    }
    bad = {k: v for k, v in surfaces.items() if v != ledger_value}
    if bad:
        raise Stage5FreezeConsistencyError(f"GalaxyPPG numeric_support disagreement across Stage-5 surfaces: {bad}")


def check_architecture_consistent_across_stage5_surfaces() -> None:
    """Attack B: selected architecture must agree across every Stage-5
    surface that states one."""
    final_arch = _load(FINAL_ARCH_PATH)
    ledger = _load(CLAIM_LEDGER_PATH)
    project_manifest = _load(PROJECT_MANIFEST_PATH)
    table_e = _load(TABLE_E_PATH)

    ledger_arch_claim = next(c for c in ledger["claims"] if c["claim_id"] == "final_architecture")
    if EXPECTED_SELECTED_CLASS not in ledger_arch_claim["exact_final_safe_wording"]:
        raise Stage5FreezeConsistencyError(f"{CLAIM_LEDGER_PATH}#final_architecture does not name {EXPECTED_SELECTED_CLASS}.")

    surfaces = {
        f"{PROJECT_MANIFEST_PATH}#final_architecture.selected_class": project_manifest["final_architecture"]["selected_class"],
        f"{TABLE_E_PATH}#final_architecture": table_e["final_architecture"],
    }
    bad = {k: v for k, v in surfaces.items() if v != final_arch["selected_class"]}
    if bad:
        raise Stage5FreezeConsistencyError(f"Selected-architecture disagreement across Stage-5 surfaces: {bad}")


EOG_FORBIDDEN_PHRASES = (
    "eog is externally validated",
    "eog externally validated",
    "eog is validated on an independent",
    "eog validated on an independent",
)


def check_eog_not_marked_externally_validated_in_stage5() -> None:
    """Attack C: EOG must never be presented as externally validated in any
    new Stage-5 surface."""
    for rel in STAGE5_JSON_ARTIFACTS:
        text = _dump_excluding_prohibition_fields(_load(rel)).lower()
        for phrase in EOG_FORBIDDEN_PHRASES:
            if phrase in text:
                raise Stage5FreezeConsistencyError(f"{rel}: forbidden phrase {phrase!r} found - EOG must never be presented as externally validated.")


def check_bioz_negative_evidence_preserved_in_final_tables() -> None:
    """Attack D: thoracic/leg BioZ negative-leaning evidence must remain in
    Table D, never silently dropped from the final synthesis tables."""
    table_d = _load(TABLE_D_PATH)
    claim_ids_present = {row["claim_id"] for row in table_d["rows"]}
    for required in ("thoracic_eis", "leg_bioz"):
        if required not in claim_ids_present:
            raise Stage5FreezeConsistencyError(f"{TABLE_D_PATH}: {required!r} missing from negative/mixed results table.")
    for row in table_d["rows"]:
        if row["claim_id"] == "thoracic_eis" and "mixed" not in row["finding"].lower() and "MIXED" not in json.dumps(row):
            raise Stage5FreezeConsistencyError(f"{TABLE_D_PATH}: thoracic_eis row no longer discloses its mixed/negative-leaning classification.")


def check_hmc_ds003838_not_complete_in_stage5() -> None:
    """Attacks E/F: HMC full-cohort / ds003838 full-cohort must never be
    marked complete anywhere in the new Stage-5 surfaces."""
    for rel in STAGE5_JSON_ARTIFACTS:
        raw = _dump_excluding_prohibition_fields(_load(rel))
        for bad in ("HMC full-cohort training: COMPLETE", "ds003838 full-cohort: COMPLETE", "FULL_COHORT_COMPLETE"):
            if bad in raw:
                raise Stage5FreezeConsistencyError(f"{rel}: HMC/ds003838 full-cohort work marked complete: {bad!r}")


def _iter_leaf_strings(node, path: str = ""):
    """Yields (path, string_value) for every leaf string in a nested
    dict/list structure - used so a disclaimer in a NEIGHBORING field can
    never mask an overclaim inside a DIFFERENT field's own text."""
    if isinstance(node, dict):
        for k, v_ in node.items():
            if k in PROHIBITION_DOCUMENTING_KEYS:
                continue
            yield from _iter_leaf_strings(v_, f"{path}.{k}")
    elif isinstance(node, list):
        for i, v_ in enumerate(node):
            yield from _iter_leaf_strings(v_, f"{path}[{i}]")
    elif isinstance(node, str):
        yield (path, node)


def check_digital_twin_not_promoted_in_stage5() -> None:
    """Attack G: Digital Twin must not be implied validated anywhere in the
    new Stage-5 surfaces. Checks each leaf string's OWN text only - a
    disclaimer in a sibling/neighboring field must never mask an overclaim
    inside a different field."""
    for rel in STAGE5_JSON_ARTIFACTS:
        for field_path, value in _iter_leaf_strings(_load(rel)):
            if "Digital Twin" not in value:
                continue
            lower = value.lower()
            if "validated" in lower and not any(
                safe in lower for safe in ("unvalidated", "not longitudinally validated", "not a trained", "not validated", "not trained or")
            ):
                raise Stage5FreezeConsistencyError(f"{rel}{field_path}: Digital Twin mentioned near 'validated' without required disclaimer in the SAME field: {value!r}")


def check_pareto_no_false_dominance_in_stage5() -> None:
    """Attack H: no Stage-5 surface may claim a unique Pareto winner or that
    CORE_PLUS_CONTEXT mathematically dominates every alternative."""
    forbidden_phrases = ("mathematically dominates", "pareto winner", "unique optimal architecture", "unique mathematical winner")
    for rel in STAGE5_JSON_ARTIFACTS:
        text = _dump_excluding_prohibition_fields(_load(rel)).lower()
        for phrase in forbidden_phrases:
            idx = text.find(phrase)
            if idx == -1:
                continue
            window = text[max(0, idx - 80):idx]
            # Allow negated context ("does NOT mathematically dominate", "never...", "no unique...").
            if "not" not in window and "never" not in window and "no " not in window:
                raise Stage5FreezeConsistencyError(f"{rel}: forbidden unqualified phrase near {phrase!r} found.")

    ledger = _load(CLAIM_LEDGER_PATH)
    pareto_claim = next(c for c in ledger["claims"] if c["claim_id"] == "pareto")
    if "MINIMAL_CORE" not in pareto_claim["limitation"]:
        raise Stage5FreezeConsistencyError(f"{CLAIM_LEDGER_PATH}#pareto limitation no longer discloses MINIMAL_CORE remaining Pareto-relevant.")


def check_gate_d_not_silently_promoted_in_stage5() -> None:
    """Attack I: Gate D must remain CONDITIONALLY_READY in every Stage-5
    surface unless the Stage-4 accepted source itself changed."""
    gate_d_source = _load(GATE_D_PATH)
    if gate_d_source["gate_d_burden_completeness"] != "CONDITIONALLY_READY":
        raise Stage5FreezeConsistencyError(f"{GATE_D_PATH} itself is no longer CONDITIONALLY_READY - Stage-4 accepted source has changed; Stage-5 must not silently assume this.")

    project_manifest = _load(PROJECT_MANIFEST_PATH)
    if project_manifest["final_architecture"]["gate_d_burden_completeness"] != "CONDITIONALLY_READY":
        raise Stage5FreezeConsistencyError(f"{PROJECT_MANIFEST_PATH}#final_architecture.gate_d_burden_completeness is not CONDITIONALLY_READY.")


def check_release_manifest_hash_integrity() -> None:
    """Attack J: recompute the canonical-text hash of every authoritative
    artifact listed in the project manifest and require it to match the
    stored hash - catches post-freeze corruption of any authoritative file."""
    project_manifest = _load(PROJECT_MANIFEST_PATH)
    mismatches = {}
    for entry in project_manifest["authoritative_artifacts"]:
        path = entry["path"]
        stored = entry["sha256_canonical_text"]
        actual = _canonical_text_sha256(path)
        if stored != actual:
            mismatches[path] = {"stored": stored, "actual": actual}
    if mismatches:
        raise Stage5FreezeConsistencyError(f"Authoritative artifact hash mismatch (corruption after freeze): {mismatches}")


def main() -> None:
    check_stage4_closure_still_honest()
    check_galaxy_numbers_consistent_across_surfaces()
    check_architecture_consistent_across_stage5_surfaces()
    check_eog_not_marked_externally_validated_in_stage5()
    check_bioz_negative_evidence_preserved_in_final_tables()
    check_hmc_ds003838_not_complete_in_stage5()
    check_digital_twin_not_promoted_in_stage5()
    check_pareto_no_false_dominance_in_stage5()
    check_gate_d_not_silently_promoted_in_stage5()
    check_release_manifest_hash_integrity()
    print("OK - all Stage-5 final synthesis & release freeze consistency checks passed")


if __name__ == "__main__":
    main()
