"""Tests for scripts/ocr_extract.py -- OCR text extraction and cleaning."""

from __future__ import annotations

import argparse
import json
import zipfile
from pathlib import Path

import pytest

import scripts.ocr_extract as ocr_extract_module
from scripts.ocr_extract import (
    _parse_page_number,
    clean_text,
    detect_layout,
    extract_text_from_zip,
    load_page_text,
    merge_pages,
    process_volume,
    reconstruct_columns,
    sort_pages,
    write_processed,
)


@pytest.fixture
def sample_text_with_hyphenation() -> str:
    return (
        "This is a sample text with a hyphen-\n"
        "ated word that spans two lines.\n"
        "Another exam-\n"
        "ple of hyphenation across a line break.\n"
        "Normal line without hyphenation.\n"
    )


@pytest.fixture
def sample_text_with_headers() -> str:
    return (
        "Page 1\n"
        "\n"
        "New Zealand Parliamentary Debates\n"
        "\n"
        "This is the actual content of the page.\n"
        "It contains important parliamentary discussion.\n"
        "\n"
        "--- page footer ---\n"
        "\n"
        "5\n"
        "\n"
    )


@pytest.fixture
def sample_multi_column_text() -> str:
    return "\n".join([f"Short col {i:02d}" for i in range(20)])


@pytest.fixture
def sample_single_column_text() -> str:
    return (
        "Full-width line of text found in single-column layout.\n"
        "Another lengthy parliamentary debate proceedings line.\n"
        "Yet another substantial line with many characters here.\n"
        "A fourth reasonably long line for testing accuracy.\n"
        "Fifth and final line of this single-column test fixture.\n"
    )


@pytest.fixture
def temp_zip_with_text(tmp_path: Path) -> Path:
    zip_path = tmp_path / "uc1_b2889853.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("0002.txt", "Page 2\n\nContent second page.\nDiscussion.\n")
        zf.writestr("0001.txt", "Page 1\n\nContent first page.\nDebate text.\n")
        zf.writestr("0003.txt", "3\n\nFinal page.\nClosing remarks.\n")
    return zip_path


@pytest.fixture
def temp_zip_no_text(tmp_path: Path) -> Path:
    zip_path = tmp_path / "no_text.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("image001.jpg", b"fake image")
    return zip_path


@pytest.fixture
def temp_bad_zip(tmp_path: Path) -> Path:
    zip_path = tmp_path / "bad.zip"
    zip_path.write_bytes(b"not a zip file")
    return zip_path


class TestCleanText:
    def test_joins_hyphenated_line_breaks(self, sample_text_with_hyphenation: str) -> None:
        result = clean_text(sample_text_with_hyphenation)
        assert "hyphenated" in result
        assert "hyphen-\nated" not in result
        assert "example" in result
        assert "exam-\nple" not in result

    def test_removes_headers_and_footers(self, sample_text_with_headers: str) -> None:
        result = clean_text(sample_text_with_headers)
        assert "Page 1" not in result
        assert "New Zealand Parliamentary Debates" not in result
        assert "page footer" not in result
        assert "actual content" in result

    def test_removes_standalone_page_numbers(self) -> None:
        text = "Some content.\n\n42\n\nMore content.\n\n105\n\nFinal.\n"
        result = clean_text(text)
        assert "Some content" in result
        assert "More content" in result
        assert "Final" in result

    def test_normalizes_whitespace(self) -> None:
        text = "Line one.\n\n\n\n\nLine two.\n   \nLine three.  \n"
        result = clean_text(text)
        assert "\n\n\n" not in result
        assert "Line one." in result
        assert "Line two." in result
        assert "Line three." in result

    def test_strips_leading_trailing_whitespace(self) -> None:
        text = "  \n  Hello world.  \n  \n"
        result = clean_text(text)
        assert result == "Hello world."

    def test_empty_string(self) -> None:
        assert clean_text("") == ""

    def test_only_whitespace(self) -> None:
        assert clean_text("   \n  \n   ") == ""

    def test_no_changes_needed(self) -> None:
        text = "Clean text without any issues.\nSecond line."
        result = clean_text(text)
        assert result == text.strip()

    def test_hyphenation_with_caps(self) -> None:
        text = "This is a CAPIT-\nALIZED word."
        result = clean_text(text)
        assert "CAPITALIZED" in result

    def test_multiple_hyphenations(self) -> None:
        text = "First hyphen-\nated word.\nSecond hyphen-\nated word."
        result = clean_text(text)
        assert "hyphenated" in result


