"""Tests for dynamic version resolution (scripts/_version.py)."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from _version import get_version  # noqa: E402


@pytest.mark.unit
def test_get_version_returns_non_empty_string() -> None:
    """Version must always resolve to a non-empty string."""
    version = get_version()
    assert isinstance(version, str)
    assert len(version) > 0


@pytest.mark.unit
def test_get_version_from_git_describe() -> None:
    """When git describe returns a tag, it should be used."""
    with patch("subprocess.run") as mock_run:
        mock_run.return_value.stdout = "v0.1.0\n"
        mock_run.return_value.returncode = 0
        version = get_version()
        assert version == "v0.1.0"


@pytest.mark.unit
def test_get_version_strips_whitespace() -> None:
    """Version should be stripped of whitespace."""
    with patch("subprocess.run") as mock_run:
        mock_run.return_value.stdout = "  v1.2.3  \n"
        mock_run.return_value.returncode = 0
        version = get_version()
        assert version == "v1.2.3"


@pytest.mark.unit
def test_get_version_fallback_on_no_tags() -> None:
    """When git describe returns a commit SHA (no tags), fall back."""
    with patch("subprocess.run") as mock_run:
        # Returns commit SHA when no tags exist
        mock_run.return_value.stdout = "abc1234\n"
        mock_run.return_value.returncode = 0
        version = get_version()
        assert isinstance(version, str)
        assert len(version) > 0


@pytest.mark.unit
def test_get_version_fallback_on_git_error() -> None:
    """When git is not available, fall back gracefully."""
    with patch("subprocess.run", side_effect=FileNotFoundError):
        version = get_version()
        assert isinstance(version, str)
        assert len(version) > 0
