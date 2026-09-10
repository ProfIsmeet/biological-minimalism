"""Regression tests for ml/check_claim_consistency.py's new Codex
parent-science-audit delta-hardening patterns.

Two things are verified per pattern: (1) the regex actually catches a
synthetic bad-example line (proves the guard has teeth, independent of
current file content), and (2) the live repository currently has zero
violations (proves the fix already applied — e.g. the Digital Twin
wording — is clean).
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from ml.check_claim_consistency import FORBIDDEN, NEGATION_MARKERS, check_stale  # noqa: E402


def _matches_some_forbidden_pattern(line: str) -> bool:
    negated = bool(NEGATION_MARKERS.search(line))
    if negated:
        return False
    return any(pattern.search(line) for pattern, _label in FORBIDDEN)


def test_hmc_chronology_overclaim_is_caught() -> None:
    bad = "The HMC split was frozen before any HMC file was opened/downloaded."
    assert _matches_some_forbidden_pattern(bad)


def test_hmc_verified_chronology_is_not_caught() -> None:
    good = "Codex verified only that the split was frozen before bounded training/evaluation."
    assert not _matches_some_forbidden_pattern(good)


def test_hmc_preregistered_claim_is_caught() -> None:
    bad = "The HMC split is preregistered and frozen ahead of any training run."
    assert _matches_some_forbidden_pattern(bad)


def test_status_self_promotion_is_caught() -> None:
    assert _matches_some_forbidden_pattern("This artifact is CANONICAL_UNCHANGED across the merge.")
    assert _matches_some_forbidden_pattern("Sleep science is SCIENCE_COMPLETE as of this commit.")


def test_status_self_promotion_negated_form_is_not_caught() -> None:
    good = "A source artifact must never claim CANONICAL_UNCHANGED without Coordinator acceptance."
    assert not _matches_some_forbidden_pattern(good)


def test_digital_twin_present_tense_learns_baseline_is_caught() -> None:
    bad = "The Digital Twin learns a personalized baseline over the first 48 hours."
    assert _matches_some_forbidden_pattern(bad)


def test_digital_twin_caveated_future_tense_is_not_caught() -> None:
    good = (
        "The Digital Twin is designed to support future personalized-baseline learning "
        "when sufficient longitudinal subject-specific data are available; this is "
        "synthetic and untrained."
    )
    assert not _matches_some_forbidden_pattern(good)


def test_live_repository_has_zero_stale_claim_violations() -> None:
    """This is the actual enforcement check — same function `main()` runs.
    Confirms the Digital Twin wording fix and all other live surfaces are
    currently clean against every FORBIDDEN pattern, including the four
    added this sprint."""
    problems = check_stale()
    assert problems == [], f"unexpected stale/forbidden claims found: {problems}"
