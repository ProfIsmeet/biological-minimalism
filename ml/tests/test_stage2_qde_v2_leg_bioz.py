"""Stage 2A scientific-failure-mode tests for the real QDE V2 training run.
No performance-threshold assertions (Section 80) - contract/integrity only."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
RESULT = json.loads((REPO_ROOT / "results" / "qde_v2_leg_bioz_stage2.json").read_text())


def test_ten_subjects_all_present_in_all_three_conditions():
    for cond in ["condition_A_arm_trunk_only", "condition_B_arm_trunk_plus_legs", "condition_C_deranged_legs"]:
        assert set(RESULT[cond]["per_subject"].keys()) == {str(i) for i in range(1, 11)}


def test_each_subject_has_nine_points():
    for sid, d in RESULT["condition_B_arm_trunk_plus_legs"]["per_subject"].items():
        assert d["n_points"] == 9


def test_loso_each_fold_has_exactly_nine_training_subjects():
    # implied by construction: 10 subjects, one held out per fold - verify by re-deriving from the trainer module
    sys.path.insert(0, str(REPO_ROOT))
    from ml.train_qde_v2_leg_bioz import load_raw
    by_subject = load_raw()
    assert len(by_subject) == 10
    for test_sid in by_subject:
        train_sids = [s for s in by_subject if s != test_sid]
        assert len(train_sids) == 9


def test_sd_uses_ddof1():
    a = RESULT["condition_A_arm_trunk_only"]
    import numpy as np
    maes = np.array([v["mae"] for v in a["per_subject"].values()])
    assert abs(a["subject_macro_mae_sd_ddof1"] - maes.std(ddof=1)) < 1e-9


def test_deterministic_full_rerun_reproduces_exactly():
    result = subprocess.run(
        [sys.executable, str(REPO_ROOT / "ml" / "train_qde_v2_leg_bioz.py")],
        cwd=REPO_ROOT, capture_output=True, text=True,
    )
    assert result.returncode == 0
    after = json.loads((REPO_ROOT / "results" / "qde_v2_leg_bioz_stage2.json").read_text())
    assert after == RESULT


def test_negative_result_not_hidden_favorable_counts_disclosed():
    agg = RESULT["aggregate"]
    assert "n_subjects_favoring_B_over_A" in agg
    assert "n_subjects_favoring_B_over_C" in agg
    assert 0 <= agg["n_subjects_favoring_B_over_A"] <= 10


def test_no_subject_silently_dropped_from_per_subject_deltas():
    assert set(RESULT["per_subject_deltas"].keys()) == {str(i) for i in range(1, 11)}


def test_control_c_baseline_point_never_deranged():
    sys.path.insert(0, str(REPO_ROOT))
    from ml.train_qde_v2_leg_bioz import build_subject_arrays, load_raw
    import numpy as np
    by_subject = load_raw()
    subjects = build_subject_arrays(by_subject, np.random.default_rng(0))
    for sid, d in subjects.items():
        assert np.allclose(d["B"][0], d["C"][0]), f"subject {sid} baseline point differs between B and C"
