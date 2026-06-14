"""Tests for scripts/fetch_hathitrust.py -- HathiTrust volume enumeration."""

from __future__ import annotations

import gzip
import hashlib
import json
import sys
from pathlib import Path

import pytest
import requests

from scripts.fetch_hathitrust import (
    _extract_year,
    _extract_year_from_title,
    _rights_code,
    build_manifest_from_hathifile,
    compute_sha256,
    lookup_volume_metadata,
    parse_args,
    parse_hathifile_line,
    write_manifest,
)

T = chr(9)  # tab character


@pytest.fixture
def sample_fields() -> list[str]:
    return [
        "uc1.b2889853",
        "pd",
        "pd",
        "NJP",
        "uc1",
        "New Zealand. Parliament. Parliamentary debates.",
        "Wellington, N.Z. :[s.n.],1886-",
        "",
        "",
        "",
        "01149942",
        "v.1 (1886)",
        "",
        "n",
        "",
        "",
    ]


@pytest.fixture
def sample_hathifile_line(sample_fields: list[str]) -> str:
    return T.join(sample_fields)


@pytest.fixture
def temp_hathifile_txt(tmp_path: Path) -> Path:
    header = ["# hathifile excerpt"]
    row1 = [
        "uc1.b2889853",
        "pd",
        "pd",
        "NJP",
        "uc1",
        "Parliamentary debates.",
        "Wellington, 1886",
        "",
        "",
        "",
        "01149942",
        "v.1 (1886)",
        "",
        "n",
        "",
        "",
    ]
    row2 = [
        "uc1.b2889854",
        "pdus",
        "pdus",
        "NJP",
        "uc1",
        "Parliamentary debates. v.2",
        "Wellington, 1887",
        "",
        "",
        "",
        "01149943",
        "v.2 (1887)",
        "",
        "n",
        "",
        "",
    ]
    row3 = [
        "mdp.123456",
        "ic",
        "ic",
        "MIU",
        "mdp",
        "Some other title",
        "Ann Arbor 1900",
        "",
        "",
        "",
        "",
        "",
        "",
        "n",
        "",
        "",
    ]
    lines = [header[0], T.join(row1), T.join(row2), T.join(row3)]
    p = tmp_path / "hathifile.txt"
    p.write_text("\n".join(lines), encoding="utf-8")
    return p


@pytest.fixture
def temp_hathifile_gz(tmp_path: Path, temp_hathifile_txt: Path) -> Path:
    p = tmp_path / "hathifile.txt.gz"
    data = temp_hathifile_txt.read_bytes()
    with gzip.open(p, "wb") as f:
        f.write(data)
    return p


class TestParseHathifileLine:
    def test_valid_line(self, sample_hathifile_line: str) -> None:
        record = parse_hathifile_line(sample_hathifile_line)
        assert record is not None
        assert record["htid"] == "uc1.b2889853"
        assert record["category"] == "debates"
        assert record["year"] == 1886
        assert record["volume"] == "v.1 (1886)"
        assert record["rights"] == "pd"
        assert record["oclc_num"] == "01149942"
        assert record["source"] == "uc1"

    def test_empty_line(self) -> None:
        assert parse_hathifile_line("") is None

    def test_whitespace_only_line(self) -> None:
        assert parse_hathifile_line("   " + T + "   \n") is None

    def test_comment_line(self) -> None:
        assert parse_hathifile_line("# this is a comment") is None

    def test_too_few_columns(self) -> None:
        line = T.join(["a", "b", "c"])
        assert parse_hathifile_line(line) is None

    def test_custom_category(self, sample_hathifile_line: str) -> None:
        record = parse_hathifile_line(sample_hathifile_line, category="hansard")
        assert record is not None
        assert record["category"] == "hansard"

    def test_custom_collection_id(self, sample_hathifile_line: str) -> None:
        record = parse_hathifile_line(sample_hathifile_line, collection_id="99999999")
        assert record is not None
        assert record["collection_id"] == "99999999"


class TestRightsCode:
    @pytest.mark.parametrize(
        ("code", "expected"),
        [
            ("pd", "pd"),
            ("pdus", "pd"),
            ("ic", "ic-world"),
            ("icus", "ic-world"),
            ("und", "undetermined"),
            ("sup", "suppressed"),
            ("nobody", "suppressed"),
            ("UNKNOWN", "undetermined"),
            ("", "undetermined"),
        ],
    )
    def test_rights_mapping(self, code: str, expected: str) -> None:
        assert _rights_code(code) == expected


