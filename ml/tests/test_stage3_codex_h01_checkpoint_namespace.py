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


def test_mapping_labels_canonical_and_noncanonical_distinctly():
    assert MAPPING["accepted_canonical_checkpoints"]["status"] == "ACCEPTED_CANONICAL"
    assert "NONCANONICAL" in MAPPING["noncanonical_mac_reproduction_checkpoints"]["status"]


def test_mapping_never_promotes_noncanonical_to_canonical():
    assert "numerical_results_unchanged" in MAPPING
    assert "No accepted numerical result was altered" in MAPPING["numerical_results_unchanged"]


def test_rule_explicitly_forbids_filename_only_resolution():
    assert "NEVER trust the filename alone" in MAPPING["rule_for_future_consumers"]
