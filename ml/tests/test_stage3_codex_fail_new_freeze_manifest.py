"""Section 32/41 regression tests: the new Stage-3 scientific freeze
manifest must exist, cover its declared file list, and use
line-ending-normalized hashes distinct from raw-byte checkpoint hashes."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "ml"))

from build_stage3_scientific_freeze_manifest import sha256_of  # noqa: E402


def test_manifest_all_files_exist():
    d = json.loads((REPO_ROOT / "results" / "stage3_scientific_freeze_manifest.json").read_text())
    assert d["all_files_exist"] is True
    assert d["n_files"] == len(d["entries"])
    assert d["n_files"] >= 21  # grew after Section 18-19 registry-derived expansion


def test_manifest_is_distinct_from_day14_manifest():
    d = json.loads((REPO_ROOT / "results" / "stage3_scientific_freeze_manifest.json").read_text())
    day14 = json.loads((REPO_ROOT / "results" / "scientific_freeze_manifest_day14.json").read_text())
    stage3_paths = {e["path"] for e in d["entries"]}
    day14_paths = {e["path"] for e in day14["entries"]}
    assert stage3_paths != day14_paths  # genuinely different package, not a retrofit


def test_hashes_are_line_ending_normalized_and_current():
    d = json.loads((REPO_ROOT / "results" / "stage3_scientific_freeze_manifest.json").read_text())
    for e in d["entries"][:5]:
        path = REPO_ROOT / e["path"]
        assert sha256_of(path) == e["sha256"], f"{e['path']} hash stale"
        assert e["hash_kind"] == "line_ending_normalized_sha256_of_text_content"


def test_stable_across_crlf_and_lf(tmp_path):
    content = '{"a": 1}\n'
    lf = tmp_path / "lf.json"
    crlf = tmp_path / "crlf.json"
    lf.write_bytes(content.encode())
    crlf.write_bytes(content.replace("\n", "\r\n").encode())
    assert sha256_of(lf) == sha256_of(crlf)
