"""Operational-cost contract invariants and read-only API coverage."""

from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app
from app.research.operational_costs import (
    STABLE_COMPONENT_IDS,
    OperationalCostCatalogReader,
    operational_cost_catalog,
)
from app.schemas.operational_cost import (
    CostAvailability,
    CostBasis,
    CostEvidenceLevel,
    CostValueKind,
    OperationalQuantity,
)
from app.schemas.research import ResearchAvailability
from app.schemas.telemetry import LiveMetricsSnapshot

client = TestClient(app)


def _catalog():
    envelope = operational_cost_catalog.catalog()
    assert envelope.availability == ResearchAvailability.AVAILABLE
    assert envelope.error is None
    assert envelope.catalog is not None
    return envelope.catalog


def _component(component_id: str):
    return next(item for item in _catalog().components if item.component_id == component_id)


def test_catalog_parses_and_component_ids_are_stable() -> None:
    catalog = _catalog()
    assert tuple(item.component_id for item in catalog.components) == STABLE_COMPONENT_IDS
    assert catalog.catalog_id == "biological-minimalism-operational-cost-v1"
    assert catalog.schema_version == "1.0.0"


def test_unknown_numeric_values_remain_null_never_zero() -> None:
    for component in _catalog().components:
        for quantity in [component.duty_cycle, *component.dimensions.values()]:
            if quantity.availability == CostAvailability.UNKNOWN:
                assert quantity.value is None
                assert quantity.minimum is None
                assert quantity.typical is None
                assert quantity.maximum is None
                assert quantity.evidence_level == CostEvidenceLevel.UNKNOWN


def test_evidence_levels_units_and_provenance_survive_serialization() -> None:
    catalog = _catalog()
    serialized = catalog.model_dump(mode="json")
    wrist = next(item for item in serialized["components"] if item["component_id"] == "wrist_imu")
    throughput = wrist["dimensions"]["raw_sample_throughput_added"]
    assert throughput["value"] == 96
    assert throughput["unit"] == "scalar_samples_per_second"
    assert throughput["evidence_level"] == "derived"
    assert throughput["provenance_ids"] == ["ppg_dalia_window_parameters"]


def test_range_contract_is_not_statistical_uncertainty() -> None:
    quantity = OperationalQuantity(
        availability=CostAvailability.KNOWN,
        value_kind=CostValueKind.RANGE,
        minimum=1.0,
        typical=2.0,
        maximum=3.0,
        unit="mW",
        basis=CostBasis.MARGINAL,
        evidence_level=CostEvidenceLevel.MANUFACTURER_SPEC,
        provenance_ids=["example-datasheet"],
        notes=["Engineering operating range; not a confidence interval."],
    )
    serialized = quantity.model_dump(mode="json")
    assert serialized["minimum"] == 1.0
    assert serialized["typical"] == 2.0
    assert serialized["maximum"] == 3.0
    assert "sd" not in serialized and "confidence" not in serialized


def test_marginal_and_total_compute_costs_remain_distinct() -> None:
    wrist = _component("wrist_imu")
    assert wrist.dimensions["baseline_model_parameters"].basis == CostBasis.TOTAL
    assert wrist.dimensions["baseline_model_parameters"].value == 8065
    assert wrist.dimensions["candidate_model_parameters"].basis == CostBasis.TOTAL
    assert wrist.dimensions["candidate_model_parameters"].value == 29089
    assert wrist.dimensions["incremental_model_parameters"].basis == CostBasis.MARGINAL
    assert wrist.dimensions["incremental_model_parameters"].value == 21024


def test_shared_hardware_forbids_naive_addition() -> None:
    for component in _catalog().components:
        assert component.shared_hardware.naive_addition_allowed is False
        assert component.shared_hardware.double_counting_risk


def test_wrist_imu_does_not_invent_a_new_contact_region() -> None:
    wrist = _component("wrist_imu")
    contact = wrist.dimensions["contact_regions_added"]
    assert contact.availability == CostAvailability.KNOWN
    assert contact.value == 0
    assert contact.evidence_level == CostEvidenceLevel.ARCHITECTURAL_COUNT
    assert wrist.shared_hardware.shared_module_id == "wrist_module"


