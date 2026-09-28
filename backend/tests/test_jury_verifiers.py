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


def _sha(data: bytes) -> str:
    import hashlib
    return hashlib.sha256(data).hexdigest()


def _write_policy(root: Path, entries: dict) -> Path:
    import json
    policy = root / "policy.json"
    policy.write_text(json.dumps({"version": 1, "entries": entries}), encoding="utf-8")
    return policy


def _rule(canonical: str | None, data: bytes | None = None, *,
          superseded: list[str] | None = None,
          audit_only: list[str] | None = None,
          reviewed: bool = True) -> dict:
    return {
        "canonical": canonical,
        "sha256": _sha(data) if data is not None else None,
        "visually_reviewed": reviewed,
        "superseded": superseded or [],
        "audit_only": audit_only or [],
    }


def test_evidence_verifier_incomplete_on_empty_root(tmp_path: Path) -> None:
    resolutions = evidence_verifier.verify(tmp_path)
    assert all(r.status == evidence_verifier.MISSING for r in resolutions)
    assert evidence_verifier.required_incomplete(resolutions)  # non-empty -> incomplete
    assert evidence_verifier.main(["--root", str(tmp_path)]) == 2


def test_evidence_verifier_detects_present_empty_and_unknown_collision(tmp_path: Path) -> None:
    qa = tmp_path / "frontend" / "qa-screenshots" / "codex-independent-final-frontend-audit"
    qa.mkdir(parents=True)
    audit = b"# audit\n"
    (qa / "AUDIT.md").write_bytes(audit)
    (qa / "FIVE_STAGE_COMPLETENESS_MATRIX.md").write_text("", encoding="utf-8")
    (qa / "a_nominal.png").write_bytes(b"x")
    (qa / "b_nominal.png").write_bytes(b"y")
    policy = _write_policy(tmp_path, {
        "audit-main": _rule(
            "frontend/qa-screenshots/codex-independent-final-frontend-audit/AUDIT.md", audit
        ),
        "audit-matrix": _rule(
            "frontend/qa-screenshots/codex-independent-final-frontend-audit/FIVE_STAGE_COMPLETENESS_MATRIX.md",
            b"",
        ),
        "state-nominal": _rule(
            "frontend/qa-screenshots/codex-independent-final-frontend-audit/a_nominal.png", b"x"
        ),
    })
    by_id = {
        r.entry.entry_id: r
        for r in evidence_verifier.verify(tmp_path, policy_path=policy)
    }
    assert by_id["audit-main"].status == evidence_verifier.PRESENT
    assert by_id["audit-matrix"].status == evidence_verifier.EMPTY
    assert by_id["state-nominal"].status == evidence_verifier.AMBIGUOUS
    assert by_id["state-nominal"].unregistered == [
        "frontend/qa-screenshots/codex-independent-final-frontend-audit/b_nominal.png"
    ]


def test_evidence_verifier_uses_per_entry_policy_and_traces_superseded(tmp_path: Path) -> None:
    older = tmp_path / "frontend" / "qa-screenshots" / "claude-stage2-3-final-acceptance"
    newer = tmp_path / "frontend" / "qa-screenshots" / "claude-stage4-5-real-visual-implementation"
    older.mkdir(parents=True)
    newer.mkdir(parents=True)
    old_audit, new_audit = b"# older audit\n", b"# newer audit\n"
    (older / "AUDIT.md").write_bytes(old_audit)
    (newer / "AUDIT.md").write_bytes(new_audit)
    (older / "state-fault-x.png").write_bytes(b"old")
    (newer / "state-fault-y.png").write_bytes(b"new")
    policy = _write_policy(tmp_path, {
        "audit-main": _rule(
            "frontend/qa-screenshots/claude-stage4-5-real-visual-implementation/AUDIT.md",
            new_audit,
            superseded=["frontend/qa-screenshots/claude-stage2-3-final-acceptance/AUDIT.md"],
        ),
        # Deliberately choose the older run for this different slot. There is no
        # global-run coupling.
        "state-fault": _rule(
            "frontend/qa-screenshots/claude-stage2-3-final-acceptance/state-fault-x.png",
            b"old",
            superseded=["frontend/qa-screenshots/claude-stage4-5-real-visual-implementation/state-fault-y.png"],
        ),
    })
    by_id = {
        r.entry.entry_id: r
        for r in evidence_verifier.verify(tmp_path, policy_path=policy)
    }

    assert by_id["audit-main"].status == evidence_verifier.PRESENT
    assert by_id["audit-main"].canonical.endswith("claude-stage4-5-real-visual-implementation/AUDIT.md")
    assert by_id["audit-main"].superseded == ["frontend/qa-screenshots/claude-stage2-3-final-acceptance/AUDIT.md"]
    assert by_id["state-fault"].status == evidence_verifier.PRESENT
    assert by_id["state-fault"].superseded == [
        "frontend/qa-screenshots/claude-stage4-5-real-visual-implementation/state-fault-y.png"
    ]


