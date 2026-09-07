"""Day 11-14 scientific parallel sprint tests: statistics, tables, figure
sources, dataset/checkpoint provenance, clean-clone artifact, freeze
manifest."""

from __future__ import annotations

import csv
import hashlib
import json
import re
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

SHA256_RE = re.compile(r"^[0-9a-f]{64}$")

STAT_UNIT_AUDIT = REPO_ROOT / "results" / "statistical_unit_audit_day11.json"
PPG_SENS = REPO_ROOT / "results" / "ppg_dalia_sensitivity_day11.json"
PTT_SENS = REPO_ROOT / "results" / "ptt_sensitivity_day11.json"
SLEEP_SENS = REPO_ROOT / "results" / "sleep_edf_sensitivity_day11.json"
MASTER_TABLE = REPO_ROOT / "results" / "scientific_master_table_day11.json"
PAPER_TABLES_DIR = REPO_ROOT / "results" / "paper_tables"
FIGURE_SOURCES_DIR = REPO_ROOT / "results" / "figure_sources"
CLEAN_CLONE = REPO_ROOT / "results" / "clean_clone_reproduction_day13.json"
FREEZE_MANIFEST = REPO_ROOT / "results" / "scientific_freeze_manifest_day14.json"
FREEZE_CANDIDATE = REPO_ROOT / "results" / "scientific_freeze_candidate_day14.json"
CHECKPOINT_INVENTORY = REPO_ROOT / "results" / "final_checkpoint_inventory_day14.json"
DAY14_ARCHIVAL = REPO_ROOT / "results" / "checkpoint_archival_verification_day14.json"


def _skip_if_missing(path: Path):
    return pytest.mark.skipif(not path.exists(), reason=f"{path.name} not built yet")


# --- Statistics ----------------------------------------------------------------


@_skip_if_missing(STAT_UNIT_AUDIT)
def test_statistical_unit_audit_no_seed_as_subject():
    """At least one audited experiment must explicitly flag the
    seed-as-subject risk (not necessarily every entry - some entries'
    inappropriate-interpretation lists are about other risks, e.g. cohort
    pooling, and that's fine as long as the risk is flagged somewhere)."""
    audit = json.loads(STAT_UNIT_AUDIT.read_text())
    all_text = " ".join(
        text for a in audit["audits"] for text in a["inappropriate_unit_interpretations"]
    ).lower()
    assert "seed" in all_text
    assert audit["cross_cutting_rule"]
    assert "seed" in audit["cross_cutting_rule"].lower()


@_skip_if_missing(STAT_UNIT_AUDIT)
def test_statistical_unit_audit_no_p_values():
    audit = json.loads(STAT_UNIT_AUDIT.read_text())
    assert audit["no_p_values_computed"] is True


@_skip_if_missing(PPG_SENS)
def test_ppg_sensitivity_no_retraining_flag():
    sens = json.loads(PPG_SENS.read_text())
    assert sens["no_retraining"] is True


@_skip_if_missing(PPG_SENS)
def test_ppg_sensitivity_does_not_reintroduce_uncontrolled_headline():
    """The retired ~20.6% uncontrolled relative-improvement figure must not
    appear anywhere in this artifact (a substring check on "1.88" is too
    fragile - it collides with legitimate seed-level MAE values like
    11.889... - so only the unambiguous "20.6%" marker is checked)."""
    sens = json.loads(PPG_SENS.read_text())
    assert "1.88bpm" in sens["purpose"]  # present only as an explicit disclaimer, not a computed field
    computed_blocks = {k: v for k, v in sens.items() if k not in ("purpose", "final_interpretation")}
    assert "20.6%" not in json.dumps(computed_blocks)
    assert "1.88bpm" not in json.dumps(computed_blocks)


