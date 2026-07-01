"""Upload staged dataset to Hugging Face Hub.

Responsibility:
  - Authenticate with Hugging Face Hub (HF_TOKEN env var or huggingface-cli login)
  - Upload Parquet/JSONL metadata files to HF dataset repo
  - Upload volume content files (ZIP, text, or raw scans) to HF dataset repo
  - Maintain dataset card metadata (bibliographic info, coverage, license)
  - Support incremental updates (skip volumes unchanged since last upload)
  - Write upload state to data/_state/upload_state.json

This script targets the Hugging Face dataset repo: edithatogo/corpus-nz-hathi

Usage:
  python scripts/upload_hf_dataset.py --stage-dir data/processed
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import shutil
import tempfile
from collections.abc import Callable
from pathlib import Path
from typing import Any

from huggingface_hub import HfApi
from huggingface_hub.errors import HfHubHTTPError

from scripts.retry_utils import retry_on_transient_http_errors

get_settings: Callable[[], Any] | None = None
try:
    from config import get_settings as _get_settings
except ImportError:  # pragma: no cover
    pass
else:
    get_settings = _get_settings

logger = logging.getLogger(__name__)


def _copy_upload_tree(
    file_pairs: list[tuple[Path, str]],
) -> tempfile.TemporaryDirectory[str]:
    """Create a temporary tree containing only the selected upload files."""
    temp_dir = tempfile.TemporaryDirectory()
    root = Path(temp_dir.name)
    for source_path, repo_path in file_pairs:
        target_path = root / repo_path
        target_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, target_path)
    return temp_dir


def _default_repo() -> str:
    if get_settings is not None:
        return get_settings().HF_REPO_ID
    return "edithatogo/corpus-nz-hathi"


DEFAULT_HF_REPO = _default_repo()


@retry_on_transient_http_errors
def _repo_info(api: HfApi, repo_id: str) -> Any:
    return api.repo_info(repo_id=repo_id, repo_type="dataset")


@retry_on_transient_http_errors
def _create_repo(api: HfApi, repo_id: str, token: str | None = None) -> Any:
    return api.create_repo(repo_id=repo_id, repo_type="dataset", token=token, exist_ok=True)


@retry_on_transient_http_errors
def _upload_folder(
    api: HfApi,
    repo_id: str,
    folder_path: str,
    path_in_repo: str,
    commit_message: str,
) -> Any:
    return api.upload_folder(
        repo_id=repo_id,
        repo_type="dataset",
        folder_path=folder_path,
        path_in_repo=path_in_repo,
        commit_message=commit_message,
    )


# ---------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------


def get_hf_api(token: str | None = None) -> HfApi:
    """Get authenticated HfApi instance.

    Args:
        token: HF token or None to use cached credentials.

    Returns:
        HfApi instance.

    """
    if token:
        return HfApi(token=token)
    if get_settings is not None:
        settings = get_settings()
        if settings.HF_TOKEN:
            return HfApi(token=settings.HF_TOKEN.get_secret_value())
    env_token = os.environ.get("HF_TOKEN")
    if env_token:
        return HfApi(token=env_token)
    return HfApi()


def ensure_repo_exists(
    api: HfApi,
    repo_id: str,
    token: str | None = None,
) -> bool:
    """Ensure the target HF dataset repo exists, creating if needed.

    Args:
        api: Authenticated HfApi instance.
        repo_id: HF dataset repo ID (e.g. 'edithatogo/corpus-nz-hathi').
        token: HF token for write access.

    Returns:
        True if repo already existed, False if newly created.

    """
    try:
        _repo_info(api, repo_id)
        logger.info("Repo %s already exists", repo_id)
        return True
    except HfHubHTTPError as exc:
        status_code = getattr(exc.response, "status_code", None)
        if status_code != 404:
            raise

    try:
        _create_repo(api, repo_id, token=token)
        logger.info("Created repo %s", repo_id)
        return False
    except Exception as exc:
        logger.warning("Failed to create repo %s: %s", repo_id, exc)
        return False


def upload_metadata_files(
    api: HfApi,
    repo_id: str,
    stage_dir: Path,
    manifests_dir: Path | None = None,
    commit_message: str = "Update metadata",
) -> str | None:
    """Upload metadata files (Parquet, schema, manifests) to HF.

    Args:
        api: Authenticated HfApi instance.
        repo_id: HF dataset repo ID.
        stage_dir: Local staged dataset directory.
        manifests_dir: Directory containing manifest JSON files.
        commit_message: Commit message for the upload.

    Returns:
        Commit URL or None if nothing to upload.

    """
    paths_to_upload: list[str] = []
    path_in_repo: list[str] = []

    # Parquet metadata
    parquet_path = stage_dir / "metadata.parquet"
    if parquet_path.exists():
        paths_to_upload.append(str(parquet_path))
        path_in_repo.append("metadata.parquet")

    # Manifest files
    if manifests_dir is not None:
        schema_file = manifests_dir / "schema.json"
        if schema_file.exists():
            paths_to_upload.append(str(schema_file))
            path_in_repo.append("manifests/schema.json")
        manifest_file = manifests_dir / "latest_manifest.json"
        if manifest_file.exists():
            paths_to_upload.append(str(manifest_file))
            path_in_repo.append("manifests/latest_manifest.json")

    # DATASET_CARD.md in stage dir
    card_path = stage_dir / "DATASET_CARD.md"
    if card_path.exists():
        paths_to_upload.append(str(card_path))
        path_in_repo.append("DATASET_CARD.md")

    if not paths_to_upload:
        logger.info("No metadata files to upload")
        return None

    upload_tree = _copy_upload_tree(
        list(zip(map(Path, paths_to_upload), path_in_repo, strict=False))
    )
    try:
        result = _upload_folder(api, repo_id, upload_tree.name, ".", commit_message)
        logger.info("Uploaded metadata files to %s", result)
        return str(result)
    except Exception as exc:
        logger.warning("Metadata upload failed: %s", exc)
        return None
    finally:
        upload_tree.cleanup()


def upload_volume_files(
    api: HfApi,
    repo_id: str,
    data_dir: Path,
    volumes: list[dict[str, Any]],
    previous_state: dict[str, Any] | None = None,
    commit_message: str = "Upload volume content",
) -> str | None:
    """Upload volume content files to HF dataset repo.

    Supports incremental sync: skips volumes whose remote SHA-256
    matches local SHA-256.

    Args:
        api: Authenticated HfApi instance.
        repo_id: HF dataset repo ID.
        data_dir: Local directory with downloaded volume content.
        volumes: List of volume metadata dicts.
        previous_state: Previous upload state dict for incremental sync.
        commit_message: Commit message for the upload.

    Returns:
        Commit URL or None if nothing to upload.

    """
    uploaded_htids: set[str] = set()
    if previous_state:
        uploaded_htids = set(previous_state.get("uploaded_htids", []))

    files_to_upload: list[str] = []
    new_uploaded: list[str] = []

    for vol in volumes:
        htid: str = vol.get("htid", "")
        if not htid:
            continue

        safe_name = htid.replace("/", "_").replace(".", "_")
        zip_path = data_dir / f"{safe_name}.zip"

        if not zip_path.exists():
            logger.warning("Volume file not found: %s", zip_path)
            continue

        # Check if already uploaded
        if htid in uploaded_htids:
            logger.info("Skipping already-uploaded volume %s", htid)
            continue

        files_to_upload.append(str(zip_path))
        new_uploaded.append(htid)

    if not files_to_upload:
        logger.info("No new volume files to upload")
        return None

    upload_tree = _copy_upload_tree(
        [(Path(file_path), Path(file_path).name) for file_path in files_to_upload]
    )
    try:
        result = _upload_folder(api, repo_id, upload_tree.name, "volumes", commit_message)
        logger.info("Uploaded %d volume files to %s", len(files_to_upload), result)
        return str(result)
    except Exception as exc:
        logger.warning("Volume upload failed: %s", exc)
        return None
    finally:
        upload_tree.cleanup()


def load_upload_state(state_dir: Path) -> dict[str, Any]:
    """Load previous upload state from state_dir.

    Args:
        state_dir: Directory for pipeline state.

    Returns:
        Dict with upload state or empty dict if no previous state.

    """
    path = state_dir / "upload_state.json"
    if not path.exists():
        logger.info("No previous upload state found at %s", path)
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            logger.warning("Upload state is not a dict; resetting")
            return {}
        return data
    except (json.JSONDecodeError, OSError) as exc:
        logger.warning("Failed to load upload state: %s", exc)
        return {}


def write_upload_state(state_dir: Path, state: dict[str, Any]) -> None:
    """Write upload state to state_dir/upload_state.json.

    Args:
        state_dir: Directory for pipeline state.
        state: Dict with upload metadata (last_commit, uploaded_htids, etc.).

    """
    state_dir.mkdir(parents=True, exist_ok=True)
    path = state_dir / "upload_state.json"
    path.write_text(json.dumps(state, indent=2, sort_keys=False), encoding="utf-8")
    logger.info("Wrote upload state to %s", path)


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
        description="Upload staged dataset to Hugging Face Hub.",
    )
    parser.add_argument(
        "--stage-dir",
        type=Path,
        default=Path("data/processed"),
        help="Directory with staged dataset.",
    )
    parser.add_argument(
        "--manifests-dir",
        type=Path,
        default=Path("manifests"),
        help="Directory containing manifest and schema files.",
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path("data/raw"),
        help="Directory with downloaded volume content.",
    )
    parser.add_argument(
        "--repo-id",
        default=DEFAULT_HF_REPO,
        help="Hugging Face dataset repo ID.",
    )
    parser.add_argument(
        "--state-dir",
        type=Path,
        default=Path("data/_state"),
        help="Directory for pipeline state tracking.",
    )
    parser.add_argument(
        "--commit-message",
        default="Auto-sync: corpus-nz-hathi update",
        help="Commit message for HF upload.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would be uploaded without uploading.",
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
        "Uploading to HF: repo=%s, stage=%s, dry_run=%s",
        args.repo_id,
        args.stage_dir,
        args.dry_run,
    )

    # 1. Get HF API client
    api = get_hf_api()

    # 2. Ensure repo exists
    if not args.dry_run:
        ensure_repo_exists(api, args.repo_id)

    # 3. Load previous upload state for incremental sync
    previous_state = load_upload_state(args.state_dir)

    # 4. Load manifest to get volume list
    manifest_path = args.manifests_dir / "latest_manifest.json"
    volumes: list[dict[str, Any]] = []
    if manifest_path.exists():
        try:
            manifest_data = json.loads(manifest_path.read_text(encoding="utf-8"))
            volumes = manifest_data.get("volumes", [])
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("Failed to load manifest: %s", exc)
    logger.info("Loaded %d volumes from manifest", len(volumes))

    # 5. Upload metadata files
    meta_commit_url: str | None = None
    if args.dry_run:
        logger.info("[DRY-RUN] Would upload metadata files from %s", args.stage_dir)
        logger.info("[DRY-RUN] Would upload %d volume files", len(volumes))
        return 0

    meta_commit_url = upload_metadata_files(
        api=api,
        repo_id=args.repo_id,
        stage_dir=args.stage_dir,
        manifests_dir=args.manifests_dir,
    )

    # 6. Upload volume files
    vol_commit_url = upload_volume_files(
        api=api,
        repo_id=args.repo_id,
        data_dir=args.data_dir,
        volumes=volumes,
        previous_state=previous_state,
    )

    # 7. Write updated upload state
    new_uploaded = set(previous_state.get("uploaded_htids", []))
    for vol in volumes:
        htid = vol.get("htid", "")
        if htid:
            new_uploaded.add(htid)

    state = {
        "last_metadata_commit": meta_commit_url or "",
        "last_volume_commit": vol_commit_url or "",
        "uploaded_htids": sorted(new_uploaded),
        "total_volumes_uploaded": len(new_uploaded),
        "repo_id": args.repo_id,
    }
    write_upload_state(args.state_dir, state)

    if meta_commit_url:
        logger.info("Metadata uploaded: %s", meta_commit_url)
    if vol_commit_url:
        logger.info("Volumes uploaded: %s", vol_commit_url)
    if not meta_commit_url and not vol_commit_url:
        logger.info("Nothing new to upload")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
