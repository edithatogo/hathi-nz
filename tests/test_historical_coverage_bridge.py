"""Tests for the evidence-only historical coverage bridge."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.build_historical_coverage_bridge import build_bridge, main, validate_bridge

ROOT = Path(__file__).resolve().parents[1]


def test_bridge_preserves_curated_seed_and_no_claim() -> None:
    inventory = json.loads(
        (ROOT / "manifests/hathitrust-nz/nz_parliamentary_debates_hansard.json").read_text(
            encoding="utf-8"
        )
    )
    bridge = build_bridge(inventory, "2026-07-12T00:00:00+00:00")
    validate_bridge(bridge)
    assert bridge["bridge_status"] == "evidence-only"
    assert bridge["policy"]["no_completeness_claim"] is True
    assert bridge["source"]["record_count"] == 510
    assert len(bridge["records"]) == 510
    assert {record["evidence_class"] for record in bridge["records"]} == {"direct_inventory"}


def test_bridge_rejects_completeness_posture() -> None:
    inventory = {
        "meta": {
            "collection_id": "71329709",
            "collection_slug": "nz_parliamentary_debates_hansard",
        },
        "volumes": [{"htid": "uc1.test", "source_url": "https://hdl.handle.net/2027/uc1.test"}],
    }
    bridge = build_bridge(inventory, "2026-07-12T00:00:00+00:00")
    bridge["bridge_status"] = "complete"
    with pytest.raises(ValueError, match="validation failed"):
        validate_bridge(bridge)


def test_bridge_cli_builds_and_checks_manifest(tmp_path: Path) -> None:
    inventory_path = tmp_path / "inventory.json"
    output_path = tmp_path / "bridge.json"
    inventory_path.write_text(
        json.dumps(
            {
                "meta": {
                    "collection_id": "71329709",
                    "collection_slug": "nz_parliamentary_debates_hansard",
                },
                "volumes": [
                    {
                        "htid": "uc1.test",
                        "source_url": "https://hdl.handle.net/2027/uc1.test",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    assert main(["--input", str(inventory_path), "--output", str(output_path)]) == 0
    assert output_path.exists()
    assert main(["--input", str(output_path), "--check"]) == 0
