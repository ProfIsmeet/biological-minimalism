"""Static deployment-contract assertions (stdlib only).

These tests do not import the FastAPI app and do not require Docker. They read
the deployment/config files directly and assert the F-08 / F-18 hardening
contract: deterministic frontend install, explicit + non-wildcard CORS, an
explicit API/WS contract, and no backend setup leakage in public frontend copy.
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
LEAK_TOKEN = "BIOMIN_PPG_DALIA" + "_PATH"  # keep this test file itself clean


def _read(rel: str) -> str:
    return (REPO_ROOT / rel).read_text(encoding="utf-8")


def _executable_directives(dockerfile_text: str) -> str:
    """Dockerfile lines that are not comments (so comments can mention things)."""
    return "\n".join(
        line for line in dockerfile_text.splitlines() if not line.lstrip().startswith("#")
    )


# --- Task A: deterministic frontend Docker install ---------------------------

def test_frontend_dockerfile_uses_npm_ci() -> None:
    directives = _executable_directives(_read("frontend/Dockerfile"))
    assert "npm ci" in directives


def test_frontend_dockerfile_copies_lockfile() -> None:
    assert "package-lock.json" in _read("frontend/Dockerfile")


def test_frontend_dockerfile_has_no_npm_install_directive() -> None:
    directives = _executable_directives(_read("frontend/Dockerfile"))
    assert "npm install" not in directives


def test_frontend_lockfile_exists_and_nonempty() -> None:
    lockfile = REPO_ROOT / "frontend" / "package-lock.json"
    assert lockfile.is_file() and lockfile.stat().st_size > 0


# --- Task B: explicit, non-wildcard CORS + API/WS contract -------------------

def test_backend_cors_is_not_wildcard() -> None:
    main_py = _read("backend/app/main.py").replace(" ", "")
    assert 'allow_origins=["*"]' not in main_py
    assert "allow_origin_regex" not in main_py


def test_compose_sets_explicit_non_wildcard_cors() -> None:
    compose = _read("docker-compose.yml")
    assert "BIOMIN_ALLOWED_ORIGINS" in compose
    assert '["*"]' not in compose.replace(" ", "")


def test_compose_pins_api_and_ws_build_args() -> None:
    compose = _read("docker-compose.yml")
    assert "NEXT_PUBLIC_API_BASE_URL" in compose
    assert "NEXT_PUBLIC_WS_URL" in compose


def test_compose_preserves_standard_local_ports() -> None:
    compose = _read("docker-compose.yml")
    assert "3000:3000" in compose
    assert "8000:8000" in compose


def test_config_ts_exposes_ws_derivation_contract() -> None:
    config = _read("frontend/src/lib/config.ts")
    assert "deriveWebSocketUrl" in config
    assert "/ws/live-feed" in config
    # empty-string coercion so an explicit-but-empty build arg falls back safely
    assert ".trim()" in config


# --- Task C / F-18: no backend setup leakage in public frontend copy ---------

def test_data_source_control_has_no_backend_env_leak() -> None:
    assert LEAK_TOKEN not in _read("frontend/src/components/demos/DataSourceControl.tsx")


def test_data_source_control_has_no_backend_setup_instructions() -> None:
    text = _read("frontend/src/components/demos/DataSourceControl.tsx").lower()
    for forbidden in ("in the backend environment", "export biomin", "/data/ppg-dalia", "uvicorn"):
        assert forbidden not in text


def test_no_rendered_env_leak_in_public_frontend_source() -> None:
    """The backend env var must not appear in RENDERED frontend copy.

    Occurrences on developer comment lines are allowed (the identifier may
    legitimately be documented in protected runtime modules and in backend
    code / operator docs, which this test does not police).
    """
    src = REPO_ROOT / "frontend" / "src"
    offenders: list[str] = []
    for path in sorted(src.rglob("*.ts*")):
        text = path.read_text(encoding="utf-8")
        if LEAK_TOKEN not in text:
            continue
        for lineno, line in enumerate(text.splitlines(), start=1):
            if LEAK_TOKEN in line and not line.lstrip().startswith(("*", "//", "/*")):
                offenders.append(f"{path.relative_to(REPO_ROOT)}:{lineno}")
    assert offenders == [], f"rendered copy exposes backend env var: {offenders}"
