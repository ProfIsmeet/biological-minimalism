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


def _sha256(path: Path) -> str | None:
    try:
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for block in iter(lambda: handle.read(65536), b""):
                digest.update(block)
        return digest.hexdigest()
    except OSError:
        return None


def resolve_entry(root: Path, entry: EvidenceEntry, want_hash: bool) -> Resolution:
    matches = sorted(p for p in root.glob(entry.pattern) if p.is_file())
    rel_matches = [str(p.relative_to(root)) for p in matches]
    if not matches:
        return Resolution(entry, MISSING, rel_matches)
    if len(matches) > 1:
        return Resolution(entry, AMBIGUOUS, rel_matches)
    only = matches[0]
    if only.stat().st_size == 0:
        return Resolution(entry, EMPTY, rel_matches)
    sha = _sha256(only) if want_hash else None
    return Resolution(entry, PRESENT, rel_matches, sha)


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
