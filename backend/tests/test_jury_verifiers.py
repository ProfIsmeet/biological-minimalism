"""Deterministic fixture tests for the two read-only jury verifier scripts.

The scripts live under ``scripts/`` (not an importable package), so they are
loaded by path via importlib and driven against temporary fixture roots. No
real evidence, dataset, or checkpoint is required.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parents[2] / "scripts"


def _load(module_name: str, filename: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(module_name, SCRIPTS_DIR / filename)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    # Register before exec so dataclass annotation resolution (which looks up
    # sys.modules[cls.__module__]) works on Python 3.12+.
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


env_verifier = _load("verify_jury_environment", "verify_jury_environment.py")
evidence_verifier = _load("verify_jury_release_evidence", "verify_jury_release_evidence.py")


# --- environment verifier ----------------------------------------------------

def _make_good_env_root(root: Path) -> None:
    (root / "frontend" / "src" / "lib").mkdir(parents=True)
    (root / "frontend" / "src" / "components" / "demos").mkdir(parents=True)
    (root / "backend" / "app" / "core").mkdir(parents=True)
    (root / "docs").mkdir(parents=True)
    (root / "frontend" / "package-lock.json").write_text('{"lockfileVersion":3}', encoding="utf-8")
    (root / "frontend" / "Dockerfile").write_text(
        "FROM node:20-slim AS deps\nCOPY package.json package-lock.json ./\nRUN npm ci\n",
        encoding="utf-8",
    )
    (root / "frontend" / "src" / "lib" / "config.ts").write_text(
        "export function deriveWebSocketUrl(u){return u+'/ws/live-feed';}", encoding="utf-8"
    )
    (root / "frontend" / "src" / "components" / "demos" / "DataSourceControl.tsx").write_text(
        "<p>Recorded replay unavailable.</p>", encoding="utf-8"
    )
    (root / "backend" / "app" / "core" / "config.py").write_text("settings = None\n", encoding="utf-8")
    (root / "backend" / "app" / "main.py").write_text(
        "app.add_middleware(CORSMiddleware, allow_origins=settings.allowed_origins)\n", encoding="utf-8"
    )
    (root / "docker-compose.yml").write_text(
        'services:\n  backend:\n    ports: ["8000:8000"]\n    environment:\n'
        '      BIOMIN_ALLOWED_ORIGINS: \'["http://localhost:3000"]\'\n'
        '  frontend:\n    ports: ["3000:3000"]\n', encoding="utf-8"
    )


def test_env_verifier_passes_on_good_root(tmp_path: Path) -> None:
    _make_good_env_root(tmp_path)
    results = env_verifier.run_checks(tmp_path)
    fails = [r for r in results if r.level == env_verifier.FAIL]
    assert fails == [], f"unexpected FAILs: {[(r.name, r.detail) for r in fails]}"
    assert env_verifier.main(["--root", str(tmp_path), "--quiet"]) == 0


def test_env_verifier_fails_on_npm_install_and_missing_lockfile(tmp_path: Path) -> None:
    (tmp_path / "frontend").mkdir()
    (tmp_path / "frontend" / "Dockerfile").write_text(
        "FROM node:20-slim AS deps\nCOPY package.json ./\nRUN npm install\n", encoding="utf-8"
    )
    results = env_verifier.run_checks(tmp_path)
    fail_names = {r.name for r in results if r.level == env_verifier.FAIL}
    assert "frontend-lockfile" in fail_names
    assert "frontend-npm-ci" in fail_names
    assert "frontend-no-npm-install" in fail_names
    assert env_verifier.main(["--root", str(tmp_path)]) == 1


def test_env_verifier_flags_wildcard_cors(tmp_path: Path) -> None:
    _make_good_env_root(tmp_path)
    (tmp_path / "backend" / "app" / "main.py").write_text(
        'app.add_middleware(CORSMiddleware, allow_origins=["*"])\n', encoding="utf-8"
    )
    results = env_verifier.run_checks(tmp_path)
    assert any(r.name == "backend-cors-wildcard" and r.level == env_verifier.FAIL for r in results)


def test_env_verifier_flags_rendered_env_leak(tmp_path: Path) -> None:
    _make_good_env_root(tmp_path)
    leak = "BIOMIN_PPG_DALIA" + "_PATH"
    (tmp_path / "frontend" / "src" / "components" / "demos" / "DataSourceControl.tsx").write_text(
        f"<p>Set {leak} in the backend environment.</p>", encoding="utf-8"
    )
    results = env_verifier.run_checks(tmp_path)
    assert any(r.name == "public-env-leak" and r.level == env_verifier.FAIL for r in results)


def test_env_verifier_allows_env_leak_in_comment(tmp_path: Path) -> None:
    _make_good_env_root(tmp_path)
    leak = "BIOMIN_PPG_DALIA" + "_PATH"
    (tmp_path / "frontend" / "src" / "lib" / "runtimeState.ts").write_text(
        f" * documents the {leak} boundary for developers\n", encoding="utf-8"
    )
    results = env_verifier.run_checks(tmp_path)
    assert any(r.name == "public-env-leak" and r.level == env_verifier.PASS for r in results)


def test_env_verifier_never_prints_secret_values(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("BIOMIN_PPG_DALIA_PATH", "/very/secret/path")
    results = env_verifier.check_env_vars()
    leak_result = next(r for r in results if r.name == "env:BIOMIN_PPG_DALIA_PATH")
    assert "/very/secret/path" not in leak_result.detail
    assert leak_result.detail == "set"


# --- release-evidence verifier -----------------------------------------------

def test_evidence_verifier_incomplete_on_empty_root(tmp_path: Path) -> None:
    resolutions = evidence_verifier.verify(tmp_path)
    assert all(r.status == evidence_verifier.MISSING for r in resolutions)
    assert evidence_verifier.required_incomplete(resolutions)  # non-empty -> incomplete
    assert evidence_verifier.main(["--root", str(tmp_path)]) == 2


def test_evidence_verifier_detects_present_empty_ambiguous(tmp_path: Path) -> None:
    qa = tmp_path / "frontend" / "qa-screenshots" / "codex-independent-final-frontend-audit"
    qa.mkdir(parents=True)
    # PRESENT: single non-empty AUDIT.md
    (qa / "AUDIT.md").write_text("# audit\n", encoding="utf-8")
    # EMPTY: zero-byte matrix
    (qa / "FIVE_STAGE_COMPLETENESS_MATRIX.md").write_text("", encoding="utf-8")
    # AMBIGUOUS: two nominal screenshots
    (qa / "a_nominal.png").write_bytes(b"x")
    (qa / "b_nominal.png").write_bytes(b"y")

    by_id = {r.entry.entry_id: r for r in evidence_verifier.verify(tmp_path)}
    assert by_id["audit-main"].status == evidence_verifier.PRESENT
    assert by_id["audit-matrix"].status == evidence_verifier.EMPTY
    assert by_id["state-nominal"].status == evidence_verifier.AMBIGUOUS
    # Overall still incomplete (many required artifacts remain MISSING).
    assert evidence_verifier.main(["--root", str(tmp_path)]) == 2


def test_evidence_verifier_hash_is_optional_and_deterministic(tmp_path: Path) -> None:
    qa = tmp_path / "frontend" / "qa-screenshots" / "x"
    qa.mkdir(parents=True)
    (qa / "AUDIT.md").write_text("stable-content", encoding="utf-8")
    first = {r.entry.entry_id: r.sha256 for r in evidence_verifier.verify(tmp_path, want_hash=True)}
    second = {r.entry.entry_id: r.sha256 for r in evidence_verifier.verify(tmp_path, want_hash=True)}
    assert first["audit-main"] is not None
    assert first == second  # deterministic
    # Without --hash there is no digest.
    no_hash = {r.entry.entry_id: r.sha256 for r in evidence_verifier.verify(tmp_path, want_hash=False)}
    assert no_hash["audit-main"] is None
