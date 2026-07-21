"""Regression tests for complete Hugging Face provenance publication."""

from pathlib import Path


def test_hf_provenance_workflow_publishes_all_child_cards() -> None:
    root = Path(__file__).resolve().parents[1]
    workflow = (root / ".github/workflows/hf_provenance_sync.yml").read_text(
        encoding="utf-8"
    )

    for dataset_id in (
        "corpus-nz-hathi",
        "hathitrust-nz-inventory",
        "hathitrust-nz-research-fulltext",
        "hathitrust-nz-htrc-extracted-features",
        "hathitrust-nz-htrc-analytics",
    ):
        assert dataset_id in workflow
    assert "README.md" in workflow
    assert "PROVENANCE.md" in workflow
    assert "PUBLICATION_METADATA.json" in workflow
    assert "sync_hf_collection.py" in workflow
