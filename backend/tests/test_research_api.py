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
    SLEEP_EDF_ABLATION_ID,
    ResearchCatalog,
    _build_sleep_supplementary_breakdowns,
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


def test_catalog_has_four_stable_experiment_identities() -> None:
    assert research_catalog.experiment_ids == (
        PPG_DALIA_ABLATION_ID,
        PPG_DALIA_ROBUSTNESS_ID,
        PTT_SITE_ABLATION_ID,
        SLEEP_EDF_ABLATION_ID,
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
    # Audit H5: the HEADLINE is now the capacity-controlled A_cap->B (~0.605 bpm),
    # NOT the uncontrolled single-seed A->B (~2.058 bpm). Delta stays in the
    # codebase candidate-baseline convention (negative = improvement).
    assert experiment.marginal_result.delta.mean == pytest.approx(-0.6053154945373536)
    assert experiment.marginal_result.direction.value == "improved"
    assert experiment.marginal_result.capacity_match_status.value == "matched"
    assert experiment.marginal_result.baseline_configuration_id == "model_a_cap"
    assert experiment.scope.held_out_subjects == ["S14", "S2", "S9"]


def test_ppg_dalia_controlled_comparisons_demote_historical() -> None:
    """Audit H5/M15: the old uncontrolled A->B survives only as a clearly labelled
    HISTORICAL_CAPACITY_CONFOUNDED_RESULT, and each comparison carries its own stats."""
    experiment = _experiment(PPG_DALIA_ABLATION_ID)
    mr = experiment.marginal_result
    assert mr is not None
    by_role = {c.role.value: c for c in mr.controlled_comparisons}
    assert set(by_role) == {
        "PRIMARY_CONTROLLED",
        "MATCHED_SHUFFLED_CONTROL",
        "HISTORICAL_CAPACITY_CONFOUNDED_RESULT",
    }
    primary = by_role["PRIMARY_CONTROLLED"]
    assert primary.delta.mean == pytest.approx(0.6053154945373536)  # baseline-candidate convention
    assert primary.n_seeds_favor_candidate == 5 and primary.n_seeds == 5
    shuffled = by_role["MATCHED_SHUFFLED_CONTROL"]
    assert shuffled.delta.mean == pytest.approx(0.7762914657592773)
    historical = by_role["HISTORICAL_CAPACITY_CONFOUNDED_RESULT"]
    # Historical is present but NOT the headline, and self-labels its confound.
    assert mr.headline_comparison_id == primary.comparison_id
    assert historical.comparison_id != mr.headline_comparison_id
    assert "capacity" in historical.interpretation.lower()


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
    assert summary_response.json()["available_count"] == 4
    assert summary_response.json()["unavailable_count"] == 0

    assert client.post("/research/experiments", json={}).status_code == 405
    assert client.get("/research/experiments/not-a-real-experiment").status_code == 404


def test_target_evidence_matrix_is_artifact_backed_and_multi_target_aware() -> None:
    response = client.get("/research/target-evidence-matrix")
    assert response.status_code == 200
    body = response.json()
    assert body["availability"] == "available"
    matrix = body["matrix"]
    # Three real experiments after Day-7 integration; Sleep-EDF is now REAL evidence.
    experiment_ids = {entry["experiment_id"] for entry in matrix["entries"]}
    assert experiment_ids == {
        "ppg-dalia-imu-ablation",
        "ptt-ppg-site-ablation",
        "sleep-edf-eeg-eog-ablation",
    }
    by_id = {entry["experiment_id"]: entry for entry in matrix["entries"]}
    # Capacity-confound and heterogeneity are represented.
    assert by_id["ppg-dalia-imu-ablation"]["capacity_match_status"] == "confounded"
    assert by_id["ptt-ppg-site-ablation"]["result_class"] == "heterogeneous_marginal_result"
    # PTT sensitivity artifact now exists -> available (was pending pre-integration).
    assert by_id["ptt-ppg-site-ablation"]["sensitivity_status"] == "available"
    # Sleep-EDF is a classification target, modestly positive, capacity-matched by design.
    assert by_id["sleep-edf-eeg-eog-ablation"]["metric_kind"] == "classification"
    assert by_id["sleep-edf-eeg-eog-ablation"]["result_class"] == "positive_marginal_value"
    assert by_id["sleep-edf-eeg-eog-ablation"]["capacity_match_status"] == "matched"
    assert "PROHIBITED" in matrix["cross_target_comparability"]
    # The three planned experiments are complete; nothing left awaiting.
    assert matrix["awaiting"] == []
    assert client.post("/research/target-evidence-matrix", json={}).status_code == 405


def test_research_models_do_not_contaminate_live_telemetry_schema() -> None:
    telemetry_fields = set(LiveMetricsSnapshot.model_fields)
    assert not telemetry_fields.intersection(
        {"research", "research_experiments", "research_summary", "marginal_result", "claim_boundaries"}
    )
    assert "research" not in json.dumps(LiveMetricsSnapshot.model_json_schema()).lower()


def test_secondary_class_level_missing_class_is_unknown_not_false() -> None:
    """A class absent from the frozen artifact must render `regresses: None`
    (unknown), never a fabricated `False` (audit-style hardening, §12 `or 0`
    sweep: the prior `(rec.get("B_minus_A") or 0) < 0` silently mapped a
    missing value to "does not regress")."""
    secondary = {
        "class_level_aggregate": {
            "Wake": {"B_minus_A": 0.02, "A_mean_f1": 0.8, "B_mean_f1": 0.82, "C_mean_f1": 0.79},
            "N3": {"B_minus_A": -0.043, "A_mean_f1": 0.7, "B_mean_f1": 0.657, "C_mean_f1": 0.69},
            # N1, N2, REM intentionally absent to simulate an incompletely regenerated artifact.
        }
    }
    breakdowns = _build_sleep_supplementary_breakdowns(control=None, persubj=None, secondary=secondary)
    class_level = next(b for b in breakdowns if b.breakdown_id == "secondary_class_level")
    by_label = {entry.label: entry for entry in class_level.entries}

    assert by_label["Wake"].dimensions["regresses"] is False
    assert by_label["N3"].dimensions["regresses"] is True
    for missing in ("N1", "N2", "REM"):
        assert by_label[missing].dimensions["b_minus_a"] is None
        assert by_label[missing].dimensions["regresses"] is None
