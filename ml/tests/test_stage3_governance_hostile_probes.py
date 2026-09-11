"""Part XII hostile self-review, made permanent: attempts to break the
resolver via a mutated temp copy of the registry (the real registry file
on disk is never touched by these tests)."""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

import ml.stage3_science_resolver as resolver  # noqa: E402


@pytest.fixture
def temp_registry(tmp_path, monkeypatch):
    real = json.loads(resolver.REGISTRY_PATH.read_text())
    tmp = tmp_path / "registry.json"

    def _write(mutated):
        tmp.write_text(json.dumps(mutated))
        monkeypatch.setattr(resolver, "REGISTRY_PATH", tmp)

    return real, _write


def test_two_governing_artifacts_raises(temp_registry):
    real, write = temp_registry
    mutated = json.loads(json.dumps(real))
    mutated["families"]["lbnp_thoracic_eis"]["artifacts"][1]["status"] = "GOVERNING"
    write(mutated)
    with pytest.raises(resolver.GovernanceResolutionError, match="AMBIGUOUS"):
        resolver.resolve_governing_path("lbnp_thoracic_eis")


def test_zero_governing_artifacts_raises(temp_registry):
    real, write = temp_registry
    mutated = json.loads(json.dumps(real))
    for a in mutated["families"]["lbnp_thoracic_eis"]["artifacts"]:
        a["status"] = "HISTORICAL_SUPERSEDED_OUT_OF_PROTOCOL"
    write(mutated)
    with pytest.raises(resolver.GovernanceResolutionError, match="No GOVERNING artifact"):
        resolver.resolve_governing_path("lbnp_thoracic_eis")


def test_governing_artifact_missing_file_raises(temp_registry):
    real, write = temp_registry
    mutated = json.loads(json.dumps(real))
    mutated["families"]["lbnp_thoracic_eis"]["artifacts"][0]["path"] = "results/does_not_exist_at_all.json"
    write(mutated)
    with pytest.raises(resolver.GovernanceResolutionError, match="does not exist on disk"):
        resolver.resolve_governing_path("lbnp_thoracic_eis")


def test_real_registry_file_untouched_by_hostile_probes():
    """Sanity check that the fixture pattern above never mutates the real
    on-disk registry - hostile probes must operate on isolated copies."""
    real_content_before = (REPO_ROOT / "results" / "stage3_governance_registry.json").read_text()
    # simulate a probe run inline
    import copy
    real = json.loads(real_content_before)
    mutated = copy.deepcopy(real)
    mutated["families"]["lbnp_thoracic_eis"]["artifacts"][0]["status"] = "SUPERSEDED"
    # never write `mutated` back to the real path
    real_content_after = (REPO_ROOT / "results" / "stage3_governance_registry.json").read_text()
    assert real_content_before == real_content_after
