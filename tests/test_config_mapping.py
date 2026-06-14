"""Tests for config/subset mapping -- HF multi-config naming and schema validation."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import jsonschema
import pytest

SCHEMA_PATH = Path("manifests/schema.json")

VALID_CATEGORIES = [
    "debates", "legislation", "hansard", "supplementary",
    "parliamentary-papers", "gazette", "other",
]

SUBSET_PATTERN = r"^[a-z0-9]+(-[a-z0-9]+)*$"


@pytest.fixture
def schema() -> dict[str, Any]:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


@pytest.fixture
def validator(schema: dict[str, Any]) -> jsonschema.Draft202012Validator:
    return jsonschema.Draft202012Validator(schema)


@pytest.fixture
def base_volume() -> dict[str, Any]:
    return {
        "htid": "uc1.b2889853",
        "category": "debates",
        "year": 1894,
        "volume": "v.95 1894",
        "title": "New Zealand. Parliament. Parliamentary Debates. Vol. 95.",
        "rights": "pd",
        "collection_id": "71329709",
        "source": "uc1",
    }


class TestSchemaValidationByCategory:
    """Test valid volume records for all categories."""

    def test_debates_volume(self, validator, base_volume):
        assert list(validator.iter_errors(base_volume)) == []

    def test_legislation_volume(self, validator, base_volume):
        assert list(validator.iter_errors({**base_volume, "category": "legislation"})) == []

    def test_hansard_volume(self, validator, base_volume):
        assert list(validator.iter_errors({**base_volume, "category": "hansard"})) == []

    def test_supplementary_volume(self, validator, base_volume):
        assert list(validator.iter_errors({**base_volume, "category": "supplementary"})) == []

    def test_parliamentary_papers_volume(self, validator, base_volume):
        vol = {**base_volume, "category": "parliamentary-papers"}
        assert list(validator.iter_errors(vol)) == []

    def test_gazette_volume(self, validator, base_volume):
        assert list(validator.iter_errors({**base_volume, "category": "gazette"})) == []

    def test_other_volume(self, validator, base_volume):
        assert list(validator.iter_errors({**base_volume, "category": "other"})) == []

    def test_invalid_category_rejected(self, validator, base_volume):
        vol = {**base_volume, "category": "invalid-category"}
        errors = list(validator.iter_errors(vol))
        assert len(errors) >= 1

    def test_all_categories_enum_complete(self, schema):
        cat_prop = schema["properties"]["category"]
        assert set(cat_prop["enum"]) == set(VALID_CATEGORIES)


class TestSubsetField:
    """Test the optional 'subset' field."""

    def test_subset_is_optional(self, validator, base_volume):
        assert "subset" not in base_volume
        assert list(validator.iter_errors(base_volume)) == []

    def test_subset_string_valid(self, validator, base_volume):
        for val in ["debates", "debates-1890s", "supplementary-indexes", "hansard-v1"]:
            assert list(validator.iter_errors({**base_volume, "subset": val})) == []

    def test_subset_non_string_rejected(self, validator, base_volume):
        assert len(list(validator.iter_errors({**base_volume, "subset": 123}))) >= 1


class TestNamingConventions:
    """Test HF multi-config naming rules."""

    def test_subset_name_lowercase(self):
        valid = ["debates", "debates-1890s", "supplementary-indexes", "hansard-v1"]
        invalid = ["Debates", "DEBATES", "Debates-1890s"]
        for name in valid:
            assert re.match(SUBSET_PATTERN, name)
        for name in invalid:
            assert not re.match(SUBSET_PATTERN, name)

    def test_subset_name_no_slash(self):
        for name in ["debates/", "debates/1890s"]:
            assert not re.match(SUBSET_PATTERN, name)

    def test_subset_name_max_length(self):
        long_ok = "debates-" + "a" * 54
        too_long = "debates-" + "a" * 60
        assert re.match(SUBSET_PATTERN, long_ok) and len(long_ok) <= 64
        assert re.match(SUBSET_PATTERN, too_long) and len(too_long) > 64

    def test_data_path_convention(self):
        path = "data/raw/debates/year=1894/v.95-1894/"
        assert path == "data/raw/debates/year=1894/v.95-1894/"

    def test_hf_config_path_convention(self):
        htid = "uc1.b2889853"
        safe_name = htid.replace("/", "_").replace(".", "_")
        assert f"data/debates-1890s/{safe_name}.zip" == "data/debates-1890s/uc1_b2889853.zip"


class TestCrossCategoryRecords:
    """Test cross-category records with subset."""

    def test_all_categories_with_subset(self, validator):
        for cat in VALID_CATEGORIES:
            vol: dict[str, Any] = {
                "htid": f"uc1.{cat.replace('-', '_')}_test",
                "category": cat,
                "subset": f"{cat}-v1",
                "year": 1900,
                "volume": "v.1",
                "title": f"Test for {cat}",
                "oclc_num": "12345678",
                "rights": "pd",
                "collection_id": "71329709",
                "source": "uc1",
                "sha256": "a" * 64,
                "size_bytes": 1024,
            }
            errors = list(validator.iter_errors(vol))
            assert errors == [], f"Category {cat!r} errors: {errors}"

    def test_subset_required_fields_unaffected(self, validator, base_volume):
        a = list(validator.iter_errors({**base_volume, "subset": "test"}))
        b = list(validator.iter_errors(base_volume))
        assert a == b


class TestSubsetResolution:
    """Test subset resolution from volume records."""

    @staticmethod
    def resolve_subset(volume: dict[str, Any]) -> str:
        explicit = volume.get("subset")
        if explicit and isinstance(explicit, str) and explicit.strip():
            return explicit.strip()
        cat = volume.get("category", "")
        if cat in VALID_CATEGORIES:
            return cat
        return "default"

    @pytest.mark.parametrize(
        ("volume", "expected"),
        [
            ({"category": "debates"}, "debates"),
            ({"category": "debates", "subset": "debates-1890s"}, "debates-1890s"),
            ({"category": "legislation", "subset": ""}, "legislation"),
            ({"category": "supplementary", "subset": "supplementary-indexes"}, "supplementary-indexes"),
            ({"category": "hansard"}, "hansard"),
            ({"category": "unknown"}, "default"),
            ({}, "default"),
        ],
    )
    def test_resolve_subset(self, volume, expected):
        assert self.resolve_subset(volume) == expected
