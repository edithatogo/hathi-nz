"""Tests for scripts/validate_catalog.py -- catalog validation pipeline."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any

import pytest

from scripts.validate_catalog import (
    _compute_sha256,
    check_manifest_consistency,
    generate_validation_report,
    parse_args,
    validate,
    validate_manifest_schema,
    verify_staged_files,
    write_report,
)


def _repo_root(start: Path) -> Path:
    for candidate in (start, *start.parents):
        if (candidate / "pixi.toml").exists():
            return candidate
    return start.parents[1]


ROOT = _repo_root(Path(__file__).resolve())
SCHEMA_PATH = ROOT / "manifests/schema.json"


@pytest.fixture
def valid_volume() -> dict[str, Any]:
    return {
        "htid": "uc1.b2889853",
        "category": "debates",
        "year": 1886,
        "volume": "v.1 (1886)",
        "title": "Parliamentary debates.",
        "rights": "pd",
        "collection_id": "71329709",
        "source": "uc1",
        "sha256": "a" * 64,
        "size_bytes": 12345,
    }


@pytest.fixture
def valid_manifest(valid_volume: dict[str, Any]) -> dict[str, Any]:
    return {
        "meta": {
            "generated_at": "2026-06-14T12:00:00+00:00",
            "source": "HathiTrust Collection ID 71329709",
            "version": "0.1.0",
            "record_count": 1,
            "schema": str(SCHEMA_PATH.relative_to(ROOT)),
        },
        "volumes": [valid_volume],
    }


@pytest.fixture
def empty_manifest() -> dict[str, Any]:
    return {
        "meta": {
            "generated_at": None,
            "source": "test",
            "version": "0.1.0",
            "record_count": 0,
            "schema": str(SCHEMA_PATH.relative_to(ROOT)),
        },
        "volumes": [],
    }


def _full_meta() -> dict[str, Any]:
    """Return a full meta dict for schema validation."""
    return {
        "generated_at": "2026-01-01",
        "source": "test",
        "version": "0.1.0",
        "record_count": 1,
        "schema": str(SCHEMA_PATH.relative_to(ROOT)),
    }


class TestValidateManifestSchema:
    def test_valid_volume_passes(self, valid_manifest: dict[str, Any]) -> None:
        errors = validate_manifest_schema(valid_manifest)
        assert errors == []

    def test_empty_manifest_passes(self, empty_manifest: dict[str, Any]) -> None:
        errors = validate_manifest_schema(empty_manifest)
        assert errors == []

    def test_missing_required_field(self, valid_volume: dict[str, Any]) -> None:
        del valid_volume["htid"]
        manifest = {"meta": _full_meta(), "volumes": [valid_volume]}
        errors = validate_manifest_schema(manifest)
        assert any("htid" in e for e in errors)

    def test_invalid_rights_enum(self, valid_volume: dict[str, Any]) -> None:
        valid_volume["rights"] = "invalid_rights_code"
        manifest = {"meta": _full_meta(), "volumes": [valid_volume]}
        errors = validate_manifest_schema(manifest)
        assert any("invalid_rights_code" in e for e in errors)

    def test_wrong_year_type(self, valid_volume: dict[str, Any]) -> None:
        valid_volume["year"] = "not_an_integer"
        manifest = {"meta": _full_meta(), "volumes": [valid_volume]}
        errors = validate_manifest_schema(manifest)
        assert any("not_an_integer" in e or "year" in e for e in errors)

    def test_extra_field_rejected(self, valid_volume: dict[str, Any]) -> None:
        valid_volume["extra_field"] = "should not be here"
        manifest = {"meta": _full_meta(), "volumes": [valid_volume]}
        errors = validate_manifest_schema(manifest)
        assert any("extra_field" in e for e in errors)

    def test_missing_meta_keys(self) -> None:
        manifest = {"meta": {}, "volumes": []}
        errors = validate_manifest_schema(manifest)
        meta_keys_found = [e for e in errors if "meta" in e]
        assert len(meta_keys_found) >= 1

    def test_volumes_not_a_list(self, valid_volume: dict[str, Any]) -> None:
        manifest: dict[str, Any] = {"meta": _full_meta(), "volumes": valid_volume}
        errors = validate_manifest_schema(manifest)
        assert any("list" in e for e in errors)

    def test_schema_file_not_found(self, valid_manifest: dict[str, Any], tmp_path: Path) -> None:
        missing = tmp_path / "nonexistent.json"
        errors = validate_manifest_schema(valid_manifest, schema_path=missing)
        assert any("not found" in e for e in errors)

    def test_schema_invalid_json(self, valid_manifest: dict[str, Any], tmp_path: Path) -> None:
        bad = tmp_path / "bad.json"
        bad.write_text("not valid json", encoding="utf-8")
        errors = validate_manifest_schema(valid_manifest, schema_path=bad)
        assert any("not valid JSON" in e for e in errors)

    def test_multiple_volumes_all_valid(self, valid_volume: dict[str, Any]) -> None:
        volumes = [dict(valid_volume) for _ in range(5)]
        for i, v in enumerate(volumes):
            v["htid"] = f"test.{i:04d}"
        manifest = {"meta": _full_meta(), "volumes": volumes}
        errors = validate_manifest_schema(manifest)
        assert errors == []

    def test_null_year_accepted(self, valid_volume: dict[str, Any]) -> None:
        valid_volume["year"] = None
        manifest = {"meta": _full_meta(), "volumes": [valid_volume]}
        errors = validate_manifest_schema(manifest)
        assert errors == []


class TestCheckManifestConsistency:
    def test_valid_volume_consistent(self, valid_volume: dict[str, Any]) -> None:
        errors = check_manifest_consistency([valid_volume])
        assert errors == []

    def test_empty_list(self) -> None:
        errors = check_manifest_consistency([])
        assert errors == []

    def test_duplicate_htid(self, valid_volume: dict[str, Any]) -> None:
        errors = check_manifest_consistency([valid_volume, dict(valid_volume)])
        assert any("duplicate" in e for e in errors)

    def test_missing_required_field(self, valid_volume: dict[str, Any]) -> None:
        del valid_volume["title"]
        errors = check_manifest_consistency([valid_volume])
        assert any("title" in e for e in errors)

    def test_year_out_of_range_low(self, valid_volume: dict[str, Any]) -> None:
        valid_volume["year"] = 1799
        errors = check_manifest_consistency([valid_volume])
        assert any("1799" in e for e in errors)

    def test_year_out_of_range_high(self, valid_volume: dict[str, Any]) -> None:
        valid_volume["year"] = 2101
        errors = check_manifest_consistency([valid_volume])
        assert any("2101" in e for e in errors)

    def test_year_null_is_ok(self, valid_volume: dict[str, Any]) -> None:
        valid_volume["year"] = None
        errors = check_manifest_consistency([valid_volume])
        assert errors == []

    def test_invalid_rights(self, valid_volume: dict[str, Any]) -> None:
        valid_volume["rights"] = "invalid_rights"
        errors = check_manifest_consistency([valid_volume])
        assert any("invalid_rights" in e for e in errors)

    def test_empty_source(self, valid_volume: dict[str, Any]) -> None:
        valid_volume["source"] = ""
        errors = check_manifest_consistency([valid_volume])
        assert any("empty" in e for e in errors)

    def test_non_dict_volume(self) -> None:
        errors = check_manifest_consistency(["not_a_dict"])  # ty: ignore[invalid-argument-type]
        assert any("not a dict" in e for e in errors)

    def test_htid_wrong_type(self, valid_volume: dict[str, Any]) -> None:
        valid_volume["htid"] = 12345
        errors = check_manifest_consistency([valid_volume])
        assert any("string" in e for e in errors)

    def test_multiple_errors_collected(self, valid_volume: dict[str, Any]) -> None:
        v1 = dict(valid_volume)
        v1["htid"] = "test.first"
        v1["year"] = 1799
        v1["rights"] = "bad"
        v2 = dict(valid_volume)
        v2["htid"] = "test.second"
        del v2["title"]
        errors = check_manifest_consistency([v1, v2])
        assert len(errors) >= 3


class TestVerifyStagedFiles:
    def test_all_files_present(self, tmp_path: Path, valid_volume: dict[str, Any]) -> None:
        content = b"test content"
        sha256 = hashlib.sha256(content).hexdigest()
        valid_volume["sha256"] = sha256
        valid_volume["size_bytes"] = len(content)
        stage_dir = tmp_path / "staged"
        src_dir = stage_dir / "uc1"
        src_dir.mkdir(parents=True)
        (src_dir / "uc1.b2889853.zip").write_bytes(content)
        checked, errors, warnings = verify_staged_files(stage_dir, [valid_volume])
        assert checked == 1
        assert errors == []
        assert warnings == []

    def test_file_not_found(self, tmp_path: Path, valid_volume: dict[str, Any]) -> None:
        stage_dir = tmp_path / "staged"
        stage_dir.mkdir()
        checked, errors, _warnings = verify_staged_files(stage_dir, [valid_volume])
        assert checked == 0
        assert any("not found" in e for e in errors)

    def test_sha256_mismatch(self, tmp_path: Path, valid_volume: dict[str, Any]) -> None:
        valid_volume["sha256"] = "f" * 64
        valid_volume["size_bytes"] = 12
        stage_dir = tmp_path / "staged"
        src_dir = stage_dir / "uc1"
        src_dir.mkdir(parents=True)
        (src_dir / "uc1.b2889853.zip").write_text("hello world")
        checked, errors, _warnings = verify_staged_files(stage_dir, [valid_volume])
        assert checked == 1
        assert any("mismatch" in e for e in errors)

    def test_size_mismatch(self, tmp_path: Path, valid_volume: dict[str, Any]) -> None:
        content = b"hello world"
        valid_volume["sha256"] = hashlib.sha256(content).hexdigest()
        valid_volume["size_bytes"] = 99999
        stage_dir = tmp_path / "staged"
        src_dir = stage_dir / "uc1"
        src_dir.mkdir(parents=True)
        (src_dir / "uc1.b2889853.zip").write_bytes(content)
        checked, errors, _warnings = verify_staged_files(stage_dir, [valid_volume])
        assert checked == 1
        assert any("mismatch" in e for e in errors)

    def test_missing_sha256_warning(self, tmp_path: Path, valid_volume: dict[str, Any]) -> None:
        valid_volume.pop("sha256", None)
        valid_volume["size_bytes"] = 11
        stage_dir = tmp_path / "staged"
        src_dir = stage_dir / "uc1"
        src_dir.mkdir(parents=True)
        (src_dir / "uc1.b2889853.zip").write_text("hello world")
        checked, errors, warnings = verify_staged_files(stage_dir, [valid_volume])
        assert checked == 1
        assert errors == []
        assert any("skipping" in w for w in warnings)

    def test_missing_htid_warning(self, valid_volume: dict[str, Any]) -> None:
        no_htid = dict(valid_volume)
        del no_htid["htid"]
        checked, _errors, warnings = verify_staged_files(Path("/nonexistent"), [no_htid])
        assert checked == 0
        assert any("skipping" in w for w in warnings)

    def test_flat_structure_fallback(self, tmp_path: Path, valid_volume: dict[str, Any]) -> None:
        content = b"flat file"
        sha256 = hashlib.sha256(content).hexdigest()
        valid_volume["sha256"] = sha256
        valid_volume["size_bytes"] = len(content)
        stage_dir = tmp_path / "staged"
        stage_dir.mkdir(parents=True)
        (stage_dir / "uc1.b2889853.zip").write_bytes(content)
        checked, errors, _warnings = verify_staged_files(stage_dir, [valid_volume])
        assert checked == 1
        assert errors == []


class TestGenerateValidationReport:
    def test_all_pass(self) -> None:
        report = generate_validation_report(
            schema_errors=[],
            consistency_errors=[],
            file_errors=[],
            file_warnings=[],
            total_volumes=5,
            files_checked=5,
        )
        assert report["results"]["passed"] is True
        assert report["results"]["total_errors"] == 0
        assert report["results"]["total_warnings"] == 0
        assert report["manifest"]["total_volumes"] == 5
        assert report["manifest"]["files_checked"] == 5
        assert "validated_at" in report

    def test_with_errors(self) -> None:
        report = generate_validation_report(
            schema_errors=["schema error 1"],
            consistency_errors=["consistency error 1", "consistency error 2"],
            file_errors=["file error 1"],
            file_warnings=["warning 1"],
            total_volumes=10,
        )
        assert report["results"]["passed"] is False
        assert report["results"]["total_errors"] == 4
        assert report["results"]["total_warnings"] == 1
        assert report["errors"]["schema"]["count"] == 1
        assert report["errors"]["consistency"]["count"] == 2
        assert report["errors"]["file_integrity"]["count"] == 1
        assert report["warnings"]["file_integrity"]["count"] == 1

    def test_zero_volumes(self) -> None:
        report = generate_validation_report(
            schema_errors=[],
            consistency_errors=[],
            file_errors=[],
            file_warnings=[],
            total_volumes=0,
        )
        assert report["results"]["passed"] is True
        assert report["manifest"]["total_volumes"] == 0


class TestWriteReport:
    def test_write_report_creates_file(self, tmp_path: Path) -> None:
        report = {"results": {"passed": True}, "manifest": {"total_volumes": 0}}
        out = tmp_path / "reports" / "report.json"
        write_report(report, out)
        assert out.exists()
        loaded = json.loads(out.read_text(encoding="utf-8"))
        assert loaded["results"]["passed"] is True

    def test_write_report_creates_parent_dirs(self, tmp_path: Path) -> None:
        report = {"results": {"passed": False}, "manifest": {"total_volumes": 1}}
        out = tmp_path / "deep" / "nested" / "report.json"
        write_report(report, out)
        assert out.exists()
        loaded = json.loads(out.read_text(encoding="utf-8"))
        assert loaded["results"]["passed"] is False


class TestComputeSha256:
    def test_missing_file(self, tmp_path: Path) -> None:
        assert _compute_sha256(tmp_path / "missing.txt") is None

    def test_compute_valid(self, tmp_path: Path) -> None:
        content = b"hello world"
        p = tmp_path / "test.txt"
        p.write_bytes(content)
        expected = hashlib.sha256(content).hexdigest()
        assert _compute_sha256(p) == expected


class TestValidate:
    def test_validate_missing_manifest(self, tmp_path: Path) -> None:
        missing = tmp_path / "missing.json"
        report, exit_code = validate(
            manifest_path=missing,
            schema_path=SCHEMA_PATH,
        )
        assert exit_code == 1
        assert report["results"]["passed"] is False

    def test_validate_empty_manifest(self, tmp_path: Path) -> None:
        manifest_path = tmp_path / "empty_manifest.json"
        manifest = {
            "meta": {
                "generated_at": "2026-01-01",
                "source": "test",
                "version": "0.1.0",
                "record_count": 0,
                "schema": str(SCHEMA_PATH.relative_to(ROOT)),
            },
            "volumes": [],
        }
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        report, exit_code = validate(
            manifest_path=manifest_path,
            schema_path=SCHEMA_PATH,
        )
        assert exit_code == 0
        assert report["results"]["passed"] is True

    def test_validate_with_errors(self, tmp_path: Path) -> None:
        manifest_path = tmp_path / "bad_manifest.json"
        manifest = {
            "meta": {
                "generated_at": "2026-01-01",
                "source": "test",
                "version": "0.1.0",
                "record_count": 2,
                "schema": str(SCHEMA_PATH.relative_to(ROOT)),
            },
            "volumes": [
                {"htid": "test.1", "category": "debates", "year": 1886, "rights": "pd"},
                {"htid": "test.1", "category": "debates", "year": 1900, "rights": "pd"},
            ],
        }
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        report, exit_code = validate(
            manifest_path=manifest_path,
            schema_path=SCHEMA_PATH,
        )
        assert exit_code == 1
        assert report["results"]["passed"] is False
        assert report["results"]["total_errors"] > 0

    def test_validate_with_stage_dir(self, tmp_path: Path) -> None:
        manifest_path = tmp_path / "manifest.json"
        content = b"test volume data"
        sha256 = hashlib.sha256(content).hexdigest()
        size = len(content)
        manifest = {
            "meta": {
                "generated_at": "2026-01-01",
                "source": "test",
                "version": "0.1.0",
                "record_count": 1,
                "schema": str(SCHEMA_PATH.relative_to(ROOT)),
            },
            "volumes": [
                {
                    "htid": "uc1.test001",
                    "category": "debates",
                    "year": 1886,
                    "volume": "v.1",
                    "title": "Test",
                    "rights": "pd",
                    "collection_id": "71329709",
                    "source": "uc1",
                    "sha256": sha256,
                    "size_bytes": size,
                }
            ],
        }
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        stage_dir = tmp_path / "staged"
        src_dir = stage_dir / "uc1"
        src_dir.mkdir(parents=True)
        (src_dir / "uc1.test001.zip").write_bytes(content)
        report, exit_code = validate(
            manifest_path=manifest_path,
            schema_path=SCHEMA_PATH,
            stage_dir=stage_dir,
        )
        assert exit_code == 0
        assert report["results"]["passed"] is True
        assert report["manifest"]["files_checked"] == 1

    def test_fail_on_warning(self, tmp_path: Path) -> None:
        manifest_path = tmp_path / "manifest.json"
        content = b"warning test"
        manifest = {
            "meta": {
                "generated_at": "2026-01-01",
                "source": "test",
                "version": "0.1.0",
                "record_count": 1,
                "schema": str(SCHEMA_PATH.relative_to(ROOT)),
            },
            "volumes": [
                {
                    "htid": "test.001",
                    "category": "debates",
                    "year": 1886,
                    "volume": "v.1",
                    "title": "Test",
                    "rights": "pd",
                    "collection_id": "71329709",
                    "source": "uc1",
                }
            ],
        }
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        stage_dir = tmp_path / "staged"
        src_dir = stage_dir / "uc1"
        src_dir.mkdir(parents=True)
        (src_dir / "test.001.zip").write_bytes(content)
        report, exit_code = validate(
            manifest_path=manifest_path,
            schema_path=SCHEMA_PATH,
            stage_dir=stage_dir,
            fail_on_warning=True,
        )
        assert exit_code == 1
        assert report["results"]["total_warnings"] > 0


class TestParseArgs:
    def test_defaults(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(sys, "argv", ["prog", "--manifest", "manifests/latest_manifest.json"])
        args = parse_args()
        assert args.manifest == Path("manifests/latest_manifest.json")
        assert args.stage_dir is None
        assert args.schema == Path("manifests/schema.json")
        assert args.report == Path("data/_state/validation_report.json")
        assert args.fail_on_warning is False
        assert args.verbose is False

    def test_custom_paths(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(
            sys,
            "argv",
            [
                "prog",
                "--manifest",
                "custom_manifest.json",
                "--stage-dir",
                "data/processed",
                "--schema",
                "custom_schema.json",
                "--report",
                "report.json",
                "--fail-on-warning",
                "--verbose",
            ],
        )
        args = parse_args()
        assert args.manifest == Path("custom_manifest.json")
        assert args.stage_dir == Path("data/processed")
        assert args.schema == Path("custom_schema.json")
        assert args.report == Path("report.json")
        assert args.fail_on_warning is True
        assert args.verbose is True
