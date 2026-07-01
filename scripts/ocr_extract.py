"""OCR text extraction and cleaning for HathiTrust volumes.

Responsibility:
  - Clean raw OCR text (de-hyphenation, header/footer pruning, whitespace normalization)
  - Extract text from HathiTrust ZIP archives
  - Detect layout patterns (single vs multi-column)
  - Process volumes end-to-end and write cleaned output to data/processed/

Usage:
  python scripts/ocr_extract.py --htid uc1.b2889853 --raw-dir data/raw --processed-dir data/processed
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import zipfile
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from loguru import logger

from scripts.logging_utils import configure_logging

# ---------------------------------------------------------------
# Constants
# ---------------------------------------------------------------

# Patterns for page headers/footers commonly found in HathiTrust OCR
HEADER_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"^Page\s+\d+\s*\n", re.MULTILINE | re.IGNORECASE),
    re.compile(r"^\d+\s*\n{2,}", re.MULTILINE),
    re.compile(r"^-{3,}.*?-{3,}", re.MULTILINE),
    re.compile(r"^\s*New\s+Zealand\s+Parliamentary\s+Debates", re.MULTILINE | re.IGNORECASE),
]

# Pattern for page number lines (standalone numbers that are page markers)
PAGE_NUM_PATTERN = re.compile(r"^\s*\d+\s*$", re.MULTILINE)

# Hyphenated line-break pattern (word at end of line followed by hyphen-newline)
HYPHEN_BREAK = re.compile(r"(\w)-\n(\w)")

# Multiple blank lines
MULTI_BLANK = re.compile(r"\n{3,}")

# Leading/trailing whitespace per line
LEADING_TRAILING_WS = re.compile(r"^[ \t]+|[ \t]+$", re.MULTILINE)

# Page number extraction from OCR member names such as 0001.txt
PAGE_NUMBER_PATTERN = re.compile(r"(?P<page>\d+)")


# ---------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------


def clean_text(raw_text: str) -> str:
    """Clean raw OCR text from a HathiTrust volume.

    Processing steps:
      1. Remove known header/footer patterns
      2. Join hyphenated line-breaks (word-at-end-of-line hyphenation)
      3. Prune standalone page numbers
      4. Normalize whitespace (collapse multiple blank lines, strip line whitespace)
      5. Final strip

    Args:
        raw_text: Raw OCR text content.

    Returns:
        Cleaned text string.

    """
    text = raw_text

    # Step 1: Remove headers/footers
    for pattern in HEADER_PATTERNS:
        text = pattern.sub("", text)

    # Step 2: Join hyphenated line-breaks
    text = HYPHEN_BREAK.sub(r"\1\2", text)

    # Step 3: Remove standalone page numbers
    text = PAGE_NUM_PATTERN.sub("", text)

    # Step 4: Normalize whitespace
    text = LEADING_TRAILING_WS.sub("", text)
    text = MULTI_BLANK.sub("\n\n", text)

    # Step 5: Final strip
    return text.strip()


def _parse_page_number(member_name: str) -> int | None:
    """Extract a numeric page number from a ZIP member name."""
    match = PAGE_NUMBER_PATTERN.search(Path(member_name).stem)
    if not match:
        return None
    try:
        return int(match.group("page"))
    except ValueError:
        return None


def load_page_text(input_dir: Path, htid: str) -> list[dict[str, Any]]:
    """Load OCR page text from a HathiTrust ZIP archive.

    Args:
        input_dir: Directory containing the ZIP archive.
        htid: HathiTrust volume ID.

    Returns:
        List of page dictionaries ordered as found in the archive.

    """
    safe_name = htid.replace("/", "_").replace(".", "_")
    zip_path = input_dir / f"{safe_name}.zip"
    if not zip_path.exists():
        logger.warning("ZIP file not found for {} at {}", htid, zip_path)
        return []

    pages: list[dict[str, Any]] = []
    with zipfile.ZipFile(zip_path, "r") as zf:
        text_members = sorted(member for member in zf.namelist() if member.endswith(".txt"))
        for member_name in text_members:
            try:
                raw = zf.read(member_name).decode("utf-8", errors="replace")
            except Exception:  # noqa: BLE001
                raw = zf.read(member_name).decode("latin-1", errors="replace")
            pages.append(
                {
                    "htid": htid,
                    "page_num": _parse_page_number(member_name),
                    "member_name": member_name,
                    "text": raw,
                    "layout": detect_layout(raw),
                }
            )
    return pages


def sort_pages(pages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return pages sorted by page number while preserving stable order."""
    return sorted(
        pages,
        key=lambda page: (
            page.get("page_num") is None,
            page.get("page_num") or 0,
            str(page.get("member_name", "")),
        ),
    )


