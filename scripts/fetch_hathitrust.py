"""HathiTrust volume enumeration and catalog manifest generation.

Supports:
- Waypoint backup parsing (Wayback Machine page listings)
- HathiFile dump analysis
- HathiTrust Data API lookups (read-only, no auth required for public collections)
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import re
from collections.abc import Callable
from datetime import UTC, datetime, timezone
from pathlib import Path
from typing import Any

import requests

try:
    from _version import get_version
except ImportError:  # pragma: no cover

    def get_version() -> str:
        return "0.0.0"


get_settings: Callable[[], Any] | None = None
try:
    from config import get_settings as _get_settings
except ImportError:  # pragma: no cover
    pass
else:
    get_settings = _get_settings

logger = logging.getLogger(__name__)


def _default_collection_id() -> str:
    if get_settings is not None:
        return get_settings().COLLECTION_ID
    return "71329709"


# Default HathiTrust collection for NZ Parliamentary Debates
DEFAULT_COLLECTION_ID = _default_collection_id()

# Base URLs
HATHI_DATA_API = "https://share.hathitrust.org/api/volume"
HATHIFILE_BASE = "https://www.hathitrust.org/hathifiles"

# Volume page URL pattern for Wayback / Hathi listing pages
VOLUME_PAGE_PATTERN = re.compile(r"/volume/(\d+)\?page=(\d+)")

# HathiFile column indices (hathifile_2026*.txt.gz format)
# Standard hathifile columns: 0=htid, 1=access, 2=rights, 3=collection_code,
# 4=source, 5=title, 6=imprint, 7=isbn, 8=issn, 9=lccn, 10=oclc_num,
# 11=enumcron, 12=description, 13=govdoc, 14=rights_determination_reason
# Updated: actual positions depend on hathifile schema version


def parse_hathifile_line(
    line: str,
    collection_id: str = DEFAULT_COLLECTION_ID,
    category: str = "debates",
) -> dict[str, Any] | None:
    """Parse a single HathiFile tab-delimited line into a volume record.

    Args:
        line: A tab-delimited line from a hathifile.
        collection_id: Target collection ID to filter by.
        category: Default content category.

    Returns:
        A volume record dict or None if the line doesn't match the collection.

    """
    # Skip comments and empty lines
    line = line.strip()
    if not line or line.startswith("#"):
        return None

    parts = line.split("	")
    if len(parts) < 14:
        return None

    htid = parts[0]
    rights = _rights_code(parts[2])

    # HathiFile does not directly embed collection_id in the basic dump;
    # we rely on the caller to filter. We record it but don't filter here.
    record: dict[str, Any] = {
        "htid": htid,
        "category": category,
        "year": _extract_year(parts[6] if len(parts) > 6 else ""),
        "volume": parts[11] if len(parts) > 11 else "",
        "title": parts[5] if len(parts) > 5 else "",
        "oclc_num": parts[10] if len(parts) > 10 and parts[10] else "",
        "rights": rights,
        "source": parts[4] if len(parts) > 4 else "",
        "enumcron": parts[11] if len(parts) > 11 else "",
        "collection_id": collection_id,
        "isbn": parts[7] if len(parts) > 7 else "",
        "issn": parts[8] if len(parts) > 8 else "",
        "lccn": parts[9] if len(parts) > 9 else "",
    }
    return record


def _rights_code(code: str) -> str:
    """Map HathiFile rights code to standard rights string."""
    mapping = {
        "pd": "pd",
        "pdus": "pd",
        "ic": "ic-world",
        "icus": "ic-world",
        "und": "undetermined",
        "sup": "suppressed",
        "nobody": "suppressed",
    }
    return mapping.get(code.lower(), "undetermined")


def _extract_year(imprint: str) -> int | None:
    """Extract a 4-digit year from an imprint string."""
    if not imprint:
        return None
    match = re.search(r"\b(1[8-9]\d{2}|20[0-2]\d)\b", imprint)
    if match:
        return int(match.group(1))
    return None


def _extract_year_from_title(title: str) -> int | None:
    """Fallback: extract year from volume title string."""
    if not title:
        return None
    match = re.search(r"\b(1[8-9]\d{2}|20[0-2]\d)\b", title)
    if match:
        return int(match.group(1))
    return None


def lookup_volume_metadata(htid: str) -> dict[str, Any] | None:
    """Look up volume metadata from HathiTrust Data API (read-only endpoint).

    Args:
        htid: HathiTrust volume ID.

    Returns:
        JSON response dict or None if not found.

    """
    url = f"{HATHI_DATA_API}/{htid}/json"
    try:
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as exc:
        logger.warning("API lookup failed for %s: %s", htid, exc)
        return None


def compute_sha256(file_path: Path) -> str | None:
    """Compute SHA-256 digest of a file.

    Args:
        file_path: Path to the file.

    Returns:
        Hex digest string or None if file doesn't exist.

    """
    if not file_path.exists():
        return None
    hasher = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def build_manifest_from_hathifile(
    hathifile_path: Path,
    collection_id: str = DEFAULT_COLLECTION_ID,
    category: str = "debates",
) -> list[dict[str, Any]]:
    """Build a volume manifest from a local HathiFile dump.

    Args:
        hathifile_path: Path to a .txt or .txt.gz hathifile.
        collection_id: Filter to this collection.
        category: Default content category.

    Returns:
        List of volume record dicts.

    """
    import gzip

    volumes: list[dict[str, Any]] = []

    open_func = gzip.open if str(hathifile_path).endswith(".gz") else open
    mode = "rt" if str(hathifile_path).endswith(".gz") else "r"

    with open_func(hathifile_path, mode, encoding="utf-8", errors="replace") as fh:  # type: ignore[operator]
        for line in fh:  # type: ignore[assignment]
            if isinstance(line, str):
                record = parse_hathifile_line(line, collection_id, category)
            else:
                record = parse_hathifile_line(line.decode("utf-8"), collection_id, category)
            if record:
                # Fill missing year from title if needed
                if record["year"] is None:
                    record["year"] = _extract_year_from_title(record["title"])
                volumes.append(record)

    return volumes


def write_manifest(
    volumes: list[dict[str, Any]],
    output_path: Path,
) -> dict[str, Any]:
    """Write a versioned manifest JSON file.

    Args:
        volumes: List of volume record dicts.
        output_path: Destination path.

    Returns:
        The manifest dict that was written.

    """
    manifest = {
        "meta": {
            "generated_at": datetime.now(UTC).isoformat(),
            "source": f"HathiTrust Collection ID {DEFAULT_COLLECTION_ID}",
            "version": get_version(),
            "record_count": len(volumes),
            "schema": "manifests/schema.json",
        },
        "volumes": volumes,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=False),
        encoding="utf-8",
    )
    logger.info("Wrote %d volume records to %s", len(volumes), output_path)
    return manifest


def parse_args(args: list[str] | None = None) -> argparse.Namespace:
    """Parse CLI arguments.

    Args:
        args: Optional list of argument strings (for testing). Defaults to sys.argv.

    Returns:
        Parsed namespace.

    """
    parser = argparse.ArgumentParser(
        description="Fetch HathiTrust volume data and build a catalog manifest."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # hathifile subcommand
    hf = sub.add_parser(
        "hathifile",
        help="Parse a local HathiFile dump into the catalog manifest.",
    )
    hf.add_argument(
        "--hathifile",
        type=Path,
        required=True,
        help="Path to hathifile .txt or .txt.gz",
    )
    hf.add_argument(
        "--output",
        type=Path,
        default=Path("manifests/latest_manifest.json"),
        help="Output manifest path",
    )
    hf.add_argument(
        "--collection-id",
        default=DEFAULT_COLLECTION_ID,
        help="HathiTrust collection ID filter",
    )
    hf.add_argument(
        "--category",
        default="debates",
        help="Default content category for records",
    )

    # api-lookup subcommand
    api = sub.add_parser(
        "api-lookup",
        help="Lookup a single volume via HathiTrust Data API.",
    )
    api.add_argument("htid", help="HathiTrust volume ID (e.g. uc1.b2889853)")

    return parser.parse_args(args)


def main() -> int:
    """CLI entry point."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s | %(message)s",
    )
    args = parse_args()

    if args.command == "hathifile":
        logger.info(
            "Parsing hathifile: %s (collection=%s, category=%s)",
            args.hathifile,
            args.collection_id,
            args.category,
        )
        volumes = build_manifest_from_hathifile(
            hathifile_path=args.hathifile,
            collection_id=args.collection_id,
            category=args.category,
        )
        manifest = write_manifest(volumes, args.output)
        print(json.dumps(manifest["meta"], indent=2))
        return 0

    if args.command == "api-lookup":
        result = lookup_volume_metadata(args.htid)
        if result:
            print(json.dumps(result, indent=2, sort_keys=True))
        else:
            print(f"Volume not found: {args.htid}")
            return 1

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
