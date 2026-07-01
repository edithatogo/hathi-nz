"""Tests for the code-quality tooling enhancement track."""

from __future__ import annotations

from pathlib import Path


def _repo_root(start: Path) -> Path:
    for candidate in (start, *start.parents):
        if (candidate / "pixi.toml").exists():
            return candidate
    return start.parents[1]


ROOT = _repo_root(Path(__file__).resolve())
PYPROJECT_PATH = ROOT / "pyproject.toml"
PIXI_PATH = ROOT / "pixi.toml"
CI_PATH = ROOT / ".github/workflows/ci.yml"
HF_SYNC_PATH = ROOT / ".github/workflows/hf_sync.yml"
CODECOV_PATH = ROOT / "codecov.yml"
PROFILE_PATH = ROOT / "scripts/profile_pipelines.py"


def test_pyproject_declares_quality_tooling() -> None:
    content = PYPROJECT_PATH.read_text(encoding="utf-8")

    assert "pyright" in content
    assert "[tool.pyright]" in content
    assert "mutmut" in content
    assert "[tool.mutmut]" in content
    assert "tenacity" in content
    assert "fail_under = 75" in content


def test_pixi_declares_quality_tooling_tasks() -> None:
    content = PIXI_PATH.read_text(encoding="utf-8")

    assert "pyright" in content
    assert "pyright-check" in content
    assert "mutmut" in content
    assert "scalene" in content
    assert "tenacity" in content
    assert "profile-pipelines-scalene" in content


def test_ci_runs_mutmutation_and_enforces_coverage() -> None:
    content = CI_PATH.read_text(encoding="utf-8")

    assert "mutmut" in content
    assert "codecov/codecov-action@v5" in content
    assert "use_oidc: true" in content
    assert "--cov-report=xml" in content
    assert "--cov-fail-under=75" in content


def test_hf_sync_uploads_coverage_and_has_no_dead_python_env() -> None:
    content = HF_SYNC_PATH.read_text(encoding="utf-8")

    assert "codecov/codecov-action@v5" in content
    assert "use_oidc: true" in content
    assert "--cov-report=xml" in content
    assert "PYTHON_VERSION" not in content


def test_codecov_configuration_sets_project_target() -> None:
    content = CODECOV_PATH.read_text(encoding="utf-8")

    assert "target: 75%" in content
    assert "comment:" in content


def test_profile_script_uses_scalene() -> None:
    content = PROFILE_PATH.read_text(encoding="utf-8")

    assert "scalene" in content
    assert "subprocess.run" in content
