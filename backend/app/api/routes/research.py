"""Read-only API for completed, frozen research experiments."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.research.catalog import research_catalog
from app.research.decision_inputs import decision_inputs
from app.research.operational_costs import operational_cost_catalog
from app.schemas.decision_inputs import ParetoDecisionInputsEnvelope
from app.schemas.operational_cost import (
    OperationalCostCatalogEnvelope,
    OperationalCostComponentEnvelope,
)
from app.schemas.research import (
    ResearchExperimentEnvelope,
    ResearchExperimentSummaryEnvelope,
    ResearchProjectSummary,
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
