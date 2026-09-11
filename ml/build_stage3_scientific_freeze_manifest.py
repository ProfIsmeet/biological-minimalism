#!/usr/bin/env python
"""Section 18-19 remediation (extended this sprint for Gate 4 closure):
the Stage-3 scientific freeze manifest is GENERATED FROM
results/stage3_governance_registry.json - there is no second,
independently maintained current-artifact list, and no manually appended
"cross-cutting docs" list. Every current-facing document (claims ledger,
handoff, architecture evidence, sensor-value matrix, completion manifest)
is now its own governed registry family.

HARD FAILURE (raises, does not silently skip) if any registry family has
zero or more than one GOVERNING artifact - the prior version silently
omitted a family with zero governing artifacts from governing_artifacts,
which is itself a fail-open bug for a system whose entire purpose is
fail-closed governance.

Hashes line-ending-normalized content (CRLF->LF) so results are stable
across Windows/Linux/macOS checkouts, distinct from the raw-byte
checkpoint SHA256 hashes recorded elsewhere."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from ml.stage3_science_resolver import GOVERNING_STATUS, REGISTRY_PATH  # noqa: E402

OUT_PATH = REPO_ROOT / "results" / "stage3_scientific_freeze_manifest.json"


class FreezeBuildError(RuntimeError):
    pass


def sha256_of(path: Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def main() -> None:
    registry = json.loads(REGISTRY_PATH.read_text())
    required_families = sorted(registry["families"].keys())

    governing_artifacts: dict[str, str] = {}
    historical_or_supporting_artifacts: dict[str, list[dict]] = {}
    all_tracked_paths: list[str] = []
    try:
        all_tracked_paths.append(str(REGISTRY_PATH.relative_to(REPO_ROOT)).replace("\\", "/"))
    except ValueError:
        pass  # REGISTRY_PATH outside REPO_ROOT (e.g. a test using an isolated temp registry)

    build_errors: list[str] = []

    for family_id in required_families:
        fd = registry["families"][family_id]
        governing_for_family = [a for a in fd["artifacts"] if a["status"] == GOVERNING_STATUS]

        if len(governing_for_family) == 0:
            build_errors.append(f"family '{family_id}' has ZERO governing artifacts - HARD FAILURE, not silently skipped")
        elif len(governing_for_family) > 1:
            build_errors.append(f"family '{family_id}' has {len(governing_for_family)} governing artifacts - AMBIGUOUS, HARD FAILURE")
        else:
            governing_artifacts[family_id] = governing_for_family[0]["path"]

        non_governing = [a for a in fd["artifacts"] if a["status"] != GOVERNING_STATUS]
        if non_governing:
            historical_or_supporting_artifacts[family_id] = non_governing

        for a in fd["artifacts"]:
            all_tracked_paths.append(a["path"])

    if build_errors:
        raise FreezeBuildError(
            "Freeze build ABORTED - required-family validation failed:\n  " + "\n  ".join(build_errors)
        )

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
            "results/stage3_governance_registry.json - not a separately "
            "maintained parallel truth, and no cross-cutting docs are "
            "appended outside the registry; every current-facing document "
            "is its own governed family."
        ),
        "source_of_truth": "results/stage3_governance_registry.json",
        "required_families_count": len(required_families),
        "required_families": required_families,
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
          len(governing_artifacts), "governing, across", len(required_families),
          "required families, all_exist:", all_exist)


if __name__ == "__main__":
    main()
