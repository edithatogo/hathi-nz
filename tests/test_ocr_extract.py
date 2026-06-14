"""Tests for scripts/ocr_extract.py -- OCR text extraction and cleaning."""

from __future__ import annotations

import zipfile
from pathlib import Path

import pytest

from scripts.ocr_extract import (
    clean_text,
    detect_layout,
    extract_text_from_zip,
    parse_args,
    process_volume,
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
    zip_path = tmp_path / "test_volume.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("0001.txt", "Page 1\n\nContent first page.\nDebate text.\n")
        zf.writestr("0002.txt", "Page 2\n\nContent second page.\nDiscussion.\n")
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

        "More content on the next logical page.\n"
    )
