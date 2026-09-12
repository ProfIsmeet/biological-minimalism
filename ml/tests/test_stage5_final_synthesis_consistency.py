"""Final consistency contract tests for Stage 5 (master prompt Part XI,
Section 48). Plain assertions against the REAL, on-disk Stage-5 artifacts -
no mutation, no mocking. Complements
ml/tests/test_stage5_final_release_freeze_hostile.py (which mutates copies
to prove the validator detects tampering); this file proves the untampered
artifacts actually say what they must say.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def _load(rel: str) -> dict:
    return json.loads((REPO_ROOT / rel).read_text(encoding="utf-8"))


def _canonical_text_sha256(rel: str) -> str:
    raw = (REPO_ROOT / rel).read_bytes()
    return hashlib.sha256(raw.replace(b"\r\n", b"\n")).hexdigest()


def test_final_architecture_is_core_plus_context():
    final_arch = _load("results/final_wearable_architecture.json")
    ledger = _load("results/final_claim_ledger.json")
    project_manifest = _load("results/final_project_manifest.json")
    assert final_arch["selected_class"] == "CORE_PLUS_CONTEXT"
    ledger_claim = next(c for c in ledger["claims"] if c["claim_id"] == "final_architecture")
    assert "CORE_PLUS_CONTEXT" in ledger_claim["exact_final_safe_wording"]
    assert project_manifest["final_architecture"]["selected_class"] == "CORE_PLUS_CONTEXT"


def test_gate_d_is_conditionally_ready_everywhere():
    gate_d = _load("results/stage4_gate_d_burden_completeness.json")
    project_manifest = _load("results/final_project_manifest.json")
    assert gate_d["gate_d_burden_completeness"] == "CONDITIONALLY_READY"
    assert project_manifest["final_architecture"]["gate_d_burden_completeness"] == "CONDITIONALLY_READY"


def test_gate_e_both_items_frozen_conditionally():
    gate_e = _load("results/stage4_gate_e_coordinator_decisions.json")
    project_manifest = _load("results/final_project_manifest.json")
    assert len(gate_e["decisions"]) == 2
    for d in gate_e["decisions"]:
        assert d["decision"] == "FREEZE_CONDITIONALLY"
        assert d["revision_trigger"]
    manifest_decisions = project_manifest["final_architecture"]["gate_e_decisions"]
    assert len(manifest_decisions) == 2
    assert all(d["decision"] == "FREEZE_CONDITIONALLY" for d in manifest_decisions)


def test_final_pareto_no_unique_winner():
    pareto = _load("results/stage4_formal_pareto_analysis.json")
    project_manifest = _load("results/final_project_manifest.json")
    assert pareto["no_unique_pareto_winner"] is True
    assert "MINIMAL_CORE" in pareto["pareto_relevant_set"]
    assert "CORE_PLUS_CONTEXT" in pareto["pareto_relevant_set"]
    assert project_manifest["pareto_state"]["no_unique_pareto_winner"] is True


def test_final_claim_ledger_covers_all_required_areas():
    ledger = _load("results/final_claim_ledger.json")
    required = {
        "sensor_minimalism_framing", "ppg_plus_imu", "galaxy_replication", "eog_incremental_value",
        "hmc", "ds003838", "second_site_ppg", "leg_bioz", "thoracic_eis", "final_architecture",
        "pareto", "engineering_burden", "robustness_fault_injection", "digital_twin",
        "astronaut_microgravity_applicability",
    }
    present = {c["claim_id"] for c in ledger["claims"]}
    assert required.issubset(present)
    for c in ledger["claims"]:
        assert c["exact_final_safe_wording"]
        assert c["governing_evidence"]
        assert c["prohibited_stronger_wording"]


def test_paper_tables_cite_governing_evidence_not_fabricated():
    for letter in "abcdef":
        table = _load(f"results/final_tables/table_{letter}_" + {
            "a": "modality_evidence", "b": "controlled_ablations", "c": "external_replication",
            "d": "negative_mixed_results", "e": "final_architecture_rationale", "f": "engineering_burden",
        }[letter] + ".json")
        assert table["provenance"]["source"]


def test_jury_pack_evidence_traces_to_claim_ledger():
    ledger = _load("results/final_claim_ledger.json")
    claim_ids = {c["claim_id"] for c in ledger["claims"]}
    jury_pack = _load("presentation/final_jury_evidence_pack.json")
    assert jury_pack["question_count"] == 14
    for q in jury_pack["questions"]:
        assert q["evidence"], f"question {q['question']!r} has no evidence"
        for e in q["evidence"]:
            assert e["claim_id"] in claim_ids


def test_hmc_and_ds003838_remain_pending_not_complete():
    project_manifest = _load("results/final_project_manifest.json")
    assert project_manifest["pending_science"]["hmc_full_cohort"] == "LOWER_PRIORITY_EXTERNAL_WORK_PENDING"
    assert project_manifest["pending_science"]["ds003838_full_cohort"] == "LOWER_PRIORITY_EXTERNAL_WORK_PENDING"
    repro = _load("results/final_reproduction_manifest.json")
    hmc_exp = next(e for e in repro["experiments"] if e["experiment_id"] == "hmc_sleep_external_replication_bounded_n7")
    assert "bounded" in hmc_exp["reproducibility_class"].lower() or "pending" in hmc_exp["reproducibility_class"].lower()


def test_digital_twin_status_unchanged_from_stage4():
    digital_twin = _load("results/digital_twin_architecture_footprint.json")
    project_manifest = _load("results/final_project_manifest.json")
    assert digital_twin["validation_status"] == "ARCHITECTURE_ONLY_UNTRAINED_UNVALIDATED"
    assert project_manifest["digital_twin_status"] == "ARCHITECTURE_ONLY_UNTRAINED_UNVALIDATED"


def test_final_project_manifest_hashes_match_disk():
    project_manifest = _load("results/final_project_manifest.json")
    for entry in project_manifest["authoritative_artifacts"]:
        assert entry["sha256_canonical_text"] == _canonical_text_sha256(entry["path"]), f"hash mismatch for {entry['path']}"
