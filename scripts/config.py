"""Typed configuration for hathi-nz pipeline.

Uses pydantic-settings to load configuration from environment variables
and ``.env`` files with type validation and secret masking.

Usage::

    from config import get_settings

    settings = get_settings()
    token = settings.HF_TOKEN.get_secret_value()
"""

from __future__ import annotations

from functools import lru_cache

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Pipeline configuration loaded from environment / .env files."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True,
    )

    # Hugging Face Hub
    HF_TOKEN: SecretStr | None = None
    HF_REPO_ID: str = "edithatogo/corpus-nz-hathi"
    HF_COLLECTION_ID: str = "edithatogo/hathitrust-nz"
    HF_INVENTORY_REPO_ID: str = "edithatogo/hathitrust-nz-inventory"
    HF_RESEARCH_FULLTEXT_REPO_ID: str = "edithatogo/hathitrust-nz-research-fulltext"
    HF_HTRC_EF_REPO_ID: str = "edithatogo/hathitrust-nz-htrc-extracted-features"
    HF_HTRC_ANALYTICS_REPO_ID: str = "edithatogo/hathitrust-nz-htrc-analytics"

    # Zenodo
    ZENODO_TOKEN: SecretStr | None = None
    ZENODO_SANDBOX: bool = False

    # OSF
    OSF_TOKEN: SecretStr | None = None
    OSF_PROJECT_ID: str | None = None

    # HathiTrust
    COLLECTION_ID: str = "71329709"
    HATHI_RSYNC_HOST: str | None = None
    HATHI_RSYNC_MODULE: str | None = None
    HATHI_RSYNC_USER: str | None = None
    HATHI_STATIC_HOST_SSH_KEY: SecretStr | None = None
    HATHI_STATIC_HOST_STAGING_DIR: str | None = None
    HTRC_EF_RSYNC_MODULE: str = "data.analytics.hathitrust.org::features-2025.04/"

    # Logging
    LOG_LEVEL: str = "INFO"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached ``Settings`` instance."""
    return Settings()
