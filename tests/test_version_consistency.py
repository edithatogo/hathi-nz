from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from check_version_consistency import SEMVER_RE, check_version_consistency  # noqa: E402


@pytest.mark.unit
def test_version_consistency_check_passes() -> None:
    assert check_version_consistency() == []


@pytest.mark.unit
def test_version_is_well_formed() -> None:
    version = (ROOT / "VERSION").read_text("utf-8").strip()
    assert SEMVER_RE.fullmatch(version)


@pytest.mark.unit
def test_pixi_version_matches_version_file() -> None:
    """pixi.toml version must match VERSION file."""
    import tomllib

    version_file = (ROOT / "VERSION").read_text("utf-8").strip()
    pixi = tomllib.loads((ROOT / "pixi.toml").read_text("utf-8"))
    assert pixi["project"]["version"] == version_file


@pytest.mark.unit
def test_pyproject_uses_dynamic_versioning() -> None:
    """pyproject.toml must use hatch-vcs dynamic versioning."""
    import tomllib

    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text("utf-8"))
    assert "version" not in pyproject["project"], "version should be dynamic, not static"
    assert "dynamic" in pyproject["project"]
    assert "version" in pyproject["project"]["dynamic"]
    build_sys = pyproject.get("build-system", {})
    assert "hatch-vcs" in build_sys.get("requires", [])
