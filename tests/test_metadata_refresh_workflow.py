"""Tests for the HathiTrust-NZ metadata refresh workflow."""

from __future__ import annotations

from pathlib import Path


def _repo_root(start: Path) -> Path:
    for candidate in (start, *start.parents):
        if (candidate / "pixi.toml").exists():
            return candidate
    return start.parents[1]


ROOT = _repo_root(Path(__file__).resolve())
WORKFLOW_PATH = ROOT / ".github/workflows/metadata_refresh.yml"


def test_metadata_refresh_workflow_exists() -> None:
    assert WORKFLOW_PATH.exists()


def test_metadata_refresh_workflow_covers_metadata_refresh_lanes() -> None:
    workflow = WORKFLOW_PATH.read_text(encoding="utf-8")

    assert "HathiTrust-NZ Metadata Refresh" in workflow
    assert "metadata-refresh" in workflow
    assert "oai_cursor" in workflow
    assert "scripts/hathitrust_nz_archive.py metadata-refresh" in workflow
    assert "Build metadata refresh bundle" in workflow
    assert "hathitrust-nz-metadata-refresh" in workflow
