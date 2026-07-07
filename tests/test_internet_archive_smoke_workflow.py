"""Tests for the Internet Archive smoke workflow."""

from __future__ import annotations

from pathlib import Path


def _repo_root(start: Path) -> Path:
    for candidate in (start, *start.parents):
        if (candidate / "pixi.toml").exists():
            return candidate
    return start.parents[1]


ROOT = _repo_root(Path(__file__).resolve())
WORKFLOW_PATH = ROOT / ".github/workflows/internet_archive_smoke.yml"


def test_internet_archive_smoke_workflow_exists() -> None:
    assert WORKFLOW_PATH.exists()


def test_internet_archive_smoke_workflow_uses_dry_run() -> None:
    workflow = WORKFLOW_PATH.read_text(encoding="utf-8")

    assert "HathiTrust-NZ Internet Archive Smoke" in workflow
    assert 'schedule:\n    - cron: "17 3 * * 1"' in workflow
    assert "--dry-run" in workflow
    assert 'default: "1"' in workflow
