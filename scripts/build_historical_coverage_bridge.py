"""Build the evidence-only HathiTrust historical coverage bridge."""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schemas" / "historical_coverage_bridge.schema.json"
DEFAULT_INPUT = ROOT / "manifests" / "hathitrust-nz" / "nz_parliamentary_debates_hansard.json"
DEFAULT_OUTPUT = ROOT / "manifests" / "hathitrust-nz" / "historical_coverage_bridge.json"


def build_bridge(inventory: dict[str, object], generated_at: str) -> dict[str, object]:
    meta = inventory.get("meta", {})
    if not isinstance(meta, dict):
        raise ValueError("inventory meta must be an object")
    volumes = inventory.get("volumes", [])
    if not isinstance(volumes, list) or not volumes:
        raise ValueError("inventory volumes must be a non-empty list")
    records = []
    for volume in volumes:
        if not isinstance(volume, dict):
            raise ValueError("inventory volume must be an object")
        htid = str(volume.get("htid", ""))
        if not htid:
            raise ValueError("inventory volume is missing htid")
        records.append(
            {
                "htid": htid,
                "title": volume.get("title", ""),
                "enumeration": volume.get("enumeration", ""),
                "evidence_class": "direct_inventory",
                "archive_state": (
                    "public_full_text"
                    if volume.get("public_full_text_allowed") is True
                    and volume.get("requires_static_host") is False
                    else "metadata_only"
                ),
                "source_url": volume.get(
                    "source_url", f"https://hdl.handle.net/2027/{htid}"
                ),
                "rights_label": volume.get("rights_label", "und"),
                "fulltext_evidence": "not_claimed",
            }
        )
    return {
        "manifest_version": 1,
        "generated_at": generated_at,
        "repository": "hathi-nz",
        "bridge_status": "evidence-only",
        "policy": {
            "no_completeness_claim": True,
            "no_bulk_acquisition": True,
            "official_sources_first": True,
            "legislation_and_gazette_excluded": True,
        },
        "source": {
            "collection_id": str(meta.get("collection_id", "")),
            "collection_slug": str(meta.get("collection_slug", "")),
            "catalog_record_id": str(meta.get("catalog_record_id", "")),
            "record_count": len(records),
            "role": "historical Hansard discovery and archive evidence",
        },
        "downstream_consumer": {
            "repository": "corpus-nz-hansard",
            "contract": "schemas/historical_coverage_breadth_integration.schema.json",
            "boundary": "HathiTrust evidence narrows gaps but does not establish historical completeness.",
        },
        "records": records,
        "no_completeness_claims": [
            "This bridge is evidence-only, not a completeness claim.",
            "The 510-record collection is a curated seed, not all historical NZ Hansard.",
            "Full-text archive state remains metadata-only until source and redistribution evidence permit publication.",
        ],
    }


def validate_bridge(bridge: dict[str, object]) -> None:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    errors = sorted(
        Draft202012Validator(schema).iter_errors(cast("dict[str, Any]", bridge)),
        key=lambda error: list(error.path),
    )
    if errors:
        details = "; ".join(error.message for error in errors[:3])
        raise ValueError(f"historical coverage bridge validation failed: {details}")
    source = cast("dict[str, Any]", bridge.get("source", {}))
    records = cast("list[object]", bridge.get("records", []))
    if source.get("record_count") != len(records):
        raise ValueError("bridge record_count does not match records")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--check", action="store_true", help="Validate an existing bridge")
    args = parser.parse_args()
    bridge = json.loads(args.input.read_text(encoding="utf-8")) if args.check else build_bridge(
        json.loads(args.input.read_text(encoding="utf-8")),
        datetime.now(UTC).replace(microsecond=0).isoformat(),
    )
    validate_bridge(bridge)
    if not args.check:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(bridge, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"valid": True, "record_count": len(bridge["records"]), "output": str(args.output)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
