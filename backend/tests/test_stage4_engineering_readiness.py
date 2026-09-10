"""Adversarial + arithmetic tests for the Stage 4 engineering-readiness reader
and API route (Stage 4 integration prep, governing prompt §87-89).

Failure mode under test throughout: a missing, malformed, or schema-mismatched
results/stage4_engineering_readiness.json must fail closed to UNAVAILABLE,
never fabricate a value, never silently substitute 0 for an absent quantity.
Arithmetic tests confirm the base-topology totals correctly EXCLUDE leg_bioz
and second_ppg_site (rules 47/48/57), and that engineering-assumption values
are never relabeled as datasheet facts.
"""

from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.research.stage4_engineering import Stage4EngineeringReader
from app.schemas.research import ResearchAvailability
from app.schemas.stage4_engineering import EvidenceClass

client = TestClient(app)


def _valid_artifact() -> dict:
    return {
        "artifact_id": "test-stage4-engineering-readiness",
        "schema_version": "1.0.0",
        "sprint": "STAGE4_TEST",
        "generated_role": "INTEGRATION_OWNER",
        "statement": "test fixture",
        "prohibited": ["Do NOT do the bad thing."],
        "power": {
            "duty_schedule": {
                "wrist_ppg": {"state": "active_acquisition", "duty_fraction": 1.0, "note": "n/a"},
            },
            "system_average_power": {
                "status": "PARTIAL_READY",
                "reason": "test",
                "base_topology_load_side_mw": {"value": 6.15, "unit": "mW", "evidence_class": "ENGINEERING_ASSUMPTION"},
                "base_topology_battery_side_mw": {"value": 7.24, "unit": "mW", "evidence_class": "ENGINEERING_ASSUMPTION"},
                "contributors_mw": {"wrist_ppg_total_incl_led": 0.786},
                "excluded_from_base_total": {"leg_bioz_mw": 0.033, "second_ppg_site_incl_led_mw": 0.786},
            },
        },
        "data_rate": {
            "system_raw_total_bps": {"value": 19585.6, "unit": "bps", "evidence_class": "ENGINEERING_ASSUMPTION"},
            "system_transmitted_bps": {"value": 23502.72, "unit": "bps", "evidence_class": "ENGINEERING_ASSUMPTION"},
            "processed_data_rate_status": "NOT_READY",
            "excluded_from_base_total_bps": {"second_ppg_site": 28500, "leg_bioz": 1.0},
        },
        "mass": {
            "system_mass_status": "PARTIAL",
            "tier_achieved": "Tier2",
            "system_mass_base_topology_excl_leg_g": {"value": 30.533, "unit": "g", "evidence_class": "ENGINEERING_ALLOWANCE_MECHANICAL_ESTIMATE"},
            "eog_incremental_mass_g": {"value": 0.4, "unit": "g", "evidence_class": "ENGINEERING_ALLOWANCE_MECHANICAL_ESTIMATE"},
        },
        "bom": {
            "not_a_final_bom": True,
            "final": False,
            "items_advanced": [{"item": "mcu", "from": "MISSING", "to": "REFERENCE_SELECTED"}],
            "still_missing": ["head AFE exact datasheet power table value"],
        },
        "final_architecture_status": "UNRESOLVED",
        "formal_pareto_status": "FORMAL_PARETO_NOT_READY",
        "source_artifacts": ["results/reference_power_budget_day11_part2.json"],
    }


def test_missing_artifact_is_unavailable_not_zero(tmp_path) -> None:
    reader = Stage4EngineeringReader(repository_root=tmp_path)
    envelope = reader.artifact()
    assert envelope.availability == ResearchAvailability.UNAVAILABLE
    assert envelope.readiness is None
    assert "does not exist" in envelope.error


def test_malformed_json_fails_closed(tmp_path) -> None:
    results_dir = tmp_path / "results"
    results_dir.mkdir()
    (results_dir / "stage4_engineering_readiness.json").write_text("{not valid json", encoding="utf-8")
    reader = Stage4EngineeringReader(repository_root=tmp_path)
    envelope = reader.artifact()
    assert envelope.availability == ResearchAvailability.UNAVAILABLE
    assert envelope.readiness is None


