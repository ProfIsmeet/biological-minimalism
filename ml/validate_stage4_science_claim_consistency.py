#!/usr/bin/env python
"""Section 37: lightweight validator for the Stage-4 science package.
Checks the new Stage-4 artifacts (not the whole repository) for the
specific failure modes this handoff exists to prevent. Raises
ClaimConsistencyError on any violation; prints OK on success."""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

STAGE4_ARTIFACTS = [
    "results/stage4_science_consumption_manifest.json",
    "results/stage4_scientific_sensor_value_matrix.json",
    "results/stage4_science_claim_ledger.json",
    "results/stage4_architecture_decision_inputs_science.json",
    "results/stage4_integration_science_allowlist.json",
    "results/stage4_architecture_science_decision_framework.json",
    "results/stage4_sensor_decision_sensitivity.json",
    "results/stage4_scientific_pareto_inputs.json",
    "results/stage4_architecture_acceptance_gates.json",
    "results/stage4_architecture_candidate_classes.json",
    # Integration Owner's own closure-prep artifacts (Stage-4 Gate D Burden
    # Closure sprint, master prompt Part XII Attack F): must never claim a
    # final architecture or a resolved formal Pareto, same as every
    # Science Owner artifact above.
    "results/stage4_gate_d_burden_completeness.json",
    "results/stage4_candidate_class_burden_comparison.json",
    "results/stage4_architecture_decision_projection.json",
    "results/stage4_gate_e_coordinator_options.json",
    "results/stage4_final_architecture_decision_packet.json",
    "results/stage4_contact_electrode_burden.json",
    "results/stage4_battery_topology_scenarios.json",
    "results/stage4_candidate_burden_matrix.json",
]

DECISION_STATUS_FIELDS = ("architecture_implication", "consumption_status", "evidence_classification")
ALLOWED_DECISION_STATUSES = {
    "STRONGLY_SUPPORTED_CORE", "SUPPORTED", "CONTEXTUAL_LOW_BURDEN", "MIXED", "DEPRIORITIZED",
    "EXPERIMENTAL", "PENDING_EXTERNAL_VALIDATION", "N/A", "GOVERNING",
    "GOVERNING (status: BOUNDED_DIAGNOSTIC - the only trained HMC evidence)",
    "GOVERNING (status: bounded diagnostic only)",
    "EXTERNAL_REPLICATION_SUPPORTIVE", "SAME_DATASET_BOUNDED_POSITIVE",
    "SAME_DATASET_BOUNDED_POSITIVE_WITH_VALID_CONTROL", "MIXED_UNRESOLVED",
    "CAPACITY_CONTROLLED_POSITIVE", "MIXED_NEGATIVE_LEANING_FRAGILE", "MIXED_HETEROGENEOUS",
    "COMPLETE_MIXED", "BOUNDED_DIAGNOSTIC_INCONCLUSIVE",
}

INVALID_GALAXY_MARKERS = ["galaxyppg_hr_external_replication_stage2.json", "galaxyppg_hr_full_grouped_cv_stage3.json"]
OLD_LBNP_MARKER = "lbnp_thoracic_eis_stage3.json"


class ClaimConsistencyError(RuntimeError):
    pass


def _read_all() -> str:
    text = ""
    for rel in STAGE4_ARTIFACTS:
        text += (REPO_ROOT / rel).read_text() + "\n"
    return text


def check_no_invalid_galaxy_referenced_as_current(text: str) -> None:
    for marker in INVALID_GALAXY_MARKERS:
        for line in text.splitlines():
            if marker in line and "GOVERNING" in line.upper() and "INVALIDATED" not in line.upper() and "excluded" not in line.lower():
                raise ClaimConsistencyError(f"Invalid Galaxy artifact '{marker}' referenced without INVALIDATED context: {line.strip()[:200]}")


def check_no_old_lbnp_referenced_as_current(text: str) -> None:
    for line in text.splitlines():
        lower = line.lower()
        if (OLD_LBNP_MARKER in line and "v2_protocol_compliant" not in line
                and "historical" not in lower and "excluded" not in lower
                and "never" not in lower and "superseded" not in lower):
            raise ClaimConsistencyError(f"Old LBNP result referenced without HISTORICAL/never/superseded context: {line.strip()[:200]}")


