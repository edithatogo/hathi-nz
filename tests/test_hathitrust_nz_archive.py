"""Tests for HathiTrust-NZ multi-source archive planning."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from scripts.hathitrust_nz_archive import (
    HATHI_RESEARCH_PD_OPEN_ACCESS,
    HATHI_RESEARCH_PD_WITH_GOOGLE,
    HATHITRUST_NZ_EXPECTED_COUNT,
    SOURCE_POLICY_REGISTRY_PATH,
    assert_expected_count,
    base_title_for_internet_archive,
    build_canonical_routing_manifest,
    build_collection_manifest,
    build_discovery_manifest,
    build_inventory,
    classify_publication_policy,
    clean_htrc_htid,
    htrc_stubbytree_path,
    load_collection_export_tsv,
    parse_volume_label,
    redundancy_source_summary,
    source_policy_entry,
    source_policy_summary,
    write_blocker_report,
    write_completeness_report,
    write_discovery_report,
    write_htrc_analytics_plan,
    write_htrc_ef_plan,
    write_htrc_solr_discovery_plan,
    write_ia_open_library_crosswalk_plan,
    write_internet_archive_overlap_plan,
    write_metadata_refresh_plan,
    write_nz_enrichment_plan,
    write_publication_evidence_report,
    write_research_dataset_plan,
    write_status_report,
)

ROOT = Path(__file__).resolve().parents[1]


def test_htrc_cleaning_and_stubbytree_path() -> None:
    """HTRC EF paths should match the documented stubbytree convention."""
    assert clean_htrc_htid("uc2.ark:/13960/t17m0815m") == "uc2.ark+=13960=t17m0815m"
    assert htrc_stubbytree_path("nyp.33433070251792") == "nyp/33759/nyp.33433070251792.json.bz2"


def test_canonical_routing_manifest_fails_closed_without_source_evidence() -> None:
    inventory = {
        "volumes": [
            {
                "htid": "uc1.test",
                "title": "Test",
                "rights_code": "17",
                "access_profile_code": "open",
            }
        ]
    }
    manifest = build_canonical_routing_manifest(inventory)
    assert manifest["record_count"] == 1
    assert manifest["routes"][0]["route"] == "metadata_only_until_source_evidence"
    assert manifest["routes"][0]["publication_eligible"] is False


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
    analytics_manifest = write_htrc_analytics_plan(inventory, tmp_path / "analytics", limit=2)
    solr_manifest = write_htrc_solr_discovery_plan(inventory, tmp_path / "solr", limit=2)
    crosswalk_manifest = write_ia_open_library_crosswalk_plan(
        inventory, tmp_path / "crosswalk", limit=2
    )
    nz_enrichment = write_nz_enrichment_plan(inventory, tmp_path / "nz", limit=2)
    research_manifest = write_research_dataset_plan(
        inventory,
        tmp_path / "research",
        source_dataset_name=HATHI_RESEARCH_PD_OPEN_ACCESS,
        limit=2,
    )
    collection_manifest = build_collection_manifest(inventory)
    discovery_manifest = build_discovery_manifest(inventory)

    assert htrc_manifest["meta"]["record_count"] == 2
    assert htrc_manifest["meta"]["route"] == "github_actions_rsync"
    assert (tmp_path / "htrc" / "htrc_ef25_files.txt").exists()
    assert analytics_manifest["meta"]["record_count"] == 2
    assert analytics_manifest["meta"]["route"] == "github_actions_metadata_and_reproducibility_only"
    assert (tmp_path / "analytics" / "htrc_workset_candidates.json").exists()
    assert solr_manifest["meta"]["record_count"] == 2
    assert solr_manifest["meta"]["source_dataset_version"] == "2.0"
    assert (tmp_path / "solr" / "htrc_solr_workset_candidates.json").exists()
    assert crosswalk_manifest["meta"]["record_count"] == 2
    assert (tmp_path / "crosswalk" / "ia_open_library_crosswalk_manifest.json").exists()
    assert nz_enrichment["meta"]["record_count"] == 2
    assert (tmp_path / "nz" / "nz_enrichment_manifest.json").exists()
    assert research_manifest["meta"]["eligible_full_text_count"] == 2
    assert (tmp_path / "research" / "research_dataset_eligible_htids.txt").exists()
    assert collection_manifest["meta"]["hf_collection"] == "edithatogo/hathitrust-nz"
    assert any(
        source["source_id"] == "internet_archive_public_domain_overlap"
        for source in collection_manifest["sources"]
    )
    assert (
        collection_manifest["source_policy_registry"][0]["source_id"]
        == "official_parliamentary_sources"
    )
    assert any(
        entry["source_id"] == "internet_archive"
        and entry["access_class"] == "public_domain_overlap_only"
        for entry in collection_manifest["source_policy_registry"]
    )
    assert len(discovery_manifest["source_families"]) == 4
    assert discovery_manifest["meta"]["htrc_versions"] == [
        {
            "source_id": "htrc_solr_ef20",
            "version": "2.0",
            "source_url": "https://solr2.htrc.illinois.edu/solr-ef20/",
        },
        {
            "source_id": "htrc_extracted_features",
            "version": "2.5",
            "source_url": "https://htrc.atlassian.net/wiki/spaces/COM/pages/43295914/Extracted+Features+v.2.0",
        },
    ]
    assert any(
        family["family_id"] == "maori_and_aotearoa"
        for family in discovery_manifest["source_families"]
    )
    assert "HathiTrust OAI feed" in discovery_manifest["source_families"][0]["source_inputs"]

    persisted = json.loads((tmp_path / "research" / "research_dataset_manifest.json").read_text())
    assert persisted["static_host_contract"]["required_variables"] == [
        "HATHI_RSYNC_HOST",
        "HATHI_RSYNC_MODULE",
        "HATHI_RSYNC_USER",
        "HATHI_STATIC_HOST_STAGING_DIR",
    ]


def test_source_policy_registry_is_stable_and_priority_sorted() -> None:
    summary = source_policy_summary()
    assert SOURCE_POLICY_REGISTRY_PATH.exists()
    assert len(summary) == len(json.loads(SOURCE_POLICY_REGISTRY_PATH.read_text(encoding="utf-8")))
    assert summary[0]["source_id"] == "official_parliamentary_sources"
    assert summary[-1]["source_id"] == "manual_evidence"
    assert (
        source_policy_entry("internet_archive")["publication_eligibility"]["hugging_face"]
        == "public_domain_overlap_only"
    )
    assert (
        source_policy_entry("hathitrust_research_dataset")["default_acquisition_mode"]
        == "static_host_rsync"
    )


def test_redundancy_source_summary_groups_metadata_and_overlap_sources() -> None:
    summary = redundancy_source_summary()

    assert [entry["source_id"] for entry in summary["metadata"]] == [
        "hathifiles",
        "hathitrust_oai_pmh",
        "hathitrust_bibliographic_api",
    ]
    assert [entry["source_id"] for entry in summary["derived_features"]] == [
        "htrc_solr_ef20",
        "htrc_extracted_features",
        "htrc_analytics",
    ]
    assert [entry["source_id"] for entry in summary["overlap"]] == [
        "internet_archive",
        "open_library",
    ]


def test_write_metadata_refresh_plan(tmp_path: Path) -> None:
    volumes = load_collection_export_tsv(ROOT / "data" / "hathi_collection_export_71329709.tsv")
    inventory = build_inventory(volumes[:2], expected_count=2)
    manifest = write_metadata_refresh_plan(
        inventory, tmp_path / "metadata", limit=2, oai_cursor="cursor-123"
    )

    assert manifest["meta"]["record_count"] == 2
    assert manifest["lanes"]["hathifiles"]["record_count"] == 2
    assert manifest["lanes"]["oai_pmh"]["requested_cursor"] == "cursor-123"
    assert (
        manifest["lanes"]["bibliographic_api"]["records"][0]["refresh_mode"]
        == "known_identifier_enrichment"
    )
    assert manifest["lanes"]["ia_open_library_crosswalk"]["record_count"] == 2
    assert manifest["lanes"]["nz_enrichment"]["record_count"] == 2
    assert manifest["lanes"]["nz_enrichment"]["source_families"] == [
        "official_parliamentary_sources",
        "digitalnz",
        "national_library_nz",
        "papers_past",
    ]
    assert (tmp_path / "metadata" / "metadata_refresh_manifest.json").exists()
    assert (tmp_path / "metadata" / "hathifiles_refresh_manifest.json").exists()
    assert (tmp_path / "metadata" / "oai_pmh_refresh_manifest.json").exists()
    assert (tmp_path / "metadata" / "bibliographic_api_refresh_manifest.json").exists()
    assert (
        tmp_path
        / "metadata"
        / "ia_open_library_crosswalk"
        / "ia_open_library_crosswalk_manifest.json"
    ).exists()
    assert (tmp_path / "metadata" / "nz_enrichment" / "nz_enrichment_manifest.json").exists()
    report = (tmp_path / "metadata" / "metadata_refresh_report.md").read_text(encoding="utf-8")
    assert "HathiTrust-NZ Metadata Refresh Plan" in report
    assert "Bibliographic API refreshes known HTID enrichment" in report
    assert "IA/Open Library crosswalk lanes provide deterministic evidence URLs" in report
    assert "NZ enrichment lanes provide metadata-only routing" in report


def test_write_completeness_report_writes_json_and_metrics(tmp_path: Path) -> None:
    volumes = load_collection_export_tsv(ROOT / "data" / "hathi_collection_export_71329709.tsv")
    inventory = build_inventory(volumes[:2], expected_count=2)
    out = tmp_path / "reports" / "archive_completeness.md"

    write_completeness_report(inventory, out)

    text = out.read_text(encoding="utf-8")
    payload = json.loads(out.with_suffix(".json").read_text(encoding="utf-8"))

    assert "Public full-text records" in text
    assert payload["counts"]["known"] == 2
    assert payload["counts"]["public_full_text"] == 2
    assert payload["counts"]["htrc_ef_available"] == 2
    assert payload["counts"]["hf_published"] is None
    assert payload["counts"]["zenodo_deposited"] is None


def test_write_publication_evidence_report_records_route_metadata(tmp_path: Path) -> None:
    volumes = load_collection_export_tsv(ROOT / "data" / "hathi_collection_export_71329709.tsv")
    inventory = build_inventory(volumes[:1], expected_count=1)
    out = tmp_path / "reports" / "publication_evidence"

    report = write_publication_evidence_report(inventory, out)

    text = (out / "publication_evidence.md").read_text(encoding="utf-8")
    payload = json.loads((out / "publication_evidence.json").read_text(encoding="utf-8"))

    assert "official HathiTrust" in text
    assert payload["meta"]["record_count"] == 1
    assert len(payload["child_datasets"]) == 5
    assert payload["child_datasets"][0]["publication_state"] == "metadata_only"
    assert "Metadata-only publication route" in payload["child_datasets"][0]["route_evidence"][3]
    assert report["child_datasets"][1]["blocked_routes"]


def test_write_blocker_report_records_external_access_blockers(tmp_path: Path) -> None:
    out = tmp_path / "reports" / "blockers"

    report = write_blocker_report(out)

    text = (out / "blocker_report.md").read_text(encoding="utf-8")
    payload = json.loads((out / "blocker_report.json").read_text(encoding="utf-8"))

    assert "HathiTrust-NZ Blocker Report" in text
    assert "HathiTrust static-host rsync" in text
    assert "Required access:" in text
    assert payload["meta"]["blocker_count"] >= 1
    assert payload["meta"]["group_count"] >= 1
    assert "blocker_groups" in payload
    assert "required_access" in payload
    assert any(group["category"] == "hathi_static_host" for group in payload["required_access"])
    assert any(
        "static-host" in item["blocker"] or "Hathi" in item["blocker"]
        for item in payload["blockers"]
    )
    assert report["meta"]["track_count"] >= 1


def test_write_blocker_report_deduplicates_blocked_access_entries(tmp_path: Path) -> None:
    track = tmp_path / "track.json"
    track.write_text(
        json.dumps(
            {
                "track_id": "track",
                "status": "in_progress",
                "blocked_until_external_access": ["HathiTrust rsync key"] * 2,
                "external_blockers": [],
            }
        ),
        encoding="utf-8",
    )

    report = write_blocker_report(
        tmp_path / "reports" / "blockers",
        track_metadata_paths=[track],
    )

    assert report["meta"]["blocker_count"] == 1


def test_write_htrc_ef_plan_routes_large_subsets_to_static_host_staging(tmp_path: Path) -> None:
    inventory = build_inventory(
        [
            {
                "htid": f"uc1.large{i}",
                "title": f"Example title {i}",
                "author": "Example author",
                "date": "1980",
                "rights_code": "17",
                "rights_label": "cc-zero",
                "htrc_ef25_rsync_path": f"vols/uc1.large{i}/uc1.large{i}.txt",
            }
            for i in range(251)
        ],
        expected_count=251,
    )

    manifest = write_htrc_ef_plan(inventory, tmp_path / "htrc", limit=0)

    assert manifest["meta"]["record_count"] == 251
    assert manifest["meta"]["route"] == "static_host_staging"
    assert (tmp_path / "htrc" / "static_host_staging_contract.sh").exists()
    assert "HATHI_STATIC_HOST_STAGING_DIR" in (
        tmp_path / "htrc" / "static_host_staging_contract.sh"
    ).read_text(encoding="utf-8")


def test_write_status_report(tmp_path: Path) -> None:
    volumes = load_collection_export_tsv(ROOT / "data" / "hathi_collection_export_71329709.tsv")
    inventory = build_inventory(volumes[:2], expected_count=2)
    metadata_refresh = write_metadata_refresh_plan(inventory, tmp_path / "metadata", limit=2)
    htrc_ef = write_htrc_ef_plan(inventory, tmp_path / "htrc_ef", limit=2)
    htrc_analytics = write_htrc_analytics_plan(inventory, tmp_path / "htrc_analytics", limit=2)
    internet_archive = {
        "meta": {
            "record_count": 2,
            "matched_count": 1,
            "review_queue_count": 1,
            "checksum_count": 1,
        }
    }

    report = write_status_report(
        inventory,
        tmp_path / "status",
        metadata_refresh=metadata_refresh,
        internet_archive=internet_archive,
        htrc_ef=htrc_ef,
        htrc_analytics=htrc_analytics,
    )

    assert report["meta"]["record_count"] == 2
    assert report["metadata_refresh"]["present"] is True
    assert report["internet_archive"]["matched_count"] == 1
    assert report["htrc"]["ef"]["record_count"] == 2
    assert report["htrc"]["analytics"]["record_count"] == 2
    assert report["redundancy"]["metadata"][0]["source_id"] == "hathifiles"
    assert report["redundancy"]["overlap"][0]["source_id"] == "internet_archive"
    assert report["tracks"][0]["track_id"] == "hathitrust_nz_multi_source_archive_20260702"
    assert (tmp_path / "status" / "status_report.json").exists()
    text = (tmp_path / "status" / "status_report.md").read_text(encoding="utf-8")
    assert "HathiTrust-NZ Status Snapshot" in text
    assert "Metadata redundancy sources" in text
    assert "hathitrust_nz_interim_acquisition_hardening_20260703" in text


def test_write_discovery_report(tmp_path: Path) -> None:
    volumes = load_collection_export_tsv(ROOT / "data" / "hathi_collection_export_71329709.tsv")
    inventory = build_inventory(volumes[:3], expected_count=3)
    discovery = build_discovery_manifest(inventory)
    out = tmp_path / "discovery" / "report.md"
    write_discovery_report(discovery, out)
    text = out.read_text(encoding="utf-8")
    assert "# HathiTrust-NZ Discovery Manifest" in text
    assert "Parliamentary and legal serials" in text


def test_discovery_manifest_keeps_seed_distinct_from_broader_families() -> None:
    volumes = load_collection_export_tsv(ROOT / "data" / "hathi_collection_export_71329709.tsv")
    inventory = build_inventory(volumes[:2], expected_count=2)
    discovery = build_discovery_manifest(inventory)

    assert discovery["meta"]["seed_record_count"] == 2
    assert discovery["meta"]["seed_collection_id"] == "71329709"
    assert discovery["seed_summary"]["record_count"] == 2
    assert len(discovery["source_families"]) == 4


def test_base_title_for_internet_archive() -> None:
    assert (
        base_title_for_internet_archive("Parliamentary debates (Hansard) v.281")
        == "Parliamentary debates (Hansard)"
    )
    assert base_title_for_internet_archive("Parliamentary debates 291") == "Parliamentary debates"


def test_write_internet_archive_overlap_plan(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    volumes = [
        {
            "htid": "uc1.test1",
            "title": "Parliamentary debates (Hansard) v.1",
            "author": "New Zealand. Parliament",
        }
    ]

    class FakeResponse:
        def __init__(
            self,
            payload: dict[str, object],
            *,
            status_code: int = 200,
            content: bytes = b"",
        ) -> None:
            self._payload = payload
            self.status_code = status_code
            self.content = content

        def raise_for_status(self) -> None:
            if self.status_code >= 400:
                raise RuntimeError("http error")

        def json(self) -> dict[str, object]:
            return self._payload

    def fake_get(
        url: str,
        params: dict[str, object] | None = None,
        headers: dict[str, str] | None = None,
        timeout: int | None = None,
    ) -> FakeResponse:
        del params, headers, timeout
        if "advancedsearch.php" in url:
            return FakeResponse(
                {
                    "response": {
                        "docs": [
                            {
                                "identifier": "parliamentarydeb1870newz",
                                "title": "Parliamentary debates (Hansard)",
                                "creator": "New Zealand. Parliament. House of Representatives",
                                "year": "1870",
                                "collection": ["americana"],
                                "publicdate": "2015-03-30 17:03:33",
                            }
                        ]
                    }
                }
            )
        if "metadata/parliamentarydeb1870newz" in url:
            return FakeResponse(
                {
                    "metadata": {"title": "Parliamentary debates (Hansard)"},
                    "files": [
                        {"name": "parliamentarydeb1870newz_djvu.txt"},
                    ],
                }
            )
        if "download/parliamentarydeb1870newz" in url:
            return FakeResponse({}, content=b"Debate text")
        raise AssertionError(f"unexpected url: {url}")

    monkeypatch.setattr("scripts.hathitrust_nz_archive.requests.get", fake_get)

    inventory = build_inventory(volumes, expected_count=1)
    manifest = write_internet_archive_overlap_plan(inventory, tmp_path / "ia", limit=0)
    assert manifest["meta"]["matched_count"] == 1
    assert manifest["meta"]["review_queue_count"] == 0
    assert manifest["meta"]["checksum_count"] == 1
    assert (tmp_path / "ia" / "internet_archive_overlap_manifest.json").exists()
    assert (tmp_path / "ia" / "texts" / "parliamentarydeb1870newz.txt").read_text(
        encoding="utf-8"
    ) == "Debate text"
    assert (tmp_path / "ia" / "internet_archive_provenance_ledger.json").exists()
    assert (tmp_path / "ia" / "internet_archive_checksum_manifest.json").exists()
    assert (tmp_path / "ia" / "internet_archive_source_evidence_report.json").exists()
    assert manifest["matched"][0]["match_confidence"] == 0.8
    assert "open_library_search_url" in manifest["matched"][0]["crosswalk"]
    checksum_manifest = json.loads(
        (tmp_path / "ia" / "internet_archive_checksum_manifest.json").read_text()
    )
    assert checksum_manifest["files"][0]["sha256"] == hashlib.sha256(b"Debate text").hexdigest()


def test_write_internet_archive_overlap_plan_routes_ambiguous_matches_to_review(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    volumes = [
        {
            "htid": "uc1.test2",
            "title": "Parliamentary debates (Hansard) v.2",
            "author": "New Zealand. Parliament",
        }
    ]

    class FakeResponse:
        def __init__(
            self,
            payload: dict[str, object],
            *,
            status_code: int = 200,
            content: bytes = b"",
        ) -> None:
            self._payload = payload
            self.status_code = status_code
            self.content = content

        def raise_for_status(self) -> None:
            if self.status_code >= 400:
                raise RuntimeError("http error")

        def json(self) -> dict[str, object]:
            return self._payload

    def fake_get(
        url: str,
        params: dict[str, object] | None = None,
        headers: dict[str, str] | None = None,
        timeout: int | None = None,
    ) -> FakeResponse:
        del params, headers, timeout
        if "advancedsearch.php" in url:
            return FakeResponse(
                {
                    "response": {
                        "docs": [
                            {
                                "identifier": "ambiguous-item",
                                "title": "Parliamentary debates (Hansard)",
                                "creator": "Another creator",
                                "year": "1871",
                                "collection": ["americana"],
                                "publicdate": "2015-03-30 17:03:33",
                            }
                        ]
                    }
                }
            )
        raise AssertionError(f"unexpected url: {url}")

    monkeypatch.setattr("scripts.hathitrust_nz_archive.requests.get", fake_get)

    inventory = build_inventory(volumes, expected_count=1)
    manifest = write_internet_archive_overlap_plan(inventory, tmp_path / "ia", limit=0)
    assert manifest["meta"]["matched_count"] == 0
    assert manifest["meta"]["review_queue_count"] == 1
    assert manifest["meta"]["checksum_count"] == 0
    assert (tmp_path / "ia" / "internet_archive_review_queue_htids.txt").read_text(
        encoding="utf-8"
    ) == "uc1.test2\n"
    review_manifest = json.loads(
        (tmp_path / "ia" / "internet_archive_overlap_manifest.json").read_text()
    )
    assert review_manifest["review_queue"][0]["review_reasons"]
    assert review_manifest["unmatched"][0]["crosswalk"]["open_library_search_url"].startswith(
        "https://openlibrary.org/search?q="
    )
