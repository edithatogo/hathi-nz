"""Upload an arbitrary local folder to a Hugging Face dataset repository."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from loguru import logger

from scripts.logging_utils import configure_logging
from scripts.upload_hf_dataset import ensure_repo_exists, get_hf_api


def upload_folder_to_hf(
    *,
    source_dir: Path,
    repo_id: str,
    path_in_repo: str = ".",
    commit_message: str = "Update HathiTrust-NZ archive artifacts",
    dry_run: bool = False,
) -> dict[str, Any]:
    """Upload ``source_dir`` to a Hugging Face dataset repository."""
    if not source_dir.exists() or not source_dir.is_dir():
        msg = f"Source directory does not exist: {source_dir}"
        raise FileNotFoundError(msg)

    files = sorted(path for path in source_dir.rglob("*") if path.is_file())
    payload = {
        "source_dir": source_dir.as_posix(),
        "repo_id": repo_id,
        "repo_type": "dataset",
        "path_in_repo": path_in_repo,
        "commit_message": commit_message,
        "file_count": len(files),
        "files": [path.relative_to(source_dir).as_posix() for path in files],
        "dry_run": dry_run,
    }
    if dry_run:
        return payload

    token = os.getenv("HF_TOKEN")
    api = get_hf_api(token=token)
    ensure_repo_exists(api, repo_id, token=token)
    result = api.upload_folder(
        repo_id=repo_id,
        repo_type="dataset",
        folder_path=str(source_dir),
        path_in_repo=path_in_repo,
        commit_message=commit_message,
    )
    payload["commit_url"] = str(result)
    return payload


def parse_args(args: list[str] | None = None) -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", type=Path, required=True)
    parser.add_argument("--repo-id", required=True)
    parser.add_argument("--path-in-repo", default=".")
    parser.add_argument("--commit-message", default="Update HathiTrust-NZ archive artifacts")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args(args)


def main() -> int:
    """CLI entry point."""
    configure_logging()
    args = parse_args()
    result = upload_folder_to_hf(
        source_dir=args.source_dir,
        repo_id=args.repo_id,
        path_in_repo=args.path_in_repo,
        commit_message=args.commit_message,
        dry_run=args.dry_run,
    )
    logger.info("HF folder upload result: {}", result)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
