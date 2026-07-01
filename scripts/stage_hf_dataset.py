"""Stage a local dataset for Hugging Face Hub upload.

Responsibility:
  - Read the latest manifest (manifests/latest_manifest.json)
  - Download/verify volume content from HathiTrust (ZIP, JSON metadata)
  - Organise structured dataset directory under data/processed/
  - Generate Parquet/JSONL sidecar files with volume metadata
  - Validate staged content against manifest (sha256, size_bytes)
  - Write staging state to data/_state/stage_state.json

This script is the bridge between raw HathiTrust data and HF-ready format.

Usage:
  python scripts/stage_hf_dataset.py --manifest manifests/latest_manifest.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import polars as pl
import requests
from loguru import logger

from scripts.logging_utils import configure_logging
from scripts.retry_utils import retry_on_transient_http_errors

HATHI_ZIP_URL = "https://babel.hathitrust.org/cgi/zip"
HATHI_META_URL = "https://share.hathitrust.org/api/volume"

try:
    from _version import get_version

    PIPELINE_VERSION = get_version()
except ImportError:  # pragma: no cover
    PIPELINE_VERSION = "0.0.0"

# ---------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------


def load_manifest(manifest_path: Path) -> list[dict[str, Any]]:
    """Load and validate the volume manifest.

    Args:
        manifest_path: Path to the manifest JSON file.

    Returns:
        List of volume record dicts.

    Raises:
        FileNotFoundError: If manifest_path doesn't exist.
        json.JSONDecodeError: If manifest is invalid JSON.

    """
    if not manifest_path.exists():
        msg = f"Manifest not found: {manifest_path}"
        raise FileNotFoundError(msg)

    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    volumes: list[dict[str, Any]] = data.get("volumes", [])
    if not isinstance(volumes, list):
        logger.warning("Manifest 'volumes' key is not a list; returning empty list")
        return []
    return volumes


@retry_on_transient_http_errors
def _download_volume(
    htid: str,
    target_dir: Path,
    skip_existing: bool = True,
) -> dict[str, Any]:
    """Download a HathiTrust volume (ZIP content) to target_dir.

    Uses HathiTrust babel ZIP download endpoint.

    Args:
        htid: HathiTrust volume ID (e.g. uc1.b2889853).
        target_dir: Directory to download into.
        skip_existing: If True and the ZIP file already exists, skip download.

    Returns:
        Dict with 'sha256' (hex str) and 'size_bytes' (int),
        or None if download failed.

    """
    target_dir.mkdir(parents=True, exist_ok=True)
    safe_name = htid.replace("/", "_").replace(".", "_")
    zip_path = target_dir / f"{safe_name}.zip"

    if skip_existing and zip_path.exists():
        actual_size = zip_path.stat().st_size
        actual_sha256 = _compute_sha256(zip_path)
        logger.info("Skipping existing {} (size={})", htid, actual_size)
        return {"sha256": actual_sha256, "size_bytes": actual_size}

    url = f"{HATHI_ZIP_URL}?id={htid}"
    logger.info("Downloading {} from {}", htid, url)
    resp = requests.get(url, timeout=300, stream=True)
    resp.raise_for_status()

    with zip_path.open("wb") as f:
        for chunk in resp.iter_content(chunk_size=65536):
            if chunk:
                f.write(chunk)

    actual_size = zip_path.stat().st_size
    actual_sha256 = _compute_sha256(zip_path)
    logger.info("Downloaded {} (size={}, sha256={})", htid, actual_size, actual_sha256)
    return {"sha256": actual_sha256, "size_bytes": actual_size}


def download_volume(
    htid: str,
    target_dir: Path,
    skip_existing: bool = True,
) -> dict[str, Any] | None:
    """Download a HathiTrust volume (ZIP content) to target_dir."""
    try:
        return _download_volume(htid, target_dir, skip_existing=skip_existing)
    except requests.RequestException as exc:
        logger.warning("Failed to download {}: {}", htid, exc)
        return None


def verify_content(
    file_path: Path,
    expected_sha256: str,
    expected_size_bytes: int,
) -> bool:
    """Verify file integrity by SHA-256 and size.

    Args:
        file_path: Path to downloaded file.
        expected_sha256: Expected SHA-256 hex digest.
        expected_size_bytes: Expected file size in bytes.

    Returns:
        True if both checks pass, False otherwise.

    """
    if not file_path.exists():
        logger.warning("File not found for verification: {}", file_path)
        return False

    actual_size = file_path.stat().st_size
    if actual_size != expected_size_bytes:
        logger.warning(
            "Size mismatch for {}: expected {}, got {}",
            file_path,
            expected_size_bytes,
            actual_size,
        )
        return False

    actual_sha256 = _compute_sha256(file_path)
    if actual_sha256 != expected_sha256:
        logger.warning(
            "SHA-256 mismatch for {}: expected {}, got {}",
            file_path,
            expected_sha256,
            actual_sha256,
        )
        return False

    return True


def build_metadata_dataframe(volumes: list[dict[str, Any]]) -> pl.DataFrame:
    """Build a Polars DataFrame of volume metadata for Parquet export.

    Args:
        volumes: List of volume record dicts.

    Returns:
        Polars DataFrame with typed columns matching manifests/schema.json.

    """
    if not volumes:
        schema: dict[str, Any] = {
            "htid": pl.String,
            "category": pl.String,
            "year": pl.Int64,
            "volume": pl.String,
            "title": pl.String,
            "oclc_num": pl.String,
            "rights": pl.String,
            "source": pl.String,
            "collection_id": pl.String,
            "sha256": pl.String,
            "size_bytes": pl.Int64,
            "pipeline_version": pl.String,
        }
        empty_cols = {col: pl.Series(col, [], dtype=dtype) for col, dtype in schema.items()}
        return pl.DataFrame(empty_cols)

    rows = [
        {
            "htid": v.get("htid", ""),
            "category": v.get("category", ""),
            "year": v.get("year"),
            "volume": v.get("volume", ""),
            "title": v.get("title", ""),
            "oclc_num": v.get("oclc_num", ""),
            "rights": v.get("rights", ""),
            "source": v.get("source", ""),
            "collection_id": v.get("collection_id", ""),
            "sha256": v.get("sha256"),
            "size_bytes": v.get("size_bytes"),
            "pipeline_version": v.get("pipeline_version", PIPELINE_VERSION),
        }
        for v in volumes
    ]
    return pl.DataFrame(rows)


def write_stage_state(state_dir: Path, state: dict[str, Any]) -> None:
    """Write staging state to state_dir/stage_state.json.

    Args:
        state_dir: Directory for state files.
        state: Dict with staging metadata.

    """
    state_dir.mkdir(parents=True, exist_ok=True)
    path = state_dir / "stage_state.json"
    path.write_text(json.dumps(state, indent=2, sort_keys=False), encoding="utf-8")
    logger.info("Wrote stage state to {}", path)


# ---------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------


def _compute_sha256(file_path: Path) -> str | None:
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


# ---------------------------------------------------------------
# CLI
# ---------------------------------------------------------------


def parse_args(args: list[str] | None = None) -> argparse.Namespace:
    """Parse CLI arguments.

    Args:
        args: Optional list of argument strings (for testing).
              Defaults to sys.argv.

    Returns:
        Parsed namespace.

    """
    parser = argparse.ArgumentParser(
        description="Stage local dataset for Hugging Face Hub upload.",
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path("manifests/latest_manifest.json"),
        help="Path to the volume manifest JSON file.",
    )
    parser.add_argument(
        "--download-dir",
        type=Path,
        default=Path("data/raw"),
        help="Directory for downloaded volume content.",
    )
    parser.add_argument(
        "--stage-dir",
        type=Path,
        default=Path("data/processed"),
        help="Directory for staged dataset output.",
    )
    parser.add_argument(
        "--state-dir",
        type=Path,
        default=Path("data/_state"),
        help="Directory for pipeline state tracking.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Limit to N volumes for testing (0 = no limit).",
    )
    return parser.parse_args(args)


def main() -> int:
    """CLI entry point."""
    configure_logging()
    args = parse_args()
    logger.info(
        "Staging dataset: manifest={}, download={}, stage={}",
        args.manifest,
        args.download_dir,
        args.stage_dir,
    )

    # 1. Load manifest
    volumes = load_manifest(args.manifest)
    logger.info("Loaded {} volumes from manifest", len(volumes))

    if args.limit > 0:
        volumes = volumes[: args.limit]
        logger.info("Limited to {} volumes for testing", len(volumes))

    # 2. Create download directory
    args.download_dir.mkdir(parents=True, exist_ok=True)

    # 3. Download and verify each volume
    staged_volumes: list[dict[str, Any]] = []
    failed_count = 0
    for vol in volumes:
        htid: str = vol.get("htid", "")
        if not htid:
            logger.warning("Skipping volume with empty htid")
            continue

        result = download_volume(htid, args.download_dir)
        if result is None:
            failed_count += 1
            logger.error("Failed to download {}", htid)
            continue

        # Verify against expected checksum (if present in manifest)
        vol_sha256: str | None = vol.get("sha256")
        vol_size: int | None = vol.get("size_bytes")
        safe_name = htid.replace("/", "_").replace(".", "_")
        zip_path = args.download_dir / f"{safe_name}.zip"

        if (
            vol_sha256 is not None
            and vol_size is not None
            and not verify_content(zip_path, vol_sha256, vol_size)
        ):
            failed_count += 1
            logger.error("Verification failed for {}", htid)
            continue

        enriched = dict(vol)
        enriched["sha256"] = result["sha256"]
        enriched["size_bytes"] = result["size_bytes"]
        enriched["pipeline_version"] = PIPELINE_VERSION
        staged_volumes.append(enriched)

    # 4. Build metadata DataFrame and write Parquet
    df = build_metadata_dataframe(staged_volumes)
    args.stage_dir.mkdir(parents=True, exist_ok=True)
    parquet_path = args.stage_dir / "metadata.parquet"
    df.write_parquet(str(parquet_path))
    logger.info("Wrote metadata parquet to {} ({} rows)", parquet_path, len(df))

    # 5. Write stage state
    state = {
        "generated_at": datetime.now(UTC).isoformat(),
        "manifest_path": str(args.manifest),
        "download_dir": str(args.download_dir),
        "stage_dir": str(args.stage_dir),
        "pipeline_version": PIPELINE_VERSION,
        "total_volumes": len(volumes),
        "staged_count": len(staged_volumes),
        "failed_count": failed_count,
        "staged_htids": [v["htid"] for v in staged_volumes],
    }
    write_stage_state(args.state_dir, state)

    if failed_count > 0:
        logger.warning(
            "Staging complete with {} failures out of {} volumes",
            failed_count,
            len(volumes),
        )
        return 1

    logger.info(
        "Staging complete: {} volumes staged successfully",
        len(staged_volumes),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
