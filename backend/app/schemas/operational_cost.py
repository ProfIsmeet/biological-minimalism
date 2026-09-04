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


class SharedHardwareContext(StrictModel):
    shared_module_id: str | None
    integration_context: str
    incremental_vs_standalone: str
    allocation_status: str
    double_counting_risk: str
    naive_addition_allowed: bool = False


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
