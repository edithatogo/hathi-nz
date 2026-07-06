"""Tests for HathiTrust-NZ Conductor track metadata synchronization."""

from __future__ import annotations

import json
from pathlib import Path


def _repo_root(start: Path) -> Path:
    for candidate in (start, *start.parents):
        if (candidate / "pixi.toml").exists():
            return candidate
    return start.parents[1]


ROOT = _repo_root(Path(__file__).resolve())
TRACK_METADATA_PATHS = [
    ROOT / "conductor/tracks/hathitrust_nz_multi_source_archive_20260702/metadata.json",
    ROOT / "conductor/tracks/hathitrust_nz_interim_acquisition_hardening_20260703/metadata.json",
]


def test_hathitrust_track_metadata_declare_redundancy_label_taxonomy() -> None:
    expected_labels = [
        "project:rare-insights",
        "source:metadata",
        "source:derived-features",
        "source:interim-overlap",
        "blocked:external-access",
    ]

    for path in TRACK_METADATA_PATHS:
        metadata = json.loads(path.read_text(encoding="utf-8"))
        assert metadata["github_labels"] == expected_labels
        assert metadata["github_project_fields"] == {
            "status": ["Todo", "In Progress", "Done"],
            "redundancy_tier": [
                "metadata",
                "derived-features",
                "interim-overlap",
                "mixed",
                "blocked",
            ],
        }


def test_interim_track_plan_mentions_redundancy_label_sync() -> None:
    plan = (ROOT / "conductor/tracks/hathitrust_nz_interim_acquisition_hardening_20260703/plan.md").read_text(
        encoding="utf-8"
    )

    assert "redundancy-label taxonomy" in plan