def reconstruct_columns(pages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Reconstruct page text from multi-column inputs when column fragments exist."""
    reconstructed: list[dict[str, Any]] = []
    for page in pages:
        new_page = dict(page)
        columns = page.get("columns")
        if isinstance(columns, list) and columns:
            column_texts = [str(column).strip() for column in columns if str(column).strip()]
            new_page["text"] = "\n\n".join(column_texts)
            new_page["layout"] = {
                **dict(page.get("layout", {})),
                "column_estimate": len(column_texts),
                "has_columns": len(column_texts) > 1,
            }
        elif isinstance(page.get("column_texts"), list) and page["column_texts"]:
            column_texts = [
                str(column).strip() for column in page["column_texts"] if str(column).strip()
            ]
            new_page["text"] = "\n\n".join(column_texts)
            new_page["layout"] = {
                **dict(page.get("layout", {})),
                "column_estimate": len(column_texts),
                "has_columns": len(column_texts) > 1,
            }
        else:
            new_page["text"] = str(page.get("text", ""))
        reconstructed.append(new_page)
    return reconstructed


def merge_pages(pages: list[dict[str, Any]]) -> str:
    """Merge cleaned page texts into a single volume text."""
    page_texts = [
        str(page.get("text", "")).strip() for page in pages if str(page.get("text", "")).strip()
    ]
    return "\n\n".join(page_texts).strip()


def write_processed(htid: str, text: str, output_dir: Path) -> Path:
    """Write processed volume text to output_dir."""
    safe_name = htid.replace("/", "_").replace(".", "_")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{safe_name}.txt"
    output_path.write_text(text, encoding="utf-8")
    return output_path


def detect_layout(page_text: str) -> dict[str, Any]:
    """Detect basic layout structure of a page.

    Uses whitespace patterns to estimate:
      - Likely column count (single vs multi-column)
      - Line count
      - Average line length

    Args:
        page_text: Text content of a single page.

    Returns:
        Dict with layout metadata:
          - 'column_estimate': int (1 or 2)
          - 'line_count': int
          - 'avg_line_length': float
          - 'max_line_length': int
          - 'has_columns': bool

    """
    lines = page_text.split("\n")
    non_empty = [ln for ln in lines if ln.strip()]

    if not non_empty:
        return {
            "column_estimate": 1,
            "line_count": 0,
            "avg_line_length": 0.0,
            "max_line_length": 0,
            "has_columns": False,
        }

    line_lengths = [len(ln.rstrip()) for ln in non_empty]
    avg_len = sum(line_lengths) / len(line_lengths) if line_lengths else 0.0
    max_len = max(line_lengths) if line_lengths else 0

    # Multi-column heuristic: many short lines with significant whitespace gaps
    # A typical full-width line in a book is 60-80 chars.
    # If avg line length is < 40 and max > 50, likely multi-column
    has_columns = avg_len < 40 and max_len > 50 and len(non_empty) > 5

    return {
        "column_estimate": 2 if has_columns else 1,
        "line_count": len(non_empty),
        "avg_line_length": round(avg_len, 1),
        "max_line_length": max_len,
        "has_columns": has_columns,
    }


def extract_text_from_zip(zip_path: Path, output_dir: Path) -> dict[str, Any]:
    """Extract text from a HathiTrust volume ZIP archive.

    HathiTrust ZIPs typically contain one text file per page (e.g. 0001.txt, 0002.txt).
    This function extracts each text file, cleans it, and writes to output_dir.

    Args:
        zip_path: Path to the HathiTrust volume ZIP file.
        output_dir: Directory to write cleaned text files.

    Returns:
        Dict with processing stats.

    """
    try:
        htid = zip_path.stem.replace("_", ".")
        raw_dir = zip_path.parent
        return process_volume(htid, raw_dir, output_dir)
    except zipfile.BadZipFile as exc:
        logger.error("Bad ZIP file {}: {}", zip_path, exc)
        return {
            "pages_extracted": 0,
            "total_chars": 0,
            "page_files": [],
            "layout_stats": {"pages": [], "error": str(exc)},
        }


def process_volume(
    htid: str,
    raw_dir: Path,
    processed_dir: Path,
    cleaning_config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Orchestrate full processing of a single HathiTrust volume.

    Args:
        htid: HathiTrust volume ID.
        raw_dir: Directory containing downloaded ZIP files.
        processed_dir: Base directory for processed output.
        cleaning_config: Optional cleaning configuration for future shared-library integration.

    Returns:
        Dict with processing results and stats.

    """
    pages = load_page_text(raw_dir, htid)
    if not pages:
        return {
            "htid": htid,
            "success": False,
            "error": f"ZIP file not found or contained no text pages for {htid}",
        }

    try:
        ordered_pages = sort_pages(pages)
        reconstructed_pages = reconstruct_columns(ordered_pages)
        cleaned_pages: list[dict[str, Any]] = []
        total_chars = 0
        page_files: list[str] = []
        layout_pages: list[dict[str, Any]] = []

        for page in reconstructed_pages:
            cleaned = clean_text(str(page.get("text", "")))
            if not cleaned:
                continue
            cleaned_page = {
                **page,
                "text": cleaned,
                "layout": detect_layout(cleaned),
            }
            cleaned_pages.append(cleaned_page)
            total_chars += len(cleaned)
            page_files.append(str(page.get("member_name", "")))
            layout_pages.append(
                {
                    "file": page.get("member_name", ""),
                    "chars": len(cleaned),
                    "layout": cleaned_page["layout"],
                }
            )

        volume_text = merge_pages(cleaned_pages)
        safe_name = htid.replace("/", "_").replace(".", "_")
        volume_output_dir = processed_dir / safe_name
        output_path = write_processed(htid, volume_text, volume_output_dir)

        page_output_dir = volume_output_dir / "pages"
        page_output_dir.mkdir(parents=True, exist_ok=True)
        for page in cleaned_pages:
            member_name = str(page.get("member_name", "page.txt"))
            out_name = Path(member_name).name
            (page_output_dir / out_name).write_text(str(page["text"]), encoding="utf-8")

        column_counts = [page["layout"]["column_estimate"] for page in cleaned_pages]
        multi_col_pct = (
            sum(1 for count in column_counts if count > 1) / max(len(column_counts), 1) * 100
        )
        layout_summary: dict[str, Any] = {
            "pages_analyzed": len(cleaned_pages),
            "multi_column_pct": round(multi_col_pct, 1),
            "avg_chars_per_page": round(total_chars / max(len(cleaned_pages), 1)),
        }

        result = {
            "htid": htid,
            "success": True,
            "pages_extracted": len(cleaned_pages),
            "total_chars": total_chars,
            "page_files": page_files,
            "layout_stats": layout_summary,
            "output_dir": str(volume_output_dir),
            "output_path": str(output_path),
            "cleaning_config": cleaning_config or {},
        }

        logger.info(
            "Processed {}: {} pages, {} chars", htid, result["pages_extracted"], total_chars
        )
        return result

    except Exception as exc:
        logger.error("Failed to process {}: {}", htid, exc)
        return {
            "htid": htid,
            "success": False,
            "error": str(exc),
        }


# ---------------------------------------------------------------
# CLI
# ---------------------------------------------------------------


def parse_args(args: list[str] | None = None) -> argparse.Namespace:
    """Parse CLI arguments.

    Args:
        args: Optional list of argument strings (for testing). Defaults to sys.argv.

    Returns:
        Parsed namespace.

    """
    parser = argparse.ArgumentParser(
        description="Extract and clean OCR text from HathiTrust volumes.",
    )
    parser.add_argument(
        "--htid",
        required=True,
        help="HathiTrust volume ID (e.g. uc1.b2889853).",
    )
    parser.add_argument(
        "--raw-dir",
        type=Path,
        default=Path("data/raw"),
        help="Directory containing downloaded ZIP files.",
    )
    parser.add_argument(
        "--processed-dir",
        type=Path,
        default=Path("data/processed"),
        help="Directory for processed output.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Optional path to write processing results as JSON.",
    )
    return parser.parse_args(args)


def main() -> int:
    """CLI entry point."""
    configure_logging()
    args = parse_args()

    logger.info(
        "Processing volume: htid={}, raw={}, processed={}",
        args.htid,
        args.raw_dir,
        args.processed_dir,
    )

    result = process_volume(
        htid=args.htid,
        raw_dir=args.raw_dir,
        processed_dir=args.processed_dir,
    )

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps(result, indent=2, sort_keys=False),
            encoding="utf-8",
        )
        logger.info("Results written to {}", args.output)

    if result.get("success"):
        print(json.dumps(result, indent=2))
        return 0

    logger.error("Processing failed: {}", result.get("error", "Unknown error"))
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
