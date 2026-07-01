"""Tests for dynamic version resolution (scripts/_version.py)."""

from __future__ import annotations

import sys
from importlib.metadata import PackageNotFoundError
from pathlib import Path
from unittest.mock import patch

import pytest


def _repo_root(start: Path) -> Path:
    for candidate in (start, *start.parents):
        if (candidate / "pixi.toml").exists():
            return candidate
    return start.parents[1]


ROOT = _repo_root(Path(__file__).resolve())
sys.path.insert(0, str(ROOT / "scripts"))

import _version as version_module  # noqa: E402
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


@pytest.mark.unit
def test_read_version_file_reads_from_repo_root(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    version_file = tmp_path / "VERSION"
    version_file.write_text("1.2.3\n", encoding="utf-8")
    monkeypatch.setattr(version_module, "ROOT", tmp_path)

    assert version_module._read_version_file() == "1.2.3"


@pytest.mark.unit
def test_from_metadata_returns_installed_version(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(version_module, "_md_version", lambda _: "4.5.6")

    assert version_module._from_metadata() == "4.5.6"


@pytest.mark.unit
def test_from_metadata_returns_none_when_package_is_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def raise_not_found(_: str) -> str:
        raise PackageNotFoundError

    monkeypatch.setattr(version_module, "_md_version", raise_not_found)

    assert version_module._from_metadata() is None


@pytest.mark.unit
@pytest.mark.parametrize(
    ("candidate", "expected"),
    [
        ("1.2.3", True),
        ("v1.2.3", True),
        ("abc1234", False),
        ("vabc1234", False),
        ("", False),
    ],
)
def test_looks_like_version(candidate: str, expected: bool) -> None:
    assert version_module._looks_like_version(candidate) is expected
