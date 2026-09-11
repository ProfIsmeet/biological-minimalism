"""Section 16 regression test: the frozen governing-artifacts chain must
never point to the superseded LBNP result as current/governing evidence,
and every declared governing artifact must exist and hash-match."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "ml"))

from build_stage3_scientific_freeze_manifest import sha256_of  # noqa: E402


def _load(name):
    return json.loads((REPO_ROOT / "results" / name).read_text())


def test_governing_lbnp_artifact_is_not_the_superseded_result():
    d = _load("stage3_scientific_freeze_manifest.json")
    governing = d["governing_artifacts"]["lbnp_eis_result"]
    assert governing == "results/lbnp_thoracic_eis_stage3_v2_protocol_compliant.json"
    assert governing != "results/lbnp_thoracic_eis_stage3.json"


def test_historical_lbnp_artifact_is_explicitly_labeled_as_such():
    d = _load("stage3_scientific_freeze_manifest.json")
    assert "historical" in d["governing_artifacts"]["lbnp_eis_result_historical_superseded"].lower() or \
        _load("lbnp_thoracic_eis_stage3.json")["status"] == "HISTORICAL_SUPERSEDED_OUT_OF_PROTOCOL"


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


def test_no_entry_marked_historical_is_a_governing_artifact():
    """A file whose own status field says HISTORICAL/SUPERSEDED must never
    simultaneously be declared as a 'governing' (non-historical-suffixed)
    key in governing_artifacts."""
    d = _load("stage3_scientific_freeze_manifest.json")
    for key, path in d["governing_artifacts"].items():
        if "historical" in key.lower():
            continue
        full = REPO_ROOT / path
        content = json.loads(full.read_text())
        status = content.get("status", "")
        assert "HISTORICAL" not in status and "SUPERSEDED" not in status, (
            f"governing_artifacts['{key}'] = {path} has status={status!r}, "
            "which should never be a non-historical governing pointer"
        )
