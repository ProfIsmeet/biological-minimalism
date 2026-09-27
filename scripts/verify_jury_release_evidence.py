#!/usr/bin/env python3
"""Read-only release-evidence verifier for the Biological Minimalism jury demo.

Given a repository root, this script checks whether the release-evidence
artifacts described in ``docs/JURY_RELEASE_EVIDENCE_MANIFEST.md`` are actually
present in that checkout. It is deliberately honest and non-destructive:

* Read-only. It never copies evidence from another checkout, never edits,
  renames, or deletes screenshots, and never fabricates placeholder evidence.
* It distinguishes MISSING, EMPTY (present but zero bytes), AMBIGUOUS (multiple
  matches for a single expected artifact), and PRESENT.
* It may compute a SHA-256 of a present file for provenance, but it does NOT
  claim that any image was visually reviewed on the basis of its hash.
* When required evidence is absent it fails (non-zero exit) and prints an
  explicit "F-07 status: INCOMPLETE" line. A manifest + verifier existing does
  not by itself mark F-07 fixed.

Usage:
    python scripts/verify_jury_release_evidence.py [--root PATH] [--hash] [--json]
"""

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path

MISSING = "MISSING"
EMPTY = "EMPTY"
AMBIGUOUS = "AMBIGUOUS"
PRESENT = "PRESENT"

# Stage-aware resolution: each QA evidence artifact (AUDIT.md, state-fault.png,
# etc.) is re-created per work run under its own `frontend/qa-screenshots/<run>/`
# directory, so a broad `**/AUDIT.md`-style glob legitimately collects one match
# per historical run once more than one run has ever existed. That is not
# missing or corrupted evidence — it is several real, independently-reviewable
# artifacts for the same manifest slot. Cross-run collisions are resolved by
# treating the highest-precedence run below as canonical for status purposes;
# matches from every other run are still reported (see Resolution.superseded)
# but do not count as AMBIGUOUS. A collision between two files inside the SAME
# run directory is a genuine, unresolvable ambiguity and still reports
# AMBIGUOUS exactly as before — this list only disambiguates *across* runs.
# Newest/most-authoritative first; any run directory not listed here sorts
# after all listed ones (stable, alphabetical tiebreak among unlisted runs).
CANONICAL_RUN_ORDER: tuple[str, ...] = (
    "claude-stage4-5-real-visual-implementation",
    "codex-independent-final-frontend-audit",
    "claude-stage4-5-visual-command-deck",
    "claude-stage2-3-final-acceptance",
    "codex-stage2-3-independent-acceptance",
    "codex-fix-01-scientific-data-integrity",
)


@dataclass(frozen=True)
class EvidenceEntry:
    entry_id: str
    pattern: str  # glob relative to root
    required: bool
    purpose: str
    runtime_critical: bool
    distributable: bool
    license_review: bool


