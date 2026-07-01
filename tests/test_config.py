"""Tests for scripts/config.py Settings class."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest


def _repo_root(start: Path) -> Path:
    for candidate in (start, *start.parents):
        if (candidate / "pixi.toml").exists():
            return candidate
    return start.parents[1]


ROOT = _repo_root(Path(__file__).resolve())
sys.path.insert(0, str(ROOT / "scripts"))

pytest.importorskip("pydantic_settings")

from config import Settings, get_settings  # noqa: E402


@pytest.mark.unit
def test_settings_has_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    """Settings should provide sensible defaults."""
    monkeypatch.delenv("OSF_TOKEN", raising=False)
    monkeypatch.delenv("OSF_PROJECT_ID", raising=False)
    settings = Settings()
    assert settings.HF_REPO_ID == "edithatogo/corpus-nz-hathi"
    assert settings.COLLECTION_ID == "71329709"
    assert settings.LOG_LEVEL == "INFO"
    assert settings.ZENODO_SANDBOX is False
    assert settings.OSF_TOKEN is None
    assert settings.OSF_PROJECT_ID is None


@pytest.mark.unit
def test_settings_hf_token_is_secret() -> None:
    """HF_TOKEN should be stored as SecretStr."""
    settings = Settings(HF_TOKEN="hf_test_token")
    assert settings.HF_TOKEN is not None
    assert settings.HF_TOKEN.get_secret_value() == "hf_test_token"


@pytest.mark.unit
def test_settings_token_none_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    """Tokens should be None when not provided (no .env loading)."""
    monkeypatch.delenv("OSF_TOKEN", raising=False)
    monkeypatch.delenv("OSF_PROJECT_ID", raising=False)
    settings = Settings(_env_file=None)
    assert settings.HF_TOKEN is None
    assert settings.ZENODO_TOKEN is None
    assert settings.OSF_TOKEN is None


@pytest.mark.unit
def test_get_settings_returns_cached_instance() -> None:
    """get_settings should return a cached instance."""
    get_settings.cache_clear()
    s1 = get_settings()
    s2 = get_settings()
    assert s1 is s2


@pytest.mark.unit
def test_settings_env_loading(monkeypatch: pytest.MonkeyPatch) -> None:
    """Settings should load from environment variables."""
    monkeypatch.setenv("HF_TOKEN", "hf_env_token")
    monkeypatch.setenv("COLLECTION_ID", "12345678")
    monkeypatch.setenv("OSF_TOKEN", "osf_env_token")
    monkeypatch.setenv("OSF_PROJECT_ID", "abcd1")
    settings = Settings()
    assert settings.HF_TOKEN is not None
    assert settings.HF_TOKEN.get_secret_value() == "hf_env_token"
    assert settings.COLLECTION_ID == "12345678"
    assert settings.OSF_TOKEN is not None
    assert settings.OSF_TOKEN.get_secret_value() == "osf_env_token"
    assert settings.OSF_PROJECT_ID == "abcd1"
