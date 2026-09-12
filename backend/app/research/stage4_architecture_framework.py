"""Reader for the second, parallel Science Owner Stage-4 package - the
architecture decision framework (`stage4-architecture-decision-framework @
fa71eec`). Same pattern as `app.research.stage4_science_manifest`: these
artifacts are static, Science-Owner-curated, and read verbatim - no
recomputation, no reinterpretation of tiers/sensitivity/gates/classes.
"""

from __future__ import annotations

import json

from app.research.catalog import REPOSITORY_ROOT
from app.schemas.stage4_architecture_framework import (
    Stage4ArchitectureAcceptanceGates,
    Stage4ArchitectureCandidateClasses,
    Stage4ArchitectureScienceDecisionFramework,
    Stage4ScientificParetoInputs,
    Stage4SensorDecisionSensitivity,
)

DECISION_FRAMEWORK_PATH = "results/stage4_architecture_science_decision_framework.json"
SENSOR_DECISION_SENSITIVITY_PATH = "results/stage4_sensor_decision_sensitivity.json"
SCIENTIFIC_PARETO_INPUTS_PATH = "results/stage4_scientific_pareto_inputs.json"
ACCEPTANCE_GATES_PATH = "results/stage4_architecture_acceptance_gates.json"
CANDIDATE_CLASSES_PATH = "results/stage4_architecture_candidate_classes.json"


def _load(path: str) -> dict:
    return json.loads((REPOSITORY_ROOT / path).read_text())


def get_architecture_science_decision_framework() -> Stage4ArchitectureScienceDecisionFramework:
    return Stage4ArchitectureScienceDecisionFramework.model_validate(_load(DECISION_FRAMEWORK_PATH))


def get_sensor_decision_sensitivity() -> Stage4SensorDecisionSensitivity:
    return Stage4SensorDecisionSensitivity.model_validate(_load(SENSOR_DECISION_SENSITIVITY_PATH))


def get_scientific_pareto_inputs() -> Stage4ScientificParetoInputs:
    return Stage4ScientificParetoInputs.model_validate(_load(SCIENTIFIC_PARETO_INPUTS_PATH))


def get_architecture_acceptance_gates() -> Stage4ArchitectureAcceptanceGates:
    return Stage4ArchitectureAcceptanceGates.model_validate(_load(ACCEPTANCE_GATES_PATH))


def get_architecture_candidate_classes() -> Stage4ArchitectureCandidateClasses:
    return Stage4ArchitectureCandidateClasses.model_validate(_load(CANDIDATE_CLASSES_PATH))
