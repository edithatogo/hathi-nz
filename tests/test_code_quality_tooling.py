"""Tests for the code-quality tooling enhancement track."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PYPROJECT_PATH = ROOT / "pyproject.toml"
PIXI_PATH = ROOT / "pixi.toml"
CI_PATH = ROOT / ".github/workflows/ci.yml"
PROFILE_PATH = ROOT / "scripts/profile_pipelines.py"


def test_pyproject_declares_quality_tooling() -> None:
    content = PYPROJECT_PATH.read_text(encoding="utf-8")

    assert "pyright" in content
    assert "[tool.pyright]" in content
    assert "mutmut" in content
    assert "[tool.mutmut]" in content
    assert "fail_under = 75" in content


def test_pixi_declares_quality_tooling_tasks() -> None:
    content = PIXI_PATH.read_text(encoding="utf-8")

    assert "pyright" in content
    assert "pyright-check" in content
    assert "mutmut" in content
    assert "scalene" in content
    assert "profile-pipelines-scalene" in content


def test_ci_runs_mutmutation_and_enforces_coverage() -> None:
    content = CI_PATH.read_text(encoding="utf-8")

    assert "mutmut" in content
    assert "--cov-fail-under=75" in content


def test_profile_script_uses_scalene() -> None:
    content = PROFILE_PATH.read_text(encoding="utf-8")

    assert "scalene" in content
    assert "subprocess.run" in content