def test_second_ppg_site_is_an_added_site_not_an_assumed_module() -> None:
    second_site = _component("second_ppg_site")
    assert second_site.dimensions["physical_sensing_sites_added"].value == 1
    assert second_site.dimensions["optical_contact_sites_added"].value == 1
    assert second_site.dimensions["contact_regions_added"].value is None
    assert second_site.dimensions["additional_module_count"].value is None


def test_no_score_frontier_dominance_or_rank_output_is_generated() -> None:
    serialized = _catalog().model_dump(mode="json")

    def keys(value):
        if isinstance(value, dict):
            yield from value.keys()
            for child in value.values():
                yield from keys(child)
        elif isinstance(value, list):
            for child in value:
                yield from keys(child)

    forbidden = {"score", "weighted_score", "ranking", "rank", "dominance", "pareto_frontier"}
    assert forbidden.isdisjoint(set(keys(serialized)))


def test_scientific_benefit_is_unresolved_and_mappings_are_exact() -> None:
    catalog = _catalog()
    assert catalog.scientific_join_contract.scientific_benefit is None
    assert _component("wrist_imu").scientific_experiment_ids == ["ppg-dalia-imu-ablation"]
    assert _component("second_ppg_site").scientific_experiment_ids == ["ptt-ppg-site-ablation"]
    assert all(item.scientific_benefit is None for item in operational_cost_catalog.pareto_ready_inputs())


def test_all_populated_numbers_have_evidence_and_paths_are_not_machine_local() -> None:
    catalog = _catalog()
    evidence_ids = {item.evidence_id for item in catalog.evidence}
    assert all(not Path(item.source_reference).is_absolute() for item in catalog.evidence)
    for component in catalog.components:
        for quantity in [component.duty_cycle, *component.dimensions.values()]:
            if quantity.availability == CostAvailability.KNOWN:
                assert quantity.provenance_ids
                assert set(quantity.provenance_ids) <= evidence_ids


def test_missing_and_malformed_catalog_fail_explicitly(tmp_path: Path) -> None:
    reader = OperationalCostCatalogReader(tmp_path)
    missing = reader.catalog()
    assert missing.availability == ResearchAvailability.UNAVAILABLE
    assert missing.catalog is None
    assert missing.error == "Operational-cost catalog unavailable: results/operational_cost_catalog.json"

    results = tmp_path / "results"
    results.mkdir()
    (results / "operational_cost_catalog.json").write_text("not-json", encoding="utf-8")
    malformed = reader.catalog()
    assert malformed.availability == ResearchAvailability.UNAVAILABLE
    assert malformed.catalog is None
    assert malformed.error is not None and "could not be read" in malformed.error


def test_catalog_serialization_is_deterministic() -> None:
    first = operational_cost_catalog.catalog().catalog
    second = operational_cost_catalog.catalog().catalog
    assert first is not None and second is not None
    assert first.model_dump_json() == second.model_dump_json()
    json.loads(first.model_dump_json())


def test_operational_cost_api_is_read_only() -> None:
    catalog_response = client.get("/research/operational-costs")
    assert catalog_response.status_code == 200
    assert catalog_response.json()["availability"] == "available"

    detail_response = client.get("/research/operational-costs/wrist_imu")
    assert detail_response.status_code == 200
    assert detail_response.json()["component"]["component_id"] == "wrist_imu"

    decision_response = client.get("/research/decision-inputs")
    assert decision_response.status_code == 200
    assert all(item["scientific_benefit"] is None for item in decision_response.json())

    assert client.get("/research/operational-costs/not-real").status_code == 404
    assert client.post("/research/operational-costs", json={}).status_code == 405
    assert client.patch("/research/operational-costs/wrist_imu", json={}).status_code == 405


def test_operational_costs_do_not_contaminate_live_telemetry() -> None:
    fields = set(LiveMetricsSnapshot.model_fields)
    assert not fields.intersection({"operational_costs", "cost_catalog", "decision_inputs", "scientific_benefit"})
