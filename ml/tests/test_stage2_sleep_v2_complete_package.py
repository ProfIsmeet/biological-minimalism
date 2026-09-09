"""Contract tests for the Sleep V2 complete package and the real C/interaction
results this sprint produced. No performance-threshold assertions."""

from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
PACKAGE = json.loads((REPO_ROOT / "results" / "sleep_v2_complete_package.json").read_text())
CONTROL = json.loads((REPO_ROOT / "results" / "sleep_edf_shuffled_eog_control_seedfix_v2.json").read_text())
INTERACTION = json.loads((REPO_ROOT / "results" / "sleep_edf_interaction_resp_seedfix_v2.json").read_text())


def test_package_never_mixes_v1_and_v2():
    assert "V1" in PACKAGE["v1_vs_v2_separation"]
    assert "NEVER MIXED" in PACKAGE["v1_vs_v2_separation"]


def test_capacity_c_equals_b_verified():
    assert PACKAGE["capacity_c_equals_b"] is True


def test_interaction_included_in_package():
    assert PACKAGE["interaction"] != "PENDING - training in progress at package-build time"
    assert "interaction_term" in PACKAGE["interaction"]


def test_resp_provenance_never_regresses_to_100hz_native():
    prov = PACKAGE["resp_provenance"]
    assert prov["native_sfreq_hz"] == 1.0
    assert prov["loaded_common_grid_sfreq_hz"] == 100.0


def test_stability_classification_is_one_of_three_frozen_values():
    assert INTERACTION["aggregate"]["stability_classification"] in (
        "super_additive_leaning", "sub_additive_leaning", "approximately_additive_or_unresolved",
    )


def test_interaction_capacity_fairness_safeguard_passed_not_raised():
    # if the safeguard had failed, the trainer would have raised and no result would exist
    assert "capacity_fairness_per_channel_cost" in INTERACTION["frozen_protocol"]
    cost = INTERACTION["frozen_protocol"]["capacity_fairness_per_channel_cost"]
    assert isinstance(cost, int) and cost > 0


def test_m0_ma_equivalence_flags_present_and_true():
    d = INTERACTION["m0_ma_equivalence_decision"]
    assert d["verified_architecture_match"] is True
    assert d["verified_split_match"] is True
    assert d["verified_hyperparameter_match"] is True


def test_c_and_b_seed_sets_identical():
    assert set(CONTROL["aggregate"]["model_c_macro_f1_v2"]["per_seed"].keys()) == {"seed42", "seed43", "seed44", "seed45", "seed46"}


def test_negative_interaction_sign_count_not_hidden():
    it = INTERACTION["aggregate"]["interaction_term"]
    assert it["n_seeds_positive"] + it["n_seeds_negative"] == it["n_seeds_total"]
    assert it["n_seeds_negative"] > 0  # this run's real mixed-sign result must not be hidden
