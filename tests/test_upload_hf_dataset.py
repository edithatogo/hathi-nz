"""Tests for scripts/upload_hf_dataset.py -- Hugging Face upload pipeline."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from scripts.upload_hf_dataset import (
    DEFAULT_HF_REPO,
    ensure_repo_exists,
    get_hf_api,
    load_upload_state,
    parse_args,
    upload_metadata_files,
    upload_volume_files,
    write_upload_state,
)

# ---------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------


@pytest.fixture
def sample_volumes() -> list[dict[str, Any]]:
    return [
        {
            "htid": "uc1.b2889853",
            "category": "debates",
            "year": 1886,
            "volume": "v.1 (1886)",
            "rights": "pd",
        },
        {
            "htid": "uc1.b2889854",
            "category": "debates",
            "year": 1887,
            "volume": "v.2 (1887)",
            "rights": "pd",
        },
    ]


@pytest.fixture
def mock_hf_api() -> Any:
    """Create a minimal mock HfApi."""

    class MockHfApi:
        def __init__(self) -> None:
            self.called_repo_info = False
            self.called_create_repo = False
            self.called_upload_folder = False
            self.last_upload_path = ""
            self.last_folder_path = ""
            self.last_path_in_repo = ""
            self.last_uploaded_files: list[str] = []

        def repo_info(self, repo_id: str, repo_type: str = "dataset") -> dict[str, Any]:  # noqa: ARG002
            self.called_repo_info = True
            return {"id": repo_id}

        def create_repo(
            self,
            repo_id: str,
            repo_type: str = "dataset",
            token: str | None = None,
            exist_ok: bool = False,  # noqa: ARG002
        ) -> dict[str, Any]:
            self.called_create_repo = True
            return {"id": repo_id}

        def upload_folder(
            self,
            repo_id: str,
            repo_type: str = "dataset",
            folder_path: str = "",
            path_in_repo: str = ".",
            commit_message: str = "",
        ) -> str:  # noqa: ARG002
            self.called_upload_folder = True
            self.last_folder_path = folder_path
            self.last_path_in_repo = path_in_repo
            root = Path(folder_path)
            self.last_uploaded_files = sorted(
                str(path.relative_to(root)).replace("\\", "/")
                for path in root.rglob("*")
                if path.is_file()
            )
            self.last_upload_path = f"https://huggingface.co/datasets/{repo_id}/commit/abc123"
            return self.last_upload_path

    return MockHfApi()


# ---------------------------------------------------------------
# Tests: get_hf_api
# ---------------------------------------------------------------


class TestGetHfApi:
    def test_default_no_token(self) -> None:
        api = get_hf_api()
        assert api is not None
        assert hasattr(api, "repo_info")

    def test_with_token(self) -> None:
        test_token = "fake_token_123"  # noqa: S105
        api = get_hf_api(token=test_token)
        assert api is not None
        # The token should be stored
        assert api.token == test_token


# ---------------------------------------------------------------
# Tests: ensure_repo_exists
# ---------------------------------------------------------------


class TestEnsureRepoExists:
    def test_repo_already_exists(self, mock_hf_api: Any) -> None:
        result = ensure_repo_exists(mock_hf_api, "edithatogo/corpus-nz-hathi")
        assert result is True
        assert mock_hf_api.called_repo_info is True
        assert mock_hf_api.called_create_repo is False

    def test_repo_created(self) -> None:
        class MockApiNoRepo:
            def __init__(self) -> None:
                self.called_create = False

            def repo_info(self, repo_id: str, repo_type: str = "dataset") -> Any:  # noqa: ARG002
                msg = "Repo not found"
                raise Exception(msg)

            def create_repo(
                self,
                repo_id: str,
                repo_type: str = "dataset",
                token: str | None = None,
                exist_ok: bool = False,  # noqa: ARG002
            ) -> Any:
                self.called_create = True
                return {"id": repo_id}

        api = MockApiNoRepo()
        result = ensure_repo_exists(api, "edithatogo/new-repo")  # type: ignore[arg-type]
        assert result is False
        assert api.called_create is True

    def test_create_fails(self) -> None:
        class MockApiFailCreate:
            def repo_info(self, repo_id: str, repo_type: str = "dataset") -> Any:  # noqa: ARG002, ARG001
                msg = "Not found"
                raise Exception(msg)

            def create_repo(
                self,
                repo_id: str,
                repo_type: str = "dataset",
                token: str | None = None,
                exist_ok: bool = False,  # noqa: ARG002, ARG001
            ) -> Any:
                msg = "Permission denied"
                raise Exception(msg)

        api = MockApiFailCreate()
        result = ensure_repo_exists(api, "edithatogo/new-repo")  # type: ignore[arg-type]
        assert result is False


# ---------------------------------------------------------------
# Tests: upload_metadata_files
# ---------------------------------------------------------------


class TestUploadMetadataFiles:
    def test_upload_parquet_only(self, tmp_path: Path, mock_hf_api: Any) -> None:
        stage_dir = tmp_path / "processed"
        stage_dir.mkdir()
        parquet = stage_dir / "metadata.parquet"
        parquet.write_text("fake parquet", encoding="utf-8")

        result = upload_metadata_files(mock_hf_api, "test/repo", stage_dir)
        assert result == "https://huggingface.co/datasets/test/repo/commit/abc123"
        assert mock_hf_api.called_upload_folder is True

    def test_no_files(self, tmp_path: Path, mock_hf_api: Any) -> None:
        stage_dir = tmp_path / "empty_stage"
        stage_dir.mkdir()
        result = upload_metadata_files(mock_hf_api, "test/repo", stage_dir)
        assert result is None

    def test_with_manifests_dir(self, tmp_path: Path, mock_hf_api: Any) -> None:
        stage_dir = tmp_path / "processed"
        stage_dir.mkdir()
        parquet = stage_dir / "metadata.parquet"
        parquet.write_text("data", encoding="utf-8")

        manifests_dir = tmp_path / "manifests"
        manifests_dir.mkdir()
        schema = manifests_dir / "schema.json"
        schema.write_text("{}", encoding="utf-8")
        manifest = manifests_dir / "latest_manifest.json"
        manifest.write_text('{"volumes": []}', encoding="utf-8")

        result = upload_metadata_files(mock_hf_api, "test/repo", stage_dir, manifests_dir)
        assert result is not None
        assert mock_hf_api.last_path_in_repo == "."
        assert "metadata.parquet" in mock_hf_api.last_uploaded_files
        assert "DATASET_CARD.md" not in mock_hf_api.last_uploaded_files
        assert "manifests/schema.json" in mock_hf_api.last_uploaded_files
        assert "manifests/latest_manifest.json" in mock_hf_api.last_uploaded_files

    def test_upload_failure(self, tmp_path: Path) -> None:
        class MockApiFailUpload:
            def upload_folder(
                self,
                repo_id: str,
                repo_type: str = "dataset",
                folder_path: str = "",
                path_in_repo: str = ".",
                commit_message: str = "",
            ) -> Any:  # noqa: ARG002, ARG001
                msg = "Upload failed"
                raise Exception(msg)

        api = MockApiFailUpload()
        stage_dir = tmp_path / "processed"
        stage_dir.mkdir()
        parquet = stage_dir / "metadata.parquet"
        parquet.write_text("data", encoding="utf-8")

        result = upload_metadata_files(api, "test/repo", stage_dir)  # type: ignore[arg-type]
        assert result is None


# ---------------------------------------------------------------
# Tests: upload_volume_files
# ---------------------------------------------------------------


class TestUploadVolumeFiles:
    def test_upload_new_volumes(
        self, tmp_path: Path, mock_hf_api: Any, sample_volumes: list[dict[str, Any]]
    ) -> None:
        data_dir = tmp_path / "raw"
        data_dir.mkdir()
        # Create fake ZIP files
        for v in sample_volumes:
            htid = v["htid"]
            safe = htid.replace("/", "_").replace(".", "_")
            (data_dir / f"{safe}.zip").write_text("zip content", encoding="utf-8")

        result = upload_volume_files(mock_hf_api, "test/repo", data_dir, sample_volumes)
        assert result == "https://huggingface.co/datasets/test/repo/commit/abc123"

    def test_skip_already_uploaded(
        self, tmp_path: Path, mock_hf_api: Any, sample_volumes: list[dict[str, Any]]
    ) -> None:
        data_dir = tmp_path / "raw"
        data_dir.mkdir()
        for v in sample_volumes:
            htid = v["htid"]
            safe = htid.replace("/", "_").replace(".", "_")
            (data_dir / f"{safe}.zip").write_text("zip", encoding="utf-8")

        prev_state = {"uploaded_htids": ["uc1.b2889853"]}
        result = upload_volume_files(
            mock_hf_api,
            "test/repo",
            data_dir,
            sample_volumes,
            previous_state=prev_state,
        )
        assert result is not None
        assert mock_hf_api.last_path_in_repo == "volumes"
        assert "uc1_b2889853.zip" not in mock_hf_api.last_uploaded_files
        assert "uc1_b2889854.zip" in mock_hf_api.last_uploaded_files

    def test_no_new_volumes(
        self, tmp_path: Path, mock_hf_api: Any, sample_volumes: list[dict[str, Any]]
    ) -> None:
        data_dir = tmp_path / "raw"
        data_dir.mkdir()

        prev_state = {"uploaded_htids": ["uc1.b2889853", "uc1.b2889854"]}
        result = upload_volume_files(
            mock_hf_api,
            "test/repo",
            data_dir,
            sample_volumes,
            previous_state=prev_state,
        )
        assert result is None

    def test_missing_zip_file(
        self, tmp_path: Path, mock_hf_api: Any, sample_volumes: list[dict[str, Any]]
    ) -> None:
        data_dir = tmp_path / "empty_raw"
        data_dir.mkdir()

        result = upload_volume_files(mock_hf_api, "test/repo", data_dir, sample_volumes)
        assert result is None  # No files to upload


# ---------------------------------------------------------------
# Tests: load_upload_state / write_upload_state
# ---------------------------------------------------------------


class TestUploadState:
    def test_write_and_load(self, tmp_path: Path) -> None:
        state = {
            "last_commit": "https://hf.co/commit/abc",
            "uploaded_htids": ["uc1.a", "uc1.b"],
        }
        write_upload_state(tmp_path, state)
        loaded = load_upload_state(tmp_path)
        assert loaded["last_commit"] == "https://hf.co/commit/abc"
        assert loaded["uploaded_htids"] == ["uc1.a", "uc1.b"]

    def test_load_missing_state(self, tmp_path: Path) -> None:
        empty_dir = tmp_path / "nonexistent"
        result = load_upload_state(empty_dir)
        assert result == {}

    def test_load_corrupt_state(self, tmp_path: Path) -> None:
        path = tmp_path / "upload_state.json"
        path.write_text("{corrupt json", encoding="utf-8")
        result = load_upload_state(tmp_path)
        assert result == {}

    def test_write_creates_dir(self, tmp_path: Path) -> None:
        nested = tmp_path / "deep" / "nested" / "state"
        state = {"key": "val"}
        write_upload_state(nested, state)
        assert (nested / "upload_state.json").exists()


# ---------------------------------------------------------------
# Tests: parse_args
# ---------------------------------------------------------------


class TestParseArgs:
    def test_defaults(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr("sys.argv", ["prog"])
        args = parse_args()
        assert args.stage_dir == Path("data/processed")
        assert args.repo_id == DEFAULT_HF_REPO
        assert args.state_dir == Path("data/_state")
        assert args.dry_run is False
        assert args.commit_message == "Auto-sync: corpus-nz-hathi update"

    def test_dry_run(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr("sys.argv", ["prog", "--dry-run"])
        args = parse_args()
        assert args.dry_run is True

    def test_custom_repo(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(
            "sys.argv",
            ["prog", "--repo-id", "custom/repo", "--stage-dir", "custom_stage"],
        )
        args = parse_args()
        assert args.repo_id == "custom/repo"
        assert args.stage_dir == Path("custom_stage")

    def test_injected_args(self) -> None:
        args = parse_args(["--repo-id", "inj/repo", "--dry-run"])
        assert args.repo_id == "inj/repo"
        assert args.dry_run is True
