"""Build local release archives for Zenodo or OSF mirroring.

The module is deliberately local-only: it validates metadata, records file
checksums, and creates an archive. It does not upload or publish anything.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import zipfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

DEFAULT_REQUIRED_FILES = (
    Path("manifests/schema.json"),
    Path("manifests/latest_manifest.json"),
    Path(".zenodo.json"),
    Path("DATASET_CARD.md"),
)
STATE_FILE_NAMES = {
    "stage_state.json",
    "upload_state.json",
    "validation_report.json",
}
ORCID_PATTERN = re.compile(r"^\d{4}-\d{4}-\d{4}-[\dX]{4}$")


def compute_checksum(archive_path: Path) -> str:
    """Return the SHA-256 checksum for a file."""
    hasher = hashlib.sha256()
    with archive_path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def validate_zenodo_json(path: Path) -> list[str]:
    """Validate the local Zenodo metadata file for required release fields."""
    required = {
        "title",
        "description",
        "creators",
        "access_right",
        "license",
        "upload_type",
        "version",
    }
    errors: list[str] = []
    if not path.exists():
        return [f"missing {path}"]

    try:
        metadata = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [f"invalid JSON in {path}: {exc}"]

    for field in sorted(required):
        if field not in metadata:
            errors.append(f"missing Zenodo field: {field}")

    creators = metadata.get("creators")
    if not isinstance(creators, list) or not creators:
        errors.append("Zenodo field 'creators' must be a non-empty list")
    else:
        for creator in creators:
            if not isinstance(creator, dict) or not creator.get("name"):
                errors.append("each Zenodo creator must include a name")
                continue
            orcid = creator.get("orcid")
            if orcid and (not isinstance(orcid, str) or not _is_valid_orcid(orcid)):
                errors.append(f"invalid Zenodo creator ORCID for {creator['name']!r}: {orcid!r}")

    return errors


def _is_valid_orcid(orcid: str) -> bool:
    if not ORCID_PATTERN.fullmatch(orcid):
        return False

    digits = orcid.replace("-", "")
    total = 0
    for char in digits[:-1]:
        total = (total + int(char)) * 2
    remainder = total % 11
    result = (12 - remainder) % 11
    check_digit = "X" if result == 10 else str(result)
    return digits[-1] == check_digit


def _iter_files(root: Path) -> list[Path]:
    if not root.exists():
        return []
    if root.is_file():
        return [root]
    return sorted(path for path in root.rglob("*") if path.is_file())


def collect_assets(
    stage_dir: Path,
    metadata_dir: Path,
    project_root: Path | None = None,
) -> dict[str, Any]:
    """Collect local files eligible for a release archive."""
    root = Path.cwd() if project_root is None else project_root
    files: list[Path] = []

    for required in DEFAULT_REQUIRED_FILES:
        required_path = root / required
        if required_path.exists():
            files.append(required_path)

    license_path = root / "LICENSE"
    if license_path.exists():
        files.append(license_path)

    for root in (stage_dir, metadata_dir):
        for path in _iter_files(root):
            if path.name in STATE_FILE_NAMES:
                continue
            if "data/raw" in path.as_posix().replace("\\", "/"):
                continue
            files.append(path)

    unique_files = sorted({path.resolve(): path for path in files}.values())
    return {
        "files": unique_files,
        "stage_dir": stage_dir,
        "metadata_dir": metadata_dir,
    }


def build_manifest(assets: dict[str, Any]) -> dict[str, Any]:
    """Build a checksummed manifest for release archive contents."""
    files = assets.get("files", [])
    entries = []
    for path in files:
        file_path = Path(path)
        entries.append(
            {
                "path": file_path.as_posix(),
                "size_bytes": file_path.stat().st_size,
                "sha256": compute_checksum(file_path),
            }
        )

    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "file_count": len(entries),
        "files": entries,
    }


def create_archive(assets: dict[str, Any], output_path: Path) -> Path:
    """Create a ZIP archive from collected release assets."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    files = [Path(path) for path in assets.get("files", [])]
    project_root = Path.cwd().resolve()
    with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in files:
            try:
                arcname = path.resolve().relative_to(project_root).as_posix()
            except ValueError:
                arcname = path.name
            archive.write(path, arcname)
    return output_path


def package(
    version: str,
    stage_dir: Path,
    metadata_dir: Path,
    output_dir: Path,
) -> dict[str, Any]:
    """Validate metadata, create a release archive, and return a manifest."""
    errors = validate_zenodo_json(Path(".zenodo.json"))
    if errors:
        msg = "; ".join(errors)
        raise ValueError(msg)

    assets = collect_assets(
        stage_dir=stage_dir,
        metadata_dir=metadata_dir,
        project_root=Path.cwd(),
    )
    archive_path = output_dir / f"corpus-nz-hathi-{version}.zip"
    create_archive(assets, archive_path)
    manifest = build_manifest(assets)
    manifest["archive"] = {
        "path": archive_path.as_posix(),
        "size_bytes": archive_path.stat().st_size,
        "sha256": compute_checksum(archive_path),
    }
    manifest_path = output_dir / f"corpus-nz-hathi-{version}-manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    manifest["manifest_path"] = manifest_path.as_posix()
    return manifest


def parse_args(args: list[str] | None = None) -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(description="Package a local corpus release.")
    parser.add_argument("--version", required=True, help="Release version, e.g. 0.1.0.")
    parser.add_argument("--stage-dir", type=Path, default=Path("data/processed"))
    parser.add_argument("--metadata-dir", type=Path, default=Path("data/metadata"))
    parser.add_argument("--output-dir", type=Path, default=Path("dist"))
    return parser.parse_args(args)


def main() -> int:
    """CLI entry point."""
    args = parse_args()
    manifest = package(
        version=args.version,
        stage_dir=args.stage_dir,
        metadata_dir=args.metadata_dir,
        output_dir=args.output_dir,
    )
    print(json.dumps(manifest, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
