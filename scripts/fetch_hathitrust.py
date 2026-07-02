"""HathiTrust volume enumeration and catalog manifest generation.

Supports:
- Waypoint backup parsing (Wayback Machine page listings)
- HathiFile dump analysis
- HathiTrust Data API lookups (read-only, no auth required for public collections)
"""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import io
import json
import re
import sys
from collections.abc import Callable
from datetime import UTC, datetime, timezone
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import requests
from loguru import logger

from scripts.logging_utils import configure_logging
from scripts.retry_utils import retry_on_transient_http_errors

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


def _default_collection_id() -> str:
    if get_settings is not None:
        return get_settings().COLLECTION_ID
    return "71329709"


# Default HathiTrust collection for NZ Parliamentary Debates
DEFAULT_COLLECTION_ID = _default_collection_id()
DEFAULT_COLLECTION_CODE = "NJP"

# Base URLs
HATHI_DATA_API = "https://share.hathitrust.org/api/volume"
HATHI_COLLECTION_EXPORT_URL = "https://babel.hathitrust.org/shcgi/mb"
HATHIFILE_BASE = "https://www.hathitrust.org/hathifiles"
HATHIFILE_LIST_URL = "https://www.hathitrust.org/files/hathifiles/hathi_file_list.json"
HATHI_REQUEST_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/126.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json,text/plain,*/*",
    "Accept-Language": "en-US,en;q=0.9",
}

# Volume page URL pattern for Wayback / Hathi listing pages
VOLUME_PAGE_PATTERN = re.compile(r"/volume/(\d+)\?page=(\d+)")

HATHIFILE_FIELDS = (
    "htid",
    "access",
    "rights",
    "ht_bib_key",
    "description",
    "source",
    "source_bib_num",
    "oclc_num",
    "isbn",
    "issn",
    "lccn",
    "title",
    "imprint",
    "rights_reason_code",
    "rights_timestamp",
    "us_gov_doc_flag",
    "rights_date_used",
    "pub_place",
    "lang",
    "bib_fmt",
    "collection_code",
    "content_provider_code",
    "responsible_entity_code",
    "digitization_agent_code",
    "access_profile_code",
    "author",
)


def _field(parts: list[str], name: str, default: str = "") -> str:
    try:
        idx = HATHIFILE_FIELDS.index(name)
    except ValueError:
        return default
    if idx >= len(parts):
        return default
    return parts[idx]


def _normalize_volume(value: str) -> str:
    value = value.strip()
    if not value:
        return ""
    match = re.search(r"\b(v\.?\s*\d+[A-Za-z0-9().,-]*)\b", value, flags=re.IGNORECASE)
    if match:
        return re.sub(r"\s+", " ", match.group(1)).strip()
    return value


def parse_hathifile_line(
    line: str,
    collection_id: str = DEFAULT_COLLECTION_ID,
    collection_code: str = DEFAULT_COLLECTION_CODE,
    htid_allowlist: set[str] | None = None,
    category: str = "debates",
) -> dict[str, Any] | None:
    """Parse a single HathiFile tab-delimited line into a volume record.

    Args:
        line: A tab-delimited line from a hathifile.
        collection_id: Target collection ID to filter by.
        collection_code: HathiFile collection code to filter by.
        htid_allowlist: Optional set of HTIDs to keep.
        category: Default content category.

    Returns:
        A volume record dict or None if the line doesn't match the collection.

    """
    # Skip comments and empty lines
    line = line.strip()
    if not line or line.startswith("#"):
        return None

    parts = line.split("	")
    if len(parts) < 16:
        return None
    if parts[0] == "htid":
        return None
    if len(parts) >= len(HATHIFILE_FIELDS):
        collection_matches = _field(parts, "collection_code") == collection_code
    elif len(parts) >= 4:
        collection_matches = parts[3] == collection_code
    else:
        collection_matches = False
    if not collection_matches:
        return None

    htid = parts[0]
    if htid_allowlist is not None and htid not in htid_allowlist:
        return None
    rights = _rights_code(parts[2])
    title = _field(parts, "title")
    description = _field(parts, "description")
    imprint = _field(parts, "imprint")

    record: dict[str, Any] = {
        "htid": htid,
        "category": category,
        "year": _extract_year(imprint) or _extract_year_from_title(title) or _extract_year_from_title(description),
        "volume": _normalize_volume(title) or _normalize_volume(description) or _normalize_volume(imprint) or title,
        "title": title or description,
        "oclc_num": _field(parts, "oclc_num"),
        "rights": rights,
        "source": _field(parts, "source"),
        "collection_id": collection_id,
        "isbn": _field(parts, "isbn"),
        "issn": _field(parts, "issn"),
        "lccn": _field(parts, "lccn"),
    }
    if not record["volume"]:
        record["volume"] = record["title"]
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


def _latest_full_hathifile_url() -> str:
    response = requests.get(HATHIFILE_LIST_URL, timeout=30, headers=HATHI_REQUEST_HEADERS)
    response.raise_for_status()
    files = response.json()
    if not isinstance(files, list):
        msg = "Unexpected Hathifile list payload"
        raise ValueError(msg)

    candidates = [
        entry
        for entry in files
        if isinstance(entry, dict)
        and entry.get("full") is True
        and isinstance(entry.get("url"), str)
    ]
    if not candidates:
        msg = "No full Hathifile entry found"
        raise ValueError(msg)

    latest = max(candidates, key=lambda entry: str(entry.get("filename") or entry.get("url")))
    return str(latest["url"])


def _download_hathifile(url: str, output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    logger.info("Downloading hathifile {} -> {}", url, output_path)
    resp = requests.get(url, timeout=300, stream=True, headers=HATHI_REQUEST_HEADERS)
    resp.raise_for_status()
    with output_path.open("wb") as fh:
        for chunk in resp.iter_content(chunk_size=1024 * 1024):
            if chunk:
                fh.write(chunk)
    return output_path


def _load_htid_allowlist(path: Path) -> set[str]:
    allowlist: set[str] = set()
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if line and not line.startswith("#"):
            allowlist.add(line)
    return allowlist


def _download_collection_export_rows(collection_id: str) -> list[dict[str, str]]:
    """Download rows for a HathiTrust collection from the collection builder export."""
    logger.info("Downloading collection metadata for {}", collection_id)
    referer = f"https://babel.hathitrust.org/cgi/mb?a=listis&c={collection_id}"
    resp = requests.post(
        HATHI_COLLECTION_EXPORT_URL,
        data={"a": "download", "c": collection_id, "format": "text"},
        timeout=300,
        headers={
            **HATHI_REQUEST_HEADERS,
            "Origin": "https://babel.hathitrust.org",
            "Referer": referer,
        },
    )
    resp.raise_for_status()

    rows = csv.DictReader(io.StringIO(resp.text), delimiter="\t")
    export_rows: list[dict[str, str]] = []
    for row in rows:
        normalized = {key: (value or "").strip() for key, value in row.items()}
        htid = normalized.get("htitem_id") or normalized.get("htid") or normalized.get("id") or ""
        if htid:
            export_rows.append(normalized)
    if not export_rows:
        raise ValueError(f"No HTIDs returned for collection {collection_id}")
    return export_rows


def _iter_remote_hathifile_lines(url: str):
    with requests.get(url, timeout=300, stream=True, headers=HATHI_REQUEST_HEADERS) as resp:
        resp.raise_for_status()
        resp.raw.decode_content = False
        with gzip.GzipFile(fileobj=resp.raw) as gz, io.TextIOWrapper(
            gz,
            encoding="utf-8",
            errors="replace",
        ) as fh:
            yield from fh


def build_manifest_from_hathifile_url(
    url: str,
    collection_id: str = DEFAULT_COLLECTION_ID,
    collection_code: str = DEFAULT_COLLECTION_CODE,
    htid_allowlist: set[str] | None = None,
    enrich_api: bool = False,
    category: str = "debates",
) -> list[dict[str, Any]]:
    """Build a volume manifest directly from a remote HathiFile URL."""
    volumes: list[dict[str, Any]] = []
    for line in _iter_remote_hathifile_lines(url):
        record = parse_hathifile_line(
            line,
            collection_id,
            collection_code,
            htid_allowlist,
            category,
        )
        if record:
            if record["year"] is None:
                record["year"] = _extract_year_from_title(record["title"])
            if enrich_api:
                record = enrich_volume_metadata(record)
            volumes.append(record)
    return volumes


@retry_on_transient_http_errors
def _lookup_volume_metadata(htid: str) -> dict[str, Any]:
    url = f"{HATHI_DATA_API}/{htid}/json"
    resp = requests.get(url, timeout=30, headers=HATHI_REQUEST_HEADERS)
    resp.raise_for_status()
    return resp.json()


def lookup_volume_metadata(htid: str) -> dict[str, Any] | None:
    """Look up volume metadata from HathiTrust Data API (read-only endpoint).

    Args:
        htid: HathiTrust volume ID.

    Returns:
        JSON response dict or None if not found.

    """
    try:
        return _lookup_volume_metadata(htid)
    except requests.RequestException as exc:
        logger.warning("API lookup failed for {}: {}", htid, exc)
        return None


def _merge_api_metadata(record: dict[str, Any], api_data: dict[str, Any]) -> dict[str, Any]:
    merged = dict(record)
    for key in ("title", "source", "collection_id", "isbn", "issn", "lccn", "oclc_num"):
        value = api_data.get(key)
        if isinstance(value, str) and value.strip():
            merged[key] = value
    year = api_data.get("year")
    if merged.get("year") is None and isinstance(year, int):
        merged["year"] = year
    rights = api_data.get("rights")
    if isinstance(rights, str) and rights.strip():
        merged["rights"] = _rights_code(rights)
    volume = api_data.get("volume")
    if isinstance(volume, str) and volume.strip():
        merged["volume"] = volume
    return merged


def enrich_volume_metadata(record: dict[str, Any]) -> dict[str, Any]:
    """Use the HathiTrust volume API to enrich a parsed record."""
    htid = str(record.get("htid") or "")
    if not htid:
        return record
    api_data = lookup_volume_metadata(htid)
    if not api_data:
        return record
    return _merge_api_metadata(record, api_data)


def _base_collection_record(htid: str, collection_id: str, category: str) -> dict[str, Any]:
    return {
        "htid": htid,
        "category": category,
        "year": None,
        "volume": htid,
        "title": htid,
        "oclc_num": "",
        "rights": "undetermined",
        "source": "HathiTrust Collection Builder",
        "collection_id": collection_id,
        "isbn": "",
        "issn": "",
        "lccn": "",
    }


def build_manifest_from_collection_export(
    collection_id: str = DEFAULT_COLLECTION_ID,
    htid_allowlist: set[str] | None = None,
    enrich_api: bool = False,
    category: str = "debates",
) -> list[dict[str, Any]]:
    """Build a volume manifest from a HathiTrust collection export TSV."""
    rows = _download_collection_export_rows(collection_id)
    allowlist = htid_allowlist if htid_allowlist is not None else None
    volumes: list[dict[str, Any]] = []
    for row in rows:
        htid = row.get("htitem_id") or row.get("htid") or row.get("id") or ""
        if allowlist is not None and htid not in allowlist:
            continue
        title = row.get("title") or htid
        record = {
            "htid": htid,
            "category": category,
            "year": _extract_year(row.get("date", "")) or _extract_year_from_title(title),
            "volume": _normalize_volume(title) or title,
            "title": title,
            "oclc_num": row.get("OCLC", ""),
            "rights": _rights_code(row.get("rights", "")),
            "source": "HathiTrust Collection Builder",
            "collection_id": collection_id,
            "isbn": row.get("ISBN", ""),
            "issn": "",
            "lccn": row.get("LCCN", ""),
        }
        if enrich_api:
            record = enrich_volume_metadata(record)
        volumes.append(record)
    return volumes


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
    collection_code: str = DEFAULT_COLLECTION_CODE,
    htid_allowlist: set[str] | None = None,
    enrich_api: bool = False,
    category: str = "debates",
) -> list[dict[str, Any]]:
    """Build a volume manifest from a local HathiFile dump.

    Args:
        hathifile_path: Path to a .txt or .txt.gz hathifile.
        collection_id: Filter to this collection.
        collection_code: HathiFile collection code filter.
        htid_allowlist: Optional set of HTIDs to keep.
        enrich_api: Enrich matching rows using the HathiTrust Data API.
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
                record = parse_hathifile_line(
                    line,
                    collection_id,
                    collection_code,
                    htid_allowlist,
                    category,
                )
            else:
                record = parse_hathifile_line(
                    line.decode("utf-8"),
                    collection_id,
                    collection_code,
                    htid_allowlist,
                    category,
                )
            if record:
                # Fill missing year from title if needed
                if record["year"] is None:
                    record["year"] = _extract_year_from_title(record["title"])
                if enrich_api:
                    record = enrich_volume_metadata(record)
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
    logger.info("Wrote {} volume records to {}", len(volumes), output_path)
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
        "--collection-code",
        default=DEFAULT_COLLECTION_CODE,
        help="HathiFile collection code filter",
    )
    hf.add_argument(
        "--htid-allowlist",
        type=Path,
        default=None,
        help="Optional text file with one HTID per line to keep.",
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

    remote = sub.add_parser(
        "remote-hathifile",
        help="Download the latest Hathifile and build the manifest from it.",
    )
    remote.add_argument(
        "--url",
        default="",
        help="Specific Hathifile URL to use. Defaults to the latest full file.",
    )
    remote.add_argument(
        "--download-to",
        type=Path,
        default=Path("data/raw/hathifiles/latest_hathifile.txt.gz"),
        help="Optional local cache path for the downloaded Hathifile.",
    )
    remote.add_argument(
        "--output",
        type=Path,
        default=Path("manifests/latest_manifest.json"),
        help="Output manifest path",
    )
    remote.add_argument(
        "--collection-id",
        default=DEFAULT_COLLECTION_ID,
        help="HathiTrust collection ID filter",
    )
    remote.add_argument(
        "--collection-code",
        default=DEFAULT_COLLECTION_CODE,
        help="HathiFile collection code filter",
    )
    remote.add_argument(
        "--htid-allowlist",
        type=Path,
        default=None,
        help="Optional text file with one HTID per line to keep.",
    )
    remote.add_argument(
        "--category",
        default="debates",
        help="Default content category for records",
    )
    remote.add_argument(
        "--enrich-api",
        action="store_true",
        help="Enrich manifest rows via the HathiTrust volume API.",
    )

    collection = sub.add_parser(
        "collection-export",
        help="Download a HathiTrust collection export TSV and build the manifest from it.",
    )
    collection.add_argument(
        "--collection-id",
        default=DEFAULT_COLLECTION_ID,
        help="HathiTrust collection ID to export",
    )
    collection.add_argument(
        "--output",
        type=Path,
        default=Path("manifests/latest_manifest.json"),
        help="Output manifest path",
    )
    collection.add_argument(
        "--htid-allowlist",
        type=Path,
        default=None,
        help="Optional text file with one HTID per line to keep.",
    )
    collection.add_argument(
        "--category",
        default="debates",
        help="Default content category for records",
    )
    collection.add_argument(
        "--enrich-api",
        action="store_true",
        default=False,
        help="Enrich manifest rows via the HathiTrust volume API.",
    )

    return parser.parse_args(args)


def main() -> int:
    """CLI entry point."""
    configure_logging()
    args = parse_args()

    if args.command == "hathifile":
        logger.info(
            "Parsing hathifile: {} (collection={}, collection_code={}, category={})",
            args.hathifile,
            args.collection_id,
            args.collection_code,
            args.category,
        )
        allowlist = _load_htid_allowlist(args.htid_allowlist) if args.htid_allowlist else None
        volumes = build_manifest_from_hathifile(
            hathifile_path=args.hathifile,
            collection_id=args.collection_id,
            collection_code=args.collection_code,
            htid_allowlist=allowlist,
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

    if args.command == "remote-hathifile":
        url = args.url or _latest_full_hathifile_url()
        logger.info(
            "Parsing remote hathifile: {} (collection={}, collection_code={}, category={})",
            url,
            args.collection_id,
            args.collection_code,
            args.category,
        )
        allowlist = _load_htid_allowlist(args.htid_allowlist) if args.htid_allowlist else None
        if args.download_to:
            _download_hathifile(url, args.download_to)
            volumes = build_manifest_from_hathifile(
                args.download_to,
                collection_id=args.collection_id,
                collection_code=args.collection_code,
                htid_allowlist=allowlist,
                enrich_api=args.enrich_api,
                category=args.category,
            )
        else:
            volumes = build_manifest_from_hathifile_url(
                url,
                collection_id=args.collection_id,
                collection_code=args.collection_code,
                htid_allowlist=allowlist,
                enrich_api=args.enrich_api,
                category=args.category,
            )
        manifest = write_manifest(volumes, args.output)
        print(json.dumps(manifest["meta"], indent=2))
        return 0

    if args.command == "collection-export":
        logger.info(
            "Parsing collection export: {} (category={})",
            args.collection_id,
            args.category,
        )
        allowlist = _load_htid_allowlist(args.htid_allowlist) if args.htid_allowlist else None
        volumes = build_manifest_from_collection_export(
            collection_id=args.collection_id,
            htid_allowlist=allowlist,
            enrich_api=args.enrich_api,
            category=args.category,
        )
        manifest = write_manifest(volumes, args.output)
        print(json.dumps(manifest["meta"], indent=2))
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
