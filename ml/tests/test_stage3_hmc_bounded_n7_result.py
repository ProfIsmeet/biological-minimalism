"""Contract tests for the real HMC bounded n=7 result. No performance
thresholds - the result is negative-leaning and that must not be hidden
or reversed by a future edit."""

from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
RESULT = json.loads((REPO_ROOT / "results" / "hmc_sleep_external_replication_stage3_bounded_n7.json").read_text())
SPLIT = json.loads((REPO_ROOT / "results" / "hmc_split_stage3_bounded_n7.json").read_text())


def test_capacity_b_equals_c():
    pc = RESULT["parameter_counts"]
    assert pc["B_eeg_plus_eog"] == pc["C_shuffled_eog"]


def test_scope_disclosure_present_and_not_canonical():
    assert "BOUNDED DIAGNOSTIC" in RESULT["scope_disclosure"]
    assert "NOT the canonical" in RESULT["scope_disclosure"]


def test_split_is_the_bounded_n7_not_full_cohort():
    assert SPLIT["bounded_cohort_size"] == 7
    assert SPLIT["full_frozen_cohort_size"] == 151


def test_negative_result_favorable_counts_disclosed_not_hidden():
    agg = RESULT["aggregate"]
    assert "n_seeds_favor_B" in agg["B_minus_A"]
    assert "n_seeds_favor_B" in agg["B_minus_C"]
    # real result: fewer than half of seeds favor B - must not be silently reported as positive
    assert agg["B_minus_A"]["n_seeds_favor_B"] <= 2


def test_five_seeds_present_in_all_three_conditions():
    for cond in ["model_a_macro_f1", "model_b_macro_f1", "model_c_macro_f1"]:
        assert set(RESULT["aggregate"][cond]["per_seed"].keys()) == {f"seed{s}" for s in (42, 43, 44, 45, 46)}
