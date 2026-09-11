"""Gate 3 closure regression tests (Sections 3-6, 15-16 of the acceptance
gate closure master prompt): the resolver must not trust a registry
GOVERNING label alone - it must independently re-verify the artifact's
own semantic content, and resolve_and_verify() must fail closed on any
hash mismatch against the frozen manifest."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

import ml.stage3_science_resolver as resolver  # noqa: E402


@pytest.fixture
def temp_registry(tmp_path, monkeypatch):
    real = json.loads(resolver.REGISTRY_PATH.read_text())

    def _write(mutated):
        tmp = tmp_path / "registry.json"
        tmp.write_text(json.dumps(mutated))
        monkeypatch.setattr(resolver, "REGISTRY_PATH", tmp)

    return real, _write


def test_relabeling_historical_lbnp_as_sole_governing_still_fails(temp_registry):
    """Section 15's mandatory hostile test: even if the registry is
    tampered so the OLD historical LBNP result is the only GOVERNING
    entry (and v2 is demoted), resolution must still fail - because the
    old file's own 'status' field independently says
    HISTORICAL_SUPERSEDED_OUT_OF_PROTOCOL."""
    real, write = temp_registry
    mutated = json.loads(json.dumps(real))
    artifacts = mutated["families"]["lbnp_thoracic_eis"]["artifacts"]
    for a in artifacts:
        a["status"] = "SUPPORTING" if "v2_protocol_compliant" in a["path"] else "GOVERNING"
    write(mutated)
    with pytest.raises(resolver.GovernanceResolutionError, match="forbidden marker"):
        resolver.resolve_governing_path("lbnp_thoracic_eis")


def test_corrupted_governing_file_fails_hash_verification(tmp_path):
    """Section 16's mandatory hostile test: a governing file modified
    after the freeze hash was generated must fail resolve_and_verify()
    with an explicit HASH_MISMATCH, never silently continue. Operates on
    a real file but restores it byte-for-byte in a finally block."""
    target = REPO_ROOT / "results" / "lbnp_thoracic_eis_stage3_v2_protocol_compliant.json"
    backup = target.read_bytes()
    try:
        d = json.loads(target.read_text())
        d["aggregate"]["A_mean"] = 999.0
        target.write_text(json.dumps(d, indent=2))
        with pytest.raises(resolver.IntegrityVerificationError, match="HASH_MISMATCH"):
            resolver.resolve_and_verify("lbnp_thoracic_eis")
    finally:
        target.write_bytes(backup)
    assert target.read_bytes() == backup


def test_resolve_and_verify_succeeds_on_unmodified_governing_artifact():
    data = resolver.resolve_and_verify("lbnp_thoracic_eis")
    assert data["classification"] == "COMPLETE_MIXED"
    data2 = resolver.resolve_and_verify("galaxyppg_external_replication")
    assert data2["final_classification"] == "EXTERNAL_REPLICATION_SUPPORTIVE"


def test_relabeling_invalidated_galaxy_as_governing_fails(temp_registry):
    real, write = temp_registry
    mutated = json.loads(json.dumps(real))
    artifacts = mutated["families"]["galaxyppg_external_replication"]["artifacts"]
    for a in artifacts:
        if "external_replication_stage2" in a["path"]:
            a["status"] = "GOVERNING"
        elif "corrected_full_cv_result" in a["path"]:
            a["status"] = "SUPPORTING"
    write(mutated)
    with pytest.raises(resolver.GovernanceResolutionError, match="forbidden marker"):
        resolver.resolve_governing_path("galaxyppg_external_replication")


def test_relabeling_noncanonical_sleep_as_governing_fails(temp_registry):
    real, write = temp_registry
    mutated = json.loads(json.dumps(real))
    artifacts = mutated["families"]["sleep_edf_primary_ab"]["artifacts"]
    for a in artifacts:
        if "noncanonical" in a["path"]:
            a["status"] = "GOVERNING"
        else:
            a["status"] = "SUPPORTING"
    write(mutated)
    with pytest.raises(resolver.GovernanceResolutionError, match="forbidden marker"):
        resolver.resolve_governing_path("sleep_edf_primary_ab")


def test_relabeling_bounded_galaxy_diagnostic_as_governing_fails(temp_registry):
    real, write = temp_registry
    mutated = json.loads(json.dumps(real))
    artifacts = mutated["families"]["galaxyppg_external_replication"]["artifacts"]
    for a in artifacts:
        if "hr_corrected_eligibility_stage3" in a["path"]:
            a["status"] = "GOVERNING"
        elif "corrected_full_cv_result" in a["path"]:
            a["status"] = "SUPPORTING"
    write(mutated)
    with pytest.raises(resolver.GovernanceResolutionError, match="forbidden marker"):
        resolver.resolve_governing_path("galaxyppg_external_replication")


def test_current_handoff_and_claims_are_governed_and_hash_verified():
    """Section 9/19-20: cross-cutting current docs must now be governed
    families, not manually appended, and must pass integrity
    verification like any other governing artifact."""
    claims = resolver.resolve_and_verify("stage3_claims")
    assert "docs/STAGE3_SAFE_UNSAFE_CLAIMS.md" == claims["path"]
    handoff = resolver.resolve_and_verify("stage3_handoff")
    assert "docs/STAGE3_HANDOFF_TO_EMIR_AND_INTEGRATION_OWNER.md" == handoff["path"]


def test_historical_doc_cannot_replace_governing_handoff_pointer(temp_registry, tmp_path):
    """Section 19: attempt to make a historical/superseded document the
    governing handoff pointer - must fail, since the substitute doc has
    no artifact_semantic_status assertion at all (an unregistered doc
    cannot silently inherit governance)."""
    real, write = temp_registry
    mutated = json.loads(json.dumps(real))
    fake_historical_doc = tmp_path / "OLD_SUPERSEDED_HANDOFF.md"
    fake_historical_doc.write_text("stale content\n")
    mutated["families"]["stage3_handoff"]["artifacts"] = [
        {
            "path": str(fake_historical_doc.relative_to(REPO_ROOT)) if fake_historical_doc.is_relative_to(REPO_ROOT) else "docs/OLD_SUPERSEDED_HANDOFF.md",
            "status": "GOVERNING",
            "status_field": None,
            # deliberately no artifact_semantic_status - simulates an
            # attempt to sneak an unvetted historical doc into governance
        }
    ]
    write(mutated)
    with pytest.raises(resolver.GovernanceResolutionError):
        resolver.resolve_governing_path("stage3_handoff")


def test_modifying_governed_handoff_fails_integrity(tmp_path):
    target = REPO_ROOT / "docs" / "STAGE3_HANDOFF_TO_EMIR_AND_INTEGRATION_OWNER.md"
    backup = target.read_bytes()
    try:
        target.write_text(target.read_text() + "\n\ntampered line\n")
        with pytest.raises(resolver.IntegrityVerificationError, match="HASH_MISMATCH"):
            resolver.resolve_and_verify("stage3_handoff")
    finally:
        target.write_bytes(backup)
    assert target.read_bytes() == backup
