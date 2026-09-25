"""CORS / allowed-origins configuration tests.

Exercise the deterministic environment parsing of ``Settings.allowed_origins``
without importing the full FastAPI app (only pydantic / pydantic-settings are
needed). Each test constructs a fresh ``Settings(_env_file=None)`` so no stray
``.env`` on disk can influence the result.
"""

from __future__ import annotations

import pytest

from app.core.config import Settings

DEFAULT_ORIGINS = ["http://localhost:3000", "http://127.0.0.1:3000"]


def _settings(monkeypatch: pytest.MonkeyPatch, value: str | None) -> Settings:
    if value is None:
        monkeypatch.delenv("BIOMIN_ALLOWED_ORIGINS", raising=False)
    else:
        monkeypatch.setenv("BIOMIN_ALLOWED_ORIGINS", value)
    return Settings(_env_file=None)


def test_default_allowed_origins(monkeypatch: pytest.MonkeyPatch) -> None:
    assert _settings(monkeypatch, None).allowed_origins == DEFAULT_ORIGINS


def test_no_wildcard_in_default(monkeypatch: pytest.MonkeyPatch) -> None:
    assert "*" not in _settings(monkeypatch, None).allowed_origins


def test_valid_override_two_exact_origins(monkeypatch: pytest.MonkeyPatch) -> None:
    value = '["https://a.example.org","https://b.example.org"]'
    assert _settings(monkeypatch, value).allowed_origins == [
        "https://a.example.org",
        "https://b.example.org",
    ]


def test_production_example_single_https_origin(monkeypatch: pytest.MonkeyPatch) -> None:
    value = '["https://demo.example.org"]'
    assert _settings(monkeypatch, value).allowed_origins == ["https://demo.example.org"]


def test_invalid_non_json_format_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    # A comma-separated string is not a JSON list -> parsing must fail loudly,
    # never silently widen access.
    with pytest.raises(Exception):
        _settings(monkeypatch, "http://a,http://b")


def test_wildcard_origin_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    with pytest.raises(Exception):
        _settings(monkeypatch, '["*"]')


def test_empty_origin_list_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    with pytest.raises(Exception):
        _settings(monkeypatch, "[]")


def test_blank_origin_entry_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    with pytest.raises(Exception):
        _settings(monkeypatch, '["http://ok"," "]')


def test_whitespace_is_trimmed(monkeypatch: pytest.MonkeyPatch) -> None:
    value = '[" https://trimmed.example.org "]'
    assert _settings(monkeypatch, value).allowed_origins == ["https://trimmed.example.org"]
