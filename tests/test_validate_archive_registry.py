"""Tests for the committed archive registry."""

import json
from pathlib import Path

import pytest

from scripts.validate_archive_registry import main, validate_registry

REGISTRY_PATH = Path("manifests/hathitrust-nz/archive_registry.json")


def test_archive_registry_is_complete_and_healthy() -> None:
    result = validate_registry()

    assert result["valid"] is True, result
    assert result["dataset_count"] == 5
    assert result["manifest_record_count"] == 510
    assert result["publication_health_score"] == 1000


def test_archive_registry_reports_invalid_dataset_entry(tmp_path) -> None:
    registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    registry["datasets"] = [{"dataset_id": "broken", "hf_url": "bad", "zenodo_doi": "bad"}]
    registry_path = tmp_path / "registry.json"
    registry_path.write_text(json.dumps(registry), encoding="utf-8")

    result = validate_registry(registry_path)

    assert result["valid"] is False
    assert any("dataset IDs differ" in error for error in result["errors"])
    assert any("missing hf_repo" in error for error in result["errors"])
    assert any("invalid Hugging Face URL" in error for error in result["errors"])


def test_archive_registry_rejects_non_object(tmp_path) -> None:
    path = tmp_path / "registry.json"
    path.write_text("[]", encoding="utf-8")

    with pytest.raises(ValueError, match="must contain a JSON object"):
        validate_registry(path)


def test_archive_registry_cli_returns_failure_for_bad_manifest(tmp_path) -> None:
    registry_path = tmp_path / "registry.json"
    registry_path.write_text(
        REGISTRY_PATH.read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps({"meta": {"record_count": 1}}), encoding="utf-8")

    assert (
        main(["--registry", str(registry_path), "--collection-manifest", str(manifest_path)]) == 1
    )
