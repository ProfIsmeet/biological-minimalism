"""HIGH-01 regression tests (Sections 34-35): the GalaxyPPG participant-
level condition-C evaluation must use deranged test ACC, not aligned ACC -
and the corrected per-participant C predictions must reconstruct the
already-valid fold-level C result (strong consistency, Section 6)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "backend"))
sys.path.insert(0, str(REPO_ROOT))


def test_deranged_acc_for_subject_differs_from_aligned_acc():
    """Tensor-level check (not a string/declaration check): the reconstructed
    per-participant deranged ACC must actually differ from the aligned ACC
    it replaces, for a real multi-window participant."""
    from ml.fix_galaxyppg_participant_c_evaluation import deranged_acc_for_subject_at_index

    rng = np.random.default_rng(0)
    aligned = rng.standard_normal((50, 3, 100)).astype(np.float32)
    deranged = deranged_acc_for_subject_at_index(aligned, seed_base=200042 + 42, subject_index=0)

    assert deranged.shape == aligned.shape
    assert not np.array_equal(deranged, aligned)
    # every row must be a real permutation of the original rows (same set of
    # window-content, no synthetic/zeroed data), and no row maps to itself
    # (no fixed points), matching deranged_acc_stable's own invariant
    used = set()
    for i in range(len(aligned)):
        match = None
        for j in range(len(aligned)):
            if np.array_equal(deranged[i], aligned[j]):
                match = j
                break
        assert match is not None, f"row {i} of deranged ACC is not any original window - fabricated data"
        assert match != i, f"row {i} mapped to itself - derangement has a fixed point"
        used.add(match)
    assert len(used) == len(aligned)  # a true permutation, not a lossy remap


def test_deranged_acc_index_matches_array_level_derangement():
    """The per-subject helper must reproduce EXACTLY what deranged_acc_stable
    computes for that subject when run at the array level - checked directly
    against the array-level function, not merely re-implemented in parallel."""
    from ml.fix_galaxyppg_participant_c_evaluation import deranged_acc_for_subject_at_index
    from ml.train_galaxyppg_hr_external_replication import deranged_acc_stable

    rng = np.random.default_rng(1)
    # three subjects, uneven window counts, to catch any accidental index-vs-count coupling
    acc_by_subject = {
        "P01": rng.standard_normal((10, 3, 100)).astype(np.float32),
        "P05": rng.standard_normal((7, 3, 100)).astype(np.float32),
        "P09": rng.standard_normal((13, 3, 100)).astype(np.float32),
    }
    subject_ids = sorted(acc_by_subject.keys())
    full_acc = np.concatenate([acc_by_subject[pid] for pid in subject_ids])
    full_subject = np.concatenate([[pid] * len(acc_by_subject[pid]) for pid in subject_ids])

    seed_base = 200042 + 43
    array_level = deranged_acc_stable(full_acc, full_subject, seed_base)

    offset = 0
    for i, pid in enumerate(subject_ids):
        n = len(acc_by_subject[pid])
        expected = array_level[offset:offset + n]
        actual = deranged_acc_for_subject_at_index(acc_by_subject[pid], seed_base, subject_index=i)
        assert np.array_equal(actual, expected), f"mismatch for {pid} at index {i}"
        offset += n


def test_strong_consistency_check_all_passed():
    check = json.loads((REPO_ROOT / "results" / "galaxyppg_high01_strong_consistency_check.json").read_text())
    assert len(check["checks"]) == 30  # 5 newly-trained folds x 5 seeds + 5 bounded-diagnostic seeds
    for c in check["checks"]:
        assert c["within_tolerance_1e-4"] is True
        assert c["abs_diff"] < 1e-4


def test_full_cv_result_carries_high01_correction_note():
    d = json.loads((REPO_ROOT / "results" / "galaxyppg_corrected_full_cv_result.json").read_text())
    assert "high01_participant_c_correction_note" in d
    note = d["high01_participant_c_correction_note"].lower()
    assert "aligned" in note and "deranged" in note


def test_ab_untouched_by_high01_fix():
    """A/B numbers must remain exactly what Codex independently found
    credible - HIGH-01 only ever touched C."""
    d = json.loads((REPO_ROOT / "results" / "galaxyppg_corrected_full_cv_result.json").read_text())
    agg = d["aggregate_across_all_18_eligible_subjects"]
    assert abs(agg["A_to_B"]["mean"] - 0.8342679686016505) < 1e-6
    assert agg["A_to_B"]["n_subjects_favor_B"] == 12