class TestLayoutReconstruction:
    def test_sort_pages_orders_by_page_number(self) -> None:
        pages = [
            {"page_num": 3, "member_name": "0003.txt", "text": "third"},
            {"page_num": 1, "member_name": "0001.txt", "text": "first"},
            {"page_num": 2, "member_name": "0002.txt", "text": "second"},
        ]

        ordered = sort_pages(pages)
        assert [page["page_num"] for page in ordered] == [1, 2, 3]

    def test_reconstruct_columns_joins_column_fragments(self) -> None:
        pages = [
            {
                "page_num": 1,
                "member_name": "0001.txt",
                "columns": ["Left column line 1\nLeft column line 2", "Right column line 1"],
            }
        ]

        reconstructed = reconstruct_columns(pages)
        assert (
            reconstructed[0]["text"]
            == "Left column line 1\nLeft column line 2\n\nRight column line 1"
        )
        assert reconstructed[0]["layout"]["column_estimate"] == 2
        assert reconstructed[0]["layout"]["has_columns"] is True

    def test_merge_pages_joins_clean_text_blocks(self) -> None:
        pages = [{"text": "First page."}, {"text": "Second page."}]
        assert merge_pages(pages) == "First page.\n\nSecond page."


class TestLowLevelHelpers:
    def test_parse_page_number_handles_numeric_and_non_numeric(self) -> None:
        assert _parse_page_number("0007.txt") == 7
        assert _parse_page_number("frontmatter.txt") is None

    def test_detect_layout_handles_empty_and_multi_column_text(self) -> None:
        assert detect_layout("") == {
            "column_estimate": 1,
            "line_count": 0,
            "avg_line_length": 0.0,
            "max_line_length": 0,
            "has_columns": False,
        }

        multi_column_text = "\n".join(
            ["short line"] * 6 + ["this is a deliberately long line to trigger the heuristic"]
        )
        layout = detect_layout(multi_column_text)
        assert layout["column_estimate"] == 2
        assert layout["has_columns"] is True

    def test_extract_text_from_zip_handles_bad_zip(
        self, temp_bad_zip: Path, tmp_path: Path
    ) -> None:
        result = extract_text_from_zip(temp_bad_zip, tmp_path)
        assert result["pages_extracted"] == 0
        assert result["layout_stats"]["error"]

    def test_extract_text_from_zip_processes_valid_zip(
        self, temp_zip_with_text: Path, tmp_path: Path
    ) -> None:
        result = extract_text_from_zip(temp_zip_with_text, tmp_path / "processed")
        assert result["success"] is True
        assert result["pages_extracted"] == 3


class TestProcessVolume:
    def test_load_page_text_reads_zip_pages(self, tmp_path: Path, temp_zip_with_text: Path) -> None:
        pages = load_page_text(tmp_path, "uc1.b2889853")
        assert len(pages) == 3
        assert [page["page_num"] for page in pages] == [1, 2, 3]

    def test_process_volume_writes_combined_text(
        self, tmp_path: Path, temp_zip_with_text: Path
    ) -> None:
        processed_dir = tmp_path / "processed"
        result = process_volume("uc1.b2889853", tmp_path, processed_dir)

        assert result["success"] is True
        assert result["pages_extracted"] == 3
        output_path = Path(result["output_path"])
        assert output_path.exists()
        content = output_path.read_text(encoding="utf-8")
        assert "Content first page." in content
        assert content.index("Content first page.") < content.index("Content second page.")
        assert (processed_dir / "uc1_b2889853" / "pages" / "0001.txt").exists()

    def test_write_processed_creates_volume_file(self, tmp_path: Path) -> None:
        output = write_processed("uc1.b2889853", "hello", tmp_path)
        assert output.exists()
        assert output.read_text(encoding="utf-8") == "hello"


class TestMain:
    def test_main_writes_output_and_returns_zero(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        output_file = tmp_path / "result.json"
        monkeypatch.setattr(
            ocr_extract_module,
            "parse_args",
            lambda args=None: argparse.Namespace(
                htid="uc1.b2889853",
                raw_dir=tmp_path,
                processed_dir=tmp_path / "processed",
                output=output_file,
            ),
        )
        monkeypatch.setattr(
            ocr_extract_module,
            "process_volume",
            lambda **_: {
                "success": True,
                "htid": "uc1.b2889853",
                "pages_extracted": 1,
            },
        )

        assert ocr_extract_module.main() == 0
        written = json.loads(output_file.read_text(encoding="utf-8"))
        assert written["success"] is True
        assert written["htid"] == "uc1.b2889853"

    def test_main_returns_one_for_failed_processing(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        monkeypatch.setattr(
            ocr_extract_module,
            "parse_args",
            lambda args=None: argparse.Namespace(
                htid="uc1.b2889853",
                raw_dir=tmp_path,
                processed_dir=tmp_path / "processed",
                output=None,
            ),
        )
        monkeypatch.setattr(
            ocr_extract_module,
            "process_volume",
            lambda **_: {"success": False, "error": "missing zip"},
        )

        assert ocr_extract_module.main() == 1
