"""Section 21-22/31 regression tests: the real Stage-3 science resolver
must fail closed against every known-bad artifact, resolve exactly the
correct governing artifact for each family, and the registry/freeze
manifest must never let a non-GOVERNING status appear as governing -
enforced by inspecting artifact METADATA, never by key-name substring
heuristics."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from ml.stage3_science_resolver import (  # noqa: E402
    GOVERNING_STATUS,
    GovernanceResolutionError,
    list_families,
    resolve_by_path_or_status,
    resolve_current,
    resolve_governing_path,
)


def _load_registry():
    return json.loads((REPO_ROOT / "results" / "stage3_governance_registry.json").read_text())


# --- Positive resolution: correct governing artifact per family ---

def test_lbnp_resolves_to_v2_protocol_compliant():
    path = resolve_governing_path("lbnp_thoracic_eis")
    assert path == "results/lbnp_thoracic_eis_stage3_v2_protocol_compliant.json"
    data = resolve_current("lbnp_thoracic_eis")
    assert data["classification"] == "COMPLETE_MIXED"


def test_galaxyppg_resolves_to_corrected_full_cv():
    path = resolve_governing_path("galaxyppg_external_replication")
    assert path == "results/galaxyppg_corrected_full_cv_result.json"
    data = resolve_current("galaxyppg_external_replication")
    assert data["final_classification"] == "EXTERNAL_REPLICATION_SUPPORTIVE"


def test_sleep_resolves_to_primary_seedfix_v2():
    path = resolve_governing_path("sleep_edf_primary_ab")
    assert path == "results/sleep_edf_primary_seedfix_v2.json"


def test_ppg_dalia_resolves_to_capacity_control():
    assert resolve_governing_path("ppg_dalia_capacity_control") == "results/ppg_dalia_capacity_control.json"


def test_ptt_resolves():
    assert resolve_governing_path("ptt_second_ppg_site") == "results/ptt_ppg_site_ablation.json"


def test_qde_resolves():
    assert resolve_governing_path("qde_v2_leg_bioz") == "results/qde_v2_leg_bioz_stage2.json"


def test_hmc_bounded_resolves():
    path = resolve_governing_path("hmc_bounded_diagnostic")
    assert "bounded_n7" in path


def test_ds003838_bounded_resolves():
    assert "bounded_diagnostic" in resolve_governing_path("ds003838_bounded_diagnostic")


# --- Negative resolution: known-bad artifacts must fail closed ---

def test_old_lbnp_result_cannot_resolve_as_current():
    with pytest.raises(GovernanceResolutionError):
        resolve_by_path_or_status("results/lbnp_thoracic_eis_stage3.json")


def test_invalid_preqc_galaxy_bounded_result_cannot_resolve():
    with pytest.raises(GovernanceResolutionError):
        resolve_by_path_or_status("results/galaxyppg_hr_external_replication_stage2.json")


def test_invalid_preqc_galaxy_full_cv_cannot_resolve():
    with pytest.raises(GovernanceResolutionError):
        resolve_by_path_or_status("results/galaxyppg_hr_full_grouped_cv_stage3.json")


def test_noncanonical_sleep_reproduction_cannot_govern():
    with pytest.raises(GovernanceResolutionError):
        resolve_by_path_or_status("results/claude_noncanonical_sleep_edf_primary_seedfix_v2_reproduction.json")


def test_unknown_family_fails_closed():
    with pytest.raises(GovernanceResolutionError):
        resolve_governing_path("this_family_does_not_exist")


# --- Structural invariants over the whole registry ---

def test_no_family_has_zero_or_multiple_governing_artifacts_where_resolvable():
    """Every family list_families() returns must resolve cleanly (exactly
    one GOVERNING) - list_families() itself is just registry keys, so this
    also proves no family is silently broken."""
    for family in list_families():
        path = resolve_governing_path(family)
        assert (REPO_ROOT / path).exists()


def test_galaxy_bounded_diagnostic_is_supporting_not_governing():
    """Section 15: the bounded single-fold diagnostic must be SUPPORTING,
    never GOVERNING - the full CV is the governing external-replication
    evidence."""
    registry = _load_registry()
    artifacts = registry["families"]["galaxyppg_external_replication"]["artifacts"]
    bounded = next(a for a in artifacts if "eligibility_stage3" in a["path"] and "full_cv" not in a["path"])
    assert bounded["status"] == "SUPPORTING"
    assert bounded["status"] != GOVERNING_STATUS


def test_no_never_governing_status_value_is_literally_governing():
    """Metadata-driven check, not a key-name heuristic: for every artifact
    in every family, if its status string is one of the defined
    never-governing statuses, it must not equal GOVERNING_STATUS (this is
    definitionally true given how load works, but guards against a future
    typo introducing a duplicate/aliased governing string)."""
    from ml.stage3_science_resolver import NEVER_GOVERNING_STATUSES

    registry = _load_registry()
    for fam, fd in registry["families"].items():
        for a in fd["artifacts"]:
            if a["status"] in NEVER_GOVERNING_STATUSES:
                assert a["status"] != GOVERNING_STATUS


def test_registry_valid_statuses_list_is_exhaustive():
    registry = _load_registry()
    valid = set(registry["valid_statuses"])
    for fam, fd in registry["families"].items():
        for a in fd["artifacts"]:
            assert a["status"] in valid, f"{fam}: unknown status {a['status']!r}"
