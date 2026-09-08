"""Stage-1B contract tests for the LBNP protocol freeze. Contract-only."""

from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
PROTOCOL = json.loads((REPO_ROOT / "results" / "lbnp_protocol_stage1b.json").read_text())
AUDIT = json.loads((REPO_ROOT / "results" / "lbnp_actual_file_audit_stage1b.json").read_text())

BANNED_INPUT_FIELDS = [
    "elapsed_time_within_session",
    "stage_sequence_index_trial_order",
    "filename_or_recording_timestamp",
]


def test_lbnp_target_not_present_in_feature_sets():
    for name, feats in PROTOCOL["feature_sets"].items():
        text = json.dumps(feats).lower()
        assert "lbnp pressure" not in text
        assert "mmhg level" not in text


def test_time_and_sequence_fields_excluded():
    excl = PROTOCOL["leakage_exclusions"]
    for field in BANNED_INPUT_FIELDS:
        assert field in excl


def test_uses_16_not_18_as_eligible_cohort():
    assert AUDIT["eligibility"]["n_eligible"] == 16
    assert AUDIT["public_vs_paper_cohort_reconciliation"]["enrolled"] == 18
    assert AUDIT["public_vs_paper_cohort_reconciliation"]["usable_final_analysis"] == 16


def test_eis_frequency_axis_not_labeled_sample_rate():
    eis = AUDIT["eis_acquisition"]
    assert "excitation_frequency_axis" in eis
    assert "temporal_acquisition_cadence" in eis
    assert eis["excitation_frequency_axis"] != eis["temporal_acquisition_cadence"]


def test_thoracic_site_selected():
    assert AUDIT["eis_acquisition"]["site_selected_for_this_experiment"] == "thorax only (per Section 13's single-site focus, to keep A/B/C a single-variable comparison)"


def test_control_c_within_subject():
    c = PROTOCOL["feature_sets"]["C"]
    assert "WITHIN subject" in c["derangement"]
    assert "cross-subject mixing forbidden" in c["derangement"]


def test_map_excluded_from_primary_inputs():
    assert any("map_invasive" in item for item in PROTOCOL["leakage_exclusions"])
    rule = PROTOCOL["secondary_target_map"]["usage_rule"]
    assert "removed from ALL inputs" in rule


def test_verified_lbnp_levels_include_full_range_not_just_prompt_example():
    levels = AUDIT["lbnp_pressure_levels"]["verified_stages_mmhg"]
    assert 100 in levels
    assert 70 in levels


def test_classification_go_with_limitations():
    assert PROTOCOL["classification"] == "GO_WITH_LIMITATIONS"
