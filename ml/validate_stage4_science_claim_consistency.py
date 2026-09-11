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
]

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


def main() -> None:
    text = _read_all()
    check_no_invalid_galaxy_referenced_as_current(text)
    check_no_old_lbnp_referenced_as_current(text)
    check_no_bare_confounded_ppg_percentage(text)
    check_digital_twin_not_validated(text)

    for rel in STAGE4_ARTIFACTS:
        d = json.loads((REPO_ROOT / rel).read_text())
        check_hmc_ds_not_marked_complete(d)
        check_architecture_not_final(d)

    print("OK - all Stage-4 science claim consistency checks passed")


if __name__ == "__main__":
    main()
