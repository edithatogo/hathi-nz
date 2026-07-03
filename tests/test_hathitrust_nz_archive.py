"""Tests for HathiTrust-NZ multi-source archive planning."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.hathitrust_nz_archive import (
    HATHI_RESEARCH_PD_OPEN_ACCESS,
    HATHI_RESEARCH_PD_WITH_GOOGLE,
    HATHITRUST_NZ_EXPECTED_COUNT,
    assert_expected_count,
    build_collection_manifest,
    build_discovery_manifest,
    build_inventory,
    classify_publication_policy,
    clean_htrc_htid,
    htrc_stubbytree_path,
    load_collection_export_tsv,
    parse_volume_label,
    write_discovery_report,
    write_htrc_ef_plan,
    write_research_dataset_plan,
)

ROOT = Path(__file__).resolve().parents[1]


def test_htrc_cleaning_and_stubbytree_path() -> None:
    """HTRC EF paths should match the documented stubbytree convention."""
    assert clean_htrc_htid("uc2.ark:/13960/t17m0815m") == "uc2.ark+=13960=t17m0815m"
    assert htrc_stubbytree_path("nyp.33433070251792") == "nyp/33759/nyp.33433070251792.json.bz2"


def test_htrc_path_requires_namespace() -> None:
    """HTRC paths should reject identifiers without a namespace separator."""
    with pytest.raises(ValueError, match="namespace separator"):
        htrc_stubbytree_path("not-a-valid-htid")


@pytest.mark.parametrize(
    ("title", "expected_number", "expected_label"),
    [
        ("Parliamentary debates (Hansard) v.281", 281, "v.281"),
        ("Parliamentary debates (Hansard) 1879:2", None, "1879:2"),
        ("Parliamentary debates (Hansard) 1854-55", None, "1854-55"),
        ("Parliamentary debates (Hansard)", None, None),
    ],
)
def test_parse_volume_label(
    title: str,
    expected_number: int | None,
    expected_label: str | None,
) -> None:
    assert parse_volume_label(title) == (expected_number, expected_label)


def test_rights_17_cc_zero_is_public_full_text() -> None:
    policy = classify_publication_policy(
        "17",
        access_profile_code="open",
        source_dataset_name=HATHI_RESEARCH_PD_OPEN_ACCESS,
    )
    assert policy["rights_label"] == "cc-zero"
    assert policy["access_class"] == "public_full_text"
    assert policy["public_full_text_allowed"] is True
    assert policy["requires_static_host"] is True


@pytest.mark.parametrize("rights_code", ["9", "pdus", "2", "ic", "5", "und"])
def test_restricted_rights_fail_closed_for_public_full_text(rights_code: str) -> None:
    policy = classify_publication_policy(rights_code, access_profile_code="open")
    assert policy["public_metadata_allowed"] is True
    assert policy["public_full_text_allowed"] is False
    assert policy["restriction_reason"]


def test_google_research_dataset_fails_closed_even_for_public_rights() -> None:
    policy = classify_publication_policy(
        "17",
        access_profile_code="open",
        source_dataset_name=HATHI_RESEARCH_PD_WITH_GOOGLE,
    )
    assert policy["public_full_text_allowed"] is False
    assert policy["requires_google_agreement"] is True
    assert "source-dataset" in policy["restriction_reason"]


def test_google_digitization_profile_fails_closed_without_agreement() -> None:
    policy = classify_publication_policy(
        "17",
        access_profile_code="google",
        digitization_agent_code="google",
        source_dataset_name=HATHI_RESEARCH_PD_OPEN_ACCESS,
    )
    assert policy["public_full_text_allowed"] is False
    assert policy["requires_google_agreement"] is True


def test_real_hansard_export_has_510_rows_and_source_specific_summary() -> None:
    volumes = load_collection_export_tsv(ROOT / "data" / "hathi_collection_export_71329709.tsv")
    inventory = build_inventory(
        volumes, source_path=ROOT / "data" / "hathi_collection_export_71329709.tsv"
    )
    assert_expected_count(inventory, HATHITRUST_NZ_EXPECTED_COUNT)
    assert inventory["meta"]["record_count"] == 510
    assert inventory["summary"]["rights_counts"] == {"cc-zero": 510}
    assert inventory["summary"]["volume_number_parse"]["parsed"] == 369
    assert inventory["summary"]["volume_number_parse"]["needs_enrichment"] == 141
    assert inventory["summary"]["enumeration_parse"]["parsed"] == 510
    assert inventory["summary"]["label_parse"]["parsed"] == 510
    assert inventory["summary"]["label_parse"]["needs_enrichment"] == 0
    assert {volume["catalog_record_id"] for volume in inventory["volumes"]} == {"007119315"}


def test_expected_count_gate_rejects_broad_manifest_drift() -> None:
    inventory = build_inventory([], expected_count=HATHITRUST_NZ_EXPECTED_COUNT)
    with pytest.raises(ValueError, match="Expected 510"):
        assert_expected_count(inventory, HATHITRUST_NZ_EXPECTED_COUNT)


def test_plan_writers_emit_required_manifests(tmp_path: Path) -> None:
    volumes = load_collection_export_tsv(ROOT / "data" / "hathi_collection_export_71329709.tsv")
    inventory = build_inventory(volumes[:3], expected_count=3)

    htrc_manifest = write_htrc_ef_plan(inventory, tmp_path / "htrc", limit=2)
    research_manifest = write_research_dataset_plan(
        inventory,
        tmp_path / "research",
        source_dataset_name=HATHI_RESEARCH_PD_OPEN_ACCESS,
        limit=2,
    )
    collection_manifest = build_collection_manifest(inventory)
    discovery_manifest = build_discovery_manifest(inventory)

    assert htrc_manifest["meta"]["record_count"] == 2
    assert (tmp_path / "htrc" / "htrc_ef25_files.txt").exists()
    assert research_manifest["meta"]["eligible_full_text_count"] == 2
    assert (tmp_path / "research" / "research_dataset_eligible_htids.txt").exists()
    assert collection_manifest["meta"]["hf_collection"] == "edithatogo/hathitrust-nz"
    assert len(discovery_manifest["source_families"]) == 4
    assert any(
        family["family_id"] == "maori_and_aotearoa" for family in discovery_manifest["source_families"]
    )
    assert "HathiTrust OAI feed" in discovery_manifest["source_families"][0]["source_inputs"]

    persisted = json.loads((tmp_path / "research" / "research_dataset_manifest.json").read_text())
    assert persisted["static_host_contract"]["required_variables"] == [
        "HATHI_RSYNC_HOST",
        "HATHI_RSYNC_MODULE",
        "HATHI_RSYNC_USER",
        "HATHI_STATIC_HOST_STAGING_DIR",
    ]


def test_write_discovery_report(tmp_path: Path) -> None:
    volumes = load_collection_export_tsv(ROOT / "data" / "hathi_collection_export_71329709.tsv")
    inventory = build_inventory(volumes[:3], expected_count=3)
    discovery = build_discovery_manifest(inventory)
    out = tmp_path / "discovery" / "report.md"
    write_discovery_report(discovery, out)
    text = out.read_text(encoding="utf-8")
    assert "# HathiTrust-NZ Discovery Manifest" in text
    assert "Parliamentary and legal serials" in text
