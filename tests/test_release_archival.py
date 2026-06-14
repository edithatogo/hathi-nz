"""Tests for local release packaging and Zenodo client boundaries."""

from __future__ import annotations

import zipfile
from pathlib import Path
from typing import Any

import pytest

from scripts.package_release import (
    build_manifest,
    collect_assets,
    compute_checksum,
    create_archive,
    validate_zenodo_json,
)
from scripts.publish_zenodo import deposit


def test_validate_zenodo_json_accepts_repo_metadata() -> None:
    assert validate_zenodo_json(Path(".zenodo.json")) == []


def test_collect_assets_excludes_state_files(tmp_path: Path) -> None:
    stage_dir = tmp_path / "processed"
    metadata_dir = tmp_path / "metadata"
    stage_dir.mkdir()
    metadata_dir.mkdir()
    (stage_dir / "metadata.parquet").write_bytes(b"parquet")
    (stage_dir / "stage_state.json").write_text("{}", encoding="utf-8")
    (metadata_dir / "uc1.test.json").write_text("{}", encoding="utf-8")

    assets = collect_assets(stage_dir=stage_dir, metadata_dir=metadata_dir)
    names = {Path(path).name for path in assets["files"]}

    assert "metadata.parquet" in names
    assert "uc1.test.json" in names
    assert "stage_state.json" not in names
    assert ".zenodo.json" in names


def test_build_manifest_records_checksums(tmp_path: Path) -> None:
    payload = tmp_path / "payload.txt"
    payload.write_text("abc", encoding="utf-8")

    manifest = build_manifest({"files": [payload]})

    assert manifest["file_count"] == 1
    assert manifest["files"][0]["path"].endswith("payload.txt")
    assert manifest["files"][0]["sha256"] == compute_checksum(payload)


def test_create_archive_contains_assets(tmp_path: Path) -> None:
    payload = tmp_path / "payload.txt"
    payload.write_text("abc", encoding="utf-8")
    archive_path = tmp_path / "release.zip"

    create_archive({"files": [payload]}, archive_path)

    assert archive_path.exists()
    with zipfile.ZipFile(archive_path) as archive:
        assert any(
            name.endswith("/payload.txt") or name == "payload.txt" for name in archive.namelist()
        )


class _Response:
    def __init__(self, payload: dict[str, Any]) -> None:
        self.payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict[str, Any]:
        return self.payload


class _Session:
    base_url = "https://sandbox.example/api"

    def __init__(self) -> None:
        self.calls: list[tuple[str, str]] = []

    def post(self, url: str, **_: Any) -> _Response:
        self.calls.append(("post", url))
        if url.endswith("/actions/publish"):
            return _Response({"doi": "10.0000/example"})
        return _Response({"id": 123, "links": {"bucket": "https://bucket.example/123"}})

    def get(self, url: str, **_: Any) -> _Response:
        self.calls.append(("get", url))
        return _Response({"links": {"bucket": "https://bucket.example/123"}})

    def put(self, url: str, **_: Any) -> _Response:
        self.calls.append(("put", url))
        return _Response({"filename": "release.zip"})


def test_deposit_uses_injected_boundaries(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    archive = tmp_path / "release.zip"
    archive.write_bytes(b"zip")
    session = _Session()

    monkeypatch.setattr("scripts.publish_zenodo.get_zenodo_api", lambda token, sandbox: session)

    result = deposit(archive, {"title": "Test"}, token="token", publish=True)

    assert result["published"] is True
    assert ("put", "https://bucket.example/123/release.zip") in session.calls
