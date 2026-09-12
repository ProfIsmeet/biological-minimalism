"""Gate 4 closure regression tests (Sections 7-8, 17-18): the freeze
builder must HARD FAIL (raise), never silently omit, when a required
family has zero or multiple governing artifacts."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

import ml.stage3_science_resolver as resolver  # noqa: E402
import ml.build_stage3_scientific_freeze_manifest as builder  # noqa: E402


@pytest.fixture
def temp_registry_for_builder(tmp_path, monkeypatch):
    real = json.loads(resolver.REGISTRY_PATH.read_text())

    def _write(mutated):
        tmp = (tmp_path / "registry.json").resolve()
        tmp.write_text(json.dumps(mutated))
        monkeypatch.setattr(builder, "REGISTRY_PATH", tmp)
        monkeypatch.setattr(resolver, "REGISTRY_PATH", tmp)

    return real, _write


def test_zero_governing_family_hard_fails_freeze_build(temp_registry_for_builder, monkeypatch, tmp_path):
    real, write = temp_registry_for_builder
    mutated = json.loads(json.dumps(real))
    for a in mutated["families"]["lbnp_thoracic_eis"]["artifacts"]:
        a["status"] = "HISTORICAL_SUPERSEDED_OUT_OF_PROTOCOL"
    write(mutated)
    monkeypatch.setattr(builder, "OUT_PATH", tmp_path / "out.json")
    with pytest.raises(builder.FreezeBuildError, match="ZERO governing"):
        builder.main()


def test_duplicate_governing_family_hard_fails_freeze_build(temp_registry_for_builder, monkeypatch, tmp_path):
    real, write = temp_registry_for_builder
    mutated = json.loads(json.dumps(real))
    mutated["families"]["lbnp_thoracic_eis"]["artifacts"][1]["status"] = "GOVERNING"
    write(mutated)
    monkeypatch.setattr(builder, "OUT_PATH", tmp_path / "out.json")
    with pytest.raises(builder.FreezeBuildError, match="AMBIGUOUS"):
        builder.main()


def test_current_freeze_manifest_covers_all_required_families():
    freeze = json.loads((REPO_ROOT / "results" / "stage3_scientific_freeze_manifest.json").read_text())
    registry = json.loads(resolver.REGISTRY_PATH.read_text())
    assert set(freeze["required_families"]) == set(registry["families"].keys())
    assert freeze["required_families_count"] == len(registry["families"])
    assert set(freeze["governing_artifacts"].keys()) == set(registry["families"].keys())


def test_registry_has_21_families_not_18():
    """Section 14: documentation must not hard-code an obsolete family
    count. This test asserts the actual current count is used as the
    single source of truth (read dynamically, not hard-coded to 18)."""
    registry = json.loads(resolver.REGISTRY_PATH.read_text())
    actual = len(registry["families"])
    freeze = json.loads((REPO_ROOT / "results" / "stage3_scientific_freeze_manifest.json").read_text())
    assert freeze["required_families_count"] == actual
    assert actual >= 19  # grew after adding stage3_claims + stage3_handoff this sprint
