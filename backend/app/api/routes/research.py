"""Read-only API for completed, frozen research experiments."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.research.catalog import research_catalog
from app.research.decision_inputs import decision_inputs
from app.research.day6 import day6_research
from app.research.engineering_readiness import engineering_readiness
from app.research.future_science_ingestion import future_science_manifest
from app.research.operational_costs import operational_cost_catalog
from app.schemas.decision_inputs import ParetoDecisionInputsEnvelope
from app.schemas.engineering_readiness import EngineeringReadinessEnvelope
from app.schemas.experiment_manifest import FutureScienceManifestEnvelope
from app.schemas.hardware_topology import HardwareTopologyEnvelope, ParetoReadinessDay6Envelope
from app.schemas.operational_cost import (
    OperationalCostCatalogEnvelope,
    OperationalCostComponentEnvelope,
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
