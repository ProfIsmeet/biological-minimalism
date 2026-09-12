r"""Audit M2/§21-§22 + §50: hash provenance policy is consistent and CRLF-safe.

Proves the canonical TEXT hash (LF-normalized) is identical for LF and CRLF
content, that the two independent implementations (ml contract builder and the
backend decision-inputs adapter) agree, and that a RAW binary hash is distinct
from the canonical one on CRLF content (so the two classes must not be conflated)."""

from __future__ import annotations

import hashlib
import importlib.util
import sys
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[2]


def _load(mod_name: str, rel_path: str):
    # Backend package imports need the backend dir on sys.path.
    backend = str(_REPO / "backend")
    if backend not in sys.path:
        sys.path.insert(0, backend)
    spec = importlib.util.spec_from_file_location(mod_name, _REPO / rel_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


contract = _load("_contract_hash", "ml/build_sensor_marginal_value_contract.py")
decision = _load("_decision_hash", "backend/app/research/decision_inputs.py")


def _canonical_text_sha256(data: bytes) -> str:
    return hashlib.sha256(data.replace(b"\r\n", b"\n")).hexdigest()


def test_canonical_text_hash_is_crlf_invariant(tmp_path):
    lf = tmp_path / "lf.json"
    crlf = tmp_path / "crlf.json"
    lf.write_bytes(b'{\n  "a": 1\n}\n')
    crlf.write_bytes(b'{\r\n  "a": 1\r\n}\r\n')
    # Both canonical-text implementations must return the SAME digest for LF and CRLF.
    assert contract._sha256(lf) == contract._sha256(crlf)
    assert decision._sha256(lf) == decision._sha256(crlf)


def test_two_implementations_agree(tmp_path):
    p = tmp_path / "x.json"
    p.write_bytes(b'{\r\n  "k": "v"\r\n}\r\n')
    assert contract._sha256(p) == decision._sha256(p) == _canonical_text_sha256(p.read_bytes())


def test_raw_binary_hash_differs_from_canonical_on_crlf(tmp_path):
    p = tmp_path / "b.bin"
    p.write_bytes(b"line1\r\nline2\r\n")
    raw = hashlib.sha256(p.read_bytes()).hexdigest()  # checkpoint-style raw hash
    canonical = contract._sha256(p)
    # A raw hash of CRLF content is NOT the canonical (LF-normalized) hash: this is
    # exactly why the two classes must not be conflated under a bare `sha256` name.
    assert raw != canonical


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(pytest.main([__file__, "-q"]))
