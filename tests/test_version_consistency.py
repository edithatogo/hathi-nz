from __future__ import annotations

import io
import sys
from contextlib import redirect_stdout
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import check_version_consistency as check_version_consistency_module  # noqa: E402
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


@pytest.mark.unit
def test_check_version_consistency_reports_all_failures(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        check_version_consistency_module,
        "_text",
        lambda path: {
            "VERSION": "1.2.3",
            "pyproject.toml": '[build-system]\nrequires = ["hatchling"]\n',
            "pixi.toml": '[project]\nversion = "1.2.4"\n',
        }[path],
    )
    monkeypatch.setattr(check_version_consistency_module, "_git_tag", lambda: "v9.9.9")

    failures = check_version_consistency()

    assert "pyproject.toml build-system missing hatch-vcs dependency" in failures
    assert "Version mismatch: pixi.toml 1.2.4 != VERSION 1.2.3" in failures
    assert "Version mismatch: git tag v9.9.9 (→9.9.9) != VERSION 1.2.3" in failures


@pytest.mark.unit
def test_main_prints_failures(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        check_version_consistency_module,
        "check_version_consistency",
        lambda: ["version mismatch"],
    )

    buffer = io.StringIO()
    with redirect_stdout(buffer):
        exit_code = check_version_consistency_module.main()

    assert exit_code == 1
    assert buffer.getvalue().strip() == "ERROR: version mismatch"
