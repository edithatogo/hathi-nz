"""Tests for OSF publication integration."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pytest

from scripts import publish_osf


def _repo_root(start: Path) -> Path:
    for candidate in (start, *start.parents):
        if (candidate / "pixi.toml").exists():
            return candidate
    return start.parents[1]


ROOT = _repo_root(Path(__file__).resolve())
README_PATH = ROOT / "README.md"
DATASET_CARD_PATH = ROOT / "DATASET_CARD.md"
OSF_METADATA_PATH = ROOT / ".osf.json"
WORKFLOW_PATH = ROOT / ".github/workflows/osf_sync.yml"
PYPROJECT_PATH = ROOT / "pyproject.toml"
PIXI_PATH = ROOT / "pixi.toml"


class _FakeStorage:
    def __init__(self) -> None:
        self.uploads: list[tuple[str, bytes, bool, bool]] = []

    def create_file(
        self,
        path: str,
        fp: Any,
        *,
        force: bool = False,
        update: bool = False,
    ) -> dict[str, str]:
        self.uploads.append((path, fp.read(), force, update))
        return {"path": path}


class _FakeProject:
    def __init__(self, storage: _FakeStorage) -> None:
        self._storage = storage

    def storage(self, provider: str = "osfstorage") -> _FakeStorage:  # noqa: ARG002
        return self._storage


class _FakeOSF:
    def __init__(self, storage: _FakeStorage) -> None:
        self.storage = storage
        self.requested_project_id: str | None = None

    def project(self, project_id: str) -> _FakeProject:
        self.requested_project_id = project_id
        return _FakeProject(self.storage)


def test_osf_metadata_has_required_fields() -> None:
    metadata = json.loads(OSF_METADATA_PATH.read_text(encoding="utf-8"))

    assert metadata["title"]
    assert metadata["description"]
    assert metadata["category"] == "data"
    assert "osf" in metadata["tags"]
    assert metadata["source_metadata"] == ".zenodo.json"


def test_publish_release_uploads_release_tree(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    release_dir = tmp_path / "dist"
    release_dir.mkdir()
    archive = release_dir / "corpus-nz-hathi-0.1.0.zip"
    archive.write_bytes(b"zip")
    manifest = release_dir / "corpus-nz-hathi-0.1.0-manifest.json"
    manifest.write_text("{}", encoding="utf-8")
    metadata = tmp_path / ".osf.json"
    metadata.write_text(
        json.dumps(
            {
                "title": "Test release",
                "description": "Test description",
                "tags": ["test", "osf"],
                "category": "data",
            }
        ),
        encoding="utf-8",
    )

    storage = _FakeStorage()
    fake_osf = _FakeOSF(storage)
    monkeypatch.setattr(publish_osf, "OSF", lambda token: fake_osf)

    result = publish_osf.publish_release(
        source_dir=release_dir,
        metadata_path=metadata,
        project_id="osf-project-id",
        token="osf-token",
        remote_dir="releases/0.1.0",
    )

    assert fake_osf.requested_project_id == "osf-project-id"
    assert result["uploaded_count"] == 3
    assert set(result["uploaded_files"]) == {
        "releases/0.1.0/corpus-nz-hathi-0.1.0-manifest.json",
        "releases/0.1.0/corpus-nz-hathi-0.1.0.zip",
        "releases/0.1.0/.osf.json",
    }
    assert {path for path, _content, _force, _update in storage.uploads} == set(
        result["uploaded_files"]
    )
    assert all(force is True for _path, _content, force, _update in storage.uploads)


def test_main_dry_run_reports_planned_uploads(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    release_dir = tmp_path / "dist"
    release_dir.mkdir()
    (release_dir / "artifact.zip").write_bytes(b"zip")
    metadata = tmp_path / ".osf.json"
    metadata.write_text(
        json.dumps(
            {
                "title": "Test release",
                "description": "Test description",
                "tags": ["test", "osf"],
                "category": "data",
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        publish_osf,
        "parse_args",
        lambda args=None: argparse.Namespace(
            source_dir=release_dir,
            metadata=metadata,
            project_id="osf-project-id",
            token_env="OSF_TOKEN",
            remote_dir="releases/0.1.0",
            storage_provider="osfstorage",
            dry_run=True,
        ),
    )
    monkeypatch.setattr(publish_osf, "OSF", lambda token: pytest.fail("OSF should not be used"))

    exit_code = publish_osf.main()
    output = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert output["dry_run"] is True
    assert output["project_id"] == "osf-project-id"
    assert set(output["planned_files"]) == {
        (release_dir / "artifact.zip").as_posix(),
        metadata.as_posix(),
    }


def test_resolve_credentials_honors_custom_token_env(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    custom_token = "".join(["custom", "-", "token"])
    monkeypatch.setenv("CUSTOM_OSF_TOKEN", custom_token)
    args = argparse.Namespace(
        token_env="CUSTOM_OSF_TOKEN",
        project_id="custom-project",
    )

    token, project_id = publish_osf._resolve_credentials(args)

    assert token == custom_token
    assert project_id == "custom-project"


def test_osf_docs_and_dependency_declarations() -> None:
    readme = README_PATH.read_text(encoding="utf-8")
    dataset_card = DATASET_CARD_PATH.read_text(encoding="utf-8")
    workflow = WORKFLOW_PATH.read_text(encoding="utf-8")
    pyproject = PYPROJECT_PATH.read_text(encoding="utf-8")
    pixi = PIXI_PATH.read_text(encoding="utf-8")

    assert "OSF Mirror" in readme
    assert "OSF_PROJECT_ID" in readme
    assert "OSF mirrors" in dataset_card
    assert "OSF_TOKEN" in dataset_card
    assert "OSF Sync" in workflow
    assert "OSF_PROJECT_ID" in workflow
    assert "available=false" in workflow
    assert "steps.credentials.outputs.available == 'true'" in workflow
    assert "osfclient" in pyproject
    assert "osfclient" in pixi
