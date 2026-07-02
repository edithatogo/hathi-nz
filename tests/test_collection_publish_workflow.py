"""Tests for the HathiTrust-NZ collection publish workflow."""

from __future__ import annotations

from pathlib import Path


def _repo_root(start: Path) -> Path:
    for candidate in (start, *start.parents):
        if (candidate / "pixi.toml").exists():
            return candidate
    return start.parents[1]


ROOT = _repo_root(Path(__file__).resolve())
WORKFLOW_PATH = ROOT / ".github/workflows/collection_publish.yml"


def test_collection_publish_workflow_exists() -> None:
    assert WORKFLOW_PATH.exists()


def test_collection_publish_workflow_runs_strict_publication_status_gate() -> None:
    workflow = WORKFLOW_PATH.read_text(encoding="utf-8")

    assert "Commit Zenodo DOI writebacks" in workflow
    assert "Verify publication status" in workflow
    assert "publication-status --strict" in workflow
    assert "inputs.publish_zenodo && inputs.production" in workflow
