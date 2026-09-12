"""Typed, non-scalar operational-cost contract for candidate sensing components."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.schemas.research import ResearchAvailability


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class CostEvidenceLevel(StrEnum):
    MEASURED = "measured"
    MANUFACTURER_SPEC = "manufacturer_spec"
    LITERATURE_ESTIMATE = "literature_estimate"
    DERIVED = "derived"
    ARCHITECTURAL_COUNT = "architectural_count"
    # An acquisition/duty schedule that is an engineering or experiment-reference
    # assumption, NOT a quantity derived or measured from a datasheet. A 100%
    # ("continuous") acquisition schedule is a reference-schedule assumption, not a
    # datasheet-derived duty cycle.
    ENGINEERING_ASSUMPTION = "engineering_assumption"
    REFERENCE_SCHEDULE = "reference_schedule"
    UNKNOWN = "unknown"


class CostAvailability(StrEnum):
    KNOWN = "known"
    UNKNOWN = "unknown"


class CostValueKind(StrEnum):
    EXACT = "exact"
    RANGE = "range"


class CostBasis(StrEnum):
    MARGINAL = "marginal"
    TOTAL = "total"


class OperationMode(StrEnum):
    CONTINUOUS = "continuous"
    PERIODIC = "periodic"
    INTERMITTENT = "intermittent"
    EVENT_DRIVEN = "event_driven"
    UNRESOLVED = "unresolved"


class HardwareIdentityStatus(StrEnum):
    REPRESENTATIVE_CANDIDATE = "representative_candidate"
    REPRESENTATIVE_COMPONENT_CLASS = "representative_component_class"
    OPEN = "open"


class DutyCycleStatus(StrEnum):
    FROZEN = "frozen"
    OPEN = "open"


class PowerBoundary(StrEnum):
    INCREMENTAL_SENSOR_IC = "incremental_sensor_ic"
    INCREMENTAL_AFE = "incremental_afe"
    INCREMENTAL_COMPONENT_CLASS = "incremental_component_class"
    UNQUANTIFIED = "unquantified"


class ComponentStatus(StrEnum):
    SCIENTIFICALLY_MAPPED = "scientifically_mapped"
    ARCHITECTURE_PLACEHOLDER = "architecture_placeholder"


class ComponentCategory(StrEnum):
    WEARABLE = "wearable"
    CABIN_CONTEXT = "cabin_context"


class OperationalQuantity(StrictModel):
    """One separately preserved cost dimension; unknown never means zero."""

    availability: CostAvailability
    value_kind: CostValueKind
    value: float | None = None
    minimum: float | None = None
    typical: float | None = None
    maximum: float | None = None
    unit: str
    basis: CostBasis
    evidence_level: CostEvidenceLevel
    provenance_ids: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_known_unknown_contract(self) -> "OperationalQuantity":
        values = (self.value, self.minimum, self.typical, self.maximum)
        if self.availability == CostAvailability.UNKNOWN:
            if any(item is not None for item in values):
                raise ValueError("unknown operational quantities cannot contain numeric values")
            if self.evidence_level != CostEvidenceLevel.UNKNOWN:
                raise ValueError("unknown operational quantities must use the unknown evidence level")
            if self.provenance_ids:
                raise ValueError("unknown operational quantities cannot cite numeric provenance")
            return self
        if self.evidence_level == CostEvidenceLevel.UNKNOWN:
            raise ValueError("known operational quantities require a non-unknown evidence level")
        if not self.provenance_ids:
            raise ValueError("known operational quantities require provenance")
        if self.value_kind == CostValueKind.EXACT:
            if self.value is None or any(item is not None for item in values[1:]):
                raise ValueError("exact operational quantities require only value")
        elif self.value is not None or all(item is None for item in values[1:]):
            raise ValueError("range operational quantities require min/typical/max fields and no exact value")
        range_values = [item for item in values[1:] if item is not None]
        if range_values != sorted(range_values):
            raise ValueError("range values must be ordered minimum <= typical <= maximum")
        return self


class CostEvidenceRecord(StrictModel):
    evidence_id: str
    evidence_level: CostEvidenceLevel
    title: str
    source_reference: str
    component_or_artifact_identity: str
    operating_condition: str
    value_characterization: str
    version_or_date: str | None = None
    assumptions: list[str] = Field(default_factory=list)
    manufacturer: str | None = None
    source_url: str | None = None
    retrieval_date: str | None = None
    page_or_section: str | None = None
    exact_parameters: list[str] = Field(default_factory=list)


class SharedHardwareContext(StrictModel):
    shared_module_id: str | None
    integration_context: str
    incremental_vs_standalone: str
    allocation_status: str
    double_counting_risk: str
    naive_addition_allowed: bool = False


class HardwareIdentity(StrictModel):
    manufacturer: str | None
    part_number_or_class: str | None
    device_class: str
    status: HardwareIdentityStatus
    rationale: str
    evidence_ids: list[str] = Field(default_factory=list)
    exclusions: list[str] = Field(default_factory=list)


class PowerEnergyCharacterization(StrictModel):
    boundary: PowerBoundary
    operating_condition: str
    duty_cycle_status: DutyCycleStatus
    duty_cycle_assumption: str
    supply_voltage: OperationalQuantity
    active_current: OperationalQuantity
    active_power: OperationalQuantity
    active_fraction: OperationalQuantity
    average_power: OperationalQuantity
    daily_energy: OperationalQuantity
    equations: list[str]
    excluded_subsystems: list[str]


class MassCharacterization(StrictModel):
    component_mass: OperationalQuantity
    pcb_or_module_incremental_mass: OperationalQuantity
    finished_wearable_mass: OperationalQuantity


class DataRateCharacterization(StrictModel):
    channel_count: OperationalQuantity
    sample_rate: OperationalQuantity
    bits_per_sample: OperationalQuantity
    scalar_sample_throughput: OperationalQuantity
    raw_payload_bit_rate: OperationalQuantity
    protocol_overhead_bit_rate: OperationalQuantity
    equation: str | None
    notes: list[str] = Field(default_factory=list)


class ComputeMemoryCharacterization(StrictModel):
    dtype: str | None
    bytes_per_value: int | None
    input_tensor_shapes: list[str] = Field(default_factory=list)
    baseline_model_weight_memory: OperationalQuantity
    candidate_model_weight_memory: OperationalQuantity
    incremental_model_weight_memory: OperationalQuantity
    baseline_input_buffer_memory: OperationalQuantity
    candidate_input_buffer_memory: OperationalQuantity
    incremental_input_buffer_memory: OperationalQuantity
    embedded_inference_latency: OperationalQuantity
    notes: list[str] = Field(default_factory=list)


class HardwareCharacterization(StrictModel):
    topology_component_id: str
    identity: HardwareIdentity
    required_afe: str
    host_interface: str
    host_mcu_status: str
    power_energy: PowerEnergyCharacterization
    mass: MassCharacterization
    data_rate: DataRateCharacterization
    compute_memory: ComputeMemoryCharacterization
    unresolved_dependencies: list[str] = Field(default_factory=list)


class OperationalCostComponent(StrictModel):
    component_id: str
    label: str
    status: ComponentStatus
    category: ComponentCategory
    sensing_modality: str
    channels: list[str]
    physical_site: str
    architecture_role: str
    operation_mode: OperationMode
    duty_cycle: OperationalQuantity
    experimental_sensor_identity: str | None
    candidate_hardware_identity: str | None
    scientific_experiment_ids: list[str] = Field(default_factory=list)
    dimensions: dict[str, OperationalQuantity]
    operational_burden_proxies: list[str] = Field(default_factory=list)
    reliability_exposure: list[str] = Field(default_factory=list)
    shared_hardware: SharedHardwareContext
    assumptions: list[str] = Field(default_factory=list)
    unknowns: list[str] = Field(default_factory=list)
    hardware_characterization: HardwareCharacterization | None = None


class CatalogRevision(StrictModel):
    schema_version: str
    source_commit: str
    source_sha256: str
    change_summary: str


class ScientificJoinContract(StrictModel):
    join_key: str
    expected_scientific_fields: list[str]
    cost_contract_status: str
    scientific_contract_status: str
    scientific_benefit: None = None
    allowed_future_outputs: list[str]
    prohibited_current_outputs: list[str]


class OperationalCostCatalog(StrictModel):
    schema_version: str
    catalog_id: str
    title: str
    methodology_path: str
    generated_from_commit: str
    evidence: list[CostEvidenceRecord]
    components: list[OperationalCostComponent]
    scientific_join_contract: ScientificJoinContract
    hardware_topology_path: str | None = None
    revision_history: list[CatalogRevision] = Field(default_factory=list)


class OperationalCostCatalogEnvelope(StrictModel):
    availability: ResearchAvailability
    catalog: OperationalCostCatalog | None = None
    error: str | None = None


class OperationalCostComponentEnvelope(StrictModel):
    component_id: str
    availability: ResearchAvailability
    component: OperationalCostComponent | None = None
    error: str | None = None


class ParetoReadyInput(StrictModel):
    """Unresolved join row. It deliberately contains no dominance or ranking output."""

    component_id: str
    operational_cost_component_id: str
    scientific_experiment_ids: list[str]
    target: str | None
    scientific_benefit: None = None
    join_status: str
