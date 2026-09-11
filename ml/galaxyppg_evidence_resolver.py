"""Section 17 remediation: a resolver that refuses to consume any GalaxyPPG
artifact listed in results/galaxyppg_invalidated_evidence_registry.json as
current governing evidence. Any code path (future analysis scripts, report
builders) that wants to cite a GalaxyPPG result as current should route
through resolve_galaxyppg_evidence() rather than reading result files
directly, so an accidental reference to invalidated evidence fails loudly
instead of silently succeeding."""

from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
REGISTRY_PATH = REPO_ROOT / "results" / "galaxyppg_invalidated_evidence_registry.json"


class InvalidatedEvidenceError(RuntimeError):
    pass


def resolve_galaxyppg_evidence(path_or_experiment_id: str) -> dict:
    """Loads and returns a GalaxyPPG result JSON's content, raising
    InvalidatedEvidenceError if the path (relative to repo root) or its
    experiment_id is registered as invalidated. This is a fail-closed
    resolver: an unrecognized path is loaded normally (this registry is an
    explicit blocklist of known-bad evidence, not an allowlist), but any
    match against the invalidated registry always refuses."""
    registry = json.loads(REGISTRY_PATH.read_text())
    invalidated_paths = {e["path"] for e in registry["invalidated"]}
    invalidated_ids = {e["experiment_id"] for e in registry["invalidated"]}

    normalized = path_or_experiment_id.replace("\\", "/")
    if normalized in invalidated_paths or path_or_experiment_id in invalidated_ids:
        entry = next(
            e for e in registry["invalidated"]
            if e["path"] == normalized or e["experiment_id"] == path_or_experiment_id
        )
        raise InvalidatedEvidenceError(
            f"Refused to resolve '{path_or_experiment_id}' as current GalaxyPPG "
            f"evidence: status={entry['status']}, reason={entry['reason']}"
        )

    target_path = REPO_ROOT / normalized if not normalized.startswith("results/") else REPO_ROOT / normalized
    if not target_path.exists():
        target_path = REPO_ROOT / "results" / normalized
    data = json.loads(target_path.read_text())

    experiment_id = data.get("experiment_id")
    if experiment_id in invalidated_ids:
        entry = next(e for e in registry["invalidated"] if e["experiment_id"] == experiment_id)
        raise InvalidatedEvidenceError(
            f"Refused to resolve '{path_or_experiment_id}' (experiment_id="
            f"'{experiment_id}') as current GalaxyPPG evidence: "
            f"status={entry['status']}, reason={entry['reason']}"
        )
    return data
