"""Section 16/37 regression test: the GalaxyPPG corrected full-CV's Fold 5
must point to (and exactly match) its true corrected source, not the
invalidated pre-fix stage2 single-fold result."""

from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def _load(name):
    return json.loads((REPO_ROOT / "results" / name).read_text())


def test_fold5_reused_from_points_to_corrected_not_invalidated_source():
    d = _load("galaxyppg_corrected_full_cv_result.json")
    fold5 = d["folds"]["5"]
    assert fold5["reused_from"] == "results/galaxyppg_hr_corrected_eligibility_stage3.json"
    assert "external_replication_stage2" not in fold5["reused_from"]


def test_fold5_note_names_correct_test_subjects():
    d = _load("galaxyppg_corrected_full_cv_result.json")
    note = d["fold5_reuse_note"]
    assert "P02" in note and "P06" in note and "P12" in note
    # the leading, authoritative statement must name the correct subjects,
    # not the stale wrong ones (the wrong ones may still appear later,
    # solely inside the disclosure sentence explaining what was fixed)
    assert note.startswith("Fold 5 (test=P02/P06/P12)")


def test_fold5_exactly_equals_true_corrected_source():
    d = _load("galaxyppg_corrected_full_cv_result.json")
    source = _load("galaxyppg_hr_corrected_eligibility_stage3.json")
    fold5 = d["folds"]["5"]

    assert fold5["test_subjects"] == source["split"]["test"]
    assert fold5["runs"] == source["runs"]
    assert fold5["window_counts"] == source["window_counts"]

    fold5_ckpts = {(c["sha256"]) for c in source["checkpoint_manifest"]}
    assert len(fold5_ckpts) == 15  # 5 seeds x 3 conditions, all distinct
