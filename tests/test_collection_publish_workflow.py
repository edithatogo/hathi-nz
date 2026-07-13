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
    assert "source-policy" in workflow
    assert "internet-archive" in workflow
    assert "metadata-refresh" in workflow
    assert "status-report" in workflow
    assert "htrc-analytics-plan" in workflow
    assert 'cp "$BUILD_DIR/research_datasets/internet_archive"' in workflow
    assert (
        'cp "$BUILD_DIR/collection/collection_manifest.json" "$BUILD_DIR/reports/source-policy/collection_manifest.json"'
        in workflow
    )
    assert '--status-report "$BUILD_DIR/reports/status/status_report.json"' in workflow
    assert (
        '--publication-evidence "$BUILD_DIR/publication_evidence/publication_evidence.json"'
        in workflow
    )
    assert '--blocker-report "$BUILD_DIR/blockers/blocker_report.json"' in workflow
    assert '--htrc-ef "$BUILD_DIR/htrc_ef/htrc_ef25_manifest.json"' in workflow
    assert '--htrc-analytics "$BUILD_DIR/htrc_analytics/htrc_analytics_manifest.json"' in workflow
    assert "publication-evidence" in workflow
    assert 'CARD_DIR="dataset_cards"' in workflow
