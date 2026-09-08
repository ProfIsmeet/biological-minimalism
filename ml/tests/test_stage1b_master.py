"""Cross-artifact consistency tests for the Stage 1B master/readiness/role-map
manifests - contract-only, no performance thresholds."""

from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
RESULTS = REPO_ROOT / "results"

MASTER = json.loads((RESULTS / "dataset_expansion_stage1b_master.json").read_text())
READINESS = json.loads((RESULTS / "science_expansion_readiness_stage1b.json").read_text())
ROLE_MAP = json.loads((RESULTS / "dataset_expansion_role_map_stage1b.json").read_text())
LINEAGE = json.loads((RESULTS / "dataset_lineage_stage1b.json").read_text())
FIVE_NAMES = {"GalaxyPPG", "HMC", "QDE_V2", "LBNP", "ds003838"}


def test_master_lists_all_five_programs():
    names = {d["dataset"] for d in MASTER["datasets"]}
    assert names == FIVE_NAMES


def test_readiness_matrix_covers_all_five():
    keys = set(READINESS.keys()) - {"purpose", "columns"}
    assert keys == FIVE_NAMES


def test_role_map_covers_all_five():
    keys = set(ROLE_MAP.keys()) - {"purpose"}
    assert keys == FIVE_NAMES


def test_no_dataset_marked_stage2_ready_true_and_readiness_blocked_simultaneously():
    for d in MASTER["datasets"]:
        name = d["dataset"]
        if d["stage2_ready"] is True:
            assert "BLOCKED" not in READINESS[name]["stage2_readiness"]


def test_qde_v2_correctly_marked_not_independent_family():
    assert LINEAGE["programs"]["QDE_V2"]["independent_dataset_family"] is False
    qde = next(d for d in MASTER["datasets"] if d["dataset"] == "QDE_V2")
    assert qde["previously_used_in_project"] is True


def test_hmc_and_lbnp_are_the_two_blocked_stage2_readiness():
    blocked = {name for name, row in READINESS.items() if isinstance(row, dict) and "BLOCKED" in row.get("stage2_readiness", "")}
    assert blocked == {"HMC", "LBNP"}


def test_no_classification_is_no_go():
    for d in MASTER["datasets"]:
        assert d["classification"] != "NO_GO"


def test_every_dataset_has_forbidden_claims_listed():
    for d in MASTER["datasets"]:
        assert len(d["forbidden_claims"]) >= 1
