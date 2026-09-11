"""Section 17/38 regression test: attempting to resolve an invalidated
GalaxyPPG artifact as current evidence must fail closed."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from ml.galaxyppg_evidence_resolver import InvalidatedEvidenceError, resolve_galaxyppg_evidence  # noqa: E402


def test_resolving_invalidated_single_fold_by_path_fails_closed():
    with pytest.raises(InvalidatedEvidenceError):
        resolve_galaxyppg_evidence("results/galaxyppg_hr_external_replication_stage2.json")


def test_resolving_invalidated_full_cv_by_path_fails_closed():
    with pytest.raises(InvalidatedEvidenceError):
        resolve_galaxyppg_evidence("results/galaxyppg_hr_full_grouped_cv_stage3.json")


def test_resolving_invalidated_full_cv_by_experiment_id_fails_closed():
    with pytest.raises(InvalidatedEvidenceError):
        resolve_galaxyppg_evidence("galaxyppg_hr_full_grouped_cv_stage3")


def test_resolving_current_evidence_succeeds():
    data = resolve_galaxyppg_evidence("results/galaxyppg_corrected_full_cv_result.json")
    assert data["experiment_id"] == "galaxyppg_hr_corrected_eligibility_full_cv_v2"


def test_resolving_current_bounded_diagnostic_succeeds():
    data = resolve_galaxyppg_evidence("results/galaxyppg_hr_corrected_eligibility_stage3.json")
    assert "aggregate" in data
