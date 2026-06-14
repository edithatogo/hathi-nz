"""Tests for scripts/stage_hf_dataset.py -- staging pipeline."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import pytest
import requests

from scripts.stage_hf_dataset import (
    _compute_sha256,
    build_metadata_dataframe,
    download_volume,
    load_manifest,
    parse_args,
    verify_content,
    write_stage_state,
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
            "title": "Parliamentary debates.",
            "oclc_num": "01149942",
            "rights": "pd",
            "source": "uc1",
            "collection_id": "71329709",
        },
        {
            "htid": "uc1.b2889854",
            "category": "debates",
            "year": 1887,
            "volume": "v.2 (1887)",
            "title": "Parliamentary debates. v.2",
            "oclc_num": "01149943",
            "rights": "pd",
            "source": "uc1",
            "collection_id": "71329709",
        },
    ]


@pytest.fixture
def manifest_file(tmp_path: Path, sample_volumes: list[dict[str, Any]]) -> Path:
    manifest = {
        "meta": {
            "generated_at": "2025-01-01T00:00:00+00:00",
            "source": "HathiTrust Collection ID 71329709",
            "version": "0.1.0",
            "record_count": len(sample_volumes),
        },
        "volumes": sample_volumes,
    }
    p = tmp_path / "manifest.json"
    p.write_text(json.dumps(manifest), encoding="utf-8")
    return p


# ---------------------------------------------------------------
# Tests: load_manifest
# ---------------------------------------------------------------


class TestLoadManifest:
    def test_load_valid(self, manifest_file: Path) -> None:
        volumes = load_manifest(manifest_file)
        assert len(volumes) == 2
        assert volumes[0]["htid"] == "uc1.b2889853"
        assert volumes[1]["htid"] == "uc1.b2889854"

    def test_missing_file(self) -> None:
        with pytest.raises(FileNotFoundError):
            load_manifest(Path("/nonexistent/manifest.json"))

    def test_invalid_json(self, tmp_path: Path) -> None:
        p = tmp_path / "bad.json"
        p.write_text("{invalid json}", encoding="utf-8")
        with pytest.raises(json.JSONDecodeError):
            load_manifest(p)

    def test_empty_volumes_list(self, tmp_path: Path) -> None:
        manifest = {"meta": {}, "volumes": []}
        p = tmp_path / "empty.json"
        p.write_text(json.dumps(manifest), encoding="utf-8")
        volumes = load_manifest(p)
        assert volumes == []

    def test_missing_volumes_key(self, tmp_path: Path) -> None:
        manifest = {"meta": {}}
        p = tmp_path / "no_volumes.json"
        p.write_text(json.dumps(manifest), encoding="utf-8")
        volumes = load_manifest(p)
        assert volumes == []

    def test_volumes_not_a_list(self, tmp_path: Path) -> None:
        manifest = {"volumes": "not_a_list"}
        p = tmp_path / "bad_volumes.json"
        p.write_text(json.dumps(manifest), encoding="utf-8")
        volumes = load_manifest(p)
        assert volumes == []


# ---------------------------------------------------------------
# Tests: download_volume
# ---------------------------------------------------------------


class TestDownloadVolume:
    def test_download_success(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        class MockResponse:
            ok = True
            status_code = 200

            @staticmethod
            def iter_content(chunk_size: int = 65536) -> Any:  # noqa: ARG004
                return [b"fake zip content"]

            @staticmethod
            def raise_for_status() -> None:
                pass

        monkeypatch.setattr("requests.get", lambda *a, **kw: MockResponse())

        result = download_volume("uc1.b2889853", tmp_path, skip_existing=False)
        assert result is not None
        assert "sha256" in result
        assert "size_bytes" in result
        assert result["size_bytes"] > 0

        # Verify file was created
        zip_path = tmp_path / "uc1_b2889853.zip"
        assert zip_path.exists()

    def test_download_failure(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        def mock_get(*args: object, **kwargs: object) -> Any:  # noqa: ARG001
            msg = "500 Server Error"
            raise requests.exceptions.RequestException(msg)

        monkeypatch.setattr("requests.get", mock_get)
        result = download_volume("uc1.b2889853", tmp_path, skip_existing=False)
        assert result is None

    def test_skip_existing(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        zip_path = tmp_path / "uc1_b2889853.zip"
        zip_path.write_text("existing content", encoding="utf-8")
        original_size = zip_path.stat().st_size

        # Even if download would fail, skip_existing should return existing file info
        def mock_get(*args: object, **kwargs: object) -> Any:  # noqa: ARG001
            msg = "Should not be called"
            raise RuntimeError(msg)

        monkeypatch.setattr("requests.get", mock_get)

        result = download_volume("uc1.b2889853", tmp_path, skip_existing=True)
        assert result is not None
        assert result["size_bytes"] == original_size

    def test_no_skip_existing(self, tmp_path: Path) -> None:
        """When skip_existing=False, downloads even if file exists."""
        # Not testing actual download, just that it tries
        result = download_volume("nonexistent.test", tmp_path, skip_existing=False)
        assert result is None  # Should fail because the URL is fake

    def test_connection_error(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        def mock_get(*args: object, **kwargs: object) -> Any:  # noqa: ARG001
            msg = "Connection refused"
            raise requests.exceptions.ConnectionError(msg)

        monkeypatch.setattr("requests.get", mock_get)
        result = download_volume("uc1.b2889853", tmp_path, skip_existing=False)
        assert result is None


# ---------------------------------------------------------------
# Tests: verify_content
# ---------------------------------------------------------------


class TestVerifyContent:
    def test_verify_success(self, tmp_path: Path) -> None:
        p = tmp_path / "test.txt"
        content = b"hello world"
        p.write_bytes(content)
        expected_sha256 = hashlib.sha256(content).hexdigest()
        expected_size = len(content)
        assert verify_content(p, expected_sha256, expected_size) is True

    def test_verify_size_mismatch(self, tmp_path: Path) -> None:
        p = tmp_path / "test.txt"
        content = b"hello world"
        p.write_bytes(content)
        expected_sha256 = hashlib.sha256(content).hexdigest()
        assert verify_content(p, expected_sha256, 999) is False

    def test_verify_sha256_mismatch(self, tmp_path: Path) -> None:
        p = tmp_path / "test.txt"
        content = b"hello world"
        p.write_bytes(content)
        actual_size = len(content)
        wrong_sha256 = "0" * 64
        assert verify_content(p, wrong_sha256, actual_size) is False

    def test_verify_missing_file(self) -> None:
        missing = Path("/nonexistent/file.zip")
        assert verify_content(missing, "a" * 64, 100) is False


# ---------------------------------------------------------------
# Tests: build_metadata_dataframe
# ---------------------------------------------------------------


class TestBuildMetadataDataframe:
    def test_build_with_volumes(self, sample_volumes: list[dict[str, Any]]) -> None:
        df = build_metadata_dataframe(sample_volumes)
        assert len(df) == 2
        assert list(df.columns) == [
            "htid",
            "category",
            "year",
            "volume",
            "title",
            "oclc_num",
            "rights",
            "source",
            "collection_id",
            "sha256",
            "size_bytes",
            "pipeline_version",
        ]
        assert df["htid"].to_list() == ["uc1.b2889853", "uc1.b2889854"]
        assert df["year"].to_list() == [1886, 1887]

    def test_build_empty_list(self) -> None:
        df = build_metadata_dataframe([])
        assert len(df) == 0
        # Should still have the expected columns
        assert "htid" in df.columns
        assert "category" in df.columns

    def test_build_with_enriched_fields(self, sample_volumes: list[dict[str, Any]]) -> None:
        volumes = list(sample_volumes)
        volumes[0]["sha256"] = "abc" * 21 + "a"  # 64 chars
        volumes[0]["size_bytes"] = 12345
        volumes[0]["pipeline_version"] = "0.2.0"

        df = build_metadata_dataframe(volumes)
        assert df["sha256"].to_list()[0] is not None
        assert df["size_bytes"].to_list()[0] == 12345
        assert df["pipeline_version"].to_list()[0] == "0.2.0"


# ---------------------------------------------------------------
# Tests: write_stage_state
# ---------------------------------------------------------------


class TestWriteStageState:
    def test_write_state(self, tmp_path: Path) -> None:
        state = {
            "pipeline_version": "0.1.0",
            "staged_count": 5,
            "staged_htids": ["uc1.a", "uc1.b"],
        }
        write_stage_state(tmp_path, state)
        state_file = tmp_path / "stage_state.json"
        assert state_file.exists()
        loaded = json.loads(state_file.read_text(encoding="utf-8"))
        assert loaded["pipeline_version"] == "0.1.0"
        assert loaded["staged_count"] == 5

    def test_write_state_creates_dir(self, tmp_path: Path) -> None:
        nested = tmp_path / "a" / "b" / "c"
        state = {"key": "value"}
        write_stage_state(nested, state)
        assert (nested / "stage_state.json").exists()


# ---------------------------------------------------------------
# Tests: _compute_sha256
# ---------------------------------------------------------------


class TestComputeSha256:
    def test_missing_file(self, tmp_path: Path) -> None:
        missing = tmp_path / "missing.txt"
        assert _compute_sha256(missing) is None

    def test_valid(self, tmp_path: Path) -> None:
        p = tmp_path / "test.bin"
        content = b"some data"
        p.write_bytes(content)
        expected = hashlib.sha256(content).hexdigest()
        assert _compute_sha256(p) == expected


# ---------------------------------------------------------------
# Tests: parse_args
# ---------------------------------------------------------------


class TestParseArgs:
    def test_defaults(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr("sys.argv", ["prog"])
        args = parse_args()
        assert args.manifest == Path("manifests/latest_manifest.json")
        assert args.download_dir == Path("data/raw")
        assert args.stage_dir == Path("data/processed")
        assert args.state_dir == Path("data/_state")
        assert args.limit == 0

    def test_custom_values(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(
            "sys.argv",
            [
                "prog",
                "--manifest",
                "custom.json",
                "--download-dir",
                "custom_dl",
                "--stage-dir",
                "custom_stage",
                "--limit",
                "10",
            ],
        )
        args = parse_args()
        assert args.manifest == Path("custom.json")
        assert args.download_dir == Path("custom_dl")
        assert args.stage_dir == Path("custom_stage")
        assert args.limit == 10

    def test_injected_args(self) -> None:
        args = parse_args(
            [
                "--manifest",
                "inj.json",
                "--download-dir",
                "dl",
            ]
        )
        assert args.manifest == Path("inj.json")
        assert args.download_dir == Path("dl")
