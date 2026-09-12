"""Day 6 physical-topology and Pareto-readiness contracts."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.operational_cost import HardwareIdentity, OperationMode
from app.schemas.research import ResearchAvailability


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class TopologyStatus(StrEnum):
    FROZEN_REFERENCE = "FROZEN_REFERENCE"
    OPEN_BOUNDARY = "OPEN_BOUNDARY"


class LocationStatus(StrEnum):
    """Whether a component's physical placement (and thus body-worn burden) is settled."""

    FROZEN = "FROZEN"
    LOCATION_UNRESOLVED = "LOCATION_UNRESOLVED"


class EvidenceConfidence(StrEnum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    OPEN = "OPEN"


class TargetEvidenceStatus(StrEnum):
    VALIDATED_POSITIVE = "VALIDATED_POSITIVE"
    VALIDATED_NEGATIVE = "VALIDATED_NEGATIVE"
    PARTIAL_EVIDENCE = "PARTIAL_EVIDENCE"
    CANDIDATE = "CANDIDATE"
    UNVALIDATED = "UNVALIDATED"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class TopologyModule(StrictModel):
    module_id: str
    label: str
    body_location: str
    worn_body: bool
    topology_status: TopologyStatus
    component_ids: list[str]
    shared_resources: list[str]
    notes: list[str] = Field(default_factory=list)


class ContactBurden(StrictModel):
    body_regions: list[str]
    contact_type: str
    new_contact_region_required: bool | None
    new_physical_sensing_site_required: bool | None
    physical_sensing_sites: int | None
    optical_interfaces: int | None
    dry_electrodes: int | None
    adhesive_or_wet_electrodes: int | None
    straps: int | None
    head_worn_hardware: bool
    external_cable_required: bool | None


class TopologyComponent(StrictModel):
    component_id: str
    label: str
    modality: str
    module_id: str
    location_status: LocationStatus = LocationStatus.FROZEN
    location_alternatives: list[str] = Field(default_factory=list)
    target_body_region: str
    physical_sensing_site: str
    operation_mode: OperationMode
    operating_schedule: str
    optionality: str
    contact_burden: ContactBurden
    required_afe: str
    required_mcu_or_interface: str
    shared_resources: list[str]
    new_module_required: bool | None
    hardware_identity: HardwareIdentity
    evidence_confidence: EvidenceConfidence
    unresolved_dependencies: list[str]


class TargetCoverageEntry(StrictModel):
    status: TargetEvidenceStatus
    evidence_ids: list[str] = Field(default_factory=list)
    note: str


class HardwareTopologyContract(StrictModel):
    schema_version: str
    topology_id: str
    title: str
    methodology_path: str
    reference_architecture_not_final_bom: bool
    stable_component_ids: list[str]
    modules: list[TopologyModule]
    components: list[TopologyComponent]
    target_coverage: dict[str, dict[str, TargetCoverageEntry]]
    global_unresolved_dependencies: list[str]


class ArchitectureResource(StrictModel):
    resource_id: str
    resource_type: str
    module_id: str
    allocation_status: str
    shared_by: list[str]
    double_count_prohibited: bool


class ArchitectureSignal(StrictModel):
    signal_id: str
    source_component_id: str
    destination: str
    interface: str
    target_ids: list[str]
    validation_status: str


class SystemArchitectureTopology(StrictModel):
    schema_version: str
    architecture_id: str
    source_topology_path: str
    modules: list[TopologyModule]
    resources: list[ArchitectureResource]
    signals: list[ArchitectureSignal]


class ReadinessStatus(StrEnum):
    AVAILABLE = "AVAILABLE"
    PARTIAL = "PARTIAL"
    MISSING = "MISSING"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class Day6ComponentReadiness(StrictModel):
    component_id: str
    scientific_benefit: ReadinessStatus
    target_coverage: ReadinessStatus
    component_power: ReadinessStatus
    average_power_and_energy: ReadinessStatus
    component_mass: ReadinessStatus
    finished_mass: ReadinessStatus
    physical_burden: ReadinessStatus
    compute_and_data: ReadinessStatus
    robustness_evidence: ReadinessStatus
    provenance: ReadinessStatus
    unresolved_dependencies: list[str]


class ParetoReadinessDay6(StrictModel):
    schema_version: str
    readiness_id: str
    topology_path: str
    operational_catalog_path: str
    decision_inputs_path: str
    global_pareto_ready: bool
    target_specific_pareto_ready: bool
    structural_assessment_available: bool
    formal_pareto_authorized: bool
    classification: str
    component_matrix: list[Day6ComponentReadiness]
    blockers: list[str]
    limited_structural_conclusion: str
    prohibited_inferences: list[str]


class HardwareTopologyEnvelope(StrictModel):
    availability: ResearchAvailability
    topology: HardwareTopologyContract | None = None
    system_architecture: SystemArchitectureTopology | None = None
    error: str | None = None


class ParetoReadinessDay6Envelope(StrictModel):
    availability: ResearchAvailability
    readiness: ParetoReadinessDay6 | None = None
    error: str | None = None