def check_no_bare_confounded_ppg_percentage(text: str) -> None:
    for marker in ("20.6%", "~23%", "23%"):
        idx = text.find(marker)
        if idx == -1:
            continue
        window = text[max(0, idx - 300):idx + 300]
        if "HISTORICAL" not in window.upper() and "CONFOUNDED" not in window.upper() and "never" not in window.lower():
            raise ClaimConsistencyError(f"Bare confounded PPG percentage '{marker}' found without historical/confounded/never-cite context.")


def check_hmc_ds_not_marked_complete(d: dict) -> None:
    raw = json.dumps(d)
    for bad in ("HMC full-cohort training: COMPLETE", "ds003838 full-cohort: COMPLETE", "FULL_COHORT_COMPLETE"):
        if bad in raw:
            raise ClaimConsistencyError(f"HMC/ds003838 full-cohort work marked complete: '{bad}'")


def check_architecture_not_final(d: dict) -> None:
    raw = json.dumps(d)
    if '"final_architecture_status": "RESOLVED"' in raw or '"final_architecture_status":"RESOLVED"' in raw:
        raise ClaimConsistencyError("final_architecture_status marked RESOLVED - must remain UNRESOLVED")
    if "final_architecture_status" in d and d["final_architecture_status"] != "UNRESOLVED":
        raise ClaimConsistencyError(f"final_architecture_status is {d['final_architecture_status']!r}, must be UNRESOLVED")


def check_digital_twin_not_validated(text: str) -> None:
    idx = text.find("Digital Twin")
    while idx != -1:
        window = text[idx:idx + 400]
        if "validated" in window.lower() and "not longitudinally validated" not in window.lower() and "not a trained" not in window.lower() and "unvalidated" not in window.lower():
            raise ClaimConsistencyError(f"Digital Twin mentioned near 'validated' without the required disclaimer: {window[:200]}")
        idx = text.find("Digital Twin", idx + 1)


def check_formal_pareto_not_ready(d: dict) -> None:
    if "formal_pareto_status" in d and d["formal_pareto_status"] != "NOT_READY":
        raise ClaimConsistencyError(f"formal_pareto_status is {d['formal_pareto_status']!r}, must be NOT_READY")


def check_no_arbitrary_keep_remove(raw: str) -> None:
    for bad in ('"KEEP"', '"REMOVE"'):
        if bad in raw:
            raise ClaimConsistencyError(f"Arbitrary final KEEP/REMOVE assignment found: {bad}")


def check_decision_statuses_are_from_allowed_vocabulary(d: dict, source: str) -> None:
    """Every decision-status-bearing field must use a value from the
    allowed vocabulary defined by the confidence-tier/architecture-
    implication framework - never an ad hoc string invented per-artifact."""

    def _walk(node):
        if isinstance(node, dict):
            for key, value in node.items():
                if key in DECISION_STATUS_FIELDS and isinstance(value, str):
                    if value not in ALLOWED_DECISION_STATUSES:
                        raise ClaimConsistencyError(
                            f"{source}: field '{key}' has value {value!r} not in the allowed decision-status vocabulary"
                        )
                _walk(value)
        elif isinstance(node, list):
            for item in node:
                _walk(item)

    _walk(d)


def main() -> None:
    text = _read_all()
    check_no_invalid_galaxy_referenced_as_current(text)
    check_no_old_lbnp_referenced_as_current(text)
    check_no_bare_confounded_ppg_percentage(text)
    check_digital_twin_not_validated(text)
    check_no_arbitrary_keep_remove(text)

    for rel in STAGE4_ARTIFACTS:
        d = json.loads((REPO_ROOT / rel).read_text())
        check_hmc_ds_not_marked_complete(d)
        check_architecture_not_final(d)
        check_formal_pareto_not_ready(d)
        check_decision_statuses_are_from_allowed_vocabulary(d, rel)

    print("OK - all Stage-4 science claim consistency checks passed")


if __name__ == "__main__":
    main()
