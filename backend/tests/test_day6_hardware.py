"""Day 6 hardware topology, evidence, honesty, and readiness invariants."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app
from app.research.catalog import REPOSITORY_ROOT
from app.research.day6 import (
    STABLE_COMPONENT_IDS,
    TARGET_IDS,
    build_operational_catalog,
    build_readiness,
    build_system_architecture,
    build_topology,
    day6_research,
)
from app.research.operational_costs import operational_cost_catalog
from app.schemas.operational_cost import CostAvailability, CostEvidenceLevel, OperationalQuantity
from app.schemas.research import ResearchAvailability

client = TestClient(app)


def _catalog():
    envelope = operational_cost_catalog.catalog()
    assert envelope.availability == ResearchAvailability.AVAILABLE
    assert envelope.catalog is not None
    return envelope.catalog


def _topology():
    envelope = day6_research.topology()
    assert envelope.availability == ResearchAvailability.AVAILABLE
    assert envelope.topology is not None
    assert envelope.system_architecture is not None
    return envelope.topology, envelope.system_architecture


def _quantities(component) -> list[OperationalQuantity]:
    hardware = component.hardware_characterization
    assert hardware is not None
    return [
        component.duty_cycle,
        *component.dimensions.values(),
        hardware.power_energy.supply_voltage,
        hardware.power_energy.active_current,
        hardware.power_energy.active_power,
        hardware.power_energy.active_fraction,
        hardware.power_energy.average_power,
        hardware.power_energy.daily_energy,
        hardware.mass.component_mass,
        hardware.mass.pcb_or_module_incremental_mass,
        hardware.mass.finished_wearable_mass,
        hardware.data_rate.channel_count,
        hardware.data_rate.sample_rate,
        hardware.data_rate.bits_per_sample,
        hardware.data_rate.scalar_sample_throughput,
        hardware.data_rate.raw_payload_bit_rate,
        hardware.data_rate.protocol_overhead_bit_rate,
        hardware.compute_memory.baseline_model_weight_memory,
        hardware.compute_memory.candidate_model_weight_memory,
        hardware.compute_memory.incremental_model_weight_memory,
        hardware.compute_memory.baseline_input_buffer_memory,
        hardware.compute_memory.candidate_input_buffer_memory,
        hardware.compute_memory.incremental_input_buffer_memory,
        hardware.compute_memory.embedded_inference_latency,
    ]


def _all_keys(value):
    if isinstance(value, dict):
        for key, child in value.items():
            yield key
            yield from _all_keys(child)
    elif isinstance(value, list):
        for child in value:
            yield from _all_keys(child)


# 1
def test_every_component_has_stable_id() -> None:
    topology, _ = _topology()
    assert tuple(topology.stable_component_ids) == STABLE_COMPONENT_IDS
    assert tuple(item.component_id for item in topology.components) == STABLE_COMPONENT_IDS
    assert tuple(item.component_id for item in _catalog().components) == STABLE_COMPONENT_IDS


# 2–5
def test_quantity_units_evidence_external_provenance_and_unknown_nulls() -> None:
    catalog = _catalog()
    evidence = {item.evidence_id: item for item in catalog.evidence}
    for component in catalog.components:
        for quantity in _quantities(component):
            assert quantity.unit
            if quantity.availability == CostAvailability.KNOWN:
                assert quantity.evidence_level != CostEvidenceLevel.UNKNOWN
                assert quantity.provenance_ids
            else:
                assert quantity.value is None
                assert quantity.minimum is None
                assert quantity.typical is None
                assert quantity.maximum is None
        hardware = component.hardware_characterization
        assert hardware is not None
        for evidence_id in hardware.identity.evidence_ids:
            source = evidence[evidence_id]
            assert source.source_url and source.source_url.startswith("https://")
            assert source.manufacturer and source.retrieval_date and source.page_or_section
            assert source.exact_parameters


# 6
def test_numeric_zero_only_represents_verified_structural_zero() -> None:
    for component in _catalog().components:
        for quantity in _quantities(component):
            if quantity.availability == CostAvailability.KNOWN and quantity.value == 0:
                assert quantity.evidence_level == CostEvidenceLevel.ARCHITECTURAL_COUNT


# 7
def test_sensor_ic_power_never_becomes_total_wearable_power() -> None:
    payload = _catalog().model_dump(mode="json")
    assert "total_wearable_power" not in set(_all_keys(payload))
    for component in _catalog().components:
        hardware = component.hardware_characterization
        assert hardware is not None
        assert hardware.power_energy.boundary != "total_wearable"
        assert "battery" in hardware.power_energy.excluded_subsystems


# 8
def test_daily_energy_requires_explicit_frozen_schedule() -> None:
    for component in _catalog().components:
        hardware = component.hardware_characterization
        assert hardware is not None
        if hardware.power_energy.daily_energy.availability == CostAvailability.KNOWN:
            assert hardware.power_energy.duty_cycle_status == "frozen"
            assert hardware.power_energy.duty_cycle_assumption
            assert any("24" in equation for equation in hardware.power_energy.equations)


# 9
def test_shared_hardware_is_allocated_once() -> None:
    _, system = _topology()
    resource_ids = [item.resource_id for item in system.resources]
    assert len(resource_ids) == len(set(resource_ids))
    assert all(item.double_count_prohibited for item in system.resources)
    assert all(not item.shared_hardware.naive_addition_allowed for item in _catalog().components)


# 10–11
def test_wrist_imu_and_second_ppg_physical_sites_are_honest() -> None:
    topology, _ = _topology()
    mapped = {item.component_id: item for item in topology.components}
    assert mapped["wrist_imu"].module_id == "wrist_module"
    assert mapped["wrist_imu"].new_module_required is False
    assert mapped["wrist_imu"].contact_burden.new_physical_sensing_site_required is False
    assert mapped["wrist_imu"].contact_burden.physical_sensing_sites == 0
    assert mapped["second_ppg_site"].contact_burden.new_physical_sensing_site_required is True
    assert mapped["second_ppg_site"].contact_burden.physical_sensing_sites == 1
    assert mapped["second_ppg_site"].new_module_required is None


# 12
def test_mass_boundaries_are_distinct_and_unfabricated() -> None:
    for component in _catalog().components:
        mass = component.hardware_characterization.mass  # type: ignore[union-attr]
        assert {mass.component_mass.unit, mass.pcb_or_module_incremental_mass.unit, mass.finished_wearable_mass.unit} == {"g"}
        assert "package dimensions are not component mass" in mass.component_mass.notes[0]
        assert "PCB" in mass.pcb_or_module_incremental_mass.notes[0]
        assert "Enclosure" in mass.finished_wearable_mass.notes[0]
        assert all(quantity.availability == CostAvailability.UNKNOWN for quantity in (mass.component_mass, mass.pcb_or_module_incremental_mass, mass.finished_wearable_mass))


# 13
def test_desktop_latency_is_not_embedded_latency() -> None:
    for component in _catalog().components:
        latency = component.hardware_characterization.compute_memory.embedded_inference_latency  # type: ignore[union-attr]
        assert latency.availability == CostAvailability.UNKNOWN
        assert latency.value is None


# 14
def test_data_rate_equations_are_deterministic() -> None:
    expected = {"wrist_ppg": 1216, "wrist_imu": 1536, "skin_temperature": 16, "ecg_chest": 12000, "frontal_eeg": 24000, "second_ppg_site": 28500}
    for component in _catalog().components:
        data = component.hardware_characterization.data_rate  # type: ignore[union-attr]
        if component.component_id in expected:
            assert data.raw_payload_bit_rate.value == expected[component.component_id]
            assert data.raw_payload_bit_rate.value == data.channel_count.value * data.sample_rate.value * data.bits_per_sample.value  # type: ignore[operator]
            assert data.equation == "raw_payload_bit_rate = channels × sample_rate × bits_per_sample"


# 15
def test_target_matrix_does_not_inflate_validation() -> None:
    topology, _ = _topology()
    assert all(tuple(rows) == TARGET_IDS for rows in topology.target_coverage.values())
    validated = {(component, target, cell.status) for component, rows in topology.target_coverage.items() for target, cell in rows.items() if cell.status.startswith("VALIDATED")}
    assert validated == {("wrist_imu", "heart_rate", "VALIDATED_POSITIVE"), ("second_ppg_site", "heart_rate", "VALIDATED_NEGATIVE")}


# 16–17
def test_final_decision_rule_exists_without_fabricated_outcome() -> None:
    rule = (REPOSITORY_ROOT / "docs/FINAL_ARCHITECTURE_DECISION_RULE.md").read_text()
    assert "frozen before any final component outcome" in rule
    assert "No final retain/remove outcome is applied" in rule
    keys = set(_all_keys(build_readiness().model_dump(mode="json")))
    assert {"winner", "selected_architecture", "retain", "remove"}.isdisjoint(keys)


# 18
def test_pareto_readiness_is_deterministic() -> None:
    assert build_readiness().model_dump(mode="json") == build_readiness().model_dump(mode="json")
    readiness = build_readiness()
    assert not readiness.global_pareto_ready
    assert not readiness.target_specific_pareto_ready
    assert not readiness.formal_pareto_authorized
    assert readiness.structural_assessment_available


# 19–20
def test_no_universal_score_or_cross_dataset_raw_ranking() -> None:
    payloads = [build_topology().model_dump(mode="json"), build_readiness().model_dump(mode="json")]
    keys = {key for payload in payloads for key in _all_keys(payload)}
    assert {"score", "weighted_score", "universal_sensor_score", "ranking", "pareto_frontier"}.isdisjoint(keys)
    decision = json.loads((REPOSITORY_ROOT / "results/pareto_decision_inputs.json").read_text())
    assert "not comparable ranking coordinates" in decision["readiness"]["cross_dataset_restriction"]


# 21
def test_frozen_source_hashes_remain_unchanged() -> None:
    expected = {
        "results/ppg_dalia_fault_robustness.json": "c40397fb0bb43b4f4a778aac4a4e0ba72b7b0387cab1aabec1e0708cc2912dcb",
        "docs/PHASE5_ROBUSTNESS_AUDIT_ADDENDUM.md": "dc2f33355a3aad65e4eafb6148254549c48d3f93b4ff1d943ba8826baf13e194",
    }
    for relative_path, digest in expected.items():
        assert hashlib.sha256((REPOSITORY_ROOT / relative_path).read_bytes()).hexdigest() == digest


# 22
def test_json_outputs_match_deterministic_builders() -> None:
    topology = build_topology()
    assert json.loads((REPOSITORY_ROOT / "results/hardware_topology_contract.json").read_text()) == topology.model_dump(mode="json")
    assert json.loads((REPOSITORY_ROOT / "results/system_architecture_topology.json").read_text()) == build_system_architecture(topology).model_dump(mode="json")
    assert json.loads((REPOSITORY_ROOT / "results/pareto_readiness_day6.json").read_text()) == build_readiness().model_dump(mode="json")
    raw_catalog = json.loads((REPOSITORY_ROOT / "results/operational_cost_catalog.json").read_text())
    assert build_operational_catalog(raw_catalog).model_dump(mode="json") == raw_catalog


# 23
def test_day6_research_apis_are_read_only() -> None:
    topology = client.get("/research/hardware-topology")
    readiness = client.get("/research/pareto-readiness")
    assert topology.status_code == 200 and topology.json()["availability"] == "available"
    assert readiness.status_code == 200 and readiness.json()["readiness"]["formal_pareto_authorized"] is False
    for path in ("/research/hardware-topology", "/research/pareto-readiness"):
        assert client.post(path, json={}).status_code == 405
        assert client.patch(path, json={}).status_code == 405
