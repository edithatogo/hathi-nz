"""Validate the committed HathiTrust-NZ publication and archive registry."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / "manifests" / "hathitrust-nz" / "archive_registry.json"
COLLECTION_MANIFEST_PATH = ROOT / "manifests" / "hathitrust-nz" / "collection_manifest.json"
EXPECTED_DATASET_IDS = {
    "corpus-nz-hathi",
    "hathitrust-nz-inventory",
    "hathitrust-nz-research-fulltext",
    "hathitrust-nz-htrc-extracted-features",
    "hathitrust-nz-htrc-analytics",
}


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def validate_registry(
    registry_path: Path = REGISTRY_PATH,
    collection_manifest_path: Path = COLLECTION_MANIFEST_PATH,
) -> dict[str, Any]:
    registry = _load(registry_path)
    collection_manifest = _load(collection_manifest_path)
    errors: list[str] = []
    datasets = registry.get("datasets")
    if not isinstance(datasets, list):
        errors.append("datasets must be a list")
        datasets = []
    actual_ids = {
        str(item.get("dataset_id"))
        for item in datasets
        if isinstance(item, dict) and item.get("dataset_id") is not None
    }
    if actual_ids != EXPECTED_DATASET_IDS:
        errors.append(f"dataset IDs differ: {sorted(actual_ids)}")
    if registry.get("collection", {}).get("curated_seed_record_count") != 510:
        errors.append("curated seed record count must remain 510")
    if registry.get("verification", {}).get("publication_health_score") != 1000:
        errors.append("publication health score must be 1000")
    for item in datasets:
        if not isinstance(item, dict):
            errors.append("dataset entry is not an object")
            continue
        dataset_id = item.get("dataset_id", "<unknown>")
        for field in (
            "dataset_id",
            "hf_repo",
            "hf_url",
            "zenodo_doi",
            "zenodo_url",
            "content_status",
        ):
            if not str(item.get(field) or "").strip():
                errors.append(f"{dataset_id} missing {field}")
        if not str(item.get("hf_url", "")).startswith("https://huggingface.co/datasets/"):
            errors.append(f"{dataset_id} has invalid Hugging Face URL")
        if not str(item.get("zenodo_doi", "")).startswith("10.5281/zenodo."):
            errors.append(f"{dataset_id} has invalid Zenodo DOI")
    manifest_count = collection_manifest.get("meta", {}).get("record_count")
    if manifest_count != 510:
        errors.append(f"collection manifest record count is {manifest_count}, expected 510")
    return {
        "registry_path": str(registry_path),
        "dataset_count": len(datasets),
        "manifest_record_count": manifest_count,
        "publication_health_score": registry.get("verification", {}).get(
            "publication_health_score"
        ),
        "valid": not errors,
        "errors": errors,
    }


def main(args: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry", type=Path, default=REGISTRY_PATH)
    parser.add_argument("--collection-manifest", type=Path, default=COLLECTION_MANIFEST_PATH)
    ns = parser.parse_args(args)
    result = validate_registry(ns.registry, ns.collection_manifest)
    print(json.dumps(result, indent=2))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
