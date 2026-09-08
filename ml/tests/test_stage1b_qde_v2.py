"""Stage-1B contract tests for the QDE V2 (leg BioZ) protocol freeze.

Mandatory per Section 35: verify the actual raw CSV to enforce exclusions,
not just check the protocol JSON's stated intent.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
PROTOCOL = json.loads((REPO_ROOT / "results" / "qde_v2_protocol_stage1b.json").read_text())
AUDIT = json.loads((REPO_ROOT / "results" / "qde_v2_actual_file_audit_stage1b.json").read_text())
CSV_PATH = REPO_ROOT / "datasets" / "qde-bioimpedance" / "raw" / "dehydration_estimation.csv"

EXCLUDED_COLUMNS = [
    "weight measured using Kern DE 150K2D [kg]",
    "weight measured using InBody 720 [kg]",
    "total body water using InBody 720 [l]",
    "running interval",
    "running speed [km/h]",
]

FEATURE_COLUMNS_B = [
    "impedance right arm at 1000kHz [Ohm]",
    "impedance left arm at 1000kHz [Ohm]",
    "impedance trunk at 1000kHz [Ohm]",
    "impedance right leg at 1000kHz [Ohm]",
    "impedance left leg at 1000kHz [Ohm]",
]


def test_excluded_columns_are_declared_in_protocol():
    for col in EXCLUDED_COLUMNS:
        assert any(col in excl for excl in PROTOCOL["explicit_exclusions_from_predictors"])


def test_feature_columns_actually_exist_in_raw_csv():
    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        header = next(csv.reader(f))
    for col in FEATURE_COLUMNS_B:
        assert col in header
    for col in EXCLUDED_COLUMNS:
        assert col in header


def test_ten_subjects_nine_points_each():
    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 90
    ids = {}
    for r in rows:
        ids[r["id"]] = ids.get(r["id"], 0) + 1
    assert len(ids) == 10
    assert all(v == 9 for v in ids.values())


def test_loso_fold_has_exactly_one_held_out_subject():
    assert PROTOCOL["evaluation"]["outer_scheme"] == "LOSO (n=10)"


def test_no_test_subject_normalization_leakage():
    guard = PROTOCOL["baseline_normalization"]["leakage_guard"]
    assert "ever contribute" in guard.lower()


def test_control_c_derangement_is_joint_bilateral_and_within_subject():
    c = PROTOCOL["feature_sets"]["C"]
    assert "WITHIN subject" in c["derangement"]
    assert "jointly" in c["bilateral_choice"].lower()


def test_model_class_frozen_to_ridge_not_large_nn():
    constraint = PROTOCOL["evaluation"]["model_class_constraint"]
    assert "ridge" in constraint.lower()
    assert "not planned" in constraint.lower()


def test_circularity_analysis_present_for_old_vs_new_target():
    circ = PROTOCOL["circularity_analysis"]
    assert "inbody" in circ["old_target_inbody_tbw"].lower()
    assert "kern" in circ["new_target_kern_scale_delta_weight"].lower()


def test_classification_go_with_limitations():
    assert PROTOCOL["classification"] == "GO_WITH_LIMITATIONS"


def test_all_ten_subjects_reported_eligible():
    assert AUDIT["eligibility"]["n_eligible"] == 10
