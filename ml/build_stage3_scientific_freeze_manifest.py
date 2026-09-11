#!/usr/bin/env python
"""Section 18-19 remediation: the Stage-3 scientific freeze manifest is
now GENERATED FROM results/stage3_governance_registry.json, not a
separately, manually maintained parallel truth. governing_artifacts and
historical_or_supporting_artifacts below are both derived directly from
the registry's per-family artifact statuses - there is no second,
independently-typed source of what counts as "governing" in this file.

Hashes line-ending-normalized content (CRLF->LF) so results are stable
across Windows/Linux/macOS checkouts, distinct from the raw-byte
checkpoint SHA256 hashes recorded elsewhere (checkpoints are binary and
must be hashed as raw bytes; every target here is text/JSON/Markdown)."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from ml.stage3_science_resolver import GOVERNING_STATUS, REGISTRY_PATH  # noqa: E402

OUT_PATH = REPO_ROOT / "results" / "stage3_scientific_freeze_manifest.json"

# Cross-cutting current-facing docs not tracked per-family in the
# governance registry (the registry covers RESULT artifacts; these are
# narrative/claim documents that must also be frozen and hash-stable).
CROSS_CUTTING_DOCS = [
    "docs/STAGE3_SAFE_UNSAFE_CLAIMS.md",
    "docs/STAGE3_HANDOFF_TO_EMIR_AND_INTEGRATION_OWNER.md",
    "docs/STAGE3_SCIENCE_COMPLETION_REPORT.md",
]


def sha256_of(path: Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def main() -> None:
    registry = json.loads(REGISTRY_PATH.read_text())

    governing_artifacts: dict[str, str] = {}
    historical_or_supporting_artifacts: dict[str, list[dict]] = {}
    all_tracked_paths: list[str] = [str(REGISTRY_PATH.relative_to(REPO_ROOT)).replace("\\", "/")]

    for family_id, fd in registry["families"].items():
        governing_for_family = [a for a in fd["artifacts"] for _ in [0] if a["status"] == GOVERNING_STATUS]
        if len(governing_for_family) == 1:
            governing_artifacts[family_id] = governing_for_family[0]["path"]
        elif len(governing_for_family) > 1:
            raise RuntimeError(f"Freeze build aborted: family '{family_id}' has {len(governing_for_family)} GOVERNING artifacts - ambiguous.")
        # else: family has zero GOVERNING artifacts (e.g. fully pending) - omitted from governing_artifacts, not an error here

        non_governing = [a for a in fd["artifacts"] if a["status"] != GOVERNING_STATUS]
        if non_governing:
            historical_or_supporting_artifacts[family_id] = non_governing

        for a in fd["artifacts"]:
            all_tracked_paths.append(a["path"])

    all_tracked_paths.extend(CROSS_CUTTING_DOCS)

    entries = []
    all_exist = True
    for rel in all_tracked_paths:
        path = REPO_ROOT / rel
        exists = path.exists()
        all_exist = all_exist and exists
        entries.append({
            "path": rel,
            "exists": exists,
            "hash_kind": "line_ending_normalized_sha256_of_text_content",
            "sha256": sha256_of(path) if exists else None,
        })

    manifest = {
        "purpose": (
            "Stage 3 scientific freeze manifest, GENERATED FROM "
            "results/stage3_governance_registry.json (Section 18-19 "
            "remediation) - not a separately maintained parallel truth. "
            "governing_artifacts and historical_or_supporting_artifacts "
            "below are both derived directly from the registry; this file "
            "does not independently decide what is governing."
        ),
        "source_of_truth": "results/stage3_governance_registry.json",
        "hash_semantics_note": (
            "All hashes here are computed on line-ending-normalized TEXT "
            "content (CRLF->LF), distinct from raw-byte SHA256 hashes used "
            "for binary checkpoint files - text hashes and checkpoint "
            "hashes are never comparable to each other and are never "
            "conflated in this repository's convention."
        ),
        "governing_artifacts": governing_artifacts,
        "historical_or_supporting_artifacts": historical_or_supporting_artifacts,
        "n_files": len(entries),
        "all_files_exist": all_exist,
        "entries": entries,
    }
    OUT_PATH.write_text(json.dumps(manifest, indent=2))
    print("Wrote", OUT_PATH, "-", len(entries), "files tracked,",
          len(governing_artifacts), "governing, all_exist:", all_exist)


if __name__ == "__main__":
    main()
