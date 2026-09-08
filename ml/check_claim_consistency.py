"""Deterministic claim-consistency & stale-claim checker (Day 8/9, sprint §19/§31).

Audits paper/dashboard/jury-facing surfaces against the frozen scientific artifacts and
flags stale or over-strong claims. It classifies *legitimate* historical/negated occurrences
(a line that prohibits, negates, or marks a claim pending) rather than blindly failing on any
string match.

Run:  python ml/check_claim_consistency.py        # exits 1 on any violation

Two checks:
  1. Traceability integrity — every non-pending claim in results/claim_traceability.json
     points to an existing source_artifact; pending claims are marked pending.
  2. Stale-claim scan — live-claim surfaces (frontend copy, backend responses, README,
     dashboard) must not assert forbidden claims as bald positives.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

# Surfaces where a stale claim would actually reach a human as an assertion.
SCAN_DIRS = [
    REPO / "frontend" / "src",
    REPO / "backend" / "app",
    REPO / "dashboard",
]
SCAN_FILES = [REPO / "README.md"]
SCAN_SUFFIXES = {".ts", ".tsx", ".js", ".jsx", ".py", ".md", ".json", ".html"}
EXCLUDE_PARTS = {"node_modules", ".next", ".venv", "__pycache__", ".pytest_cache"}

# A line is treated as a legitimate negation/definition (not a bald claim) if it
# contains any of these markers.
NEGATION_MARKERS = re.compile(
    r"\b(not|never|no|non|without|prohibit|unsafe|unsupported|must not|do not|don't|"
    r"cannot|avoid|false|caveat|confounded|pending|preliminary|untrained|unvalidated|"
    r"forbidden|stale|deprecated|historical|limitation|NOT_READY|UNRESOLVED)\b",
    re.IGNORECASE,
)

# Forbidden bald-positive claim patterns.
FORBIDDEN = [
    (re.compile(r"\bfour validated sensors\b", re.IGNORECASE), "'four validated sensors'"),
    (re.compile(r"\boptimal (sensor )?architecture\b", re.IGNORECASE), "'optimal architecture'"),
    (re.compile(r"\btrained digital twin\b", re.IGNORECASE), "'trained Digital Twin'"),
    (re.compile(r"\b(astronaut|microgravity|spaceflight)[- ]?validated\b", re.IGNORECASE), "astronaut/microgravity validated"),
    (re.compile(r"\b59\s*/\s*41\b"), "'59/41' decomposition"),
    (re.compile(r"\b23\s*%\s*(pure|imu)", re.IGNORECASE), "'23%' IMU claim"),
    (re.compile(r"\bpure\b[^.\n]{0,40}\b20\.6\s*%", re.IGNORECASE), "'20.6% pure IMU' claim"),
    (re.compile(r"\b20\.6\s*%[^.\n]{0,40}\bpure\b", re.IGNORECASE), "'20.6% pure IMU' claim"),
    (re.compile(r"\b1\.88(0|8|79)?\s*bpm\b[^.\n]{0,30}\b(clean|current|pure)\b", re.IGNORECASE), "'1.88 bpm current clean IMU' claim"),
    (re.compile(r"\b68\s*%[^.\n]{0,40}\b(pure|parameter|causal)", re.IGNORECASE), "'68% pure parameter' claim"),
    # Day-10 forbidden bald claims (§33). Each is exempt when the line carries a
    # negation marker, so legitimate "does NOT prove...", "NOT ready", "not a final
    # BOM" copy passes; only bald positive assertions are flagged.
    (re.compile(r"\bsynerg(y|istic)\b", re.IGNORECASE), "sensor 'synergy' claim (EOG+Resp interaction is approximately additive/unresolved)"),
    (re.compile(r"\binteractions?\s+(are\s+|is\s+)?(absent|globally\s+absent|proven\s+absent|don't\s+matter|do\s+not\s+matter)\b", re.IGNORECASE), "'interactions absent/proven' claim"),
    (re.compile(r"\bfinal\s+BOM\b", re.IGNORECASE), "'final BOM' claim (only reference BOM readiness exists)"),
    (re.compile(r"\bfinal\s+architecture\s+(is\s+)?(selected|chosen|decided|resolved|frozen)\b", re.IGNORECASE), "'final architecture selected' claim (architecture is UNRESOLVED)"),
    (re.compile(r"\bsystem\s+(average\s+)?power\s+(is\s+)?(known|quantified|determined|ready)\b", re.IGNORECASE), "'system power known' claim (SYSTEM_AVERAGE_POWER_NOT_READY)"),
    (re.compile(r"\bsystem\s+mass\s+(is\s+)?(known|quantified|determined|ready)\b", re.IGNORECASE), "'system mass known' claim (SYSTEM_MASS_NOT_READY)"),
    (re.compile(r"\bpareto\s+(frontier\s+)?(is\s+)?ready\b", re.IGNORECASE), "'Pareto ready' claim (FORMAL_PARETO_NOT_READY)"),
    (re.compile(r"scientific\s+freeze\b[^.\n]{0,25}\b(=|equals|is|means)\b[^.\n]{0,25}\b(final|product|project)\s+freeze", re.IGNORECASE), "'scientific freeze = final/project freeze' conflation"),
    # Day-11 (§19) forbidden bald engineering claims. Each is exempt when the line
    # carries a negation marker (NOT_READY, not, no, without, ...), so legitimate
    # "system average power is NOT_READY" and "EOG burden is NOT zero" copy passes.
    (re.compile(r"\b(system|total\s+wearable)\s+(average\s+)?power\s*(=|:|is|of)\s*[~<>]?\s*\d", re.IGNORECASE), "bald 'system/total power = <number>' claim (SYSTEM_AVERAGE_POWER_NOT_READY)"),
    (re.compile(r"\bsystem\s+mass\s*(=|:|is|of)\s*[~<>]?\s*\d", re.IGNORECASE), "bald 'system mass = <number>' claim (SYSTEM_MASS_NOT_READY)"),
    (re.compile(r"\bfinal\s+BOM\s+(is\s+)?(selected|chosen|frozen|complete|ready)\b", re.IGNORECASE), "'final BOM selected' claim (only reference BOM readiness exists)"),
    (re.compile(r"\b(EOG|IMU|second[- ]?PPG)\b[^.\n]{0,40}\b(adds?|add|=)\b[^.\n]{0,20}\bzero\s+burden\b", re.IGNORECASE), "'<sensor> adds zero burden' claim (burden is never zeroed)"),
    (re.compile(r"\bzero\s+(added\s+)?burden\b", re.IGNORECASE), "'zero burden' claim (incremental burden is never zeroed)"),
    (re.compile(r"\bpareto[- ]?(optimized|optimised|optimal)\b", re.IGNORECASE), "'Pareto optimized/optimal' claim (FORMAL_PARETO_NOT_READY)"),
    (re.compile(r"\boptimal\s+sensor\s+(set|subset|architecture|selection)\b", re.IGNORECASE), "'optimal sensor set' claim (architecture is UNRESOLVED)"),
]

# Bare "robust" as an adjective claim (word boundary excludes "robustness").
ROBUST = re.compile(r"\brobust\b", re.IGNORECASE)

# Post-integration stale-pending assertions: statements that were TRUE on the
# systems branch before Ismet's Day-8/9 science merged, but are now FALSE. These
# contain their own negation words, so they are checked independently of
# NEGATION_MARKERS; a line is exempt only if it is CLEARLY historical/resolved.
STALE_PENDING = [
    (re.compile(r"no shuffled[- ]?eog\b", re.IGNORECASE), "'no shuffled-EOG control' (now integrated)"),
    (re.compile(r"per[- ]subject\b[^.\n]{0,40}\bnot (yet )?(computed|available|performed)", re.IGNORECASE), "'per-subject decomposition not computed' (now integrated)"),
    (re.compile(r"no per[- ]subject\b", re.IGNORECASE), "'no per-subject decomposition' (now integrated)"),
    (re.compile(r"secondary[- ]holdout[^.\n]{0,30}\bpending\b", re.IGNORECASE), "'secondary holdout pending' (now integrated)"),
    (re.compile(r"\bpending[^.\n]{0,30}secondary[- ]holdout\b", re.IGNORECASE), "'pending secondary holdout' (now integrated)"),
]

# A stale-pending line is allowed only when explicitly framed as history/resolved.
HISTORICAL_MARKERS = re.compile(
    r"\b(historical|superseded|supersedes|resolved|was |were |previously|prior to|"
    r"day[- ]?7|no longer|used to|before integration|now integrated|now complete|"
    r"COMPLETE|RESOLVED)\b",
    re.IGNORECASE,
)


def _iter_files() -> list[Path]:
    files: list[Path] = [f for f in SCAN_FILES if f.is_file()]
    for base in SCAN_DIRS:
        if not base.is_dir():
            continue
        for path in base.rglob("*"):
            if path.suffix.lower() not in SCAN_SUFFIXES:
                continue
            if any(part in EXCLUDE_PARTS for part in path.parts):
                continue
            files.append(path)
    return files


# Known live research API routes (path templates, concrete ids -> {}). A claim's
# api_surface must match one of these; a nonexistent route (audit M4 §26) fails.
KNOWN_ROUTES = {
    "GET /research/summary",
    "GET /research/experiments",
    "GET /research/experiments/{}",
    "GET /research/target-evidence-matrix",
    "GET /research/engineering-readiness",
    "GET /research/pareto-readiness",
    "GET /research/hardware-topology",
    "GET /research/decision-inputs",
    "GET /research/operational-costs",
    "GET /research/operational-costs/{}",
    "GET /digital-twin",
}


def _normalize_route(api_surface: str) -> str:
    """Collapse a concrete trailing id segment to {} so routes match templates."""
    try:
        method, path = api_surface.split(" ", 1)
    except ValueError:
        return api_surface
    segments = path.split("/")
    # Replace a concrete experiment/component id in the last segment with {}.
    if len(segments) > 3 and segments[-2] in {"experiments", "operational-costs"}:
        segments[-1] = "{}"
    return f"{method} {'/'.join(segments)}"


def _resolve_field(obj, dotted: str) -> tuple[bool, str | None]:
    """Resolve a simple dotted path with optional [n] list indices. Returns
    (resolved, failing_segment). Mechanical existence check only (audit M4 §24)."""
    cur = obj
    for part in dotted.split("."):
        m = re.match(r"^(.*?)\[(\d+)\]$", part)
        key = m.group(1) if m else part
        if key:
            if not isinstance(cur, dict) or key not in cur:
                return False, part
            cur = cur[key]
        if m:
            idx = int(m.group(2))
            if not isinstance(cur, list) or idx >= len(cur):
                return False, part
            cur = cur[idx]
    return True, None


def check_traceability() -> list[str]:
    problems: list[str] = []
    path = REPO / "results" / "claim_traceability.json"
    if not path.is_file():
        return ["results/claim_traceability.json is missing"]
    data = json.loads(path.read_text(encoding="utf-8"))
    for claim in data.get("claims", []):
        cid = claim.get("claim_id", "<unknown>")
        status = claim.get("status", "")
        artifact = claim.get("source_artifact", "")
        if status.startswith("pending"):
            if claim.get("api_surface") != "PENDING":
                problems.append(f"[trace] {cid}: pending claim must have api_surface=PENDING")
            continue
        # 1. source_artifact must exist.
        if not artifact or not (REPO / artifact).is_file():
            problems.append(f"[trace] {cid}: source_artifact missing -> {artifact!r}")
            continue
        # 2. source_field must resolve inside the artifact (audit M4 §24/§26).
        field = claim.get("source_field", "")
        if field:
            try:
                obj = json.loads((REPO / artifact).read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                problems.append(f"[trace] {cid}: source_artifact unreadable -> {exc}")
                continue
            resolved, where = _resolve_field(obj, field)
            if not resolved:
                problems.append(
                    f"[trace] {cid}: source_field does not resolve -> {artifact}::{field} (at {where!r})"
                )
        # 3. api_surface must be a real live route (audit M4 §26 nonexistent route).
        api = claim.get("api_surface", "")
        if api and _normalize_route(api) not in KNOWN_ROUTES:
            problems.append(f"[trace] {cid}: api_surface route does not exist -> {api!r}")
    return problems


def check_stale() -> list[str]:
    problems: list[str] = []
    for path in _iter_files():
        rel = path.relative_to(REPO)
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        for lineno, line in enumerate(text.splitlines(), start=1):
            negated = bool(NEGATION_MARKERS.search(line))
            for pattern, label in FORBIDDEN:
                if pattern.search(line) and not negated:
                    problems.append(f"[stale] {rel}:{lineno}: bald {label}")
            # Post-integration stale-pending assertions (checked regardless of the
            # generic negation exemption; allowed only if explicitly historical).
            historical = bool(HISTORICAL_MARKERS.search(line))
            for pattern, label in STALE_PENDING:
                if pattern.search(line) and not historical:
                    problems.append(f"[stale-pending] {rel}:{lineno}: {label}")
            # 'robust' only in live UI/response copy, excluding the word 'robustness'
            if ROBUST.search(line) and not negated and "robustness" not in line.lower():
                if path.suffix.lower() in {".tsx", ".jsx", ".ts", ".js"}:
                    problems.append(f"[stale] {rel}:{lineno}: bald 'robust' claim in UI copy")
    return problems


def main() -> int:
    problems = check_traceability() + check_stale()
    if problems:
        print(f"CLAIM CONSISTENCY: {len(problems)} issue(s) found\n")
        for p in problems:
            print("  -", p)
        return 1
    # Audit M4/§25: this is NOT a semantic proof that all claims are scientifically
    # valid. It is a structured traceability + forbidden-pattern guard. Semantic
    # paraphrases can bypass the lexical FORBIDDEN rules, and the traceability check
    # only verifies that artifact/field/route EXIST, not that the number is correct.
    print("STRUCTURED_TRACEABILITY_AND_FORBIDDEN_PATTERN_CHECK_PASS")
    print(
        "  Scope: every non-pending claim resolves to an existing source artifact, an existing "
        "JSON field path, and a live API route; and no forbidden bald-positive pattern appears on "
        "live surfaces."
    )
    print(
        "  Limitation: this is NOT comprehensive semantic claim certification. Lexical rules can be "
        "bypassed by paraphrase, and field/route checks verify existence, not numerical correctness."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
