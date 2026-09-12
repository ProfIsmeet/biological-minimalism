"""Stage-4 science handoff regression tests: the claim-consistency
validator passes, every governing number in the consumption manifest
matches the resolver's live-resolved content, and the required
architecture/Pareto UNRESOLVED/NOT_READY guards hold."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

import ml.stage3_science_resolver as resolver  # noqa: E402
from ml.validate_stage4_science_claim_consistency import main as run_validator  # noqa: E402


def _load(rel):
    return json.loads((REPO_ROOT / rel).read_text())


def test_claim_consistency_validator_passes():
    run_validator()  # raises on any violation


def test_consumption_manifest_covers_minimum_required_families():
    d = _load("results/stage4_science_consumption_manifest.json")
    family_ids = {f["family_id"] for f in d["families"]}
    required = {
        "sleep_edf_primary_ab", "sleep_edf_shuffled_control_c", "sleep_edf_interaction",
        "ppg_dalia_capacity_control", "ptt_second_ppg_site", "qde_v2_leg_bioz",
        "galaxyppg_external_replication", "lbnp_thoracic_eis",
        "hmc_bounded_diagnostic", "ds003838_bounded_diagnostic",
    }
    assert required.issubset(family_ids)


def test_consumption_manifest_numbers_match_live_resolved_content():
    d = _load("results/stage4_science_consumption_manifest.json")
    galaxy_family = next(f for f in d["families"] if f["family_id"] == "galaxyppg_external_replication")
    live = resolver.resolve_current("galaxyppg_external_replication")
    agg = live["aggregate_across_all_18_eligible_subjects"]
    assert abs(galaxy_family["governing_numeric_result"]["participant_level_A_cap_to_B"] - agg["A_to_B"]["mean"]) < 1e-6

    lbnp_family = next(f for f in d["families"] if f["family_id"] == "lbnp_thoracic_eis")
    live_lbnp = resolver.resolve_current("lbnp_thoracic_eis")
    assert abs(lbnp_family["governing_numeric_result"]["A"] - live_lbnp["aggregate"]["A_mean"]) < 1e-6
    assert lbnp_family["evidence_classification"] == live_lbnp["classification"]


def test_consumption_manifest_architecture_status_unresolved():
    d = _load("results/stage4_science_consumption_manifest.json")
    assert d["final_architecture_status"] == "UNRESOLVED"
    assert d["formal_pareto_status"] == "NOT_READY"


def test_sensor_value_matrix_never_uses_keep_remove():
    d = _load("results/stage4_scientific_sensor_value_matrix.json")
    allowed = {
        "STRONGLY_SUPPORTED_CORE", "SUPPORTED", "CONTEXTUAL_LOW_BURDEN",
        "MIXED", "DEPRIORITIZED", "EXPERIMENTAL", "PENDING_EXTERNAL_VALIDATION", "N/A",
    }
    for m in d["modalities"]:
        assert m["architecture_implication"] in allowed
    assert d["final_architecture_status"] == "UNRESOLVED"


def test_sensor_value_matrix_covers_minimum_modalities():
    d = _load("results/stage4_scientific_sensor_value_matrix.json")
    names = {m["modality"] for m in d["modalities"]}
    required = {"wrist PPG", "wrist IMU", "chest ECG", "thoracic BioZ/EIS", "frontal EEG", "EOG", "leg BioZ", "second-site PPG"}
    assert required.issubset(names)


def test_claim_ledger_covers_minimum_areas():
    d = _load("results/stage4_science_claim_ledger.json")
    ids = {c["claim_id"] for c in d["claims"]}
    required = {
        "ppg_plus_imu", "galaxy_replication", "eog_incremental_value", "sleep_interaction",
        "second_site_ppg", "leg_bioz", "thoracic_eis", "hmc", "ds003838",
        "digital_twin", "final_architecture", "pareto", "astronaut_microgravity_applicability",
    }
    assert required.issubset(ids)
    for c in d["claims"]:
        assert c["strength"] in d["strength_enum"]


def test_claim_ledger_old_ppg_headline_is_historical_only():
    d = _load("results/stage4_science_claim_ledger.json")
    c = next(c for c in d["claims"] if c["claim_id"] == "old_ppg_imu_headline_20_6_23_percent")
    assert c["strength"] == "HISTORICAL_ONLY"


def test_architecture_decision_inputs_never_resolves_architecture():
    d = _load("results/stage4_architecture_decision_inputs_science.json")
    assert d["final_architecture_status"] == "UNRESOLVED"
    assert d["formal_pareto_status"] == "NOT_READY"
    for c in d["candidates"]:
        value = c["decision_sensitivity_to_pending_science"]
        assert value.split(" ", 1)[0] in {"HIGH", "MEDIUM", "LOW"}, value


def test_allowlist_excludes_all_known_bad_artifacts():
    d = _load("results/stage4_integration_science_allowlist.json")
    excluded_items = " ".join(e["item"] for e in d["explicitly_excluded"])
    for bad in (
        "sensor_marginal_value_contract.json",
        "galaxyppg_hr_external_replication_stage2.json",
        "galaxyppg_hr_full_grouped_cv_stage3.json",
        "lbnp_thoracic_eis_stage3.json",
        "claude_noncanonical_sleep_edf_primary_seedfix_v2_reproduction.json",
    ):
        assert bad in excluded_items


def test_final_science_non_regression():
    galaxy = resolver.resolve_current("galaxyppg_external_replication")
    agg = galaxy["aggregate_across_all_18_eligible_subjects"]
    assert abs(agg["A_to_B"]["mean"] - 0.8342679686016505) < 1e-9
    assert abs(agg["C_to_B"]["mean"] - 0.9162305063671538) < 1e-9

    lbnp = resolver.resolve_current("lbnp_thoracic_eis")
    assert abs(lbnp["aggregate"]["A_mean"] - 20.97267498504867) < 1e-9
    assert abs(lbnp["aggregate"]["B_mean"] - 21.42505992137661) < 1e-9
    assert abs(lbnp["aggregate"]["C_mean"] - 20.13177842144602) < 1e-9
    assert lbnp["classification"] == "COMPLETE_MIXED"
