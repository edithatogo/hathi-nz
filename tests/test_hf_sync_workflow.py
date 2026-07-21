"""Regression tests for the rights-gated Hugging Face sync workflow."""

from __future__ import annotations

from pathlib import Path


def _repo_root(start: Path) -> Path:
    for candidate in (start, *start.parents):
        if (candidate / "pixi.toml").exists():
            return candidate
    return start.parents[1]


def test_hf_sync_is_metadata_only_and_fail_closed() -> None:
    workflow = (
        _repo_root(Path(__file__).resolve())
        / ".github/workflows/hf_sync.yml"
    ).read_text(encoding="utf-8")

    assert "Build metadata-only publication bundle" in workflow
    assert "upload_hf_folder.py" in workflow
    assert "stage_hf_dataset.py" not in workflow
    assert "HATHI_API_CONSUMER_KEY" not in workflow
    assert "--path-in-repo \"archive-metadata\"" in workflow
    assert "--stage-dir" not in workflow
