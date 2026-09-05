"""Day 5 scientific/operational integration and honesty invariants."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.research.catalog import REPOSITORY_ROOT
from app.research.decision_inputs import (
    DECISION_INPUTS_PATH,
    FROZEN_ROBUSTNESS_SHA256,
    DecisionInputsReader,
    build_decision_inputs,
    decision_inputs,
)
from app.schemas.research import ResearchAvailability

client = TestClient(app)


@pytest.fixture(scope="module")
def artifact():
    envelope = decision_inputs.artifact()
    assert envelope.availability == ResearchAvailability.AVAILABLE
    assert envelope.decision_inputs is not None
    return envelope.decision_inputs


def _component(artifact, component_id: str):
    return next(item for item in artifact.components if item.component_id == component_id)


def _all_keys(value):
    if isinstance(value, dict):
        for key, child in value.items():
            yield key
            yield from _all_keys(child)
    elif isinstance(value, list):
        for child in value:
            yield from _all_keys(child)


# 1
def test_ismet_day5_artifacts_are_integrated() -> None:
    for relative in (
        "docs/SENSOR_MARGINAL_VALUE_METHODOLOGY.md",
        "results/sensor_marginal_value_contract.json",
        "docs/EMIR_PARETO_HANDOFF_DAY5.md",
        "ml/tests/test_sensor_marginal_value_contract.py",
    ):
        assert (REPOSITORY_ROOT / relative).is_file()


# 2
def test_exact_scientific_benefits_come_from_contract(artifact) -> None:
    source = json.loads((REPOSITORY_ROOT / "results/sensor_marginal_value_contract.json").read_text())
    for component_id, experiment_id in (
        ("wrist_imu", "ppg_dalia_imu_hr"),
        ("second_ppg_site", "ptt_second_ppg_site_hr"),
    ):
        joined = _component(artifact, component_id).scientific_marginal_value
        experiment = source["experiments"][experiment_id]
        assert joined.absolute_benefit == experiment["absolute_benefit"]
        assert joined.relative_improvement == experiment["relative_improvement"]


# 3
def test_wrist_imu_join_is_exact(artifact) -> None:
    wrist = _component(artifact, "wrist_imu")
    assert wrist.scientific_marginal_value.scientific_component_id == "wrist_imu_accelerometer"
    assert wrist.experiment_id == "ppg_dalia_imu_hr"
    assert wrist.scientific_marginal_value.absolute_benefit["mae_bpm"] == pytest.approx(2.058361530303955)
    assert wrist.scientific_marginal_value.direction == "POSITIVE"


# 4
def test_second_ppg_site_join_is_exact(artifact) -> None:
    second = _component(artifact, "second_ppg_site")
    assert second.scientific_marginal_value.scientific_component_id == "second_physical_ppg_site_proximal_phalanx"
    assert second.experiment_id == "ptt_second_ppg_site_hr"
    assert second.scientific_marginal_value.absolute_benefit["mae_bpm"] == pytest.approx(-1.4624088287353523)
    assert second.scientific_marginal_value.direction == "NEGATIVE"


# 5
def test_cross_dataset_raw_mae_is_not_a_ranking_axis(artifact) -> None:
    datasets = {item.scientific_marginal_value.dataset_id for item in artifact.components}
    assert datasets == {"ppg_dalia", "pulse_transit_time_ppg"}
    assert "not comparable" in artifact.readiness.cross_dataset_restriction
    assert artifact.readiness.formal_pareto_calculated is False


# 6
def test_unknown_physical_costs_remain_null(artifact) -> None:
    for component in artifact.components:
        for dimension in ("incremental_power_mw", "incremental_mass_g"):
            quantity = component.operational_cost.dimensions[dimension]
            assert quantity.availability == "unknown"
            assert quantity.value is None
            assert quantity.minimum is None
            assert quantity.typical is None
            assert quantity.maximum is None


# 7
def test_missing_ismet_robustness_status_is_resolved_from_real_source(artifact) -> None:
    scientific = json.loads((REPOSITORY_ROOT / "results/sensor_marginal_value_contract.json").read_text())
    assert scientific["experiments"]["ppg_dalia_fault_robustness"]["status"] == "SOURCE_ARTIFACT_NOT_FOUND"
    robustness = _component(artifact, "wrist_imu").robustness_evidence
    assert robustness is not None
    assert robustness.status == "RESOLVED_FROM_INTEGRATION_SOURCE"
    assert robustness.condition_count == 114
    assert robustness.total_condition_windows == 510264


# 8
def test_frozen_robustness_source_identity_is_unchanged() -> None:
    content = (REPOSITORY_ROOT / "results/ppg_dalia_fault_robustness.json").read_bytes()
    assert hashlib.sha256(content).hexdigest() == FROZEN_ROBUSTNESS_SHA256


# 9
def test_imu_calibration_caveat_survives(artifact) -> None:
    robustness = _component(artifact, "wrist_imu").robustness_evidence
    assert robustness is not None
    assert "first affected S14 batch" in robustness.imu_calibration_caveat
    assert "not proof of robustness to severe corruption" in robustness.imu_calibration_caveat


# 10
def test_packet_loss_interpretation_survives(artifact) -> None:
    robustness = _component(artifact, "wrist_imu").robustness_evidence
    assert robustness is not None
    assert "fail-closed input rejection" in robustness.packet_loss_interpretation
    assert "prediction availability" in robustness.packet_loss_interpretation


# 11
def test_scientific_benefit_and_robustness_are_separate(artifact) -> None:
    wrist = _component(artifact, "wrist_imu").model_dump(mode="json")
    assert "robustness_evidence" not in wrist["scientific_marginal_value"]
    assert "robustness_evidence" not in wrist["operational_cost"]
    assert wrist["robustness_evidence"]["clean_prediction_availability"] == 1.0


# 12
def test_no_universal_scalar_sensor_value_exists(artifact) -> None:
    keys = set(_all_keys(artifact.model_dump(mode="json")))
    assert "universal_sensor_score" not in keys
    assert "combined_mae_rmse_score" not in keys
    assert "weighted_score" not in keys


# 13
def test_no_rank_or_architecture_action_fields_exist(artifact) -> None:
    keys = set(_all_keys(artifact.model_dump(mode="json")))
    assert {"rank", "ranking", "keep", "remove", "winner", "pareto_frontier"}.isdisjoint(keys)


# 14
def test_readiness_reports_missing_dimensions_honestly(artifact) -> None:
    assert artifact.readiness.pareto_status == "NOT_READY"
    assert len(artifact.readiness.missing_requirements) == 7
    matrix = {item.component_id: item for item in artifact.readiness.component_matrix}
    assert matrix["wrist_imu"].power == "PARTIAL"
    assert matrix["wrist_imu"].mass == "MISSING"
    assert matrix["second_ppg_site"].contact_burden == "PARTIAL"
    assert matrix["second_ppg_site"].module_burden == "MISSING"


# 15
def test_integrated_artifact_serialization_is_deterministic() -> None:
    committed = json.loads((REPOSITORY_ROOT / DECISION_INPUTS_PATH).read_text())
    first = build_decision_inputs().model_dump(mode="json")
    second = build_decision_inputs().model_dump(mode="json")
    assert committed == first == second


def test_decision_input_api_is_read_only_and_source_verified() -> None:
    response = client.get("/research/decision-inputs")
    assert response.status_code == 200
    assert response.json()["availability"] == "available"
    assert response.json()["decision_inputs"]["readiness"]["pareto_status"] == "NOT_READY"
    assert client.post("/research/decision-inputs", json={}).status_code == 405


def test_missing_committed_artifact_fails_explicitly(tmp_path: Path) -> None:
    envelope = DecisionInputsReader(tmp_path).artifact()
    assert envelope.availability == ResearchAvailability.UNAVAILABLE
    assert envelope.decision_inputs is None
    assert envelope.error == "Decision-input artifact unavailable: results/pareto_decision_inputs.json"
