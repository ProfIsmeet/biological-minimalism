#!/usr/bin/env python3
"""Read-only jury-environment verifier for the Biological Minimalism demo.

Checks that a clean checkout has the deterministic-deployment prerequisites in
place before a jury demonstration. This script is intentionally conservative:

* It only reads files and probes for optional tooling on PATH. It never starts
  or stops servers, never edits source, environment, replay, or fault state,
  never writes environment files, and never downloads datasets, models, or
  packages. It does not modify Docker state.
* It never prints the *value* of a secret/environment variable; it only reports
  whether an expected variable is set.
* It is deterministic and safe to run repeatedly.

Exit code is 0 only when every mandatory (FAIL-level) check passes. WARN-level
findings do not fail the exit code but are reported distinctly and are never
silently treated as passes.

Usage:
    python scripts/verify_jury_environment.py [--root PATH] [--quiet]
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

PASS = "PASS"
WARN = "WARN"
FAIL = "FAIL"


@dataclass(frozen=True)
class Result:
    level: str
    name: str
    detail: str


def _read_text(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None


def _tool_version(binary: str, *args: str) -> str | None:
    """Return a tool's version string, or None if unavailable. Read-only."""
    if shutil.which(binary) is None:
        return None
    try:
        completed = subprocess.run(  # noqa: S603 - fixed, read-only version probe
            [binary, *args],
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    output = (completed.stdout or completed.stderr or "").strip().splitlines()
    return output[0] if output else ""


def check_frontend_lockfile(root: Path) -> Result:
    lockfile = root / "frontend" / "package-lock.json"
    if lockfile.is_file() and lockfile.stat().st_size > 0:
        return Result(PASS, "frontend-lockfile", "frontend/package-lock.json present")
    return Result(FAIL, "frontend-lockfile", "frontend/package-lock.json missing or empty")


def check_frontend_dockerfile(root: Path) -> list[Result]:
    dockerfile = root / "frontend" / "Dockerfile"
    text = _read_text(dockerfile)
    if text is None:
        return [Result(FAIL, "frontend-dockerfile", "frontend/Dockerfile missing")]
    results: list[Result] = []
    # Only inspect executable directives, not comments: the Dockerfile
    # legitimately *mentions* `npm install` in a comment explaining why it was
    # replaced. A comment must never be mistaken for the actual command.
    directive_lines = [
        line for line in text.splitlines() if not line.lstrip().startswith("#")
    ]
    directives = "\n".join(directive_lines)
    if "npm ci" in directives:
        results.append(Result(PASS, "frontend-npm-ci", "deps stage uses `npm ci`"))
    else:
        results.append(Result(FAIL, "frontend-npm-ci", "deps stage does not use `npm ci`"))
    # `npm install` in an executable directive is the non-deterministic pattern F-08 fixed.
    if "npm install" in directives:
        results.append(
            Result(FAIL, "frontend-no-npm-install", "Dockerfile RUN directive uses `npm install`")
        )
    else:
        results.append(Result(PASS, "frontend-no-npm-install", "no `npm install` directive in Dockerfile"))
    if "package-lock.json" in text:
        results.append(Result(PASS, "frontend-lock-copied", "Dockerfile copies package-lock.json"))
    else:
        results.append(
            Result(FAIL, "frontend-lock-copied", "Dockerfile does not copy package-lock.json")
        )
    return results


def check_no_wildcard_cors(root: Path) -> list[Result]:
    results: list[Result] = []
    main_py = _read_text(root / "backend" / "app" / "main.py") or ""
    if 'allow_origins=["*"]' in main_py.replace(" ", "") or "allow_origin_regex" in main_py:
        results.append(Result(FAIL, "backend-cors-wildcard", "backend enables wildcard/regex CORS"))
    else:
        results.append(Result(PASS, "backend-cors-wildcard", "backend uses exact-origin CORS"))
    compose = _read_text(root / "docker-compose.yml") or ""
    if '["*"]' in compose.replace(" ", "") or "BIOMIN_ALLOWED_ORIGINS: '*'" in compose:
        results.append(Result(FAIL, "compose-cors-wildcard", "compose sets wildcard CORS origins"))
    else:
        results.append(Result(PASS, "compose-cors-wildcard", "compose CORS origins are not wildcard"))
    return results


def check_public_env_leak(root: Path) -> Result:
    """Fail if the leaked backend env var appears in *rendered* frontend copy.

    F-18 concerns user-facing copy. The identifier may legitimately remain in
    developer code comments (e.g. protected runtime modules) and in backend
    code / operator docs, so occurrences on comment lines are allowed.
    """
    token = "BIOMIN_PPG_DALIA" + "_PATH"  # split to keep this checker itself clean
    src = root / "frontend" / "src"
    if not src.is_dir():
        return Result(WARN, "public-env-leak", "frontend/src not found; leak check skipped")
    offending: list[str] = []
    for path in sorted(src.rglob("*.ts*")):
        text = _read_text(path)
        if text is None or token not in text:
            continue
        for lineno, line in enumerate(text.splitlines(), start=1):
            if token not in line:
                continue
            stripped = line.lstrip()
            is_comment = stripped.startswith(("*", "//", "/*"))
            if not is_comment:
                rel = path.relative_to(root)
                offending.append(f"{rel}:{lineno}")
    if offending:
        return Result(FAIL, "public-env-leak", "rendered copy exposes backend env var: " + ", ".join(offending))
    return Result(PASS, "public-env-leak", "no backend env var in rendered frontend copy")


def check_files_present(root: Path) -> list[Result]:
    mandatory = {
        "frontend/src/lib/config.ts": "frontend API/WS config",
        "backend/app/core/config.py": "backend settings/CORS",
        "docker-compose.yml": "compose topology",
    }
    optional = {
        "frontend/.env.local.example": "frontend env template",
        "backend/.env.example": "backend env template",
        "docs/JURY_DEPLOYMENT_RUNBOOK.md": "jury deployment runbook",
        "docs/JURY_RELEASE_EVIDENCE_MANIFEST.md": "release evidence manifest",
        "docs/DATASET_REPLAY.md": "dataset replay operator doc",
    }
    results: list[Result] = []
    for rel, purpose in mandatory.items():
        present = (root / rel).is_file()
        results.append(Result(PASS if present else FAIL, f"file:{rel}", purpose if present else f"missing ({purpose})"))
    for rel, purpose in optional.items():
        present = (root / rel).is_file()
        results.append(Result(PASS if present else WARN, f"file:{rel}", purpose if present else f"missing ({purpose})"))
    return results


def check_ws_contract(root: Path) -> Result:
    config = _read_text(root / "frontend" / "src" / "lib" / "config.ts") or ""
    if "deriveWebSocketUrl" in config and "/ws/live-feed" in config:
        return Result(PASS, "frontend-ws-contract", "config.ts exposes the WS derivation contract")
    return Result(WARN, "frontend-ws-contract", "config.ts WS derivation contract not detected")


def check_dataset_and_checkpoint(root: Path) -> list[Result]:
    """Dataset/checkpoint are large, unbundled artifacts: absence is a WARN."""
    results: list[Result] = []
    checkpoint = root / "ml" / "checkpoints" / "model_b_ppg_plus_imu_ppg_dalia.pt"
    if checkpoint.is_file() and checkpoint.stat().st_size > 0:
        results.append(Result(PASS, "hr-checkpoint", "PPG+IMU HR checkpoint present"))
    else:
        results.append(Result(WARN, "hr-checkpoint", "HR checkpoint absent (replay HR inference disabled)"))
    dataset_dir = root / "datasets" / "ppg-dalia"
    if dataset_dir.is_dir():
        has_payload = any(
            (p.suffix in {".zip", ".pkl"} or p.is_dir())
            for p in dataset_dir.iterdir()
            if p.name != "README.md"
        )
    else:
        has_payload = False
    if has_payload:
        results.append(Result(PASS, "ppg-dalia-dataset", "PPG-DaLiA data present"))
    else:
        results.append(Result(WARN, "ppg-dalia-dataset", "PPG-DaLiA data absent (synthetic demo still works)"))
    return results


def check_tooling() -> list[Result]:
    """Report tool availability. Absence is a WARN (environments differ)."""
    results: list[Result] = []
    probes = {
        "node": ("node", "--version"),
        "npm": ("npm", "--version"),
        "python": ("python3", "--version"),
        "docker": ("docker", "--version"),
    }
    for label, (binary, flag) in probes.items():
        version = _tool_version(binary, flag)
        if version is None:
            results.append(Result(WARN, f"tool:{label}", f"{binary} not found on PATH"))
        else:
            results.append(Result(PASS, f"tool:{label}", version))
    # docker compose plugin (do NOT run `up`; `version` is read-only)
    if shutil.which("docker") is not None:
        compose_version = _tool_version("docker", "compose", "version")
        if compose_version:
            results.append(Result(PASS, "tool:docker-compose", compose_version))
        else:
            results.append(Result(WARN, "tool:docker-compose", "docker compose plugin not detected"))
    else:
        results.append(Result(WARN, "tool:docker-compose", "docker not found; cannot check compose plugin"))
    return results


def check_env_vars() -> list[Result]:
    """Report whether relevant env vars are SET, never their values."""
    results: list[Result] = []
    for name in ("BIOMIN_ALLOWED_ORIGINS", "BIOMIN_PPG_DALIA_PATH", "NEXT_PUBLIC_API_BASE_URL"):
        is_set = bool(os.environ.get(name, "").strip())
        results.append(Result(PASS if is_set else WARN, f"env:{name}", "set" if is_set else "not set (default applies)"))
    return results


def run_checks(root: Path) -> list[Result]:
    results: list[Result] = []
    results.append(check_frontend_lockfile(root))
    results.extend(check_frontend_dockerfile(root))
    results.extend(check_no_wildcard_cors(root))
    results.append(check_public_env_leak(root))
    results.extend(check_files_present(root))
    results.append(check_ws_contract(root))
    results.extend(check_dataset_and_checkpoint(root))
    results.extend(check_tooling())
    results.extend(check_env_vars())
    return results


def default_root() -> Path:
    # scripts/ lives directly under the repository root.
    return Path(__file__).resolve().parents[1]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="verify_jury_environment.py",
        description="Read-only verification of local jury deployment prerequisites.",
    )
    parser.add_argument("--root", type=Path, default=default_root(), help="Repository root to inspect.")
    parser.add_argument("--quiet", action="store_true", help="Only print the summary line and any FAILs.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = args.root.resolve()
    results = run_checks(root)

    counts = {PASS: 0, WARN: 0, FAIL: 0}
    for result in results:
        counts[result.level] += 1
        if args.quiet and result.level == PASS:
            continue
        print(f"[{result.level}] {result.name}: {result.detail}")

    print(f"SUMMARY root={root} PASS={counts[PASS]} WARN={counts[WARN]} FAIL={counts[FAIL]}")
    return 1 if counts[FAIL] else 0


if __name__ == "__main__":
    raise SystemExit(main())
