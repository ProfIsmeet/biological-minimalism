"""Regression test for Codex remediation Section 28: the Day-14 scientific
freeze manifest's sha256_of() must hash line-ending-normalized content, so
the manifest is stable across CRLF (Windows) and LF (Linux/macOS) checkouts
of the same git-tracked text content, rather than treating an incidental
CRLF-vs-LF difference as a real content change."""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "ml"))

from build_scientific_freeze_day14 import sha256_of  # noqa: E402


def test_sha256_of_is_stable_across_crlf_and_lf(tmp_path):
    lf_path = tmp_path / "lf.json"
    crlf_path = tmp_path / "crlf.json"
    content = '{"a": 1,\n"b": 2}\n'
    lf_path.write_bytes(content.encode("utf-8"))
    crlf_path.write_bytes(content.replace("\n", "\r\n").encode("utf-8"))
    assert sha256_of(lf_path) == sha256_of(crlf_path)


def test_sha256_of_still_detects_real_content_changes(tmp_path):
    a = tmp_path / "a.json"
    b = tmp_path / "b.json"
    a.write_bytes(b'{"a": 1}\n')
    b.write_bytes(b'{"a": 2}\n')
    assert sha256_of(a) != sha256_of(b)
