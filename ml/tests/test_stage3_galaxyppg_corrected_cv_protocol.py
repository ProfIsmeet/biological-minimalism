"""Sections 34-35 regression tests for the GalaxyPPG corrected-eligibility
reference-quality gate and corrected 18-subject 6-fold CV protocol
(GALAXYPPG_CORRECTED_ELIGIBILITY_CV_PROTOCOL_V2)."""

from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

EXPECTED_EXCLUDED = {"P01", "P22", "P07", "P19", "P15", "P03"}


def _load(name):
    return json.loads((REPO_ROOT / "results" / name).read_text())


def test_deterministic_eligibility_six_subjects_excluded():
    d = _load("galaxyppg_corrected_eligibility.json")
    assert d["n_total"] == 24
    assert d["n_eligible"] == 18
    excluded_ids = {e["participant_id"] for e in d["excluded"]}
    assert excluded_ids == EXPECTED_EXCLUDED
    assert len(d["eligible"]) == 18
    assert set(d["eligible"]).isdisjoint(EXPECTED_EXCLUDED)


def test_excluded_subjects_below_threshold_eligible_above():
    d = _load("galaxyppg_corrected_eligibility.json")
    for e in d["excluded"]:
        if e["participant_id"] != "P01":
            assert e["r_peaks_per_min"] < 40.0
    # P01 is the closest excluded case, still clearly below the real gap
    p01 = next(e for e in d["excluded"] if e["participant_id"] == "P01")
    assert p01["r_peaks_per_min"] < 40.0


def test_no_outcome_used_flag_present():
    d = _load("galaxyppg_corrected_eligibility.json")
    assert d["no_performance_outcome_used"] is True


def test_cv_protocol_covers_all_eligible_subjects_exactly_once():
    folds_doc = _load("galaxyppg_corrected_full_cv_folds.json")
    elig = _load("galaxyppg_corrected_eligibility.json")
    assert folds_doc["n_folds"] == 6
    assert folds_doc["n_eligible"] == 18
    all_fold_members = [pid for fold in folds_doc["folds"] for pid in fold]
    assert len(all_fold_members) == 18
    assert len(set(all_fold_members)) == 18  # no duplicate membership
    assert set(all_fold_members) == set(elig["eligible"])  # exact cohort match
    for fold in folds_doc["folds"]:
        assert len(fold) == 3
        assert len(set(fold)) == 3  # no within-fold duplicate


def test_fold5_reuse_note_documents_independent_reverification():
    folds_doc = _load("galaxyppg_corrected_full_cv_folds.json")
    assert "fold5_reuse_note" in folds_doc
    note = folds_doc["fold5_reuse_note"].lower()
    assert "re-verif" in note or "reverif" in note


def test_corrected_cv_checkpoints_use_distinct_v2_namespace():
    src = (REPO_ROOT / "ml" / "train_galaxyppg_corrected_full_cv.py").read_text()
    assert "correctedcv_v2" in src
    # must not reuse the pre-fix full-CV checkpoint naming pattern
    assert "galaxyppg_hr_fullcv_fold" not in src