class TestExtractYear:
    @pytest.mark.parametrize(
        ("imprint", "expected"),
        [
            ("Wellington, 1886", 1886),
            ("London, 1901", 1901),
            ("New York, 1999", 1999),
            ("Published 1854.", 1854),
            ("[1923]", 1923),
            ("Printed in 2020", 2020),
            ("", None),
            ("No date here", None),
            ("18th century", None),
            ("v.1 (1886)", 1886),
        ],
    )
    def test_extract_year(self, imprint: str, expected: int | None) -> None:
        assert _extract_year(imprint) == expected


class TestExtractYearFromTitle:
    @pytest.mark.parametrize(
        ("title", "expected"),
        [
            ("Parliamentary debates. 1886", 1886),
            ("Vol. 1 (1890)", 1890),
            ("Annual Report 1954", 1954),
            ("No year here", None),
            ("", None),
            ("20th Century History", None),
        ],
    )
    def test_extract_year_from_title(self, title: str, expected: int | None) -> None:
        assert _extract_year_from_title(title) == expected


class TestComputeSha256:
    def test_compute_sha256_missing_file(self, tmp_path: Path) -> None:
        missing = tmp_path / "does_not_exist.txt"
        assert compute_sha256(missing) is None

    def test_compute_sha256_valid(self, tmp_path: Path) -> None:
        p = tmp_path / "test.txt"
        content = b"hello world"
        p.write_bytes(content)
        expected = hashlib.sha256(content).hexdigest()
        assert compute_sha256(p) == expected


class TestBuildManifestFromHathifile:
    def test_build_from_txt(self, temp_hathifile_txt: Path) -> None:
        volumes = build_manifest_from_hathifile(temp_hathifile_txt)
        assert len(volumes) == 3
        assert volumes[0]["htid"] == "uc1.b2889853"
        assert volumes[1]["htid"] == "uc1.b2889854"
        assert volumes[2]["htid"] == "mdp.123456"

    def test_build_from_txt_missing_year_filled(self, tmp_path: Path) -> None:
        row = T.join(
            [
                "uc1.b2889855",
                "pd",
                "pd",
                "NJP",
                "uc1",
                "Debates. 1888",
                "No year in imprint",
                "",
                "",
                "",
                "",
                "v.3",
                "",
                "n",
                "",
                "",
            ]
        )
        p = tmp_path / "hathi_no_imprint_year.txt"
        p.write_text(row, encoding="utf-8")
        volumes = build_manifest_from_hathifile(p)
        assert len(volumes) == 1
        assert volumes[0]["year"] == 1888

    def test_build_from_gz(self, temp_hathifile_gz: Path) -> None:
        volumes = build_manifest_from_hathifile(temp_hathifile_gz)
        assert len(volumes) == 3

    def test_empty_hathifile(self, tmp_path: Path) -> None:
        p = tmp_path / "empty.txt"
        p.write_text("", encoding="utf-8")
        volumes = build_manifest_from_hathifile(p)
        assert volumes == []

    def test_comments_only(self, tmp_path: Path) -> None:
        p = tmp_path / "comments.txt"
        p.write_text("# line1\n# line2\n", encoding="utf-8")
        volumes = build_manifest_from_hathifile(p)
        assert volumes == []


class TestWriteManifest:
    def test_write_manifest_basic(self, tmp_path: Path) -> None:
        volumes = [
            {
                "htid": "uc1.b2889853",
                "category": "debates",
                "year": 1886,
                "volume": "v.1",
                "title": "Parliamentary debates.",
                "rights": "pd",
            }
        ]
        out = tmp_path / "manifest.json"
        manifest = write_manifest(volumes, out)

        assert manifest["meta"]["record_count"] == 1
        assert manifest["meta"]["version"] == "0.1.0"
        assert manifest["meta"]["source"] is not None
        assert "generated_at" in manifest["meta"]
        assert manifest["volumes"] == volumes
        assert out.exists()
        loaded = json.loads(out.read_text(encoding="utf-8"))
        assert loaded == manifest

    def test_write_manifest_empty(self, tmp_path: Path) -> None:
        out = tmp_path / "empty_manifest.json"
        manifest = write_manifest([], out)
        assert manifest["meta"]["record_count"] == 0
        assert manifest["volumes"] == []

    def test_write_manifest_creates_parent_dir(self, tmp_path: Path) -> None:
        nested = tmp_path / "sub" / "nested" / "manifest.json"
        volumes = [
            {
                "htid": "mdp.123456",
                "category": "debates",
                "year": 1900,
                "volume": "",
                "title": "Test",
                "rights": "pd",
            }
        ]
        write_manifest(volumes, nested)
        assert nested.exists()
        loaded = json.loads(nested.read_text(encoding="utf-8"))
        assert loaded["meta"]["record_count"] == 1


