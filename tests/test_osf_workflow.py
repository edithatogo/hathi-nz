"""Regression tests for OSF publication configuration."""

from pathlib import Path


def test_osf_workflow_reads_project_id_variable_with_secret_fallback() -> None:
    root = Path(__file__).resolve().parents[1]
    workflow = (root / ".github/workflows/osf_sync.yml").read_text(encoding="utf-8")

    assert "vars.OSF_PROJECT_ID || secrets.OSF_PROJECT_ID" in workflow
    assert "docs/provenance-and-reproducibility.md" in (root / ".osf.json").read_text(
        encoding="utf-8"
    )
