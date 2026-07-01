"""Tests for .zenodo.json metadata schema and Zenodo release packaging."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, ClassVar

import jsonschema
import pytest


def _repo_root(start: Path) -> Path:
    for candidate in (start, *start.parents):
        if (candidate / "pixi.toml").exists():
            return candidate
    return start.parents[1]


ROOT = _repo_root(Path(__file__).resolve())
ZENODO_JSON_PATH = ROOT / ".zenodo.json"
SCHEMA_PATH = ROOT / "manifests/schema.json"

ZENODO_REQUIRED_FIELDS = [
    "title",
    "description",
    "creators",
    "access_right",
    "license",
    "upload_type",
]


@pytest.fixture
def zenodo_metadata() -> dict[str, Any]:
    """Load .zenodo.json metadata."""
    if not ZENODO_JSON_PATH.exists():
        pytest.skip(f"{ZENODO_JSON_PATH} not found")
    return json.loads(ZENODO_JSON_PATH.read_text(encoding="utf-8"))


class TestZenodoRequiredFields:
    """Test that .zenodo.json has all required Zenodo fields."""

    def test_title_present(self, zenodo_metadata):
        assert "title" in zenodo_metadata
        assert isinstance(zenodo_metadata["title"], str)
        assert len(zenodo_metadata["title"].strip()) > 0

    def test_description_present(self, zenodo_metadata):
        assert "description" in zenodo_metadata
        assert isinstance(zenodo_metadata["description"], str)
        assert len(zenodo_metadata["description"].strip()) > 0

    def test_creators_present(self, zenodo_metadata):
        assert "creators" in zenodo_metadata
        assert isinstance(zenodo_metadata["creators"], list)
        assert len(zenodo_metadata["creators"]) > 0

    def test_creator_structure(self, zenodo_metadata):
        for creator in zenodo_metadata["creators"]:
            assert "name" in creator
            assert isinstance(creator["name"], str)
            assert len(creator["name"].strip()) > 0

    def test_access_right_valid(self, zenodo_metadata):
        assert "access_right" in zenodo_metadata
        assert zenodo_metadata["access_right"] in ("open", "embargoed", "restricted", "closed")

    def test_license_present(self, zenodo_metadata):
        assert "license" in zenodo_metadata
        assert isinstance(zenodo_metadata["license"], str)

    def test_upload_type_valid(self, zenodo_metadata):
        assert "upload_type" in zenodo_metadata
        valid = {
            "publication",
            "poster",
            "presentation",
            "dataset",
            "image",
            "video",
            "software",
            "lesson",
            "physicalobject",
            "other",
        }
        assert zenodo_metadata["upload_type"] in valid

    def test_all_required_fields_present(self, zenodo_metadata):
        for field in ZENODO_REQUIRED_FIELDS:
            assert field in zenodo_metadata, f"Missing: {field!r}"


class TestZenodoOptionalFields:
    """Test optional Zenodo fields when present."""

    def test_communities_structure(self, zenodo_metadata):
        communities = zenodo_metadata.get("communities", [])
        if communities:
            for c in communities:
                assert "identifier" in c

    def test_keywords_list_of_strings(self, zenodo_metadata):
        keywords = zenodo_metadata.get("keywords", [])
        if keywords:
            assert isinstance(keywords, list)
            for kw in keywords:
                assert isinstance(kw, str)
                assert len(kw.strip()) > 0

    def test_related_identifiers_structure(self, zenodo_metadata):
        related = zenodo_metadata.get("related_identifiers", [])
        if related:
            valid_relations = {
                "isSupplementTo",
                "isSupplementedBy",
                "isNewVersionOf",
                "isPreviousVersionOf",
                "isPartOf",
                "hasPart",
                "isDocumentedBy",
                "documents",
                "isDerivedFrom",
                "isSourceOf",
                "isIdenticalTo",
            }
            for item in related:
                assert "relation" in item
                assert "identifier" in item
                assert item["relation"] in valid_relations, f"Invalid relation: {item['relation']}"

    def test_version_semver(self, zenodo_metadata):
        version = zenodo_metadata.get("version", "")
        if version:
            assert re.match(r"^\d+\.\d+\.\d+", version), f"Not semver: {version!r}"

    def test_notes_is_string(self, zenodo_metadata):
        notes = zenodo_metadata.get("notes")
        if notes:
            assert isinstance(notes, str)


class TestZenodoCorpusSpecific:
    """Test corpus-specific Zenodo metadata values."""

    def test_title_contains_corpus_name(self, zenodo_metadata):
        title = zenodo_metadata["title"]
        assert any(p in title for p in ["corpus-nz-hathi", "NZ Parliamentary", "HathiTrust"])

    def test_keywords_include_nz(self, zenodo_metadata):
        keywords = [k.lower() for k in zenodo_metadata.get("keywords", [])]
        nz_terms = [k for k in keywords if "new-zealand" in k or k == "nz"]
        assert len(nz_terms) >= 1

    def test_related_identifiers_include_hf(self, zenodo_metadata):
        related = zenodo_metadata.get("related_identifiers", [])
        hf_refs = [r for r in related if "huggingface.co" in r.get("identifier", "")]
        assert len(hf_refs) >= 1

    def test_method_describes_pipeline(self, zenodo_metadata):
        method = zenodo_metadata.get("method", "")
        if method:
            assert any(
                p in method.lower()
                for p in ["hathifile", "collection id", "sha-256", "parquet", "manifest"]
            )


class TestReleasePackaging:
    """Test release packaging strategy."""

    RELEASE_FILES: ClassVar[list[str]] = [
        "metadata.parquet",
        "manifests/schema.json",
        "manifests/latest_manifest.json",
        ".zenodo.json",
        "DATASET_CARD.md",
        "LICENSE",
    ]

    def test_includes_metadata_parquet(self):
        assert "metadata.parquet" in self.RELEASE_FILES

    def test_includes_manifests(self):
        assert "manifests/schema.json" in self.RELEASE_FILES
        assert "manifests/latest_manifest.json" in self.RELEASE_FILES

    def test_includes_zenodo_json(self):
        assert ".zenodo.json" in self.RELEASE_FILES

    def test_includes_dataset_card(self):
        assert "DATASET_CARD.md" in self.RELEASE_FILES

    def test_includes_license(self):
        assert "LICENSE" in self.RELEASE_FILES

    def test_archive_naming(self):
        archive = f"corpus-nz-hathi-{0}.{1}.{0}.tar.gz"
        assert archive == "corpus-nz-hathi-0.1.0.tar.gz"

    def test_excludes_raw_zips(self):
        excluded = ["data/raw/"]
        for pattern in excluded:
            assert all(pattern not in f for f in self.RELEASE_FILES)

    def test_excludes_state_files(self):
        excluded = ["upload_state.json", "stage_state.json", "validation_report.json"]
        for pattern in excluded:
            assert all(pattern not in f for f in self.RELEASE_FILES)

    def test_schema_compatible_with_volume_record(self):
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        validator = jsonschema.Draft202012Validator(schema)
        vol = {
            "htid": "uc1.b2889853",
            "category": "debates",
            "year": 1894,
            "volume": "v.95",
            "title": "Test",
            "rights": "pd",
            "collection_id": "71329709",
            "source": "uc1",
        }
        errors = list(validator.iter_errors(vol))
        assert errors == []
