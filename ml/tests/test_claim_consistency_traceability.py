"""Regression tests for the mechanical traceability checks (audit M4 §24/§26).

Prove that the checker actually FAILS on a nonexistent field path or a nonexistent
API route (not just a missing file), and that the canonical claim_traceability.json
has no broken references."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

_CHECKER = Path(__file__).resolve().parents[1] / "check_claim_consistency.py"
_spec = importlib.util.spec_from_file_location("check_claim_consistency", _CHECKER)
cc = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(cc)


def test_resolve_field_dotted_and_index() -> None:
    obj = {"a": {"b": [{"c": 1}, {"c": 2}]}}
    assert cc._resolve_field(obj, "a.b[1].c") == (True, None)
    ok, where = cc._resolve_field(obj, "a.b[9].c")
    assert ok is False and where == "b[9]"
    ok, where = cc._resolve_field(obj, "a.missing")
    assert ok is False and where == "missing"


def test_normalize_route_collapses_ids() -> None:
    assert cc._normalize_route("GET /research/experiments/ppg-dalia-imu-ablation") == "GET /research/experiments/{}"
    assert cc._normalize_route("GET /research/summary") == "GET /research/summary"


def test_known_routes_gate_nonexistent_routes() -> None:
    assert cc._normalize_route("GET /research/reproducibility") not in cc.KNOWN_ROUTES  # nonexistent
    assert cc._normalize_route("GET /research/summary") in cc.KNOWN_ROUTES


def test_canonical_traceability_has_no_broken_references() -> None:
    """The real claim_traceability.json must resolve every artifact/field/route."""
    problems = cc.check_traceability()
    assert problems == [], "broken traceability references:\n" + "\n".join(problems)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(pytest.main([__file__, "-q"]))
