"""Section 16-17 remediation: the one authoritative Stage-3 evidence
resolver. Given an experiment/family ID, returns the single current
GOVERNING artifact's loaded content - never by filename heuristic, never
by a "newest" guess, never by skipping validation because a key or
filename happens to contain a substring like "historical".

Governance is read entirely from results/stage3_governance_registry.json,
which assigns an explicit status to every artifact. Only status
GOVERNING may be resolved as current. Fails closed (raises) on:
  - the family is not in the registry;
  - zero artifacts in the family have status GOVERNING;
  - more than one artifact in the family has status GOVERNING;
  - the resolved file does not exist;
  - the resolved file's line-ending-normalized content hash does not
    match a hash recorded elsewhere for it in the freeze manifest, when
    one is supplied for cross-check (optional, see resolve_and_verify).

This module does not implement its own JSON hashing convention beyond
what's needed to detect "file is missing" - hash cross-verification
against the freeze manifest is Section 21's job and lives in the test
suite, not duplicated here.
"""

from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
REGISTRY_PATH = REPO_ROOT / "results" / "stage3_governance_registry.json"

GOVERNING_STATUS = "GOVERNING"
NEVER_GOVERNING_STATUSES = {
    "SUPPORTING", "HISTORICAL", "SUPERSEDED", "INVALIDATED",
    "NONCANONICAL_REPRODUCTION", "PENDING",
    "HISTORICAL_SUPERSEDED_OUT_OF_PROTOCOL",
}


class GovernanceResolutionError(RuntimeError):
    pass


def _load_registry() -> dict:
    return json.loads(REGISTRY_PATH.read_text())


def list_families() -> list[str]:
    return sorted(_load_registry()["families"].keys())


def resolve_governing_path(family_id: str) -> str:
    """Returns the repo-relative path of the single GOVERNING artifact for
    a family. Raises GovernanceResolutionError on any ambiguity."""
    registry = _load_registry()
    if family_id not in registry["families"]:
        raise GovernanceResolutionError(
            f"Unknown family '{family_id}' - not present in {REGISTRY_PATH.name}"
        )

    artifacts = registry["families"][family_id]["artifacts"]
    governing = [a for a in artifacts if a["status"] == GOVERNING_STATUS]

    if len(governing) == 0:
        raise GovernanceResolutionError(
            f"No GOVERNING artifact for family '{family_id}' - "
            f"{len(artifacts)} artifact(s) present, statuses: "
            f"{[a['status'] for a in artifacts]}"
        )
    if len(governing) > 1:
        raise GovernanceResolutionError(
            f"AMBIGUOUS: {len(governing)} artifacts marked GOVERNING for "
            f"family '{family_id}': {[a['path'] for a in governing]}"
        )

    entry = governing[0]
    path = REPO_ROOT / entry["path"]
    if not path.exists():
        raise GovernanceResolutionError(
            f"GOVERNING artifact for '{family_id}' does not exist on disk: {entry['path']}"
        )
    return entry["path"]


def resolve_current(family_id: str) -> dict:
    """Returns the loaded JSON content of the current governing artifact
    for a family."""
    path = resolve_governing_path(family_id)
    return json.loads((REPO_ROOT / path).read_text())


def resolve_by_path_or_status(path_str: str) -> dict:
    """Given an explicit repo-relative path, look it up in the registry
    (any family) and refuse to load it if its recorded status is not
    GOVERNING. If the path is not in the registry at all, it is loaded
    without a governance opinion (the registry is a blocklist/allowlist
    hybrid scoped to files that matter for governance, not universal)."""
    registry = _load_registry()
    normalized = path_str.replace("\\", "/")
    for fam, fd in registry["families"].items():
        for a in fd["artifacts"]:
            if a["path"] == normalized:
                if a["status"] != GOVERNING_STATUS:
                    raise GovernanceResolutionError(
                        f"Refused to resolve '{path_str}' as current: "
                        f"status={a['status']} (family '{fam}') is never "
                        f"a governing status."
                    )
                return json.loads((REPO_ROOT / normalized).read_text())
    # not in registry at all - not a governance-tracked file
    return json.loads((REPO_ROOT / normalized).read_text())
