"""Tests for local release packaging and Zenodo client boundaries."""

from __future__ import annotations

import argparse
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
from scripts.publish_zenodo import deposit, update_dataset_card_doi


def _repo_root(start: Path) -> Path:
    for candidate in (start, *start.parents):
        if (candidate / "pixi.toml").exists():
            return candidate
    return start.parents[1]


ROOT = _repo_root(Path(__file__).resolve())


def test_validate_zenodo_json_accepts_repo_metadata() -> None:
    assert validate_zenodo_json(ROOT / ".zenodo.json") == []


def test_collect_assets_excludes_state_files(tmp_path: Path) -> None:
    project_root = tmp_path / "repo"
    stage_dir = project_root / "processed"
    metadata_dir = project_root / "metadata"
    manifests_dir = project_root / "manifests"
    project_root.mkdir()
    stage_dir.mkdir()
    metadata_dir.mkdir()
    manifests_dir.mkdir()
    (project_root / ".zenodo.json").write_text("{}", encoding="utf-8")
    (project_root / "DATASET_CARD.md").write_text("# Dataset", encoding="utf-8")
    (manifests_dir / "schema.json").write_text("{}", encoding="utf-8")
    (manifests_dir / "latest_manifest.json").write_text("{}", encoding="utf-8")
    (stage_dir / "metadata.parquet").write_bytes(b"parquet")
    (stage_dir / "stage_state.json").write_text("{}", encoding="utf-8")
    (metadata_dir / "uc1.test.json").write_text("{}", encoding="utf-8")

    assets = collect_assets(
        stage_dir=stage_dir,
        metadata_dir=metadata_dir,
        project_root=project_root,
    )
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
    card = tmp_path / "DATASET_CARD.md"
    card.write_text(
        "For academic citation, use the Zenodo DOI _(once available)_.\n",
        encoding="utf-8",
    )
    session = _Session()

    monkeypatch.setattr("scripts.publish_zenodo.get_zenodo_api", lambda token, sandbox: session)

    result = deposit(
        archive,
        {"title": "Test"},
        token="token",
        publish=True,
        dataset_card_path=card,
    )

    assert result["published"] is True
    assert result["dataset_card_updated"] is True
    assert ("put", "https://bucket.example/123/release.zip") in session.calls
    assert "[10.0000/example](https://doi.org/10.0000/example)" in card.read_text(encoding="utf-8")


def test_update_dataset_card_doi_rewrites_placeholder(tmp_path: Path) -> None:
    card = tmp_path / "DATASET_CARD.md"
    card.write_text(
        "For academic citation, use the Zenodo DOI _(once available)_.\n",
        encoding="utf-8",
    )

    assert update_dataset_card_doi(card, "10.1234/example")
    assert card.read_text(encoding="utf-8") == (
        "For academic citation, use the Zenodo DOI [10.1234/example]"
        "(https://doi.org/10.1234/example).\n"
    )


def test_main_honors_custom_token_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    archive = tmp_path / "release.zip"
    metadata = tmp_path / ".zenodo.json"
    archive.write_bytes(b"zip")
    metadata.write_text("{}", encoding="utf-8")
    custom_token = "".join(["custom", "-", "token"])
    monkeypatch.setenv("CUSTOM_ZENODO_TOKEN", custom_token)

    session = _Session()
    captured: dict[str, str | bool] = {}

    def _get_api(token: str, sandbox: bool) -> _Session:
        captured["token"] = token
        captured["sandbox"] = str(sandbox)
        return session

    def _parse_args() -> argparse.Namespace:
        return argparse.Namespace(
            archive=archive,
            metadata=metadata,
            dataset_card=None,
            token_env="CUSTOM_ZENODO_TOKEN",
            production=False,
            publish=False,
            dry_run=False,
        )

    monkeypatch.setattr("scripts.publish_zenodo.get_zenodo_api", _get_api)
    monkeypatch.setattr("scripts.publish_zenodo.parse_args", _parse_args)

    from scripts import publish_zenodo

    assert publish_zenodo.main() == 0
    assert captured["token"] == custom_token
    assert session.calls[0] == ("post", "https://sandbox.example/api/deposit/depositions")
