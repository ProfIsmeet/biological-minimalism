"""Research Mode serves frozen artifacts without entering live telemetry state."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.research.catalog import (
    PPG_DALIA_ABLATION_ID,
    PPG_DALIA_ROBUSTNESS_ID,
    PTT_SITE_ABLATION_ID,
    ResearchCatalog,
    research_catalog,
)
from app.schemas.research import ResearchAvailability
from app.schemas.telemetry import LiveMetricsSnapshot

client = TestClient(app)


def _experiment(experiment_id: str):
    envelope = research_catalog.get(experiment_id)
    assert envelope.availability == ResearchAvailability.AVAILABLE
    assert envelope.error is None
    assert envelope.experiment is not None
    return envelope.experiment


def test_catalog_has_three_stable_experiment_identities() -> None:
    assert research_catalog.experiment_ids == (
        PPG_DALIA_ABLATION_ID,
        PPG_DALIA_ROBUSTNESS_ID,
        PTT_SITE_ABLATION_ID,
    )
    assert all(item.availability == ResearchAvailability.AVAILABLE for item in research_catalog.list())


def test_ppg_dalia_marginal_result_preserves_exact_artifact_values() -> None:
    experiment = _experiment(PPG_DALIA_ABLATION_ID)
    metrics = {configuration.configuration_id: configuration.metrics for configuration in experiment.configurations}

    assert experiment.dataset == "PPG-DaLiA"
    assert experiment.target == "Heart rate"
    assert metrics["model_a_ppg_only"]["mae"].mean == pytest.approx(9.090062141418457)
    assert metrics["model_b_ppg_plus_imu"]["mae"].mean == pytest.approx(7.031700611114502)
    assert metrics["model_c_ppg_plus_shuffled_imu"]["mae"].mean == pytest.approx(7.956958293914795)
    assert experiment.marginal_result is not None
    assert experiment.marginal_result.delta.mean == pytest.approx(-2.058361530303955)
    assert experiment.marginal_result.direction.value == "improved"
    assert experiment.scope.held_out_subjects == ["S14", "S2", "S9"]


def test_ptt_negative_result_preserves_exact_values_and_direction() -> None:
    experiment = _experiment(PTT_SITE_ABLATION_ID)
    metrics = {configuration.configuration_id: configuration.metrics for configuration in experiment.configurations}

    assert experiment.dataset == "PhysioNet Pulse Transit Time PPG Dataset v1.1.0"
    assert experiment.target == "ECG-referenced heart rate"
    assert metrics["model_a"]["mae"].mean == pytest.approx(17.540314865112304)
    assert metrics["model_b"]["mae"].mean == pytest.approx(19.002723693847656)
    assert experiment.marginal_result is not None
    assert experiment.marginal_result.delta.mean == pytest.approx(1.4624088287353516)
    assert experiment.marginal_result.delta.sd == pytest.approx(0.7875715821800415)
    assert experiment.marginal_result.direction.value == "worsened"
    assert experiment.marginal_result.candidate_worsened_count == 5
    assert experiment.scope.held_out_subjects == ["s2", "s9", "s14", "s20"]


def test_robustness_keeps_availability_separate_from_undefined_accuracy() -> None:
    experiment = _experiment(PPG_DALIA_ROBUSTNESS_ID)
    condition_breakdown = next(item for item in experiment.breakdowns if item.breakdown_id == "fault_conditions")
    aggregate_breakdown = next(
        item for item in experiment.breakdowns if item.breakdown_id == "stochastic_fault_aggregates"
    )
    unavailable = next(
        entry
        for entry in condition_breakdown.entries
        if entry.configuration_metrics["canonical_pipeline"]["availability"].mean == 0
    )
    unavailable_metrics = unavailable.configuration_metrics["canonical_pipeline"]

    assert experiment.dataset == "PPG-DaLiA"
    assert experiment.target == "Heart rate"
    assert experiment.configurations[0].metrics["mae"].mean == pytest.approx(5.0838541984558105)
    assert len(condition_breakdown.entries) == 114
    assert len(aggregate_breakdown.entries) == 20
    assert unavailable_metrics["mae"].mean is None
    assert unavailable_metrics["rmse"].mean is None
    assert unavailable_metrics["availability"].mean == 0


def test_claim_boundaries_serialize_and_provenance_is_repository_relative() -> None:
    for experiment_id in research_catalog.experiment_ids:
        experiment = _experiment(experiment_id)
        serialized = experiment.model_dump(mode="json")
        assert serialized["claim_boundaries"]["supported"]
        assert serialized["claim_boundaries"]["unsupported"]
        assert serialized["claim_boundaries"]["limitations"]
        provenance = experiment.provenance
        paths = [provenance.source_artifact, *provenance.supporting_artifacts]
        assert paths
        assert all(not Path(path).is_absolute() for path in paths)
        assert all("checkpoint_path" not in item for item in serialized["provenance"]["checkpoints"])


def test_missing_and_malformed_artifacts_are_explicitly_unavailable(tmp_path: Path) -> None:
    catalog = ResearchCatalog(tmp_path)
    missing = catalog.get(PPG_DALIA_ABLATION_ID)
    assert missing.availability == ResearchAvailability.UNAVAILABLE
    assert missing.experiment is None
    assert missing.error == "Research artifact unavailable: results/ppg_dalia_imu_ablation.json"

    results = tmp_path / "results"
    results.mkdir()
    (results / "ppg_dalia_imu_ablation.json").write_text("not-json", encoding="utf-8")
    malformed = catalog.get(PPG_DALIA_ABLATION_ID)
    assert malformed.availability == ResearchAvailability.UNAVAILABLE
    assert malformed.experiment is None
    assert malformed.error is not None
    assert "could not be read" in malformed.error


def test_research_routes_are_read_only_and_report_unknown_ids() -> None:
    list_response = client.get("/research/experiments")
    assert list_response.status_code == 200
    assert [item["experiment_id"] for item in list_response.json()] == list(research_catalog.experiment_ids)

    detail_response = client.get(f"/research/experiments/{PTT_SITE_ABLATION_ID}")
    assert detail_response.status_code == 200
    assert detail_response.json()["experiment"]["result_class"] == "negative_marginal_result"

    summary_response = client.get("/research/summary")
    assert summary_response.status_code == 200
    assert summary_response.json()["available_count"] == 3
    assert summary_response.json()["unavailable_count"] == 0

    assert client.post("/research/experiments", json={}).status_code == 405
    assert client.get("/research/experiments/not-a-real-experiment").status_code == 404


def test_target_evidence_matrix_is_artifact_backed_and_multi_target_aware() -> None:
    response = client.get("/research/target-evidence-matrix")
    assert response.status_code == 200
    body = response.json()
    assert body["availability"] == "available"
    matrix = body["matrix"]
    # Only the two real experiments; Sleep-EDF/EOG must NOT be fabricated.
    experiment_ids = {entry["experiment_id"] for entry in matrix["entries"]}
    assert experiment_ids == {"ppg-dalia-imu-ablation", "ptt-ppg-site-ablation"}
    by_id = {entry["experiment_id"]: entry for entry in matrix["entries"]}
    # Capacity-confound and heterogeneity are represented.
    assert by_id["ppg-dalia-imu-ablation"]["capacity_match_status"] == "confounded"
    assert by_id["ptt-ppg-site-ablation"]["result_class"] == "heterogeneous_marginal_result"
    assert by_id["ptt-ppg-site-ablation"]["sensitivity_status"] == "pending"
    assert "PROHIBITED" in matrix["cross_target_comparability"]
    # Awaiting list names the not-yet-produced classification target.
    assert any("Sleep-EDF" in item for item in matrix["awaiting"])
    assert client.post("/research/target-evidence-matrix", json={}).status_code == 405


def test_research_models_do_not_contaminate_live_telemetry_schema() -> None:
    telemetry_fields = set(LiveMetricsSnapshot.model_fields)
    assert not telemetry_fields.intersection(
        {"research", "research_experiments", "research_summary", "marginal_result", "claim_boundaries"}
    )
    assert "research" not in json.dumps(LiveMetricsSnapshot.model_json_schema()).lower()