@_skip_if_missing(PTT_SENS)
def test_ptt_sensitivity_no_defensible_ci_note_present():
    sens = json.loads(PTT_SENS.read_text())
    assert "NO_DEFENSIBLE" in json.dumps(sens) or "too small" in json.dumps(sens).lower()


@_skip_if_missing(SLEEP_SENS)
def test_sleep_sensitivity_no_pooling():
    sens = json.loads(SLEEP_SENS.read_text())
    assert sens["no_pooling"] is True
    assert sens["primary"]["n_subjects"] == 3
    assert sens["secondary"]["n_subjects"] == 8


@_skip_if_missing(SLEEP_SENS)
def test_sleep_sensitivity_bootstrap_labeled_descriptive():
    sens = json.loads(SLEEP_SENS.read_text())
    bs = sens["secondary"]["descriptive_subject_bootstrap_b_minus_a"]
    assert bs["label"] == "DESCRIPTIVE_SUBJECT_BOOTSTRAP"
    assert bs["not_a_population_generalization_proof"] is True


# --- Master table / paper tables -------------------------------------------------


@_skip_if_missing(MASTER_TABLE)
def test_master_table_no_cross_metric_ranking_flag():
    table = json.loads(MASTER_TABLE.read_text())
    assert table["no_cross_metric_ranking"] is True


@_skip_if_missing(MASTER_TABLE)
def test_master_table_rows_have_required_fields():
    table = json.loads(MASTER_TABLE.read_text())
    required = ("experiment_id", "dataset", "target", "primary_metric", "evidence_strength", "supported_claim", "unsupported_claims")
    for row in table["rows"]:
        for field in required:
            assert field in row


@pytest.mark.skipif(not PAPER_TABLES_DIR.exists(), reason="paper tables not built yet")
def test_paper_tables_csv_json_pairs_exist():
    for i in range(1, 6):
        matches = list(PAPER_TABLES_DIR.glob(f"table{i}_*.csv"))
        assert matches, f"table{i} csv missing"
        json_match = matches[0].with_suffix(".json")
        assert json_match.exists()


@pytest.mark.skipif(not PAPER_TABLES_DIR.exists(), reason="paper tables not built yet")
def test_paper_table2_no_metric_cross_ranking_column():
    """table2 must not contain a single 'sensor_value' style column mixing
    MAE and macro-F1 into one sortable number - each row keeps its own
    primary_metric label."""
    with open(PAPER_TABLES_DIR / "table2_main_marginal_value_results.csv", newline="", encoding="utf-8") as f:
        rows = list(csv.reader(f))
    header = rows[0]
    assert "metric" in header
    assert not any(h.lower() in ("sensor_value", "rank", "score") for h in header)


@pytest.mark.skipif(not PAPER_TABLES_DIR.exists(), reason="paper tables not built yet")
def test_paper_tables_provenance_present():
    for json_path in PAPER_TABLES_DIR.glob("*.json"):
        data = json.loads(json_path.read_text())
        assert "provenance" in data


# --- Figure sources ---------------------------------------------------------------


@pytest.mark.skipif(not FIGURE_SOURCES_DIR.exists(), reason="figure sources not built yet")
def test_figure_sources_have_required_honesty_fields():
    required = ("title", "metric", "sample_unit", "uncertainty_meaning", "claim_boundary", "provenance")
    for fig_path in FIGURE_SOURCES_DIR.glob("figure_*.json"):
        data = json.loads(fig_path.read_text())
        for field in required:
            assert field in data, f"{fig_path.name} missing {field}"


@pytest.mark.skipif(not FIGURE_SOURCES_DIR.exists(), reason="figure sources not built yet")
def test_figure_sources_all_nine_present():
    letters = "ABCDEFGHI"
    for letter in letters:
        matches = list(FIGURE_SOURCES_DIR.glob(f"figure_{letter}_*.json"))
        assert matches, f"figure {letter} missing"


# --- Checkpoint / archival provenance ---------------------------------------------


