"""Tests for generic Hugging Face folder upload helper."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from scripts import upload_hf_folder
from scripts.upload_hf_folder import parse_args, upload_folder_to_hf


def test_upload_folder_dry_run_lists_files(tmp_path: Path) -> None:
    source_dir = tmp_path / "archive"
    source_dir.mkdir()
    (source_dir / "manifest.json").write_text("{}", encoding="utf-8")
    (source_dir / "nested").mkdir()
    (source_dir / "nested" / "htids.txt").write_text("uc1.test\n", encoding="utf-8")

    result = upload_folder_to_hf(
        source_dir=source_dir,
        repo_id="edithatogo/hathitrust-nz-inventory",
        path_in_repo="manifests",
        dry_run=True,
    )

    assert result["dry_run"] is True
    assert result["file_count"] == 2
    assert result["files"] == ["manifest.json", "nested/htids.txt"]


def test_upload_folder_missing_source_raises(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        upload_folder_to_hf(
            source_dir=tmp_path / "missing",
            repo_id="edithatogo/hathitrust-nz-inventory",
            dry_run=True,
        )


def test_upload_folder_execute_uses_hf_api(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source_dir = tmp_path / "archive"
    source_dir.mkdir()
    (source_dir / "manifest.json").write_text("{}", encoding="utf-8")

    class MockApi:
        def __init__(self) -> None:
            self.uploaded: dict[str, Any] = {}

        def upload_folder(
            self,
            *,
            repo_id: str,
            repo_type: str,
            folder_path: str,
            path_in_repo: str,
            commit_message: str,
        ) -> str:
            self.uploaded = {
                "repo_id": repo_id,
                "repo_type": repo_type,
                "folder_path": folder_path,
                "path_in_repo": path_in_repo,
                "commit_message": commit_message,
            }
            return "https://huggingface.co/datasets/test/repo/commit/abc"

    api = MockApi()
    monkeypatch.setattr(upload_hf_folder, "get_hf_api", lambda token=None: api)
    monkeypatch.setattr(upload_hf_folder, "ensure_repo_exists", lambda *args, **kwargs: True)

    result = upload_folder_to_hf(
        source_dir=source_dir,
        repo_id="test/repo",
        path_in_repo="manifests",
        commit_message="test upload",
    )

    assert result["commit_url"] == "https://huggingface.co/datasets/test/repo/commit/abc"
    assert api.uploaded["repo_id"] == "test/repo"
    assert api.uploaded["path_in_repo"] == "manifests"


def test_parse_args() -> None:
    args = parse_args(
        [
            "--source-dir",
            "generated",
            "--repo-id",
            "test/repo",
            "--path-in-repo",
            "archive",
            "--dry-run",
        ]
    )
    assert args.source_dir == Path("generated")
    assert args.repo_id == "test/repo"
    assert args.path_in_repo == "archive"
    assert args.dry_run is True
