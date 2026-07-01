"""Tests for the Zenodo GitHub Actions release workflow."""

from __future__ import annotations

from pathlib import Path


def _repo_root(start: Path) -> Path:
    for candidate in (start, *start.parents):
        if (candidate / "pixi.toml").exists():
            return candidate
    return start.parents[1]


ROOT = _repo_root(Path(__file__).resolve())
WORKFLOW_PATH = ROOT / ".github/workflows/zenodo_release.yml"
README_PATH = ROOT / "README.md"
DATASET_CARD_PATH = ROOT / "DATASET_CARD.md"


def test_zenodo_release_workflow_exists() -> None:
    assert WORKFLOW_PATH.exists()


def test_zenodo_release_workflow_covers_release_trigger_and_version_input() -> None:
    workflow = WORKFLOW_PATH.read_text(encoding="utf-8")

    assert "release:" in workflow
    assert "types:" in workflow
    assert "published" in workflow
    assert "workflow_dispatch:" in workflow
    assert "version:" in workflow
    assert "production:" in workflow
    assert "workflow_dispatch requires a version input" in workflow


def test_zenodo_release_workflow_invokes_release_pipeline() -> None:
    workflow = WORKFLOW_PATH.read_text(encoding="utf-8")

    assert "scripts/check_version_consistency.py" in workflow
    assert "scripts/package_release.py" in workflow
    assert "scripts/publish_zenodo.py" in workflow
    assert "set -euo pipefail" in workflow
    assert "--publish" in workflow
    assert "--execute" in workflow
    assert "DATASET_CARD.md" in workflow
    assert "ZENODO_TOKEN" in workflow
    assert "GITHUB_STEP_SUMMARY" in workflow
    assert "id: publish" in workflow


def test_release_docs_point_to_zenodo_workflow() -> None:
    readme = README_PATH.read_text(encoding="utf-8")
    dataset_card = DATASET_CARD_PATH.read_text(encoding="utf-8")

    assert "Zenodo DOI" in readme
    assert "Zenodo Release Workflow" in readme
    assert "workflow_dispatch" in readme
    assert "Zenodo Release Workflow" in dataset_card
    assert "workflow_dispatch" in dataset_card
