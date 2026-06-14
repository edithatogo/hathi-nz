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
import logging
import re
import zipfile
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


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
    output_dir.mkdir(parents=True, exist_ok=True)

    pages_extracted = 0
    total_chars = 0
    page_files: list[str] = []
    layout_stats: dict[str, list[dict[str, Any]]] = {"pages": []}

    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            text_members = sorted(
                [m for m in zf.namelist() if m.endswith(".txt")],
            )

            for member_name in text_members:
                try:
                    raw = zf.read(member_name).decode("utf-8", errors="replace")
                except Exception:
                    raw = zf.read(member_name).decode("latin-1", errors="replace")

                cleaned = clean_text(raw)
                if not cleaned.strip():
                    continue

                # Write cleaned page
                out_name = Path(member_name).name
                out_path = output_dir / out_name
                out_path.write_text(cleaned, encoding="utf-8")

                # Detect layout
                layout = detect_layout(cleaned)
                layout_stats["pages"].append(
                    {
                        "file": out_name,
                        "chars": len(cleaned),
                        "layout": layout,
                    }
                )

                pages_extracted += 1
                total_chars += len(cleaned)
                page_files.append(out_name)

    except zipfile.BadZipFile as exc:
        logger.error("Bad ZIP file %s: %s", zip_path, exc)
        return {
            "pages_extracted": 0,
            "total_chars": 0,
            "page_files": [],
            "layout_stats": {"pages": [], "error": str(exc)},
        }

    # Compute aggregate layout stats
    column_counts = [p["layout"]["column_estimate"] for p in layout_stats["pages"]]
    multi_col_pct = sum(1 for c in column_counts if c > 1) / max(len(column_counts), 1) * 100

    layout_summary: dict[str, Any] = {
        "pages_analyzed": len(layout_stats["pages"]),
        "multi_column_pct": round(multi_col_pct, 1),
        "avg_chars_per_page": round(total_chars / max(pages_extracted, 1)),
    }

    return {
        "pages_extracted": pages_extracted,
        "total_chars": total_chars,
        "page_files": page_files,
        "layout_stats": layout_summary,
    }


def process_volume(
    htid: str,
    raw_dir: Path,
    processed_dir: Path,
) -> dict[str, Any]:
    """Orchestrate full processing of a single HathiTrust volume.

    Args:
        htid: HathiTrust volume ID.
        raw_dir: Directory containing downloaded ZIP files.
        processed_dir: Base directory for processed output.

    Returns:
        Dict with processing results and stats.

    """
    safe_name = htid.replace("/", "_").replace(".", "_")
    zip_path = raw_dir / f"{safe_name}.zip"

    if not zip_path.exists():
        logger.warning("ZIP file not found for %s at %s", htid, zip_path)
        return {
            "htid": htid,
            "success": False,
            "error": f"ZIP file not found: {zip_path}",
        }

    volume_output_dir = processed_dir / safe_name

    try:
        result = extract_text_from_zip(zip_path, volume_output_dir)
        result["htid"] = htid
        result["success"] = True
        result["output_dir"] = str(volume_output_dir)

        logger.info(
            "Processed %s: %d pages, %d chars",
            htid,
            result["pages_extracted"],
            result["total_chars"],
        )
        return result

    except Exception as exc:
        logger.error("Failed to process %s: %s", htid, exc)
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
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s | %(message)s",
    )
    args = parse_args()

    logger.info(
        "Processing volume: htid=%s, raw=%s, processed=%s",
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
        logger.info("Results written to %s", args.output)

    if result.get("success"):
        print(json.dumps(result, indent=2))
        return 0

    logger.error("Processing failed: %s", result.get("error", "Unknown error"))
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
