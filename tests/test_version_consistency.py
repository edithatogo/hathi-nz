from __future__ import annotations

import io
import sys
from contextlib import redirect_stdout
from pathlib import Path

import pytest


def _repo_root(start: Path) -> Path:
    for candidate in (start, *start.parents):
        if (candidate / "pixi.toml").exists():
            return candidate
    return start.parents[1]


ROOT = _repo_root(Path(__file__).resolve())
sys.path.insert(0, str(ROOT / "scripts"))

import check_version_consistency as check_version_consistency_module  # noqa: E402
from check_version_consistency import SEMVER_RE, check_version_consistency  # noqa: E402


@pytest.mark.unit
def test_version_consistency_check_passes() -> None:
    assert check_version_consistency() == []


@pytest.mark.unit
def test_version_is_well_formed() -> None:
    import tomllib

    pixi = tomllib.loads((ROOT / "pixi.toml").read_text("utf-8"))
    version = pixi["project"]["version"]
    assert SEMVER_RE.fullmatch(version)


@pytest.mark.unit
def test_pixi_version_matches_git_tag() -> None:
    """pixi.toml version must match the repository git tag."""
    import tomllib

    pixi = tomllib.loads((ROOT / "pixi.toml").read_text("utf-8"))
    git_tag = check_version_consistency_module._git_tag()
    assert git_tag is not None
    assert pixi["project"]["version"] == git_tag.removeprefix("v")


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
            "pyproject.toml": '[build-system]\nrequires = ["hatchling"]\n',
            "pixi.toml": '[project]\nversion = "1.2.4"\n',
        }[path],
    )
    monkeypatch.setattr(check_version_consistency_module, "_git_tag", lambda: "v9.9.9")

    failures = check_version_consistency()

    assert "pyproject.toml build-system missing hatch-vcs dependency" in failures
    assert "Version mismatch: git tag v9.9.9 (→9.9.9) != pixi.toml 1.2.4" in failures


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