# The canonical evidence list. Keep in sync with
# docs/JURY_RELEASE_EVIDENCE_MANIFEST.md. Patterns intentionally point at the
# QA-evidence tree location used by this project; on the source-only base
# commit these are expected to be MISSING, which is the honest F-07 signal.
EVIDENCE: list[EvidenceEntry] = [
    EvidenceEntry("audit-main", "frontend/qa-screenshots/**/AUDIT.md", True,
                  "Independent final frontend audit", False, True, False),
    EvidenceEntry("audit-matrix", "frontend/qa-screenshots/**/FIVE_STAGE_COMPLETENESS_MATRIX.md", True,
                  "Five-stage completeness matrix", False, True, False),
    EvidenceEntry("audit-recommendation", "frontend/qa-screenshots/**/JURY_DEMO_RECOMMENDATION.md", True,
                  "Jury demo recommendation", False, True, False),
    EvidenceEntry("prompt-3bc-human-visual", "frontend/qa-screenshots/**/prompt-3*/**/*", True,
                  "Prompt 3B/3C human & visual evidence", False, True, True),
    EvidenceEntry("prompt-4-a11y-hardening", "frontend/qa-screenshots/**/prompt-4*/**/*", True,
                  "Prompt 4/4A accessibility & hardening evidence", False, True, False),
    EvidenceEntry("prompt-5-hostile-dossier", "frontend/qa-screenshots/**/prompt-5*/**/*", True,
                  "Prompt 5 hostile-audit dossier", False, True, False),
    EvidenceEntry("presenter-script", "**/presenter*script*.*", True,
                  "Presenter script", False, True, False),
    EvidenceEntry("recovery-card", "**/recovery*card*.*", True,
                  "Non-technical recovery card", False, True, False),
    EvidenceEntry("state-nominal", "frontend/qa-screenshots/**/*nominal*.png", True,
                  "Nominal state screenshot", True, True, False),
    EvidenceEntry("state-fault", "frontend/qa-screenshots/**/*fault*.png", True,
                  "Fault state screenshot", True, True, False),
    EvidenceEntry("state-rebuilding", "frontend/qa-screenshots/**/*rebuild*.png", True,
                  "Rebuilding state screenshot", True, True, False),
    EvidenceEntry("state-recovered", "frontend/qa-screenshots/**/*recover*.png", True,
                  "Recovered state screenshot", True, True, False),
    EvidenceEntry("state-disconnected", "frontend/qa-screenshots/**/*disconnect*.png", True,
                  "Disconnected state screenshot", True, True, False),
    EvidenceEntry("mobile-mission-overview", "frontend/qa-screenshots/**/*mobile*mission*overview*.png", True,
                  "Mobile Mission Overview screenshot", True, True, False),
    EvidenceEntry("live-monitoring", "frontend/qa-screenshots/**/*live*monitoring*.png", True,
                  "Live Monitoring screenshot", True, True, False),
    EvidenceEntry("system-brief", "frontend/qa-screenshots/**/*system*brief*.png", True,
                  "System Brief screenshot", True, True, False),
    EvidenceEntry("experimental", "frontend/qa-screenshots/**/*experimental*.png", True,
                  "Experimental screenshot", True, True, False),
    EvidenceEntry("digital-twin", "frontend/qa-screenshots/**/*digital*twin*.png", True,
                  "Digital Twin screenshot", True, True, False),
    EvidenceEntry("presenter-preflight", "frontend/qa-screenshots/**/*preflight*.png", True,
                  "Presenter Preflight screenshot", True, True, False),
    EvidenceEntry("zoom-200", "frontend/qa-screenshots/**/*200*zoom*.png", True,
                  "200% zoom accessibility evidence", True, True, False),
    EvidenceEntry("human-front", "frontend/qa-screenshots/**/*human*front*.png", True,
                  "Human figure front view", False, True, True),
    EvidenceEntry("human-side", "frontend/qa-screenshots/**/*human*side*.png", True,
                  "Human figure side view", False, True, True),
    EvidenceEntry("human-three-quarter", "frontend/qa-screenshots/**/*human*three*quarter*.png", True,
                  "Human figure three-quarter view", False, True, True),
    EvidenceEntry("rejected-cesiumman", "frontend/qa-screenshots/**/*cesium*", False,
                  "Rejected CesiumMan evidence & provenance record", False, False, True),
]


@dataclass
class Resolution:
    entry: EvidenceEntry
    status: str
    matches: list[str] = field(default_factory=list)
    sha256: str | None = None
    superseded: list[str] = field(default_factory=list)


def _sha256(path: Path) -> str | None:
    try:
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for block in iter(lambda: handle.read(65536), b""):
                digest.update(block)
        return digest.hexdigest()
    except OSError:
        return None


def _run_key(root: Path, path: Path) -> str | None:
    """The `frontend/qa-screenshots/<run>/...` run-directory name for `path`,
    or None if `path` does not live under that tree (no cross-run precedence
    is possible for such a match; it is grouped on its own)."""
    qa_root = root / "frontend" / "qa-screenshots"
    try:
        rel = path.relative_to(qa_root)
    except ValueError:
        return None
    return rel.parts[0] if rel.parts else None


def _run_precedence(run_key: str | None) -> tuple[int, str]:
    if run_key is None:
        # Ungrouped matches never collide with a run-keyed canonical match by
        # construction (see resolve_entry): give them the lowest precedence.
        return (len(CANONICAL_RUN_ORDER) + 1, "")
    try:
        return (CANONICAL_RUN_ORDER.index(run_key), run_key)
    except ValueError:
        return (len(CANONICAL_RUN_ORDER), run_key)