def test_unknown_future_run_fails_closed_until_registered(tmp_path: Path) -> None:
    accepted = tmp_path / "frontend" / "qa-screenshots" / "accepted"
    future = tmp_path / "frontend" / "qa-screenshots" / "future-run"
    accepted.mkdir(parents=True)
    future.mkdir(parents=True)
    (accepted / "AUDIT.md").write_bytes(b"accepted")
    (future / "AUDIT.md").write_bytes(b"future")
    policy = _write_policy(tmp_path, {
        "audit-main": _rule("frontend/qa-screenshots/accepted/AUDIT.md", b"accepted")
    })
    result = {
        r.entry.entry_id: r for r in evidence_verifier.verify(tmp_path, policy_path=policy)
    }["audit-main"]
    assert result.status == evidence_verifier.AMBIGUOUS
    assert result.unregistered == ["frontend/qa-screenshots/future-run/AUDIT.md"]


def test_independent_audit_can_be_explicitly_audit_only(tmp_path: Path) -> None:
    accepted = tmp_path / "frontend" / "qa-screenshots" / "accepted"
    independent = tmp_path / "frontend" / "qa-screenshots" / "codex-independent"
    accepted.mkdir(parents=True)
    independent.mkdir(parents=True)
    (accepted / "AUDIT.md").write_bytes(b"accepted")
    (independent / "AUDIT.md").write_bytes(b"review")
    audit_only = "frontend/qa-screenshots/codex-independent/AUDIT.md"
    policy = _write_policy(tmp_path, {
        "audit-main": _rule(
            "frontend/qa-screenshots/accepted/AUDIT.md", b"accepted",
            audit_only=[audit_only],
        )
    })
    result = {
        r.entry.entry_id: r for r in evidence_verifier.verify(tmp_path, policy_path=policy)
    }["audit-main"]
    assert result.status == evidence_verifier.PRESENT
    assert result.canonical == "frontend/qa-screenshots/accepted/AUDIT.md"
    assert result.audit_only == [audit_only]


def test_hash_drift_and_unreviewed_canonical_fail_closed(tmp_path: Path) -> None:
    qa = tmp_path / "frontend" / "qa-screenshots" / "accepted"
    qa.mkdir(parents=True)
    (qa / "AUDIT.md").write_bytes(b"actual")
    canonical = "frontend/qa-screenshots/accepted/AUDIT.md"
    drift = _write_policy(tmp_path, {"audit-main": _rule(canonical, b"different")})
    result = {
        r.entry.entry_id: r for r in evidence_verifier.verify(tmp_path, policy_path=drift)
    }["audit-main"]
    assert result.status == evidence_verifier.AMBIGUOUS
    assert "canonical SHA-256 does not match policy" in result.issues

    unreviewed = _write_policy(
        tmp_path, {"audit-main": _rule(canonical, b"actual", reviewed=False)}
    )
    result2 = {
        r.entry.entry_id: r for r in evidence_verifier.verify(tmp_path, policy_path=unreviewed)
    }["audit-main"]
    assert result2.status == evidence_verifier.AMBIGUOUS
    assert "canonical artifact lacks explicit visual-review approval" in result2.issues


def test_evidence_verifier_hash_output_is_optional_but_validation_is_always_on(tmp_path: Path) -> None:
    qa = tmp_path / "frontend" / "qa-screenshots" / "x"
    qa.mkdir(parents=True)
    data = b"stable-content"
    (qa / "AUDIT.md").write_bytes(data)
    policy = _write_policy(tmp_path, {
        "audit-main": _rule("frontend/qa-screenshots/x/AUDIT.md", data)
    })
    first = {
        r.entry.entry_id: r.sha256
        for r in evidence_verifier.verify(tmp_path, want_hash=True, policy_path=policy)
    }
    second = {
        r.entry.entry_id: r.sha256
        for r in evidence_verifier.verify(tmp_path, want_hash=True, policy_path=policy)
    }
    assert first["audit-main"] is not None
    assert first == second
    no_hash = {
        r.entry.entry_id: r.sha256
        for r in evidence_verifier.verify(tmp_path, want_hash=False, policy_path=policy)
    }
    assert no_hash["audit-main"] is None
