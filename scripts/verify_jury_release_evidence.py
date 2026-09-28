#!/usr/bin/env python3
"""Fail-closed verifier for jury-release evidence.

Canonical selection is data, not directory-name precedence. Every manifest slot
is bound in ``docs/JURY_RELEASE_EVIDENCE_POLICY.json`` to one exact path and
SHA-256 digest. Other glob matches must be explicitly classified as superseded
or audit-only. Unknown collisions, hash drift, and unapproved canonical files
fail closed as AMBIGUOUS.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

MISSING = "MISSING"
EMPTY = "EMPTY"
AMBIGUOUS = "AMBIGUOUS"
PRESENT = "PRESENT"
POLICY_RELATIVE_PATH = Path("docs/JURY_RELEASE_EVIDENCE_POLICY.json")


@dataclass(frozen=True)
class EvidenceEntry:
    entry_id: str
    pattern: str
    required: bool
    purpose: str
    runtime_critical: bool
    distributable: bool
    license_review: bool


EVIDENCE: list[EvidenceEntry] = [
    EvidenceEntry("audit-main", "frontend/qa-screenshots/**/AUDIT.md", True, "Independent final frontend audit", False, True, False),
    EvidenceEntry("audit-matrix", "frontend/qa-screenshots/**/FIVE_STAGE_COMPLETENESS_MATRIX.md", True, "Five-stage completeness matrix", False, True, False),
    EvidenceEntry("audit-recommendation", "frontend/qa-screenshots/**/JURY_DEMO_RECOMMENDATION.md", True, "Jury demo recommendation", False, True, False),
    EvidenceEntry("prompt-3bc-human-visual", "frontend/qa-screenshots/**/prompt-3*/**/*", True, "Prompt 3B/3C human & visual evidence", False, True, True),
    EvidenceEntry("prompt-4-a11y-hardening", "frontend/qa-screenshots/**/prompt-4*/**/*", True, "Prompt 4/4A accessibility & hardening evidence", False, True, False),
    EvidenceEntry("prompt-5-hostile-dossier", "frontend/qa-screenshots/**/prompt-5*/**/*", True, "Prompt 5 hostile-audit dossier", False, True, False),
    EvidenceEntry("presenter-script", "**/presenter*script*.*", True, "Presenter script", False, True, False),
    EvidenceEntry("recovery-card", "**/recovery*card*.*", True, "Non-technical recovery card", False, True, False),
    EvidenceEntry("state-nominal", "frontend/qa-screenshots/**/*nominal*.png", True, "Nominal state screenshot", True, True, False),
    EvidenceEntry("state-fault", "frontend/qa-screenshots/**/*fault*.png", True, "Fault state screenshot", True, True, False),
    EvidenceEntry("state-rebuilding", "frontend/qa-screenshots/**/*rebuild*.png", True, "Rebuilding state screenshot", True, True, False),
    EvidenceEntry("state-recovered", "frontend/qa-screenshots/**/*recover*.png", True, "Recovered state screenshot", True, True, False),
    EvidenceEntry("state-disconnected", "frontend/qa-screenshots/**/*disconnect*.png", True, "Disconnected state screenshot", True, True, False),
    EvidenceEntry("mobile-mission-overview", "frontend/qa-screenshots/**/*mobile*mission*overview*.png", True, "Mobile Mission Overview screenshot", True, True, False),
    EvidenceEntry("live-monitoring", "frontend/qa-screenshots/**/*live*monitoring*.png", True, "Live Monitoring screenshot", True, True, False),
    EvidenceEntry("system-brief", "frontend/qa-screenshots/**/*system*brief*.png", True, "System Brief screenshot", True, True, False),
    EvidenceEntry("experimental", "frontend/qa-screenshots/**/*experimental*.png", True, "Experimental screenshot", True, True, False),
    EvidenceEntry("digital-twin", "frontend/qa-screenshots/**/*digital*twin*.png", True, "Digital Twin screenshot", True, True, False),
    EvidenceEntry("presenter-preflight", "frontend/qa-screenshots/**/*preflight*.png", True, "Presenter Preflight screenshot", True, True, False),
    EvidenceEntry("zoom-200", "frontend/qa-screenshots/**/*200*zoom*.png", True, "200% zoom accessibility evidence", True, True, False),
    EvidenceEntry("human-front", "frontend/qa-screenshots/**/*human*front*.png", True, "Human figure front view", False, True, True),
    EvidenceEntry("human-side", "frontend/qa-screenshots/**/*human*side*.png", True, "Human figure side view", False, True, True),
    EvidenceEntry("human-three-quarter", "frontend/qa-screenshots/**/*human*three*quarter*.png", True, "Human figure three-quarter view", False, True, True),
    EvidenceEntry("rejected-cesiumman", "frontend/qa-screenshots/**/*cesium*", False, "Rejected CesiumMan evidence & provenance record", False, False, True),
]


@dataclass
class Resolution:
    entry: EvidenceEntry
    status: str
    matches: list[str] = field(default_factory=list)
    sha256: str | None = None
    canonical: str | None = None
    expected_sha256: str | None = None
    superseded: list[str] = field(default_factory=list)
    audit_only: list[str] = field(default_factory=list)
    unregistered: list[str] = field(default_factory=list)
    issues: list[str] = field(default_factory=list)


def _sha256(path: Path) -> str | None:
    try:
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for block in iter(lambda: handle.read(65536), b""):
                digest.update(block)
        return digest.hexdigest()
    except OSError:
        return None


def load_policy(root: Path, policy_path: Path | None = None) -> tuple[dict[str, Any], list[str]]:
    path = policy_path or root / POLICY_RELATIVE_PATH
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {}, [f"policy unavailable or invalid: {path}: {exc}"]
    if raw.get("version") != 1 or not isinstance(raw.get("entries"), dict):
        return {}, ["policy must have version=1 and an entries object"]
    return raw, []


def resolve_entry(root: Path, entry: EvidenceEntry, want_hash: bool, policy: dict[str, Any]) -> Resolution:
    matches = sorted(p for p in root.glob(entry.pattern) if p.is_file())
    rel_matches = [p.relative_to(root).as_posix() for p in matches]
    rule = policy.get("entries", {}).get(entry.entry_id)
    if not isinstance(rule, dict):
        return Resolution(entry, MISSING, rel_matches, issues=["missing per-entry policy"])

    canonical = rule.get("canonical")
    expected = rule.get("sha256")
    superseded = sorted(set(rule.get("superseded", [])))
    audit_only = sorted(set(rule.get("audit_only", [])))
    registered = set(superseded) | set(audit_only)
    if canonical:
        registered.add(canonical)
    unregistered = sorted(set(rel_matches) - registered)
    issues: list[str] = []
    if unregistered:
        issues.append("unregistered matching artifact(s); future collisions require explicit adjudication")
    if set(superseded) & set(audit_only):
        issues.append("artifact classified as both superseded and audit-only")
    if canonical and (canonical in superseded or canonical in audit_only):
        issues.append("canonical artifact cannot also be superseded or audit-only")

    if canonical is None:
        if entry.required:
            issues.append("required entry has no canonical artifact")
        status = AMBIGUOUS if unregistered or issues else MISSING
        return Resolution(entry, status, rel_matches, canonical=None,
                          superseded=superseded, audit_only=audit_only,
                          unregistered=unregistered, issues=issues)

    canonical_path = root / canonical
    if not canonical_path.is_file():
        issues.append("declared canonical artifact is missing")
        status = AMBIGUOUS if unregistered else MISSING
        return Resolution(entry, status, rel_matches, canonical=canonical,
                          expected_sha256=expected, superseded=superseded,
                          audit_only=audit_only, unregistered=unregistered, issues=issues)
    if canonical_path.stat().st_size == 0:
        issues.append("declared canonical artifact is empty")
        return Resolution(entry, EMPTY, rel_matches, canonical=canonical,
                          expected_sha256=expected, superseded=superseded,
                          audit_only=audit_only, unregistered=unregistered, issues=issues)

    actual = _sha256(canonical_path)
    if not rule.get("visually_reviewed", False):
        issues.append("canonical artifact lacks explicit visual-review approval")
    if not isinstance(expected, str) or len(expected) != 64:
        issues.append("canonical artifact lacks a valid pinned SHA-256")
    elif actual != expected:
        issues.append("canonical SHA-256 does not match policy")
    if canonical not in rel_matches:
        issues.append("canonical path does not match the manifest slot pattern")
    status = AMBIGUOUS if issues or unregistered else PRESENT
    return Resolution(entry, status, rel_matches, actual if want_hash else None,
                      canonical, expected, superseded, audit_only, unregistered, issues)


def verify(root: Path, want_hash: bool = False, policy_path: Path | None = None) -> list[Resolution]:
    policy, policy_issues = load_policy(root, policy_path)
    if policy_issues:
        policy = {"entries": {}}
    results = [resolve_entry(root, entry, want_hash, policy) for entry in EVIDENCE]
    if policy_issues:
        for result in results:
            result.issues.extend(policy_issues)
    return results


def summarize(resolutions: list[Resolution]) -> dict[str, int]:
    counts = {MISSING: 0, EMPTY: 0, AMBIGUOUS: 0, PRESENT: 0}
    for result in resolutions:
        counts[result.status] += 1
    return counts


def required_incomplete(resolutions: list[Resolution]) -> list[Resolution]:
    return [r for r in resolutions if r.entry.required and r.status != PRESENT]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Verify jury evidence against explicit canonical policy.")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--policy", type=Path, default=None)
    parser.add_argument("--hash", action="store_true", help="Include verified canonical SHA-256 values in output.")
    parser.add_argument("--json", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = args.root.resolve()
    resolutions = verify(root, args.hash, args.policy)
    counts = summarize(resolutions)
    incomplete = required_incomplete(resolutions)
    complete = not incomplete
    if args.json:
        print(json.dumps({
            "root": str(root), "policy": str(args.policy or POLICY_RELATIVE_PATH),
            "policy_version": 1, "counts": counts, "complete": complete,
            "f07_status": "COMPLETE" if complete else "INCOMPLETE",
            "entries": [{
                "id": r.entry.entry_id, "status": r.status, "required": r.entry.required,
                "runtime_critical": r.entry.runtime_critical, "distributable": r.entry.distributable,
                "license_review": r.entry.license_review, "canonical": r.canonical,
                "expected_sha256": r.expected_sha256, "sha256": r.sha256,
                "matches": r.matches, "superseded": r.superseded,
                "audit_only": r.audit_only, "unregistered": r.unregistered,
                "issues": r.issues,
            } for r in resolutions],
        }, indent=2, sort_keys=True))
    else:
        for r in resolutions:
            req = "required" if r.entry.required else "optional"
            print(f"[{r.status}] {r.entry.entry_id} ({req}): canonical={r.canonical or '-'}")
            if r.superseded:
                print(f"  superseded={r.superseded}")
            if r.audit_only:
                print(f"  audit-only={r.audit_only}")
            if r.unregistered:
                print(f"  unregistered={r.unregistered}")
            for issue in r.issues:
                print(f"  issue={issue}")
        print(f"SUMMARY root={root} PRESENT={counts[PRESENT]} MISSING={counts[MISSING]} EMPTY={counts[EMPTY]} AMBIGUOUS={counts[AMBIGUOUS]}")
        print("F-07 status: EVIDENCE PRESENT (visual review separately recorded in policy)" if complete else
              f"F-07 status: INCOMPLETE — {len(incomplete)} required evidence artifact(s) failed closed")
    return 0 if complete else 2


if __name__ == "__main__":
    raise SystemExit(main())
