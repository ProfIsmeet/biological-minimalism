"""Hostile-review contract tests for the Stage 4 Final Architecture Closure
sprint (master prompt Part XI, Attacks A-H). Each test takes the REAL,
currently-passing closure artifacts, mutates a deep copy to simulate one
specific tampering scenario, and asserts that
ml.validate_stage4_final_architecture_closure catches it. A sibling
"baseline" test confirms the validator passes cleanly on the real,
untampered data - proving these tests exercise real detection logic, not a
vacuously-always-failing check.
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

import ml.validate_stage4_final_architecture_closure as closure_validator  # noqa: E402


def _real(rel: str) -> dict:
    return json.loads((REPO_ROOT / rel).read_text(encoding="utf-8"))


def _patched_load(overrides: dict[str, dict]):
    """Returns a function matching closure_validator._load's signature that
    serves `overrides[rel]` for the given path and the real on-disk content
    for everything else - so a single-artifact mutation doesn't require
    rebuilding every other artifact by hand."""

    def _load(rel: str) -> dict:
        if rel in overrides:
            return overrides[rel]
        return _real(rel)

    return _load


def test_baseline_validator_passes_on_real_untampered_data():
    closure_validator.main()


def test_attack_a_selected_architecture_disagrees_across_surfaces():
    """Attack A: change selected architecture in one surface only."""
    tampered_pareto = copy.deepcopy(_real(closure_validator.FORMAL_PARETO_PATH))
    tampered_pareto["coordinator_selected_architecture"] = "MINIMAL_CORE"
    with patch.object(closure_validator, "_load", _patched_load({closure_validator.FORMAL_PARETO_PATH: tampered_pareto})):
        with pytest.raises(closure_validator.FinalClosureConsistencyError, match="disagreement"):
            closure_validator.check_selected_class_consistent_everywhere()


def test_attack_b_gate_d_promoted_to_ready_without_evidence():
    """Attack B: change Gate D from CONDITIONALLY_READY to READY without new evidence."""
    tampered_gate_d = copy.deepcopy(_real(closure_validator.GATE_D_PATH))
    tampered_gate_d["gate_d_burden_completeness"] = "READY"
    with patch.object(closure_validator, "_load", _patched_load({closure_validator.GATE_D_PATH: tampered_gate_d})):
        with pytest.raises(closure_validator.FinalClosureConsistencyError, match="CONDITIONALLY_READY"):
            closure_validator.check_gate_d_not_silently_ready()


def test_attack_c_eog_marked_externally_validated():
    """Attack C: change EOG to externally validated."""
    tampered_gate_e = copy.deepcopy(_real(closure_validator.GATE_E_DECISIONS_PATH))
    tampered_gate_e["decisions"][0]["claim_limitations"] = "EOG is externally validated on an independent cohort."
    with patch.object(closure_validator, "_load", _patched_load({closure_validator.GATE_E_DECISIONS_PATH: tampered_gate_e})):
        with pytest.raises(closure_validator.FinalClosureConsistencyError, match="externally validated"):
            closure_validator.check_eog_not_marked_externally_validated()


def test_attack_d_hmc_full_cohort_marked_complete():
    """Attack D: mark HMC full complete."""
    tampered_gate_e = copy.deepcopy(_real(closure_validator.GATE_E_DECISIONS_PATH))
    tampered_gate_e["pending_science_still_pending"] = "HMC full-cohort training: COMPLETE"
    with patch.object(closure_validator, "_load", _patched_load({closure_validator.GATE_E_DECISIONS_PATH: tampered_gate_e})):
        with pytest.raises(closure_validator.FinalClosureConsistencyError, match="complete"):
            closure_validator.check_hmc_ds003838_not_complete_in_closure_artifacts()


def test_attack_e_ds003838_marked_complete():
    """Attack E: mark ds003838 full complete."""
    tampered_gate_e = copy.deepcopy(_real(closure_validator.GATE_E_DECISIONS_PATH))
    tampered_gate_e["pending_science_still_pending"] = "ds003838 full-cohort: COMPLETE"
    with patch.object(closure_validator, "_load", _patched_load({closure_validator.GATE_E_DECISIONS_PATH: tampered_gate_e})):
        with pytest.raises(closure_validator.FinalClosureConsistencyError, match="complete"):
            closure_validator.check_hmc_ds003838_not_complete_in_closure_artifacts()


def test_attack_f_bioz_negative_evidence_removed():
    """Attack F: remove BioZ negative/mixed evidence from exclusion rationale."""
    tampered_final_arch = copy.deepcopy(_real(closure_validator.FINAL_ARCH_PATH))
    tampered_final_arch["exclusion_rationale"]["thoracic_bioz_eis"]["reason"] = "Excluded for scope reasons."
    with patch.object(closure_validator, "_load", _patched_load({closure_validator.FINAL_ARCH_PATH: tampered_final_arch})):
        with pytest.raises(closure_validator.FinalClosureConsistencyError, match="COMPLETE_MIXED"):
            closure_validator.check_bioz_negative_evidence_not_removed()


def test_attack_g_false_pareto_dominance_claimed():
    """Attack G: declare CORE_PLUS_CONTEXT uniquely Pareto dominant when methodology does not support it."""
    tampered_pareto = copy.deepcopy(_real(closure_validator.FORMAL_PARETO_PATH))
    tampered_pareto["no_unique_pareto_winner"] = False
    with patch.object(closure_validator, "_load", _patched_load({closure_validator.FORMAL_PARETO_PATH: tampered_pareto})):
        with pytest.raises(closure_validator.FinalClosureConsistencyError, match="no_unique_pareto_winner"):
            closure_validator.check_formal_pareto_no_false_dominance()

    tampered_pareto_2 = copy.deepcopy(_real(closure_validator.FORMAL_PARETO_PATH))
    for entry in tampered_pareto_2["pairwise_dominance_analysis"]:
        if entry["class_a"] == "MINIMAL_CORE" and entry["class_b"] == "CORE_PLUS_CONTEXT":
            entry["verdict"] = "CORE_PLUS_CONTEXT_DOMINATES"
    with patch.object(closure_validator, "_load", _patched_load({closure_validator.FORMAL_PARETO_PATH: tampered_pareto_2})):
        with pytest.raises(closure_validator.FinalClosureConsistencyError, match="dominate MINIMAL_CORE"):
            closure_validator.check_formal_pareto_no_false_dominance()


def test_attack_h_digital_twin_promoted_to_validated():
    """Attack H: promote Digital Twin to validated."""
    tampered_final_arch = copy.deepcopy(_real(closure_validator.FINAL_ARCH_PATH))
    tampered_final_arch["science_rationale"]["note"] = "The Digital Twin has been fully validated against real longitudinal data."
    with patch.object(closure_validator, "_load", _patched_load({closure_validator.FINAL_ARCH_PATH: tampered_final_arch})):
        with pytest.raises(closure_validator.FinalClosureConsistencyError, match="Digital Twin"):
            closure_validator.check_digital_twin_not_promoted()
