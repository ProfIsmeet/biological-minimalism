"""Regression tests for Codex remediation Sections 26-27: HMC bounded-n7
result's split_source must point to the real file actually used, and
chronology wording must use the safe 'frozen before any bounded
training/evaluation' phrasing rather than unsupported 'before any HMC
file was opened/downloaded' or 'preregistered' claims."""

from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def test_bounded_n7_result_split_source_points_to_real_file_used():
    d = json.loads((REPO_ROOT / "results" / "hmc_sleep_external_replication_stage3_bounded_n7.json").read_text())
    assert d["split_source"] == "results/hmc_split_stage3_bounded_n7.json"
    assert d["reduced_cohort_deviation_doc"] == "docs/HMC_FULL_COHORT_CERT_EXPIRY_BLOCKER.md"
    assert "provenance_correction_note" in d


def test_trainer_source_matches_corrected_pointers():
    src = (REPO_ROOT / "ml" / "train_hmc_sleep_a_b_c_bounded_n7.py").read_text()
    assert '"split_source": "results/hmc_split_stage3_bounded_n7.json"' in src
    assert '"reduced_cohort_deviation_doc": "docs/HMC_FULL_COHORT_CERT_EXPIRY_BLOCKER.md"' in src


def test_no_unsupported_chronology_claims_in_own_split_docs():
    for fname in ("HMC_STAGE3_SPLIT_STRATEGY_DEVIATION.md", "HMC_PILOT_DISPOSITION.md"):
        text = (REPO_ROOT / "docs" / fname).read_text()
        assert "before any HMC file was opened" not in text
        assert "before any HMC file was downloaded" not in text
        assert "bounded training/evaluation" in text
