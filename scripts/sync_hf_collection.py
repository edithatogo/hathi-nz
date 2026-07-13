"""Create/update the HathiTrust-NZ Hugging Face collection."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Literal, TypedDict

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from huggingface_hub import HfApi
from loguru import logger

from scripts.hathitrust_nz_archive import HUGGING_FACE_COLLECTION, child_datasets
from scripts.logging_utils import configure_logging

HF_COLLECTION_DESCRIPTION_LIMIT = 149
DEFAULT_COLLECTION_DESCRIPTION = (
    "HathiTrust-NZ archive: inventory, Research Dataset plans, HTRC EF, "
    "HTRC Analytics, and corpus-nz-hathi."
)


class CollectionDatasetItem(TypedDict):
    """Dataset item payload for a Hugging Face collection."""

    item_id: str
    item_type: Literal["dataset"]
    note: str


def _collection_slug(collection: Any) -> str:
    slug = getattr(collection, "slug", None)
    if isinstance(slug, str) and slug:
        return slug
    data = getattr(collection, "__dict__", {})
    if isinstance(data, dict) and isinstance(data.get("slug"), str):
        return data["slug"]
    msg = "Hugging Face collection response did not expose a slug"
    raise ValueError(msg)


def _dataset_items(manifest: dict[str, Any] | None = None) -> list[CollectionDatasetItem]:
    datasets = manifest.get("child_datasets", []) if manifest else child_datasets()
    items: list[CollectionDatasetItem] = []
    for dataset in datasets:
        repo_id = str(dataset.get("hf_repo_id", "")).strip()
        if not repo_id:
            continue
        items.append(
            {
                "item_id": repo_id,
                "item_type": "dataset",
                "note": str(dataset.get("role", dataset.get("dataset_id", ""))),
            }
        )
    return items


def sync_hf_collection(
    *,
    title: str,
    namespace: str,
    description: str,
    collection_slug: str | None = None,
    manifest: dict[str, Any] | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Create/update a Hugging Face collection and add dataset items."""
    description = description.strip()
    if len(description) > HF_COLLECTION_DESCRIPTION_LIMIT:
        description = description[:HF_COLLECTION_DESCRIPTION_LIMIT].rstrip()
    items = _dataset_items(manifest)
    payload: dict[str, Any] = {
        "title": title,
        "namespace": namespace,
        "collection_slug": collection_slug or HUGGING_FACE_COLLECTION,
        "description": description,
        "items": items,
        "dry_run": dry_run,
    }
    if dry_run:
        return payload

    token = os.getenv("HF_TOKEN")
    api = HfApi(token=token)
    if collection_slug:
        collection = api.get_collection(collection_slug, token=token)
        resolved_slug = _collection_slug(collection)
        api.update_collection_metadata(
            resolved_slug,
            title=title,
            description=description,
            private=False,
            token=token,
        )
    else:
        collection = api.create_collection(
            title,
            namespace=namespace,
            description=description,
            private=False,
            exists_ok=True,
            token=token,
        )
        resolved_slug = _collection_slug(collection)

    for item in items:
        api.add_collection_item(
            resolved_slug,
            item["item_id"],
            item["item_type"],
            note=item["note"],
            exists_ok=True,
            token=token,
        )
    payload["resolved_slug"] = resolved_slug
    payload["item_count"] = len(items)
    return payload


def parse_args(args: list[str] | None = None) -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--title", default="hathitrust-nz")
    parser.add_argument("--namespace", default="edithatogo")
    parser.add_argument("--collection-slug")
    parser.add_argument("--manifest", type=Path)
    parser.add_argument(
        "--description",
        default=DEFAULT_COLLECTION_DESCRIPTION,
    )
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args(args)


def main() -> int:
    """CLI entry point."""
    configure_logging()
    args = parse_args()
    manifest = None
    if args.manifest is not None:
        manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    result = sync_hf_collection(
        title=args.title,
        namespace=args.namespace,
        description=args.description,
        collection_slug=args.collection_slug,
        manifest=manifest,
        dry_run=args.dry_run,
    )
    logger.info("HF collection sync result: {}", result)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