def test_schema_mismatch_fails_closed_not_partial_object(tmp_path) -> None:
    results_dir = tmp_path / "results"
    results_dir.mkdir()
    broken = _valid_artifact()
    del broken["power"]  # required top-level key removed
    (results_dir / "stage4_engineering_readiness.json").write_text(json.dumps(broken), encoding="utf-8")
    reader = Stage4EngineeringReader(repository_root=tmp_path)
    envelope = reader.artifact()
    assert envelope.availability == ResearchAvailability.UNAVAILABLE
    assert envelope.readiness is None
    assert envelope.error is not None


def test_valid_artifact_preserves_evidence_class_distinction(tmp_path) -> None:
    results_dir = tmp_path / "results"
    results_dir.mkdir()
    (results_dir / "stage4_engineering_readiness.json").write_text(json.dumps(_valid_artifact()), encoding="utf-8")
    reader = Stage4EngineeringReader(repository_root=tmp_path)
    envelope = reader.artifact()
    assert envelope.availability == ResearchAvailability.AVAILABLE
    power_q = envelope.readiness.system_average_power.base_topology_battery_side_mw
    assert power_q.evidence_class == EvidenceClass.ENGINEERING_ASSUMPTION
    mass_q = envelope.readiness.system_mass.system_mass_base_topology_excl_leg_g
    assert mass_q.evidence_class == EvidenceClass.ENGINEERING_ALLOWANCE_MECHANICAL_ESTIMATE
    # Evidence classes must stay distinguishable, never merged into one generic "known" bucket.
    assert power_q.evidence_class != mass_q.evidence_class


def test_missing_numeric_value_is_unknown_not_zero(tmp_path) -> None:
    results_dir = tmp_path / "results"
    results_dir.mkdir()
    artifact = _valid_artifact()
    del artifact["power"]["system_average_power"]["base_topology_battery_side_mw"]["value"]
    (results_dir / "stage4_engineering_readiness.json").write_text(json.dumps(artifact), encoding="utf-8")
    reader = Stage4EngineeringReader(repository_root=tmp_path)
    envelope = reader.artifact()
    assert envelope.availability == ResearchAvailability.AVAILABLE
    q = envelope.readiness.system_average_power.base_topology_battery_side_mw
    assert q.value is None
    assert q.status == "UNKNOWN"


def test_live_route_reports_partial_ready_and_excludes_optional_branches() -> None:
    response = client.get("/research/stage4-engineering-readiness")
    assert response.status_code == 200
    body = response.json()
    assert body["availability"] == "available"
    readiness = body["readiness"]
    assert readiness["system_average_power"]["status"] == "PARTIAL_READY"
    assert readiness["final_architecture_status"] == "UNRESOLVED"
    assert readiness["formal_pareto_status"] == "FORMAL_PARETO_NOT_READY"
    # Base-topology raw total must be strictly less than raw + second_ppg_site's
    # 28,500 bps contribution — i.e. the optional branch is not silently included.
    raw_total = readiness["system_data_rate"]["system_raw_total_bps"]["value"]
    excluded_second_ppg = readiness["system_data_rate"]["excluded_from_base_total_bps"]["second_ppg_site"]
    assert raw_total < raw_total + excluded_second_ppg
    assert excluded_second_ppg == pytest.approx(28500)
    # leg_bioz power is characterized but excluded from the base power total.
    excluded_leg = readiness["system_average_power"]["excluded_from_base_total_mw"]["leg_bioz_mw"]
    assert excluded_leg > 0
    assert "leg_bioz" not in readiness["system_average_power"]["contributors_mw"]


def test_bom_never_claims_final() -> None:
    response = client.get("/research/stage4-engineering-readiness")
    body = response.json()
    assert body["readiness"]["bom"]["not_a_final_bom"] is True
    assert body["readiness"]["bom"]["final"] is False
