"""Section 16-17 remediation (extended this sprint for Gate 3 closure):
the one authoritative Stage-3 evidence resolver.

Given an experiment/family ID, returns the single current GOVERNING
artifact's loaded content - never by filename heuristic, never by a
"newest" guess, never by trusting the registry's GOVERNING label alone.

TWO INDEPENDENT CHECKS must both pass before an artifact is treated as
current:
  1. Registry check: exactly one artifact in the family has registry
     status GOVERNING.
  2. Semantic content check: that artifact's OWN machine-readable content
     is re-read live and checked for forbidden markers (HISTORICAL,
     SUPERSEDED, INVALIDATED, NONCANONICAL, PENDING, OUT_OF_PROTOCOL,
     SUPPORTING/SUPPORTING_ONLY) in the field the registry's
     artifact_status_contract names for that artifact (status_field), or
     in the registry-asserted artifact_semantic_status fallback when the
     artifact has no natural status-bearing field.

This defends against the specific attack of flipping ONE registry status
label to GOVERNING without the underlying artifact supporting that claim:
even if someone edits the registry to mark the old, superseded LBNP
result as the sole GOVERNING entry, that file's own 'status' field still
says HISTORICAL_SUPERSEDED_OUT_OF_PROTOCOL, and resolution fails.

resolve_and_verify() additionally cross-checks the resolved file's
line-ending-normalized content hash against the frozen hash recorded in
results/stage3_scientific_freeze_manifest.json, failing closed on any
mismatch (a governing file modified after the freeze was generated).
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
REGISTRY_PATH = REPO_ROOT / "results" / "stage3_governance_registry.json"
FREEZE_PATH = REPO_ROOT / "results" / "stage3_scientific_freeze_manifest.json"

GOVERNING_STATUS = "GOVERNING"
NEVER_GOVERNING_STATUSES = {
    "SUPPORTING", "HISTORICAL", "SUPERSEDED", "INVALIDATED",
    "NONCANONICAL_REPRODUCTION", "PENDING",
    "HISTORICAL_SUPERSEDED_OUT_OF_PROTOCOL",
}


class GovernanceResolutionError(RuntimeError):
    pass


class IntegrityVerificationError(RuntimeError):
    pass


def _load_registry() -> dict:
    return json.loads(REGISTRY_PATH.read_text())


def _forbidden_markers() -> list[str]:
    return _load_registry()["artifact_status_contract"]["forbidden_semantic_markers"]


def _sha256_of(path: Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def list_families() -> list[str]:
    return sorted(_load_registry()["families"].keys())


def _semantic_check(entry: dict, loaded_content: dict | None) -> None:
    """Independently re-checks an artifact's own content for forbidden
    semantic markers, using the field the registry names for it (or the
    registry-asserted fallback if the artifact has no natural field).
    Raises GovernanceResolutionError on any forbidden marker found."""
    markers = _forbidden_markers()
    status_field = entry.get("status_field")
    path = entry["path"]

    if status_field:
        if loaded_content is None or status_field not in loaded_content:
            raise GovernanceResolutionError(
                f"Semantic validation failed for '{path}': declared "
                f"status_field '{status_field}' is missing from the "
                f"artifact's own content - cannot independently verify "
                f"governance eligibility."
            )
        live_value = str(loaded_content[status_field])
        for marker in markers:
            if marker in live_value:
                raise GovernanceResolutionError(
                    f"Semantic validation failed for '{path}': its own "
                    f"'{status_field}' field says {live_value!r}, which "
                    f"contains the forbidden marker '{marker}' - this "
                    f"artifact cannot be governing regardless of its "
                    f"registry status label."
                )
        return

    # No natural status field - fall back to the registry-asserted value,
    # explicitly weaker (disclosed, never silently treated as equivalent).
    asserted = entry.get("artifact_semantic_status")
    if asserted is None:
        raise GovernanceResolutionError(
            f"Semantic validation failed for '{path}': no status_field and "
            f"no artifact_semantic_status fallback declared - registry "
            f"entry is incomplete per the artifact_status_contract."
        )
    for marker in markers:
        if marker in asserted:
            raise GovernanceResolutionError(
                f"Semantic validation failed for '{path}': registry-"
                f"asserted artifact_semantic_status {asserted!r} contains "
                f"the forbidden marker '{marker}'."
            )


def resolve_governing_path(family_id: str) -> str:
    """Returns the repo-relative path of the single GOVERNING artifact for
    a family, after both the registry check and the independent semantic
    content check pass. Raises GovernanceResolutionError on any ambiguity
    or semantic contradiction."""
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

    is_markdown = registry["families"][family_id].get("artifact_type") == "markdown"
    loaded_content = None
    if not is_markdown:
        try:
            loaded_content = json.loads(path.read_text())
        except json.JSONDecodeError as e:
            raise GovernanceResolutionError(f"GOVERNING artifact '{entry['path']}' is not valid JSON: {e}")

    _semantic_check(entry, loaded_content)

    return entry["path"]


def resolve_current(family_id: str) -> dict:
    """Returns the loaded JSON content of the current governing artifact
    for a family (JSON families only - markdown families should use
    resolve_governing_path + Path.read_text)."""
    path = resolve_governing_path(family_id)
    return json.loads((REPO_ROOT / path).read_text())


def resolve_and_verify(family_id: str) -> dict:
    """Full governance + integrity resolution:
      1. resolve exactly one governing artifact (registry + semantic check);
      2. confirm the path exists (done inside resolve_governing_path);
      3. locate its frozen integrity record in the freeze manifest;
      4. recompute the line-ending-normalized hash;
      5. compare to the frozen hash;
      6. fail closed (IntegrityVerificationError) on mismatch or missing
         freeze entry;
      7. only then return the loaded artifact content (or, for markdown
         families, {"path": ..., "text": ...}).
    """
    path = resolve_governing_path(family_id)
    full_path = REPO_ROOT / path

    freeze = json.loads(FREEZE_PATH.read_text())
    entry = next((e for e in freeze["entries"] if e["path"] == path), None)
    if entry is None:
        raise IntegrityVerificationError(
            f"No freeze-manifest entry found for governing artifact '{path}' "
            f"- cannot verify integrity. Regenerate the freeze manifest."
        )

    live_hash = _sha256_of(full_path)
    if live_hash != entry["sha256"]:
        raise IntegrityVerificationError(
            f"HASH_MISMATCH for '{path}': live hash {live_hash} != frozen "
            f"hash {entry['sha256']} - this governing artifact was modified "
            f"after the freeze was generated. Refusing to resolve."
        )

    registry = _load_registry()
    is_markdown = registry["families"][family_id].get("artifact_type") == "markdown"
    if is_markdown:
        return {"path": path, "text": full_path.read_text()}
    return json.loads(full_path.read_text())


def resolve_by_path_or_status(path_str: str) -> dict:
    """Given an explicit repo-relative path, look it up in the registry
    (any family) and refuse to load it if its recorded status is not
    GOVERNING, or if it fails the independent semantic content check. If
    the path is not in the registry at all, it is loaded without a
    governance opinion."""
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
                is_markdown = fd.get("artifact_type") == "markdown"
                loaded = None
                if not is_markdown:
                    loaded = json.loads((REPO_ROOT / normalized).read_text())
                _semantic_check(a, loaded)
                return loaded if loaded is not None else {"path": normalized}
    return json.loads((REPO_ROOT / normalized).read_text())
