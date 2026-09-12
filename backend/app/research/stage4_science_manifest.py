"""Reader for Ismet's (Science Owner) Stage-4 science handoff package.

Unlike `app.research.stage3_evidence` (which re-resolves raw governing
artifacts on every call), these four artifacts are already static,
Science-Owner-curated summaries - built once by reading every number
through the resolver, then frozen for consumption (same pattern as
`app.research.decision_inputs`/`operational_costs`). Integration Owner
reads them directly, but independently re-verifies that each family's
`governing_artifact` still matches what the live resolver reports as
governing - defense-in-depth against silent drift between when Ismet
built this package and whenever Stage-4 code reads it.
"""

from __future__ import annotations

import json
import sys

from app.research.catalog import REPOSITORY_ROOT
from app.schemas.stage4_science_manifest import (
    Stage4ArchitectureDecisionInputsScience,
    Stage4ScienceClaimLedger,
    Stage4ScienceConsumptionManifest,
    Stage4SensorValueMatrix,
)

if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from ml.stage3_science_resolver import GovernanceResolutionError, resolve_governing_path  # noqa: E402

CONSUMPTION_MANIFEST_PATH = "results/stage4_science_consumption_manifest.json"
SENSOR_VALUE_MATRIX_PATH = "results/stage4_scientific_sensor_value_matrix.json"
CLAIM_LEDGER_PATH = "results/stage4_science_claim_ledger.json"
ARCHITECTURE_DECISION_INPUTS_PATH = "results/stage4_architecture_decision_inputs_science.json"


class Stage4ScienceManifestDrift(RuntimeError):
    """Raised when the frozen science package disagrees with the live
    resolver about which artifact governs a family - fail closed rather
    than serve a manifest that may have been built against a stale/
    since-corrected registry state."""


def _load(path: str) -> dict:
    return json.loads((REPOSITORY_ROOT / path).read_text())


def get_science_consumption_manifest() -> Stage4ScienceConsumptionManifest:
    raw = _load(CONSUMPTION_MANIFEST_PATH)
    manifest = Stage4ScienceConsumptionManifest.model_validate(raw)
    for family in manifest.families:
        try:
            live_path = resolve_governing_path(family.family_id)
        except GovernanceResolutionError as exc:
            raise Stage4ScienceManifestDrift(
                f"Family '{family.family_id}' in the science consumption manifest no "
                f"longer resolves live: {exc}"
            ) from exc
        if live_path != family.governing_artifact:
            raise Stage4ScienceManifestDrift(
                f"Family '{family.family_id}' governing artifact drift: manifest says "
                f"'{family.governing_artifact}', live resolver says '{live_path}'."
            )
    return manifest


def get_sensor_value_matrix() -> Stage4SensorValueMatrix:
    return Stage4SensorValueMatrix.model_validate(_load(SENSOR_VALUE_MATRIX_PATH))


def get_science_claim_ledger() -> Stage4ScienceClaimLedger:
    return Stage4ScienceClaimLedger.model_validate(_load(CLAIM_LEDGER_PATH))


def get_architecture_decision_inputs_science() -> Stage4ArchitectureDecisionInputsScience:
    return Stage4ArchitectureDecisionInputsScience.model_validate(_load(ARCHITECTURE_DECISION_INPUTS_PATH))
