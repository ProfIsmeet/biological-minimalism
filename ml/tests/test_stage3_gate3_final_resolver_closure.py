"""Gate 3 final closure regression tests: reproduces the independent
auditor's exact attack (resolve_current accepted corrupted content while
resolve_and_verify rejected it) and confirms BOTH public current-
resolution routes now reject hash-corrupted governing content
identically. Also covers Tests A-H from the master prompt."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

import ml.stage3_science_resolver as resolver  # noqa: E402

TARGET = REPO_ROOT / "results" / "lbnp_thoracic_eis_stage3_v2_protocol_compliant.json"


@pytest.fixture
def corrupted_lbnp():
    backup = TARGET.read_bytes()
    d = json.loads(TARGET.read_text())
    d["aggregate"]["A_mean"] = 999.0
    TARGET.write_text(json.dumps(d, indent=2))
    yield
    TARGET.write_bytes(backup)
    assert TARGET.read_bytes() == backup


@pytest.fixture
def temp_registry(tmp_path, monkeypatch):
    real = json.loads(resolver.REGISTRY_PATH.read_text())

    def _write(mutated):
        tmp = tmp_path / "registry.json"
        tmp.write_text(json.dumps(mutated))
        monkeypatch.setattr(resolver, "REGISTRY_PATH", tmp)

    return real, _write


# --- Test A/B: valid resolution succeeds through both APIs ---

def test_a_resolve_current_succeeds_on_valid_governing_artifact():
    data = resolver.resolve_current("lbnp_thoracic_eis")
    assert data["classification"] == "COMPLETE_MIXED"


def test_b_resolve_and_verify_succeeds_on_valid_governing_artifact():
    data = resolver.resolve_and_verify("lbnp_thoracic_eis")
    assert data["classification"] == "COMPLETE_MIXED"


# --- Test C/D: corrupted governing LBNP fails through both APIs ---

def test_c_resolve_current_rejects_corrupted_governing_lbnp(corrupted_lbnp):
    with pytest.raises(resolver.IntegrityVerificationError, match="HASH_MISMATCH"):
        resolver.resolve_current("lbnp_thoracic_eis")


def test_d_resolve_and_verify_rejects_corrupted_governing_lbnp(corrupted_lbnp):
    with pytest.raises(resolver.IntegrityVerificationError, match="HASH_MISMATCH"):
        resolver.resolve_and_verify("lbnp_thoracic_eis")


def test_reproduces_auditors_exact_attack_both_apis_reject(corrupted_lbnp):
    """The exact scenario the independent auditor demonstrated:
    resolve_current: ACCEPTED_CORRUPTED 999.0
    resolve_and_verify: REJECTED IntegrityVerificationError HASH_MISMATCH
    Both must now reject identically."""
    results = {}
    for name, fn in (("resolve_current", resolver.resolve_current), ("resolve_and_verify", resolver.resolve_and_verify)):
        try:
            data = fn("lbnp_thoracic_eis")
            results[name] = ("ACCEPTED_CORRUPTED", data["aggregate"]["A_mean"])
        except resolver.IntegrityVerificationError as e:
            results[name] = ("REJECTED", "HASH_MISMATCH" in str(e))
    assert results["resolve_current"] == ("REJECTED", True)
    assert results["resolve_and_verify"] == ("REJECTED", True)


# --- Test E/F/G: relabeled known-bad artifacts fail through BOTH APIs ---

def test_e_historical_lbnp_relabeled_governing_fails_both_apis(temp_registry):
    real, write = temp_registry
    mutated = json.loads(json.dumps(real))
    artifacts = mutated["families"]["lbnp_thoracic_eis"]["artifacts"]
    for a in artifacts:
        a["status"] = "SUPPORTING" if "v2_protocol_compliant" in a["path"] else "GOVERNING"
    write(mutated)
    with pytest.raises(resolver.GovernanceResolutionError, match="forbidden marker"):
        resolver.resolve_current("lbnp_thoracic_eis")
    with pytest.raises(resolver.GovernanceResolutionError, match="forbidden marker"):
        resolver.resolve_and_verify("lbnp_thoracic_eis")


def test_f_invalid_galaxy_relabeled_governing_fails_both_apis(temp_registry):
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
        resolver.resolve_current("galaxyppg_external_replication")
    with pytest.raises(resolver.GovernanceResolutionError, match="forbidden marker"):
        resolver.resolve_and_verify("galaxyppg_external_replication")


def test_g_noncanonical_sleep_relabeled_governing_fails_both_apis(temp_registry):
    real, write = temp_registry
    mutated = json.loads(json.dumps(real))
    artifacts = mutated["families"]["sleep_edf_primary_ab"]["artifacts"]
    for a in artifacts:
        a["status"] = "GOVERNING" if "noncanonical" in a["path"] else "SUPPORTING"
    write(mutated)
    with pytest.raises(resolver.GovernanceResolutionError, match="forbidden marker"):
        resolver.resolve_current("sleep_edf_primary_ab")
    with pytest.raises(resolver.GovernanceResolutionError, match="forbidden marker"):
        resolver.resolve_and_verify("sleep_edf_primary_ab")


# --- Test H: zero/duplicate governing remain fail-closed through both APIs ---

def test_h_zero_governing_fails_closed_both_apis(temp_registry):
    real, write = temp_registry
    mutated = json.loads(json.dumps(real))
    for a in mutated["families"]["lbnp_thoracic_eis"]["artifacts"]:
        a["status"] = "HISTORICAL_SUPERSEDED_OUT_OF_PROTOCOL"
    write(mutated)
    with pytest.raises(resolver.GovernanceResolutionError, match="No GOVERNING artifact"):
        resolver.resolve_current("lbnp_thoracic_eis")
    with pytest.raises(resolver.GovernanceResolutionError, match="No GOVERNING artifact"):
        resolver.resolve_and_verify("lbnp_thoracic_eis")


def test_h_duplicate_governing_fails_closed_both_apis(temp_registry):
    real, write = temp_registry
    mutated = json.loads(json.dumps(real))
    mutated["families"]["lbnp_thoracic_eis"]["artifacts"][1]["status"] = "GOVERNING"
    write(mutated)
    with pytest.raises(resolver.GovernanceResolutionError, match="AMBIGUOUS"):
        resolver.resolve_current("lbnp_thoracic_eis")
    with pytest.raises(resolver.GovernanceResolutionError, match="AMBIGUOUS"):
        resolver.resolve_and_verify("lbnp_thoracic_eis")


# --- resolve_by_path_or_status also enforces integrity now ---

def test_resolve_by_path_or_status_rejects_corrupted_governing_lbnp(corrupted_lbnp):
    with pytest.raises(resolver.IntegrityVerificationError, match="HASH_MISMATCH"):
        resolver.resolve_by_path_or_status("results/lbnp_thoracic_eis_stage3_v2_protocol_compliant.json")


# --- resolve_current is literally an alias, not a parallel implementation ---

def test_resolve_current_is_alias_for_resolve_and_verify():
    import inspect
    src = inspect.getsource(resolver.resolve_current)
    assert "resolve_and_verify" in src


def test_unverified_helper_is_private_and_undocumented_as_safe():
    assert resolver._resolve_current_unverified.__name__.startswith("_")
    assert "NEVER" in resolver._resolve_current_unverified.__doc__