def resolve_entry(root: Path, entry: EvidenceEntry, want_hash: bool) -> Resolution:
    matches = sorted(p for p in root.glob(entry.pattern) if p.is_file())
    rel_matches = [str(p.relative_to(root)) for p in matches]
    if not matches:
        return Resolution(entry, MISSING, rel_matches)

    groups: dict[str | None, list[Path]] = {}
    for p in matches:
        groups.setdefault(_run_key(root, p), []).append(p)

    if len(groups) <= 1:
        # Single run directory (or no run-directory structure at all): identical
        # to the original, pre-stage-aware behavior. This is the only branch
        # exercised by the existing single-fixture-root unit tests.
        canonical = matches
        superseded: list[Path] = []
    else:
        best_key = min(groups, key=_run_precedence)
        canonical = groups[best_key]
        superseded = [p for key, paths in groups.items() if key != best_key for p in paths]

    rel_superseded = [str(p.relative_to(root)) for p in sorted(superseded)]

    if not canonical:
        return Resolution(entry, MISSING, rel_matches, superseded=rel_superseded)
    if len(canonical) > 1:
        return Resolution(entry, AMBIGUOUS, rel_matches, superseded=rel_superseded)
    only = canonical[0]
    if only.stat().st_size == 0:
        return Resolution(entry, EMPTY, rel_matches, superseded=rel_superseded)
    sha = _sha256(only) if want_hash else None
    return Resolution(entry, PRESENT, rel_matches, sha, superseded=rel_superseded)


def verify(root: Path, want_hash: bool = False) -> list[Resolution]:
    return [resolve_entry(root, entry, want_hash) for entry in EVIDENCE]


def summarize(resolutions: list[Resolution]) -> dict[str, int]:
    counts = {MISSING: 0, EMPTY: 0, AMBIGUOUS: 0, PRESENT: 0}
    for res in resolutions:
        counts[res.status] += 1
    return counts


def required_incomplete(resolutions: list[Resolution]) -> list[Resolution]:
    return [r for r in resolutions if r.entry.required and r.status != PRESENT]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="verify_jury_release_evidence.py",
        description="Read-only verification of jury release evidence against the manifest.",
    )
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1],
                        help="Repository root to inspect.")
    parser.add_argument("--hash", action="store_true", help="Compute SHA-256 of present files (provenance only).")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON instead of text.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = args.root.resolve()
    resolutions = verify(root, want_hash=args.hash)
    counts = summarize(resolutions)
    incomplete = required_incomplete(resolutions)
    complete = not incomplete

    if args.json:
        payload = {
            "root": str(root),
            "counts": counts,
            "complete": complete,
            "f07_status": "COMPLETE" if complete else "INCOMPLETE",
            "entries": [
                {
                    "id": r.entry.entry_id,
                    "status": r.status,
                    "required": r.entry.required,
                    "runtime_critical": r.entry.runtime_critical,
                    "distributable": r.entry.distributable,
                    "license_review": r.entry.license_review,
                    "matches": r.matches,
                    "superseded": r.superseded,
                    "sha256": r.sha256,
                }
                for r in resolutions
            ],
        }
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        for r in resolutions:
            marker = "audit-only" if not r.entry.runtime_critical else "runtime-critical"
            req = "required" if r.entry.required else "optional"
            extra = f" -> {r.matches}" if r.matches else ""
            if r.superseded:
                extra += f" (superseded by canonical run: {r.superseded})"
            print(f"[{r.status}] {r.entry.entry_id} ({req}, {marker}): {r.entry.purpose}{extra}")
        print(
            f"SUMMARY root={root} PRESENT={counts[PRESENT]} MISSING={counts[MISSING]} "
            f"EMPTY={counts[EMPTY]} AMBIGUOUS={counts[AMBIGUOUS]}"
        )
        if complete:
            print("F-07 status: EVIDENCE PRESENT (visual review still required separately)")
        else:
            print(
                f"F-07 status: INCOMPLETE — {len(incomplete)} required evidence artifact(s) not "
                "PRESENT in this checkout. This is expected on a source-only checkout that does "
                "not carry the QA evidence tree; do not mark F-07 fixed until the approved "
                "evidence bundle is actually present."
            )
    return 0 if complete else 2


if __name__ == "__main__":
    raise SystemExit(main())
