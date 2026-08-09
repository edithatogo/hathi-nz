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
SECURITY_GATE_PATH = ROOT / ".github/workflows/security_gate.yml"
HF_SYNC_PATH = ROOT / ".github/workflows/hf_sync.yml"
CODECOV_PATH = ROOT / "codecov.yml"
PROFILE_PATH = ROOT / "scripts/profile_pipelines.py"
STAGE_HF_PATH = ROOT / "scripts/stage_hf_dataset.py"


def test_pyproject_declares_quality_tooling() -> None:
    content = PYPROJECT_PATH.read_text(encoding="utf-8")

    assert "pyright" in content
    assert "[tool.pyright]" in content
    assert "mutmut" in content
    assert "[tool.mutmut]" in content
    assert "tenacity" in content
    assert "fail_under = 90" in content


def test_pixi_declares_quality_tooling_tasks() -> None:
    content = PIXI_PATH.read_text(encoding="utf-8")

    assert "pyright" in content
    assert "pyright-check" in content
    assert "mutmut" in content
    assert "scalene" in content
    assert "tenacity" in content
    assert "profile-pipelines-scalene" in content
    assert "lint-strict" in content


def test_ci_runs_mutmutation_and_enforces_coverage() -> None:
    content = CI_PATH.read_text(encoding="utf-8")

    assert "mutmut" in content
    assert "codecov/codecov-action@v5" in content
    assert "use_oidc: true" in content
    assert "--cov-report=xml" in content
    assert "--cov-fail-under=90" in content or "--cov-fail-under=90" in PIXI_PATH.read_text(
        encoding="utf-8"
    )


def test_security_gate_fails_on_high_or_critical_alerts() -> None:
    content = SECURITY_GATE_PATH.read_text(encoding="utf-8")

    assert "security-events: read" in content
    assert 'security_severity_level == "high"' in content
    assert 'security_severity_level == "critical"' in content
    assert 'test "${count}" -eq 0' in content


def test_retired_hathitrust_data_api_signer_is_absent() -> None:
    content = STAGE_HF_PATH.read_text(encoding="utf-8")

    assert "HMAC-SHA1" not in content
    assert "HATHI_API_CONSUMER_SECRET" not in content
    assert "/cgi/htd/aggregate" not in content


def test_hf_sync_is_not_blocked_by_auxiliary_coverage_upload() -> None:
    hf_content = HF_SYNC_PATH.read_text(encoding="utf-8")
    ci_content = CI_PATH.read_text(encoding="utf-8")

    assert "codecov/codecov-action@v5" not in hf_content
    assert "HATHI_API_CONSUMER_KEY" not in hf_content
    assert "PYTHON_VERSION" not in hf_content
    assert "codecov/codecov-action@v5" in ci_content
    assert "--cov-report=xml" in ci_content


def test_codecov_configuration_sets_project_target() -> None:
    content = CODECOV_PATH.read_text(encoding="utf-8")

    assert "target: 90%" in content
    assert "comment:" in content


def test_profile_script_uses_scalene() -> None:
    content = PROFILE_PATH.read_text(encoding="utf-8")

    assert "scalene" in content
    assert "subprocess.run" in content
