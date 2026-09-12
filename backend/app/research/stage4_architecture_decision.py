"""Read-only adapters for this closure-prep sprint's own generated artifacts
(Gate D assessment, candidate burden comparison, architecture decision
projection, Gate E options, final decision packet). Same discipline as
`app.research.stage4_engineering`: never caches, never recomputes, never
falls back to a stale value - each reader reports its own honest
unavailability if the frozen artifact is missing or fails schema projection.
"""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import ValidationError

from app.research.catalog import REPOSITORY_ROOT
from app.schemas.research import ResearchAvailability
from app.schemas.stage4_architecture_decision import (
    Stage4ArchitectureDecisionProjection,
    Stage4ArchitectureDecisionProjectionEnvelope,
    Stage4CandidateClassBurdenComparison,
    Stage4CandidateClassBurdenComparisonEnvelope,
    Stage4FinalArchitectureDecisionPacket,
    Stage4FinalArchitectureDecisionPacketEnvelope,
    Stage4GateDBurdenCompleteness,
    Stage4GateDBurdenCompletenessEnvelope,
    Stage4GateECoordinatorOptions,
    Stage4GateECoordinatorOptionsEnvelope,
)

GATE_D_PATH = "results/stage4_gate_d_burden_completeness.json"
CANDIDATE_BURDEN_COMPARISON_PATH = "results/stage4_candidate_class_burden_comparison.json"
DECISION_PROJECTION_PATH = "results/stage4_architecture_decision_projection.json"
GATE_E_PATH = "results/stage4_gate_e_coordinator_options.json"
FINAL_PACKET_PATH = "results/stage4_final_architecture_decision_packet.json"


def _read_json(root: Path, relative_path: str) -> tuple[dict | None, str | None]:
    path = root / relative_path
    if not path.is_file():
        return None, f"{relative_path} does not exist."
    try:
        return json.loads(path.read_text(encoding="utf-8")), None
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        return None, f"{relative_path} is malformed: {exc}"


class Stage4ArchitectureDecisionReader:
    def __init__(self, repository_root: str | Path = REPOSITORY_ROOT) -> None:
        self.repository_root = Path(repository_root).resolve()

    def gate_d_burden_completeness(self) -> Stage4GateDBurdenCompletenessEnvelope:
        raw, error = _read_json(self.repository_root, GATE_D_PATH)
        if error:
            return Stage4GateDBurdenCompletenessEnvelope(availability=ResearchAvailability.UNAVAILABLE, error=error)
        try:
            assessment = Stage4GateDBurdenCompleteness.model_validate(raw)
        except ValidationError as exc:
            return Stage4GateDBurdenCompletenessEnvelope(
                availability=ResearchAvailability.UNAVAILABLE, error=f"{GATE_D_PATH} failed schema projection: {exc}"
            )
        return Stage4GateDBurdenCompletenessEnvelope(availability=ResearchAvailability.AVAILABLE, assessment=assessment)

    def candidate_class_burden_comparison(self) -> Stage4CandidateClassBurdenComparisonEnvelope:
        raw, error = _read_json(self.repository_root, CANDIDATE_BURDEN_COMPARISON_PATH)
        if error:
            return Stage4CandidateClassBurdenComparisonEnvelope(availability=ResearchAvailability.UNAVAILABLE, error=error)
        try:
            comparison = Stage4CandidateClassBurdenComparison.model_validate(raw)
        except ValidationError as exc:
            return Stage4CandidateClassBurdenComparisonEnvelope(
                availability=ResearchAvailability.UNAVAILABLE,
                error=f"{CANDIDATE_BURDEN_COMPARISON_PATH} failed schema projection: {exc}",
            )
        return Stage4CandidateClassBurdenComparisonEnvelope(availability=ResearchAvailability.AVAILABLE, comparison=comparison)

    def architecture_decision_projection(self) -> Stage4ArchitectureDecisionProjectionEnvelope:
        raw, error = _read_json(self.repository_root, DECISION_PROJECTION_PATH)
        if error:
            return Stage4ArchitectureDecisionProjectionEnvelope(availability=ResearchAvailability.UNAVAILABLE, error=error)
        try:
            projection = Stage4ArchitectureDecisionProjection.model_validate(raw)
        except ValidationError as exc:
            return Stage4ArchitectureDecisionProjectionEnvelope(
                availability=ResearchAvailability.UNAVAILABLE, error=f"{DECISION_PROJECTION_PATH} failed schema projection: {exc}"
            )
        return Stage4ArchitectureDecisionProjectionEnvelope(availability=ResearchAvailability.AVAILABLE, projection=projection)

    def gate_e_coordinator_options(self) -> Stage4GateECoordinatorOptionsEnvelope:
        raw, error = _read_json(self.repository_root, GATE_E_PATH)
        if error:
            return Stage4GateECoordinatorOptionsEnvelope(availability=ResearchAvailability.UNAVAILABLE, error=error)
        try:
            options = Stage4GateECoordinatorOptions.model_validate(raw)
        except ValidationError as exc:
            return Stage4GateECoordinatorOptionsEnvelope(
                availability=ResearchAvailability.UNAVAILABLE, error=f"{GATE_E_PATH} failed schema projection: {exc}"
            )
        return Stage4GateECoordinatorOptionsEnvelope(availability=ResearchAvailability.AVAILABLE, options=options)

    def final_architecture_decision_packet(self) -> Stage4FinalArchitectureDecisionPacketEnvelope:
        raw, error = _read_json(self.repository_root, FINAL_PACKET_PATH)
        if error:
            return Stage4FinalArchitectureDecisionPacketEnvelope(availability=ResearchAvailability.UNAVAILABLE, error=error)
        try:
            packet = Stage4FinalArchitectureDecisionPacket.model_validate(raw)
        except ValidationError as exc:
            return Stage4FinalArchitectureDecisionPacketEnvelope(
                availability=ResearchAvailability.UNAVAILABLE, error=f"{FINAL_PACKET_PATH} failed schema projection: {exc}"
            )
        return Stage4FinalArchitectureDecisionPacketEnvelope(availability=ResearchAvailability.AVAILABLE, packet=packet)


stage4_architecture_decision = Stage4ArchitectureDecisionReader()
