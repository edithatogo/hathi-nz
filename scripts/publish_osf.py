"""OSF publication client for prepared release archives.

The script is intentionally conservative:
- dry-run mode is the default
- file uploads target an existing OSF project
- all upload paths are derived from a local release directory
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from loguru import logger

from scripts.config import get_settings
from scripts.logging_utils import configure_logging

try:  # pragma: no cover - import availability is validated through runtime tests
    from osfclient import OSF as _OSF
except ImportError:  # pragma: no cover
    _OSF = None

OSF = _OSF

REQUIRED_METADATA_FIELDS = ("title", "description", "tags", "category")
DEFAULT_AUTH_ENV = "OSF_TOKEN"


def load_osf_metadata(metadata_path: Path) -> dict[str, Any]:
    """Load and validate the local OSF metadata file."""
    if not metadata_path.exists():
        msg = f"OSF metadata file not found: {metadata_path}"
        raise FileNotFoundError(msg)

    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    if not isinstance(metadata, dict):
        msg = "OSF metadata must be a JSON object"
        raise TypeError(msg)

    missing = [field for field in REQUIRED_METADATA_FIELDS if field not in metadata]
    if missing:
        msg = f"OSF metadata missing required field(s): {', '.join(missing)}"
        raise ValueError(msg)

    tags = metadata.get("tags")
    if not isinstance(tags, list) or not all(isinstance(tag, str) and tag.strip() for tag in tags):
        msg = "OSF metadata 'tags' must be a non-empty list of strings"
        raise ValueError(msg)

    return metadata


def collect_release_files(source_dir: Path, metadata_path: Path | None = None) -> list[Path]:
    """Return the local release files that should be mirrored to OSF."""
    if not source_dir.exists():
        msg = f"Release source directory not found: {source_dir}"
        raise FileNotFoundError(msg)

    files: list[Path] = []
    if source_dir.is_file():
        files.append(source_dir)
    else:
        files.extend(path for path in sorted(source_dir.rglob("*")) if path.is_file())

    if metadata_path is not None and metadata_path.exists():
        resolved_metadata = metadata_path.resolve()
        if resolved_metadata not in {path.resolve() for path in files}:
            files.append(metadata_path)

    return sorted({path.resolve(): path for path in files}.values())


def _relative_remote_path(path: Path, source_root: Path) -> Path:
    """Return the path relative to the release root or the filename fallback."""
    if path == source_root:
        return Path(path.name)
    try:
        return path.relative_to(source_root)
    except ValueError:
        return Path(path.name)


def _resolve_credentials(
    args: argparse.Namespace,
) -> tuple[str | None, str | None]:
    """Resolve the OSF token and project ID from args and environment settings."""
    settings = get_settings()

    token: str | None = None
    if args.token_env == DEFAULT_AUTH_ENV and settings.OSF_TOKEN:
        token = settings.OSF_TOKEN.get_secret_value()

    project_id = args.project_id or settings.OSF_PROJECT_ID
    return token, project_id


def _get_osf_client(token: str) -> Any:
    if OSF is None:
        msg = "osfclient is not installed"
        raise RuntimeError(msg)
    return OSF(token=token)


def publish_release(
    source_dir: Path,
    metadata_path: Path,
    project_id: str,
    token: str,
    remote_dir: str = "releases",
    storage_provider: str = "osfstorage",
) -> dict[str, Any]:
    """Upload a release directory and its OSF metadata file to an existing project."""
    client = _get_osf_client(token)
    project = client.project(project_id)
    storage = project.storage(storage_provider)

    uploaded_files: list[str] = []
    for file_path in collect_release_files(source_dir, metadata_path):
        relative = _relative_remote_path(file_path, source_dir)
        remote_path = Path(remote_dir) / relative if remote_dir else relative
        logger.info("Uploading {} to OSF at {}", file_path, remote_path)
        with file_path.open("rb") as fp:
            storage.create_file(remote_path.as_posix(), fp, update=True)
        uploaded_files.append(remote_path.as_posix())

    return {
        "project_id": project_id,
        "remote_dir": remote_dir,
        "storage_provider": storage_provider,
        "uploaded_files": uploaded_files,
        "uploaded_count": len(uploaded_files),
        "metadata_path": metadata_path.as_posix(),
        "source_dir": source_dir.as_posix(),
    }


def parse_args(args: list[str] | None = None) -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(description="Publish a prepared release bundle to OSF.")
    parser.add_argument(
        "--source-dir",
        type=Path,
        default=Path("dist"),
        help="Directory containing the packaged release files.",
    )
    parser.add_argument(
        "--metadata",
        type=Path,
        default=Path(".osf.json"),
        help="Path to the local OSF metadata file.",
    )
    parser.add_argument(
        "--project-id",
        default=None,
        help="Target OSF project ID. Defaults to OSF_PROJECT_ID from the environment.",
    )
    parser.add_argument(
        "--token-env",
        default=DEFAULT_AUTH_ENV,
        help="Environment variable name that holds the OSF token.",
    )
    parser.add_argument(
        "--remote-dir",
        default="releases",
        help="Remote directory prefix inside the OSF project.",
    )
    parser.add_argument(
        "--storage-provider",
        default="osfstorage",
        help="OSF storage provider name.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=True,
        help="Print the planned upload actions without contacting OSF.",
    )
    parser.add_argument(
        "--execute",
        action="store_false",
        dest="dry_run",
        help="Execute the upload instead of performing a dry run.",
    )
    return parser.parse_args(args)


def main() -> int:
    """CLI entry point."""
    configure_logging()
    args = parse_args()
    metadata = load_osf_metadata(args.metadata)
    release_files = collect_release_files(args.source_dir, args.metadata)
    token, project_id = _resolve_credentials(args)

    if args.dry_run:
        logger.info(
            "Dry run: source={}, metadata={}, project_id={}, remote_dir={}",
            args.source_dir,
            args.metadata,
            project_id or "<unset>",
            args.remote_dir,
        )
        print(
            json.dumps(
                {
                    "dry_run": True,
                    "source_dir": args.source_dir.as_posix(),
                    "metadata_path": args.metadata.as_posix(),
                    "project_id": project_id,
                    "remote_dir": args.remote_dir,
                    "storage_provider": args.storage_provider,
                    "metadata": metadata,
                    "planned_files": [path.as_posix() for path in release_files],
                },
                indent=2,
            )
        )
        return 0

    if not token:
        logger.error("Missing OSF token. Set {} or configure scripts.config.", args.token_env)
        return 2
    if not project_id:
        logger.error("Missing OSF project ID. Set OSF_PROJECT_ID or pass --project-id.")
        return 2

    result = publish_release(
        source_dir=args.source_dir,
        metadata_path=args.metadata,
        project_id=project_id,
        token=token,
        remote_dir=args.remote_dir,
        storage_provider=args.storage_provider,
    )
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
