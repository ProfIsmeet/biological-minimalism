"""Read-only API for completed, frozen research experiments."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.research.catalog import research_catalog
from app.research.decision_inputs import decision_inputs
from app.research.day6 import day6_research
from app.research.engineering_readiness import engineering_readiness
from app.research.future_science_ingestion import future_science_manifest
from app.research.operational_costs import operational_cost_catalog
from app.research.stage3_evidence import (
    Stage3EvidenceUnavailable,
    get_stage3_evidence_entry,
    get_stage3_evidence_envelope,
)
from app.research.stage4_engineering import stage4_engineering_readiness
from app.research.stage4_science_manifest import (
    Stage4ScienceManifestDrift,
    get_architecture_decision_inputs_science,
    get_science_claim_ledger,
    get_science_consumption_manifest,
    get_sensor_value_matrix,
)
from app.schemas.decision_inputs import ParetoDecisionInputsEnvelope
from app.schemas.engineering_readiness import EngineeringReadinessEnvelope
from app.schemas.experiment_manifest import FutureScienceManifestEnvelope
from app.schemas.hardware_topology import HardwareTopologyEnvelope, ParetoReadinessDay6Envelope
from app.schemas.operational_cost import (
    OperationalCostCatalogEnvelope,
    OperationalCostComponentEnvelope,
)
from app.schemas.stage3_evidence import Stage3EvidenceEntry, Stage3EvidenceEnvelope
from app.schemas.stage4_engineering import Stage4EngineeringReadinessEnvelope
from app.schemas.stage4_science_manifest import (
    Stage4ArchitectureDecisionInputsScience,
    Stage4ScienceClaimLedger,
    Stage4ScienceConsumptionManifest,
    Stage4SensorValueMatrix,
)
from app.schemas.research import (
    ResearchExperimentEnvelope,
    ResearchExperimentSummaryEnvelope,
    ResearchProjectSummary,
    TargetEvidenceMatrixEnvelope,
)

router = APIRouter()


@router.get(
    "/experiments",
    response_model=list[ResearchExperimentSummaryEnvelope],
    summary="List completed research experiments and artifact availability",
)
def list_research_experiments() -> list[ResearchExperimentSummaryEnvelope]:
    return research_catalog.list()


@router.get(
    "/experiments/{experiment_id}",
    response_model=ResearchExperimentEnvelope,
    summary="Read one canonical research experiment",
)
def get_research_experiment(experiment_id: str) -> ResearchExperimentEnvelope:
    try:
        return research_catalog.get(experiment_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"Unknown research experiment {experiment_id!r}.") from exc


@router.get(
    "/summary",
    response_model=ResearchProjectSummary,
    summary="Project-level status of committed research evidence",
)
def get_research_summary() -> ResearchProjectSummary:
    return research_catalog.summary()


@router.get(
    "/target-evidence-matrix",
    response_model=TargetEvidenceMatrixEnvelope,
    summary="Target-specific evidence matrix (multi-target, capacity & heterogeneity aware)",
)
def get_target_evidence_matrix() -> TargetEvidenceMatrixEnvelope:
    return research_catalog.target_evidence_matrix()


@router.get(
    "/operational-costs",
    response_model=OperationalCostCatalogEnvelope,
    summary="Read the provenance-bearing operational-cost catalog",
)
def get_operational_cost_catalog() -> OperationalCostCatalogEnvelope:
    return operational_cost_catalog.catalog()


@router.get(
    "/operational-costs/{component_id}",
    response_model=OperationalCostComponentEnvelope,
    summary="Read one operational-cost component",
)
def get_operational_cost_component(component_id: str) -> OperationalCostComponentEnvelope:
    try:
        return operational_cost_catalog.get(component_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"Unknown operational-cost component {component_id!r}.") from exc


@router.get(
    "/decision-inputs",
    response_model=ParetoDecisionInputsEnvelope,
    summary="Read reviewed scientific and operational decision inputs",
)
def get_decision_inputs() -> ParetoDecisionInputsEnvelope:
    return decision_inputs.artifact()


@router.get(
    "/hardware-topology",
    response_model=HardwareTopologyEnvelope,
    summary="Read the frozen Day 6 hardware reference topology",
)
def get_hardware_topology() -> HardwareTopologyEnvelope:
    return day6_research.topology()


@router.get(
    "/pareto-readiness",
    response_model=ParetoReadinessDay6Envelope,
    summary="Read the Day 6 Pareto-readiness audit",
)
def get_pareto_readiness() -> ParetoReadinessDay6Envelope:
    return day6_research.readiness()


@router.get(
    "/engineering-readiness",
    response_model=EngineeringReadinessEnvelope,
    summary="Read the Day 11 engineering-readiness summary (power/mass/BOM/data-rate/architecture)",
)
def get_engineering_readiness() -> EngineeringReadinessEnvelope:
    return engineering_readiness.artifact()


@router.get(
    "/future-science-manifest",
    response_model=FutureScienceManifestEnvelope,
    summary=(
        "Read the future Ismet science-completion manifest, if any. Reports "
        "PENDING_SCIENCE_HANDOFF (not a 404 or a fabricated result) until Ismet's "
        "in-progress science-completion sprint produces one; fails closed with a "
        "typed error code if a manifest is present but malformed/invalid."
    ),
)
def get_future_science_manifest() -> FutureScienceManifestEnvelope:
    return future_science_manifest.status()


@router.get(
    "/stage4-engineering-readiness",
    response_model=Stage4EngineeringReadinessEnvelope,
    summary=(
        "Read the Stage 4 engineering-readiness summary — advances Day 11 Part-2 "
        "power/data-rate/mass/BOM from NOT_READY toward PARTIAL_READY using explicit, "
        "separately-labeled engineering assumptions. Not a final architecture or BOM."
    ),
)
def get_stage4_engineering_readiness() -> Stage4EngineeringReadinessEnvelope:
    return stage4_engineering_readiness.artifact()


@router.get(
    "/stage3-evidence",
    response_model=Stage3EvidenceEnvelope,
    summary=(
        "Read all 21 Stage-3 accepted governing-science families, resolved live "
        "through the integrity-verified resolver (registry + semantic + hash "
        "checks). Fails closed (503) rather than returning stale/unverified "
        "content if any family's governance cannot be independently verified."
    ),
)
def get_stage3_evidence() -> Stage3EvidenceEnvelope:
    try:
        return get_stage3_evidence_envelope()
    except Stage3EvidenceUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.get(
    "/stage3-evidence/{family_id}",
    response_model=Stage3EvidenceEntry,
    summary="Read one Stage-3 accepted governing-science family by resolver family_id.",
)
def get_stage3_evidence_family(family_id: str) -> Stage3EvidenceEntry:
    try:
        return get_stage3_evidence_entry(family_id)
    except Stage3EvidenceUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.get(
    "/stage4-science-manifest",
    response_model=Stage4ScienceConsumptionManifest,
    summary=(
        "Read the Science Owner's Stage-4 science consumption manifest — the "
        "AUTHORITATIVE per-family safe-claim/classification surface, cross-"
        "verified against the live resolver on every read. Fails closed (503) "
        "if the frozen manifest disagrees with current governance."
    ),
)
def get_stage4_science_manifest() -> Stage4ScienceConsumptionManifest:
    try:
        return get_science_consumption_manifest()
    except Stage4ScienceManifestDrift as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.get(
    "/stage4-sensor-value-matrix",
    response_model=Stage4SensorValueMatrix,
    summary="Read the Science Owner's Stage-4 sensor-value decision-input matrix (architecture_implication tiers, never KEEP/REMOVE).",
)
def get_stage4_sensor_value_matrix() -> Stage4SensorValueMatrix:
    return get_sensor_value_matrix()


@router.get(
    "/stage4-science-claims",
    response_model=Stage4ScienceClaimLedger,
    summary="Read the Science Owner's Stage-4 claim ledger — exact safe wording and prohibited stronger wording per claim area.",
)
def get_stage4_science_claims() -> Stage4ScienceClaimLedger:
    return get_science_claim_ledger()


@router.get(
    "/stage4-architecture-decision-inputs-science",
    response_model=Stage4ArchitectureDecisionInputsScience,
    summary="Read the Science Owner's Stage-4 architecture decision inputs (analysis inputs only — architecture selection remains a Project Coordinator decision).",
)
def get_stage4_architecture_decision_inputs_science() -> Stage4ArchitectureDecisionInputsScience:
    return get_architecture_decision_inputs_science()
