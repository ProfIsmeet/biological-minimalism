"""Section 13/16 regression test (rewritten this sprint): the frozen
governing-artifacts chain must never point to a superseded/historical/
invalid/noncanonical/pending artifact - determined ENTIRELY from each
artifact's own registry status metadata, never from a key-name substring
heuristic (the prior version of this file contained exactly the
`if "historical" in key.lower(): continue` anti-pattern Codex flagged as
a governance-validation bypass - removed)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "ml"))

from build_stage3_scientific_freeze_manifest import sha256_of  # noqa: E402


def _load(name):
    return json.loads((REPO_ROOT / "results" / name).read_text())


def _registry_status_by_path() -> dict:
    registry = _load("stage3_governance_registry.json")
    out = {}
    for fam, fd in registry["families"].items():
        for a in fd["artifacts"]:
            out[a["path"]] = a["status"]
    return out


def test_governing_lbnp_artifact_is_not_the_superseded_result():
    d = _load("stage3_scientific_freeze_manifest.json")
    governing = d["governing_artifacts"]["lbnp_thoracic_eis"]
    assert governing == "results/lbnp_thoracic_eis_stage3_v2_protocol_compliant.json"
    assert governing != "results/lbnp_thoracic_eis_stage3.json"


def test_all_governing_artifacts_exist_and_are_tracked_in_entries():
    d = _load("stage3_scientific_freeze_manifest.json")
    tracked_paths = {e["path"] for e in d["entries"]}
    for key, path in d["governing_artifacts"].items():
        full = REPO_ROOT / path
        assert full.exists(), f"governing artifact {key} ({path}) does not exist"
        assert path in tracked_paths, f"governing artifact {key} ({path}) is not hash-tracked in entries"


def test_all_entry_hashes_match_current_content():
    d = _load("stage3_scientific_freeze_manifest.json")
    for e in d["entries"]:
        path = REPO_ROOT / e["path"]
        assert sha256_of(path) == e["sha256"], f"{e['path']} hash stale - freeze manifest not regenerated"


def test_no_governing_artifact_has_a_non_governing_registry_status():
    """Metadata-driven, no key-name exceptions of any kind: every path in
    governing_artifacts must have registry status exactly GOVERNING."""
    d = _load("stage3_scientific_freeze_manifest.json")
    status_by_path = _registry_status_by_path()
    for key, path in d["governing_artifacts"].items():
        assert status_by_path[path] == "GOVERNING", (
            f"governing_artifacts['{key}'] = {path} has registry status "
            f"{status_by_path[path]!r}, not GOVERNING - this must never happen "
            "regardless of what the dict key is named"
        )
