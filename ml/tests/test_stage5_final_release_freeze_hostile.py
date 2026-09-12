"""Hostile-review contract tests for the Stage 5 Final Synthesis & Release
Freeze sprint (master prompt Part XII, Attacks A-J). Each test takes the
REAL, currently-passing Stage-5 artifacts, mutates a deep copy to simulate
one specific tampering scenario, and asserts that
ml.validate_stage5_final_release_freeze catches it. A sibling "baseline"
test confirms the validator passes cleanly on the real, untampered data.
"""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

import ml.validate_stage5_final_release_freeze as v  # noqa: E402


def _real(rel: str) -> dict:
    return json.loads((REPO_ROOT / rel).read_text(encoding="utf-8"))


def _patched_load(overrides: dict[str, dict]):
    def _load(rel: str) -> dict:
        if rel in overrides:
            return overrides[rel]
        return _real(rel)

    return _load


def test_baseline_validator_passes_on_real_untampered_data():
    v.main()


def test_attack_a_galaxy_number_changed_in_paper_export():
    tampered_abstract = copy.deepcopy(_real(v.ABSTRACT_FACT_SHEET_PATH))
    for s in tampered_abstract["statements"]:
        if s["claim_id"] == "galaxy_replication":
            s["numeric_support"] = "FABRICATED: 24/24 subjects, +5.0 bpm"
    with patch.object(v, "_load", _patched_load({v.ABSTRACT_FACT_SHEET_PATH: tampered_abstract})):
        with pytest.raises(v.Stage5FreezeConsistencyError, match="GalaxyPPG numeric_support disagreement"):
            v.check_galaxy_numbers_consistent_across_surfaces()


def test_attack_b_architecture_changed_in_presentation_export():
    tampered_table_e = copy.deepcopy(_real(v.TABLE_E_PATH))
    tampered_table_e["final_architecture"] = "MINIMAL_CORE"
    with patch.object(v, "_load", _patched_load({v.TABLE_E_PATH: tampered_table_e})):
        with pytest.raises(v.Stage5FreezeConsistencyError, match="disagreement"):
            v.check_architecture_consistent_across_stage5_surfaces()


def test_attack_c_eog_wording_changed_to_externally_validated():
    tampered_ledger = copy.deepcopy(_real(v.CLAIM_LEDGER_PATH))
    for c in tampered_ledger["claims"]:
        if c["claim_id"] == "eog_incremental_value":
            c["exact_final_safe_wording"] = "EOG is externally validated on an independent cohort."
            c["jury_safe_wording"] = c["exact_final_safe_wording"]
            c["paper_safe_wording"] = c["exact_final_safe_wording"]
    with patch.object(v, "_load", _patched_load({v.CLAIM_LEDGER_PATH: tampered_ledger})):
        with pytest.raises(v.Stage5FreezeConsistencyError, match="externally validated"):
            v.check_eog_not_marked_externally_validated_in_stage5()


def test_attack_d_negative_bioz_evidence_removed_from_final_tables():
    tampered_table_d = copy.deepcopy(_real(v.TABLE_D_PATH))
    tampered_table_d["rows"] = [r for r in tampered_table_d["rows"] if r["claim_id"] != "thoracic_eis"]
    with patch.object(v, "_load", _patched_load({v.TABLE_D_PATH: tampered_table_d})):
        with pytest.raises(v.Stage5FreezeConsistencyError, match="thoracic_eis"):
            v.check_bioz_negative_evidence_preserved_in_final_tables()


def test_attack_e_hmc_full_marked_complete():
    tampered_ledger = copy.deepcopy(_real(v.CLAIM_LEDGER_PATH))
    tampered_ledger["injected_status"] = "HMC full-cohort training: COMPLETE"
    with patch.object(v, "_load", _patched_load({v.CLAIM_LEDGER_PATH: tampered_ledger})):
        with pytest.raises(v.Stage5FreezeConsistencyError, match="complete"):
            v.check_hmc_ds003838_not_complete_in_stage5()


def test_attack_f_ds003838_full_marked_complete():
    tampered_ledger = copy.deepcopy(_real(v.CLAIM_LEDGER_PATH))
    tampered_ledger["injected_status"] = "ds003838 full-cohort: COMPLETE"
    with patch.object(v, "_load", _patched_load({v.CLAIM_LEDGER_PATH: tampered_ledger})):
        with pytest.raises(v.Stage5FreezeConsistencyError, match="complete"):
            v.check_hmc_ds003838_not_complete_in_stage5()


def test_attack_g_digital_twin_promoted_to_validated():
    tampered_ledger = copy.deepcopy(_real(v.CLAIM_LEDGER_PATH))
    for c in tampered_ledger["claims"]:
        if c["claim_id"] == "digital_twin":
            c["exact_final_safe_wording"] = "The Digital Twin has been fully validated against real longitudinal astronaut data."
    with patch.object(v, "_load", _patched_load({v.CLAIM_LEDGER_PATH: tampered_ledger})):
        with pytest.raises(v.Stage5FreezeConsistencyError, match="Digital Twin"):
            v.check_digital_twin_not_promoted_in_stage5()


def test_attack_h_pareto_changed_to_unique_winner():
    tampered_ledger = copy.deepcopy(_real(v.CLAIM_LEDGER_PATH))
    for c in tampered_ledger["claims"]:
        if c["claim_id"] == "pareto":
            c["exact_final_safe_wording"] = "CORE_PLUS_CONTEXT mathematically dominates every alternative architecture."
    with patch.object(v, "_load", _patched_load({v.CLAIM_LEDGER_PATH: tampered_ledger})):
        with pytest.raises(v.Stage5FreezeConsistencyError, match="mathematically dominates"):
            v.check_pareto_no_false_dominance_in_stage5()


def test_attack_i_gate_d_changed_to_fully_ready():
    tampered_manifest = copy.deepcopy(_real(v.PROJECT_MANIFEST_PATH))
    tampered_manifest["final_architecture"]["gate_d_burden_completeness"] = "READY"
    with patch.object(v, "_load", _patched_load({v.PROJECT_MANIFEST_PATH: tampered_manifest})):
        with pytest.raises(v.Stage5FreezeConsistencyError, match="CONDITIONALLY_READY"):
            v.check_gate_d_not_silently_promoted_in_stage5()


def test_attack_j_authoritative_artifact_corrupted_after_freeze():
    tampered_manifest = copy.deepcopy(_real(v.PROJECT_MANIFEST_PATH))
    # Corrupt one stored hash so it no longer matches the real on-disk file.
    tampered_manifest["authoritative_artifacts"][0]["sha256_canonical_text"] = "0" * 64
    with patch.object(v, "_load", _patched_load({v.PROJECT_MANIFEST_PATH: tampered_manifest})):
        with pytest.raises(v.Stage5FreezeConsistencyError, match="hash mismatch"):
            v.check_release_manifest_hash_integrity()
