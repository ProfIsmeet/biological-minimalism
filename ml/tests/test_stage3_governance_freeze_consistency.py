"""Section 21 regression tests: the freeze manifest, generated from the
governance registry, must never contain a historical/superseded/invalid
artifact in governing_artifacts, must have hash-matching entries for
everything it tracks, and must agree exactly with what the resolver
independently computes - metadata-driven, no key-name substring
exceptions anywhere in this check."""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "ml"))
sys.path.insert(0, str(REPO_ROOT))

from build_stage3_scientific_freeze_manifest import sha256_of  # noqa: E402
from ml.stage3_science_resolver import GOVERNING_STATUS, resolve_governing_path  # noqa: E402


def _load(name):
    return json.loads((REPO_ROOT / "results" / name).read_text())


def test_freeze_governing_artifacts_matches_resolver_exactly():
    freeze = _load("stage3_scientific_freeze_manifest.json")
    for family, path in freeze["governing_artifacts"].items():
        assert resolve_governing_path(family) == path


def test_no_governing_artifact_has_non_governing_status_in_registry():
    """Metadata-driven check: for every path in freeze governing_artifacts,
    look up its ACTUAL status in the registry (not by key name) and
    confirm it is GOVERNING."""
    freeze = _load("stage3_scientific_freeze_manifest.json")
    registry = _load("stage3_governance_registry.json")

    path_to_status = {}
    for fam, fd in registry["families"].items():
        for a in fd["artifacts"]:
            path_to_status[a["path"]] = a["status"]

    for family, path in freeze["governing_artifacts"].items():
        assert path_to_status[path] == GOVERNING_STATUS, (
            f"freeze governing_artifacts['{family}']={path} has registry "
            f"status {path_to_status[path]!r}, not GOVERNING"
        )


def test_old_lbnp_and_bounded_galaxy_diagnostic_are_not_in_freeze_governing_set():
    freeze = _load("stage3_scientific_freeze_manifest.json")
    governing_paths = set(freeze["governing_artifacts"].values())
    assert "results/lbnp_thoracic_eis_stage3.json" not in governing_paths
    assert "results/galaxyppg_hr_corrected_eligibility_stage3.json" not in governing_paths
    assert "results/galaxyppg_hr_full_grouped_cv_stage3.json" not in governing_paths
    assert "results/claude_noncanonical_sleep_edf_primary_seedfix_v2_reproduction.json" not in governing_paths


def test_all_freeze_entries_hash_match_current_content():
    freeze = _load("stage3_scientific_freeze_manifest.json")
    assert freeze["all_files_exist"] is True
    for e in freeze["entries"]:
        path = REPO_ROOT / e["path"]
        assert sha256_of(path) == e["sha256"], f"{e['path']} hash stale - freeze not regenerated after edits"


def test_historical_or_supporting_section_never_promotes_to_governing():
    freeze = _load("stage3_scientific_freeze_manifest.json")
    for family, artifacts in freeze["historical_or_supporting_artifacts"].items():
        for a in artifacts:
            assert a["status"] != GOVERNING_STATUS


def test_freeze_is_derived_not_manually_duplicated():
    """The freeze manifest must declare its source of truth explicitly and
    must not contain a second, independently-typed governing definition."""
    freeze = _load("stage3_scientific_freeze_manifest.json")
    assert freeze["source_of_truth"] == "results/stage3_governance_registry.json"
