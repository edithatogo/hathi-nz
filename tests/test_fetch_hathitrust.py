"""Tests for scripts/fetch_hathitrust.py -- HathiTrust volume enumeration."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import io
import json
import sys
from pathlib import Path
from typing import Self

import pytest
import requests

from scripts.fetch_hathitrust import (
    _extract_year,
    _extract_year_from_title,
    _latest_full_hathifile_url,
    _rights_code,
    build_manifest_from_collection_export,
    build_manifest_from_hathifile,
    build_manifest_from_hathifile_url,
    compute_sha256,
    enrich_volume_metadata,
    lookup_volume_metadata,
    main,
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
        "uc1.31175035194995",
        "New Zealand. Parliament. Parliamentary debates.",
        "uc1",
        "",
        "01149942",
        "",
        "",
        "",
        "New Zealand. Parliament. Parliamentary debates (Hansard) v.1",
        "Wellington, 1886",
        "",
        "n",
        "",
        "",
        "Wellington",
        "eng",
        "txt",
        "NJP",
        "UC1",
        "UC1",
        "Google",
        "pd",
        "New Zealand. Parliament.",
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
        "uc1.31175035194995",
        "Parliamentary debates.",
        "uc1",
        "",
        "01149942",
        "",
        "",
        "",
        "Parliamentary debates (Hansard) v.1",
        "Wellington, 1886",
        "",
        "n",
        "",
        "",
        "Wellington",
        "eng",
        "txt",
        "NJP",
        "UC1",
        "UC1",
        "Google",
        "pd",
        "New Zealand. Parliament.",
    ]
    row2 = [
        "uc1.b2889854",
        "pdus",
        "pdus",
        "uc1.31175035194996",
        "Parliamentary debates. v.2",
        "uc1",
        "",
        "01149943",
        "",
        "",
        "",
        "Parliamentary debates (Hansard) v.2",
        "Wellington, 1887",
        "",
        "n",
        "",
        "",
        "Wellington",
        "eng",
        "txt",
        "NJP",
        "UC1",
        "UC1",
        "Google",
        "pd",
        "New Zealand. Parliament.",
    ]
    row3 = [
        "mdp.123456",
        "ic",
        "ic",
        "mdp.123456",
        "Some other title",
        "mdp",
        "",
        "99999999",
        "",
        "",
        "",
        "Some other title v.1",
        "Ann Arbor, 1900",
        "n",
        "",
        "",
        "Ann Arbor",
        "eng",
        "txt",
        "MIU",
        "MIU",
        "MIU",
        "Google",
        "ic",
        "Some author",
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
        assert record["volume"] == "v.1"
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

    def test_filters_nonmatching_collection_code(self, sample_hathifile_line: str) -> None:
        assert parse_hathifile_line(sample_hathifile_line, collection_code="MIU") is None

    def test_filters_nonmatching_htid_allowlist(self, sample_hathifile_line: str) -> None:
        assert parse_hathifile_line(
            sample_hathifile_line,
            htid_allowlist={"other.id"},
        ) is None


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
        assert len(volumes) == 2
        assert volumes[0]["htid"] == "uc1.b2889853"
        assert volumes[1]["htid"] == "uc1.b2889854"

    def test_build_from_txt_missing_year_filled(self, tmp_path: Path) -> None:
        row = T.join(
            [
                "uc1.b2889855",
                "pd",
                "pd",
                "uc1.31175035194997",
                "Debates. 1888",
                "uc1",
                "",
                "",
                "",
                "",
                "",
                "Debates (Hansard) v.3",
                "No year in imprint",
                "",
                "n",
                "",
                "",
                "Wellington",
                "eng",
                "txt",
                "NJP",
                "UC1",
                "UC1",
                "Google",
                "pd",
                "New Zealand. Parliament.",
            ]
        )
        p = tmp_path / "hathi_no_imprint_year.txt"
        p.write_text(row, encoding="utf-8")
        volumes = build_manifest_from_hathifile(p)
        assert len(volumes) == 1
        assert volumes[0]["year"] == 1888

    def test_build_from_gz(self, temp_hathifile_gz: Path) -> None:
        volumes = build_manifest_from_hathifile(temp_hathifile_gz)
        assert len(volumes) == 2

    def test_build_from_txt_with_allowlist(self, temp_hathifile_txt: Path) -> None:
        volumes = build_manifest_from_hathifile(
            temp_hathifile_txt,
            htid_allowlist={"uc1.b2889854"},
        )
        assert len(volumes) == 1
        assert volumes[0]["htid"] == "uc1.b2889854"

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
                "collection_id": "71329709",
                "source": "uc1",
            }
        ]
        out = tmp_path / "manifest.json"
        manifest = write_manifest(volumes, out)

        assert manifest["meta"]["record_count"] == 1
        assert manifest["meta"]["version"]  # non-empty dynamic version
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
                "collection_id": "71329709",
                "source": "mdp",
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

    def test_lookup_retries_transient_errors(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        calls = {"count": 0}

        class MockResponse:
            @staticmethod
            def json() -> dict[str, str]:
                return {"htid": "uc1.b2889853"}

            @staticmethod
            def raise_for_status() -> None:
                return None

        def mock_get(*args: object, **kwargs: object) -> MockResponse:  # noqa: ARG001
            calls["count"] += 1
            if calls["count"] < 3:
                msg = "temporary network failure"
                raise requests.exceptions.ConnectionError(msg)
            return MockResponse()

        monkeypatch.setattr("requests.get", mock_get)
        result = lookup_volume_metadata("uc1.b2889853")

        assert result is not None
        assert result["htid"] == "uc1.b2889853"
        assert calls["count"] == 3


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
        assert args.collection_code == "NJP"
        assert args.category == "debates"

    def test_parse_hathifile_allowlist(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(
            sys,
            "argv",
            [
                "prog",
                "hathifile",
                "--hathifile",
                "some_file.txt",
                "--htid-allowlist",
                "allow.txt",
            ],
        )
        args = parse_args()
        assert args.htid_allowlist == Path("allow.txt")

    def test_parse_api_lookup_command(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(sys, "argv", ["prog", "api-lookup", "uc1.b2889853"])
        args = parse_args()
        assert args.command == "api-lookup"
        assert args.htid == "uc1.b2889853"

    def test_parse_hathifile_defaults(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(sys, "argv", ["prog", "hathifile", "--hathifile", "data.txt"])
        args = parse_args()
        assert args.output == Path("manifests/latest_manifest.json")

    def test_parse_collection_export_defaults(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(sys, "argv", ["prog", "collection-export"])
        args = parse_args()
        assert args.command == "collection-export"
        assert args.collection_id == "71329709"
        assert args.enrich_api is False

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
                "--collection-code",
                "MIU",
                "--category",
                "hansard",
            ],
        )
        args = parse_args()
        assert args.collection_id == "12345"
        assert args.collection_code == "MIU"
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
        assert loaded["meta"]["record_count"] == 2
        assert len(loaded["volumes"]) == 2

        for vol in loaded["volumes"]:
            assert "htid" in vol
            assert "category" in vol
            assert "year" in vol
            assert "volume" in vol
            assert "title" in vol
            assert "rights" in vol


class TestRemoteHathifile:
    def test_latest_full_hathifile_url_picks_full_file(self, monkeypatch: pytest.MonkeyPatch) -> None:
        payload = [
            {"filename": "hathi_upd_20260701.txt.gz", "full": False, "url": "https://example.com/upd"},
            {"filename": "hathi_full_20260701.txt.gz", "full": True, "url": "https://example.com/full"},
        ]

        class Response:
            @staticmethod
            def raise_for_status() -> None:
                return None

            @staticmethod
            def json() -> list[dict[str, object]]:
                return payload

        monkeypatch.setattr("requests.get", lambda *a, **kw: Response())
        assert _latest_full_hathifile_url() == "https://example.com/full"

    def test_build_manifest_from_hathifile_url(self, monkeypatch: pytest.MonkeyPatch) -> None:
        rows = "\n".join(
            [
                T.join(
                    [
                        "uc1.b2889853",
                        "pd",
                        "pd",
                        "uc1.31175035194995",
                        "Parliamentary debates.",
                        "uc1",
                        "",
                        "01149942",
                        "",
                        "",
                        "",
                        "Parliamentary debates (Hansard) v.1",
                        "Wellington, 1886",
                        "",
                        "n",
                        "",
                        "",
                        "Wellington",
                        "eng",
                        "txt",
                        "NJP",
                        "UC1",
                        "UC1",
                        "Google",
                        "pd",
                        "New Zealand. Parliament.",
                    ]
                ),
                T.join(
                    [
                        "mdp.123456",
                        "ic",
                        "ic",
                        "mdp.123456",
                        "Other",
                        "mdp",
                        "",
                        "99999999",
                        "",
                        "",
                        "",
                        "Other",
                        "Ann Arbor, 1900",
                        "",
                        "n",
                        "",
                        "",
                        "Ann Arbor",
                        "eng",
                        "txt",
                        "MIU",
                        "MIU",
                        "MIU",
                        "Google",
                        "ic",
                        "Some author",
                    ]
                ),
            ]
        ).encode("utf-8")
        compressed = io.BytesIO()
        with gzip.GzipFile(fileobj=compressed, mode="wb") as gz:
            gz.write(rows)
        payload = compressed.getvalue()

        class Response:
            ok = True
            status_code = 200
            raw = io.BytesIO(payload)

            def __enter__(self) -> Self:
                return self

            def __exit__(self, exc_type, exc, tb) -> None:
                return None

            @staticmethod
            def raise_for_status() -> None:
                return None

        def fake_get(*args: object, **kwargs: object) -> Response:  # noqa: ARG001
            return Response()

        monkeypatch.setattr("requests.get", fake_get)
        volumes = build_manifest_from_hathifile_url("https://example.com/full.gz")
        assert len(volumes) == 1
        assert volumes[0]["htid"] == "uc1.b2889853"

    def test_build_manifest_from_hathifile_url_with_api_enrichment(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        rows = "\n".join(
            [
                T.join(
                    [
                        "uc1.b2889853",
                        "allow",
                        "cc-zero",
                        "007119315",
                        "1854-55",
                        "UC",
                        "b15154233",
                        "173322878,173355174,248552646,4826506",
                        "",
                        "0111-5642",
                        "",
                        "Parliamentary debates (Hansard)",
                        "by authority, Government Printer",
                        "con",
                        "2017-03-20 14:46:17",
                        "0",
                        "1855",
                        "nz ",
                        "eng",
                        "SE",
                        "NJP",
                        "universityofcalifornia",
                        "universityofcalifornia",
                        "google",
                        "google",
                        "New Zealand. Parliament",
                    ]
                )
            ]
        ).encode("utf-8")
        compressed = io.BytesIO()
        with gzip.GzipFile(fileobj=compressed, mode="wb") as gz:
            gz.write(rows)
        payload = compressed.getvalue()

        class Response:
            ok = True
            status_code = 200
            raw = io.BytesIO(payload)

            def __enter__(self) -> Self:
                return self

            def __exit__(self, exc_type, exc, tb) -> None:
                return None

            @staticmethod
            def raise_for_status() -> None:
                return None

        def fake_get(
            url: str,
            timeout: int,
            stream: bool = False,
            **kwargs: object,
        ):  # type: ignore[no-untyped-def]
            if stream:
                return Response()

            class ApiResponse:
                @staticmethod
                def raise_for_status() -> None:
                    return None

                @staticmethod
                def json() -> dict[str, object]:
                    return {
                        "htid": "uc1.b2889853",
                        "title": "Parliamentary debates (Hansard)",
                        "source": "UC",
                        "year": 1855,
                        "rights": "allow",
                        "volume": "v.1",
                    }

            return ApiResponse()

        monkeypatch.setattr("requests.get", fake_get)
        volumes = build_manifest_from_hathifile_url(
            "https://example.com/full.gz",
            enrich_api=True,
        )
        assert len(volumes) == 1
        assert volumes[0]["title"] == "Parliamentary debates (Hansard)"
        assert volumes[0]["volume"] == "v.1"
        assert volumes[0]["source"] == "UC"

    def test_build_manifest_from_collection_export(self, monkeypatch: pytest.MonkeyPatch) -> None:
        tsv = "\n".join(
            [
                "htitem_id\ttitle",
                "uc1.b2889853\tParliamentary debates (Hansard) v.1",
                "uc1.b2889854\tParliamentary debates (Hansard) v.2",
            ]
        )

        class ExportResponse:
            @staticmethod
            def raise_for_status() -> None:
                return None

            @property
            def text(self) -> str:
                return tsv

        def fake_post(*args: object, **kwargs: object) -> ExportResponse:  # noqa: ARG001
            return ExportResponse()

        def fake_get(*args: object, **kwargs: object):  # type: ignore[no-untyped-def]
            class ApiResponse:
                @staticmethod
                def raise_for_status() -> None:
                    return None

                @staticmethod
                def json() -> dict[str, object]:
                    return {
                        "htid": "uc1.b2889853",
                        "title": "Parliamentary debates (Hansard) v.1",
                        "source": "UC",
                        "year": 1886,
                        "rights": "allow",
                        "volume": "v.1",
                    }

            return ApiResponse()

        monkeypatch.setattr("requests.post", fake_post)
        monkeypatch.setattr("requests.get", fake_get)
        volumes = build_manifest_from_collection_export("71329709")
        assert len(volumes) == 2
        assert volumes[0]["htid"] == "uc1.b2889853"
        assert volumes[0]["title"] == "Parliamentary debates (Hansard) v.1"
        assert volumes[0]["collection_id"] == "71329709"
        assert volumes[1]["htid"] == "uc1.b2889854"

    def test_enrich_volume_metadata(self, monkeypatch: pytest.MonkeyPatch) -> None:
        def fake_get(*args: object, **kwargs: object):  # type: ignore[no-untyped-def]
            class ApiResponse:
                @staticmethod
                def raise_for_status() -> None:
                    return None

                @staticmethod
                def json() -> dict[str, object]:
                    return {
                        "htid": "uc1.b2889853",
                        "title": "Parliamentary debates (Hansard)",
                        "source": "UC",
                        "year": 1855,
                        "rights": "allow",
                        "volume": "v.1",
                    }

            return ApiResponse()

        monkeypatch.setattr("requests.get", fake_get)
        record = {"htid": "uc1.b2889853", "title": "X", "year": None, "rights": "pd"}
        enriched = enrich_volume_metadata(record)
        assert enriched["title"] == "Parliamentary debates (Hansard)"
        assert enriched["year"] == 1855
        assert enriched["source"] == "UC"

    def test_main_hathifile_branch(self, monkeypatch: pytest.MonkeyPatch, temp_hathifile_txt: Path, tmp_path: Path) -> None:
        output = tmp_path / "manifest.json"

        monkeypatch.setattr(
            "scripts.fetch_hathitrust.parse_args",
            lambda args=None: argparse.Namespace(
                command="hathifile",
                hathifile=temp_hathifile_txt,
                output=output,
                collection_id="71329709",
                collection_code="NJP",
                htid_allowlist=None,
                category="debates",
            ),
        )

        exit_code = main()

        assert exit_code == 0
        assert output.exists()
        manifest = json.loads(output.read_text(encoding="utf-8"))
        assert manifest["meta"]["record_count"] == 2

    def test_main_remote_hathifile_without_download_path(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        output = tmp_path / "manifest.json"
        rows = [T.join([
            "uc1.b2889853",
            "pd",
            "pd",
            "uc1.31175035194995",
            "Parliamentary debates.",
            "uc1",
            "",
            "01149942",
            "",
            "",
            "",
            "Parliamentary debates (Hansard) v.1",
            "Wellington, 1886",
            "",
            "n",
            "",
            "",
            "Wellington",
            "eng",
            "txt",
            "NJP",
            "UC1",
            "UC1",
            "Google",
            "pd",
            "New Zealand. Parliament.",
        ])]

        monkeypatch.setattr(
            "scripts.fetch_hathitrust.parse_args",
            lambda args=None: argparse.Namespace(
                command="remote-hathifile",
                url="https://example.com/full.gz",
                download_to=None,
                output=output,
                collection_id="71329709",
                collection_code="NJP",
                htid_allowlist=None,
                category="debates",
                enrich_api=False,
            ),
        )
        monkeypatch.setattr(
            "scripts.fetch_hathitrust._iter_remote_hathifile_lines",
            lambda url: iter(rows),
        )

        exit_code = main()

        assert exit_code == 0
        assert output.exists()
        manifest = json.loads(output.read_text(encoding="utf-8"))
        assert manifest["meta"]["record_count"] == 1

    def test_main_collection_export_branch(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        output = tmp_path / "collection.json"
        called: dict[str, object] = {}

        monkeypatch.setattr(
            "scripts.fetch_hathitrust.parse_args",
            lambda args=None: argparse.Namespace(
                command="collection-export",
                collection_id="71329709",
                output=output,
                htid_allowlist=None,
                category="debates",
                export_file=None,
                enrich_api=True,
            ),
        )
        monkeypatch.setattr(
            "scripts.fetch_hathitrust.build_manifest_from_collection_export",
            lambda **kwargs: called.update(kwargs) or [{"htid": "uc1.b2889853", "title": "x"}],
        )
        monkeypatch.setattr(
            "scripts.fetch_hathitrust.write_manifest",
            lambda volumes, output_path: {"meta": {"record_count": len(volumes)}},
        )

        exit_code = main()

        assert exit_code == 0
        assert called["collection_id"] == "71329709"
        assert called["enrich_api"] is True
