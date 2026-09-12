"""Read-only adapters for the Stage-4 Final Architecture Closure sprint's own
generated artifacts (Gate E coordinator decisions, formal Pareto analysis,
final wearable architecture, final closure manifest). Same discipline as
`app.research.stage4_architecture_decision`: never caches, never
recomputes, never falls back to a stale value - each reader reports its own
honest unavailability if the frozen artifact is missing or fails schema
projection.
"""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import ValidationError

from app.research.catalog import REPOSITORY_ROOT
from app.schemas.research import ResearchAvailability
from app.schemas.stage4_final_architecture_closure import (
    FinalWearableArchitecture,
    FinalWearableArchitectureEnvelope,
    Stage4FinalClosureManifest,
    Stage4FinalClosureManifestEnvelope,
    Stage4FormalParetoAnalysis,
    Stage4FormalParetoAnalysisEnvelope,
    Stage4GateECoordinatorDecisions,
    Stage4GateECoordinatorDecisionsEnvelope,
)

GATE_E_DECISIONS_PATH = "results/stage4_gate_e_coordinator_decisions.json"
FORMAL_PARETO_PATH = "results/stage4_formal_pareto_analysis.json"
FINAL_ARCHITECTURE_PATH = "results/final_wearable_architecture.json"
FINAL_CLOSURE_MANIFEST_PATH = "results/stage4_final_closure_manifest.json"


def _read_json(root: Path, relative_path: str) -> tuple[dict | None, str | None]:
    path = root / relative_path
    if not path.is_file():
        return None, f"{relative_path} does not exist."
    try:
        return json.loads(path.read_text(encoding="utf-8")), None
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        return None, f"{relative_path} is malformed: {exc}"


class Stage4FinalArchitectureClosureReader:
    def __init__(self, repository_root: str | Path = REPOSITORY_ROOT) -> None:
        self.repository_root = Path(repository_root).resolve()

    def gate_e_coordinator_decisions(self) -> Stage4GateECoordinatorDecisionsEnvelope:
        raw, error = _read_json(self.repository_root, GATE_E_DECISIONS_PATH)
        if error:
            return Stage4GateECoordinatorDecisionsEnvelope(availability=ResearchAvailability.UNAVAILABLE, error=error)
        try:
            decisions = Stage4GateECoordinatorDecisions.model_validate(raw)
        except ValidationError as exc:
            return Stage4GateECoordinatorDecisionsEnvelope(
                availability=ResearchAvailability.UNAVAILABLE, error=f"{GATE_E_DECISIONS_PATH} failed schema projection: {exc}"
            )
        return Stage4GateECoordinatorDecisionsEnvelope(availability=ResearchAvailability.AVAILABLE, decisions=decisions)

    def formal_pareto_analysis(self) -> Stage4FormalParetoAnalysisEnvelope:
        raw, error = _read_json(self.repository_root, FORMAL_PARETO_PATH)
        if error:
            return Stage4FormalParetoAnalysisEnvelope(availability=ResearchAvailability.UNAVAILABLE, error=error)
        try:
            analysis = Stage4FormalParetoAnalysis.model_validate(raw)
        except ValidationError as exc:
            return Stage4FormalParetoAnalysisEnvelope(
                availability=ResearchAvailability.UNAVAILABLE, error=f"{FORMAL_PARETO_PATH} failed schema projection: {exc}"
            )
        return Stage4FormalParetoAnalysisEnvelope(availability=ResearchAvailability.AVAILABLE, analysis=analysis)

    def final_wearable_architecture(self) -> FinalWearableArchitectureEnvelope:
        raw, error = _read_json(self.repository_root, FINAL_ARCHITECTURE_PATH)
        if error:
            return FinalWearableArchitectureEnvelope(availability=ResearchAvailability.UNAVAILABLE, error=error)
        try:
            architecture = FinalWearableArchitecture.model_validate(raw)
        except ValidationError as exc:
            return FinalWearableArchitectureEnvelope(
                availability=ResearchAvailability.UNAVAILABLE, error=f"{FINAL_ARCHITECTURE_PATH} failed schema projection: {exc}"
            )
        return FinalWearableArchitectureEnvelope(availability=ResearchAvailability.AVAILABLE, architecture=architecture)

    def final_closure_manifest(self) -> Stage4FinalClosureManifestEnvelope:
        raw, error = _read_json(self.repository_root, FINAL_CLOSURE_MANIFEST_PATH)
        if error:
            return Stage4FinalClosureManifestEnvelope(availability=ResearchAvailability.UNAVAILABLE, error=error)
        try:
            manifest = Stage4FinalClosureManifest.model_validate(raw)
        except ValidationError as exc:
            return Stage4FinalClosureManifestEnvelope(
                availability=ResearchAvailability.UNAVAILABLE, error=f"{FINAL_CLOSURE_MANIFEST_PATH} failed schema projection: {exc}"
            )
        return Stage4FinalClosureManifestEnvelope(availability=ResearchAvailability.AVAILABLE, manifest=manifest)


stage4_final_architecture_closure = Stage4FinalArchitectureClosureReader()