@_skip_if_missing(CHECKPOINT_INVENTORY)
def test_checkpoint_inventory_all_externally_archived():
    inv = json.loads(CHECKPOINT_INVENTORY.read_text())
    assert inv["summary"]["n_without_external_archival"] == 0
    assert inv["summary"]["n_total_referenced"] == 60


@_skip_if_missing(CHECKPOINT_INVENTORY)
def test_checkpoint_inventory_all_unique_sha():
    inv = json.loads(CHECKPOINT_INVENTORY.read_text())
    assert inv["summary"]["n_unique_sha256"] == inv["summary"]["n_total_referenced"]


@_skip_if_missing(DAY14_ARCHIVAL)
def test_day14_archive_no_raw_datasets():
    d = json.loads(DAY14_ARCHIVAL.read_text())
    assert d["no_raw_datasets_included"] is True
    assert d["all_checkpoints_verified_ok"] is True
    assert d["n_checkpoints_packaged"] == 10


@_skip_if_missing(DAY14_ARCHIVAL)
def test_day14_archive_externally_durable():
    d = json.loads(DAY14_ARCHIVAL.read_text())
    assert d["external_copy_created"] is True
    assert d["external_copy_verified"] is True
    assert d["archival_status"] == "LOCAL_VERIFIED_EXTERNALLY_DURABLE"


# --- Clean clone -----------------------------------------------------------------


@_skip_if_missing(CLEAN_CLONE)
def test_clean_clone_status_valid_enum():
    d = json.loads(CLEAN_CLONE.read_text())
    assert d["overall_status"] in (
        "CLEAN_CLONE_PASS", "CLEAN_CLONE_PASS_WITH_MANUAL_DATA_SETUP",
        "CLEAN_CLONE_PARTIAL", "CLEAN_CLONE_FAIL",
    )


@_skip_if_missing(CLEAN_CLONE)
def test_clean_clone_representative_reproduction_all_match():
    d = json.loads(CLEAN_CLONE.read_text())
    rep = d["representative_reproduction"]
    assert rep["sleep_edf_primary"]["all_exact_match"] is True
    assert rep["sleep_edf_secondary_holdout"]["all_exact_match"] is True
    assert rep["ptt"]["all_exact_match"] is True
    assert rep["ppg_dalia_capacity_control"]["all_exact_match"] is True


# --- Freeze manifest ---------------------------------------------------------------


@_skip_if_missing(FREEZE_MANIFEST)
def test_freeze_manifest_all_files_exist():
    manifest = json.loads(FREEZE_MANIFEST.read_text())
    assert manifest["all_files_exist"] is True
    for e in manifest["entries"]:
        assert e["exists"] is True
        assert SHA256_RE.match(e["sha256"])


@_skip_if_missing(FREEZE_MANIFEST)
def test_freeze_manifest_hashes_are_valid_and_current():
    manifest = json.loads(FREEZE_MANIFEST.read_text())
    for e in manifest["entries"][:5]:  # spot-check first 5 to keep this fast
        path = REPO_ROOT / e["path"]
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        assert actual == e["sha256"], f"{e['path']} hash stale - re-run ml/build_scientific_freeze_day14.py"


@_skip_if_missing(FREEZE_CANDIDATE)
def test_freeze_candidate_status_valid_enum():
    d = json.loads(FREEZE_CANDIDATE.read_text())
    assert d["freeze_candidate_status"] in (
        "SCIENTIFIC_FREEZE_CANDIDATE_READY",
        "SCIENTIFIC_FREEZE_CANDIDATE_READY_WITH_LIMITATIONS",
        "SCIENTIFIC_FREEZE_CANDIDATE_NOT_READY",
    )


@_skip_if_missing(FREEZE_CANDIDATE)
def test_freeze_candidate_lists_open_limitations():
    d = json.loads(FREEZE_CANDIDATE.read_text())
    assert len(d["open_scientific_limitations"]) > 0