class TestLookupVolumeMetadata:
    def test_lookup_success(self, monkeypatch: pytest.MonkeyPatch) -> None:
        def mock_get(*args: object, **kwargs: object) -> object:
            class MockResponse:
                ok = True
                status_code = 200

                @staticmethod
                def json() -> dict[str, object]:
                    return {"htid": "uc1.b2889853", "title": "Debates"}

                @staticmethod
                def raise_for_status() -> None:
                    pass

            return MockResponse()

        monkeypatch.setattr("requests.get", mock_get)
        result = lookup_volume_metadata("uc1.b2889853")
        assert result is not None
        assert result["htid"] == "uc1.b2889853"

    def test_lookup_failure(self, monkeypatch: pytest.MonkeyPatch) -> None:
        def mock_get(*args: object, **kwargs: object) -> object:
            class MockResponse:
                ok = False
                status_code = 404

                @staticmethod
                def raise_for_status() -> None:
                    msg = "404 Not Found"
                    raise requests.exceptions.RequestException(msg)

            return MockResponse()

        monkeypatch.setattr("requests.get", mock_get)
        result = lookup_volume_metadata("nonexistent.volume")
        assert result is None

    def test_lookup_connection_error(self, monkeypatch: pytest.MonkeyPatch) -> None:
        def mock_get(*args: object, **kwargs: object) -> object:
            msg = "Connection refused"
            raise requests.exceptions.ConnectionError(msg)

        monkeypatch.setattr("requests.get", mock_get)
        result = lookup_volume_metadata("uc1.b2889853")
        assert result is None


class TestParseArgs:
    def test_parse_hathifile_command(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(
            sys,
            "argv",
            ["prog", "hathifile", "--hathifile", "some_file.txt", "--output", "custom.json"],
        )
        args = parse_args()
        assert args.command == "hathifile"
        assert args.hathifile == Path("some_file.txt")
        assert args.output == Path("custom.json")
        assert args.collection_id == "71329709"
        assert args.category == "debates"

    def test_parse_api_lookup_command(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(sys, "argv", ["prog", "api-lookup", "uc1.b2889853"])
        args = parse_args()
        assert args.command == "api-lookup"
        assert args.htid == "uc1.b2889853"

    def test_parse_hathifile_defaults(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(sys, "argv", ["prog", "hathifile", "--hathifile", "data.txt"])
        args = parse_args()
        assert args.output == Path("manifests/latest_manifest.json")

    def test_parse_missing_subcommand(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(sys, "argv", ["prog"])
        with pytest.raises(SystemExit):
            parse_args()

    def test_parse_custom_collection(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(
            sys,
            "argv",
            [
                "prog",
                "hathifile",
                "--hathifile",
                "data.txt",
                "--collection-id",
                "12345",
                "--category",
                "hansard",
            ],
        )
        args = parse_args()
        assert args.collection_id == "12345"
        assert args.category == "hansard"


class TestRoundTrip:
    """End-to-end: hathifile -> build manifest -> verify JSON."""

    def test_round_trip(self, temp_hathifile_txt: Path, tmp_path: Path) -> None:
        volumes = build_manifest_from_hathifile(temp_hathifile_txt)
        manifest_path = tmp_path / "roundtrip.json"
        write_manifest(volumes, manifest_path)

        loaded = json.loads(manifest_path.read_text(encoding="utf-8"))
        assert "meta" in loaded
        assert "volumes" in loaded
        assert loaded["meta"]["record_count"] == 3
        assert len(loaded["volumes"]) == 3

        for vol in loaded["volumes"]:
            assert "htid" in vol
            assert "category" in vol
            assert "year" in vol
            assert "volume" in vol
            assert "title" in vol
            assert "rights" in vol
