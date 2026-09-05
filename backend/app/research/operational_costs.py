"""Read-only adapter for the committed operational-cost catalog."""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import ValidationError

from app.research.catalog import REPOSITORY_ROOT, ResearchArtifactError
from app.schemas.operational_cost import (
    CostAvailability,
    OperationalCostCatalog,
    OperationalCostCatalogEnvelope,
    OperationalCostComponent,
    OperationalCostComponentEnvelope,
    ParetoReadyInput,
)
from app.schemas.research import ResearchAvailability

CATALOG_PATH = "results/operational_cost_catalog.json"
STABLE_COMPONENT_IDS = (
    "wrist_imu",
    "second_ppg_site",
    "wrist_ppg",
    "ecg_chest",
    "thoracic_bioz",
    "skin_temperature",
    "light_sensor",
    "frontal_eeg",
    "leg_bioz",
)


def _validate_catalog(catalog: OperationalCostCatalog) -> OperationalCostCatalog:
    component_ids = tuple(component.component_id for component in catalog.components)
    if component_ids != STABLE_COMPONENT_IDS:
        raise ResearchArtifactError(
            f"Operational-cost component IDs/order changed: expected {STABLE_COMPONENT_IDS}, found {component_ids}."
        )
    if catalog.scientific_join_contract.scientific_benefit is not None:
        raise ResearchArtifactError("Scientific benefit must remain unresolved until the reviewed contract is integrated.")

    evidence_ids = {item.evidence_id for item in catalog.evidence}
    if len(evidence_ids) != len(catalog.evidence):
        raise ResearchArtifactError("Operational-cost evidence IDs must be unique.")
    for evidence in catalog.evidence:
        if Path(evidence.source_reference).is_absolute():
            raise ResearchArtifactError(f"Machine-local evidence path is prohibited: {evidence.source_reference}")
        if evidence.source_url is not None:
            if not evidence.source_url.startswith("https://"):
                raise ResearchArtifactError(f"External evidence URL must use HTTPS: {evidence.evidence_id}")
            required_external = (
                evidence.manufacturer,
                evidence.retrieval_date,
                evidence.page_or_section,
                evidence.exact_parameters,
            )
            if not all(required_external):
                raise ResearchArtifactError(
                    f"External evidence lacks manufacturer/date/location/parameters: {evidence.evidence_id}"
                )

    for component in catalog.components:
        quantities = [component.duty_cycle, *component.dimensions.values()]
        hardware = component.hardware_characterization
        if hardware is not None:
            quantities.extend(
                [
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
            )
            missing_identity = set(hardware.identity.evidence_ids) - evidence_ids
            if missing_identity:
                raise ResearchArtifactError(
                    f"{component.component_id} identity references unknown evidence IDs: {sorted(missing_identity)}"
                )
        for quantity in quantities:
            if quantity.availability == CostAvailability.KNOWN:
                missing = set(quantity.provenance_ids) - evidence_ids
                if missing:
                    raise ResearchArtifactError(
                        f"{component.component_id} references unknown evidence IDs: {sorted(missing)}"
                    )
    mapped = {component.component_id: component for component in catalog.components}
    if mapped["wrist_imu"].scientific_experiment_ids != ["ppg-dalia-imu-ablation"]:
        raise ResearchArtifactError("wrist_imu scientific experiment mapping changed.")
    if mapped["second_ppg_site"].scientific_experiment_ids != ["ptt-ppg-site-ablation"]:
        raise ResearchArtifactError("second_ppg_site scientific experiment mapping changed.")
    return catalog


class OperationalCostCatalogReader:
    """Loads the source artifact on demand and never mutates or caches it."""

    def __init__(self, repository_root: str | Path = REPOSITORY_ROOT) -> None:
        self.repository_root = Path(repository_root).resolve()

    def _read(self) -> OperationalCostCatalog:
        path = self.repository_root / CATALOG_PATH
        if not path.is_file():
            raise ResearchArtifactError(f"Operational-cost catalog unavailable: {CATALOG_PATH}")
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
            catalog = OperationalCostCatalog.model_validate(raw)
        except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValidationError) as exc:
            raise ResearchArtifactError(f"Operational-cost catalog could not be read: {exc}") from exc
        return _validate_catalog(catalog)

    def catalog(self) -> OperationalCostCatalogEnvelope:
        try:
            catalog = self._read()
        except ResearchArtifactError as exc:
            return OperationalCostCatalogEnvelope(
                availability=ResearchAvailability.UNAVAILABLE,
                error=str(exc),
            )
        return OperationalCostCatalogEnvelope(
            availability=ResearchAvailability.AVAILABLE,
            catalog=catalog,
        )

    def get(self, component_id: str) -> OperationalCostComponentEnvelope:
        if component_id not in STABLE_COMPONENT_IDS:
            raise KeyError(component_id)
        envelope = self.catalog()
        if envelope.catalog is None:
            return OperationalCostComponentEnvelope(
                component_id=component_id,
                availability=ResearchAvailability.UNAVAILABLE,
                error=envelope.error,
            )
        component = next(item for item in envelope.catalog.components if item.component_id == component_id)
        return OperationalCostComponentEnvelope(
            component_id=component_id,
            availability=ResearchAvailability.AVAILABLE,
            component=component,
        )

    def pareto_ready_inputs(self) -> list[ParetoReadyInput]:
        """Expose unresolved join rows, never a Pareto computation."""
        envelope = self.catalog()
        if envelope.catalog is None:
            raise ResearchArtifactError(envelope.error or "Operational-cost catalog unavailable.")
        return [
            ParetoReadyInput(
                component_id=component.component_id,
                operational_cost_component_id=component.component_id,
                scientific_experiment_ids=component.scientific_experiment_ids,
                target="heart_rate" if component.scientific_experiment_ids else None,
                scientific_benefit=None,
                join_status=(
                    "awaiting_reviewed_scientific_contract"
                    if component.scientific_experiment_ids
                    else "no_scientific_contract_yet"
                ),
            )
            for component in envelope.catalog.components
        ]


operational_cost_catalog = OperationalCostCatalogReader()
