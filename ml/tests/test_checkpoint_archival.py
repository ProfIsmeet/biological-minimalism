"""Tests for the Day 8 checkpoint manifest and durable archival package."""

from __future__ import annotations

import json
import sys
import tarfile
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

MANIFEST_PATH = REPO_ROOT / "results" / "checkpoint_manifest_consolidated.json"
VERIFICATION_PATH = REPO_ROOT / "results" / "checkpoint_archival_verification.json"
ARCHIVE_PATH = REPO_ROOT / "archival" / "biological_minimalism_checkpoints_day8.tar.gz"

requires_manifest = pytest.mark.skipif(not MANIFEST_PATH.exists(), reason="checkpoint manifest not built yet")
requires_archive = pytest.mark.skipif(not ARCHIVE_PATH.exists(), reason="archival package not built yet")


@requires_manifest
def test_manifest_no_duplicate_paths_marked_unique_twice():
    manifest = json.loads(MANIFEST_PATH.read_text())
    unique_ids = [e["checkpoint_id"] for e in manifest["entries"] if e["unique_file"]]
    assert len(unique_ids) == len(set(unique_ids))


@requires_manifest
def test_manifest_summary_counts_consistent():
    manifest = json.loads(MANIFEST_PATH.read_text())
    entries = manifest["entries"]
    summary = manifest["summary"]
    assert summary["total_references"] == len(entries)
    assert summary["present_on_this_machine"] == sum(1 for e in entries if e["current_machine_present"])
    assert summary["missing_on_this_machine"] == sum(1 for e in entries if not e["current_machine_present"])


@requires_manifest
def test_manifest_every_present_entry_has_sha256():
    manifest = json.loads(MANIFEST_PATH.read_text())
    for e in manifest["entries"]:
        if e["current_machine_present"]:
            assert e["sha256"] is not None and len(e["sha256"]) == 64
        else:
            assert e["sha256"] is None


@requires_manifest
def test_manifest_no_fabricated_regeneration():
    """No entry may claim a missing checkpoint was regenerated and treated
    as original - regeneration_status must say otherwise for any missing file."""
    manifest = json.loads(MANIFEST_PATH.read_text())
    for e in manifest["entries"]:
        if not e["current_machine_present"]:
            assert e["regeneration_status"] != "REGENERATED_AS_ORIGINAL"


@requires_archive
def test_archive_contains_no_raw_dataset_files():
    with tarfile.open(ARCHIVE_PATH, "r:gz") as tar:
        names = [m.name for m in tar.getmembers()]
    forbidden_ext = (".edf", ".pkl", ".npz", ".csv", ".dat", ".hea")
    hits = [n for n in names if n.lower().endswith(forbidden_ext)]
    assert hits == [], f"raw-dataset-like files found in archive: {hits}"


@requires_archive
def test_archive_contains_manifest_and_checksums():
    with tarfile.open(ARCHIVE_PATH, "r:gz") as tar:
        names = [m.name for m in tar.getmembers()]
    assert any(n.endswith("MANIFEST.json") for n in names)
    assert any(n.endswith("SHA256SUMS.txt") for n in names)
    assert any(n.endswith("README.md") for n in names)


@requires_archive
def test_archive_checkpoint_count_matches_present_unique_manifest_entries():
    manifest = json.loads(MANIFEST_PATH.read_text())
    expected_count = sum(1 for e in manifest["entries"] if e["current_machine_present"] and e["unique_file"])
    with tarfile.open(ARCHIVE_PATH, "r:gz") as tar:
        pt_files = [m for m in tar.getmembers() if m.name.endswith(".pt")]
    assert len(pt_files) == expected_count


@pytest.mark.skipif(not VERIFICATION_PATH.exists(), reason="archival verification not run yet")
def test_archival_verification_all_ok():
    verification = json.loads(VERIFICATION_PATH.read_text())
    assert verification["all_checkpoints_verified_ok"] is True
    assert verification["no_raw_datasets_included"] is True
    assert verification["n_checkpoints_verified_ok"] == verification["n_checkpoints_packaged"]
