"""Regression test for Codex finding H-01: accepted canonical Sleep V2
checkpoints and Claude's noncanonical Mac reproduction share identical
filenames but different byte content - filename alone must never be
treated as authoritative."""

from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
MAPPING = json.loads((REPO_ROOT / "results" / "sleep_v2_checkpoint_accepted_mapping.json").read_text())
CANONICAL = json.loads((REPO_ROOT / "results" / "sleep_edf_primary_seedfix_v2.json").read_text())
TRANSFER = json.loads((REPO_ROOT / "results" / "claude_to_ismet_science_transfer_manifest.json").read_text())


def test_real_filename_collision_confirmed_different_sha256():
    canonical_entry = next(e for e in CANONICAL["checkpoint_manifest"] if e["config"] == "baseline_eeg_only" and e["seed"] == 42)
    noncanon_entry = next(e for e in TRANSFER["checkpoints"] if e["config"] == "baseline_eeg_only" and e["seed"] == 42)
    assert canonical_entry["path"].split("\\")[-1].split("/")[-1] == noncanon_entry["path"].split("\\")[-1].split("/")[-1]
    assert canonical_entry["sha256"] != noncanon_entry["sha256"]


def test_mapping_labels_primary_and_noncanonical_distinctly():
    assert MAPPING["primary_checkpoints"]["status"] == "SCIENCE_OWNER_REPORTED_PRIMARY"
    assert "NOT_PROMOTED" in MAPPING["mac_reproduction_checkpoints"]["status"]


def test_mapping_never_uses_unearned_canonical_label():
    """Section 24/29: no STATUS FIELD may be labeled CANONICAL/ACCEPTED
    without a recorded Emir acceptance - none exists yet. (The old label
    may still appear inside the disclosure note explaining the rename.)"""
    assert MAPPING["primary_checkpoints"]["status"] != "ACCEPTED_CANONICAL"
    for e in MAPPING["primary_checkpoints"]["entries"]:
        assert e["scientific_status"] != "ACCEPTED_CANONICAL"
        assert "CANONICAL" not in e["scientific_status"] or "REPORTED" in e["scientific_status"]


def test_mapping_never_promotes_noncanonical_to_canonical():
    assert "numerical_results_unchanged" in MAPPING
    assert "No accepted numerical result was altered" in MAPPING["numerical_results_unchanged"]


def test_rule_explicitly_forbids_filename_only_resolution():
    assert "NEVER trust the filename alone" in MAPPING["rule_for_future_consumers"]


def test_mapping_is_complete_not_partial():
    """Section 24/42: the mapping must cover all real entries on both
    sides, not a 2-entry spot-check."""
    assert MAPPING["primary_checkpoints"]["n_entries"] == 10
    assert MAPPING["mac_reproduction_checkpoints"]["n_entries"] == 10
    assert len(MAPPING["primary_checkpoints"]["entries"]) == 10
    assert len(MAPPING["mac_reproduction_checkpoints"]["entries"]) == 10


def test_every_entry_has_unambiguous_disjoint_logical_identity():
    """Every primary and mac-reproduction entry must carry a distinct
    (protocol, arm, seed, sha256) identity - filename alone never
    disambiguates, but the full logical identity always does."""
    seen = set()
    for e in MAPPING["primary_checkpoints"]["entries"] + MAPPING["mac_reproduction_checkpoints"]["entries"]:
        key = (e["protocol"], e["arm"], e["seed"], e["sha256"])
        assert key not in seen, f"duplicate logical identity: {key}"
        seen.add(key)
        assert e["byte_availability_status"] in {"PRESENT_ON_DISK", "RECORDED_HASH_BYTES_UNAVAILABLE"}
    assert len(seen) == 20
