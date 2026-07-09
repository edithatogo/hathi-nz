"""Tests for the publication status workflow."""

from __future__ import annotations

from pathlib import Path


def _repo_root(start: Path) -> Path:
    for candidate in (start, *start.parents):
        if (candidate / "pixi.toml").exists():
            return candidate
    return start.parents[1]


ROOT = _repo_root(Path(__file__).resolve())
WORKFLOW_PATH = ROOT / ".github/workflows/publication_status.yml"
PIXITOML_PATH = ROOT / "pixi.toml"


def test_publication_status_workflow_exists() -> None:
    assert WORKFLOW_PATH.exists()


def test_publication_status_workflow_reports_non_blocking_status() -> None:
    workflow = WORKFLOW_PATH.read_text(encoding="utf-8")

    assert "Publication Status" in workflow
    assert "schedule:" in workflow
    assert "workflow_dispatch" in workflow
    assert "workflow_run_id" in workflow
    assert "actions/download-artifact@v5" in workflow
    assert "pixi run -e dev publication-status" in workflow
    assert '--status-report "$RUNNER_TEMP/publication-status-artifact/reports/status/status_report.json"' in workflow
    assert '--publication-evidence "$RUNNER_TEMP/publication-status-artifact/publication_evidence/publication_evidence.json"' in workflow


def test_pixi_declares_publication_status_task() -> None:
    pixi = PIXITOML_PATH.read_text(encoding="utf-8")

    assert "publication-status" in pixi
    assert "check_publication_status.py" in pixi
