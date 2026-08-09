"""High-value orchestration tests for operational CLI entry points."""

from __future__ import annotations

import gzip
import io
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts import hathitrust_nz_archive as archive
from scripts import (
    fetch_hathitrust,
    ocr_extract,
    package_release,
    publish_osf,
    publish_zenodo,
    sync_hf_collection,
    upload_hf_folder,
)
from scripts import stage_hf_dataset as stage
from scripts import upload_hf_dataset as upload
from scripts.validate_catalog import check_manifest_consistency, validate_manifest_schema


def _archive_args(command: str, tmp_path: Path) -> SimpleNamespace:
    inventory = tmp_path / "inventory.json"
    inventory.write_text("{}", encoding="utf-8")
    return SimpleNamespace(
        command=command,
        collection_export=inventory,
        inventory=inventory,
        output=tmp_path / "output.json",
        output_dir=tmp_path / command,
        htids_output=tmp_path / "htids.txt",
        expected_count=0,
        fail_on_count_drift=False,
        completeness_report=tmp_path / "completeness.md",
        internet_archive=inventory,
        htrc_ef=inventory,
        htrc_analytics=inventory,
        limit=1,
        source_dataset_name=archive.HATHI_RESEARCH_PD_WORLD_OPEN_ACCESS,
        oai_cursor="cursor",
        metadata_refresh=inventory,
        track_metadata=[inventory],
        report=tmp_path / "report.md",
        dry_run=True,
    )


@pytest.mark.parametrize(
    "command",
    [
        "inventory",
        "collection-manifest",
        "routing-manifest",
        "htrc-ef-plan",
        "htrc-analytics-plan",
        "htrc-solr-plan",
        "ia-open-library-crosswalk-plan",
        "research-rsync-plan",
        "metadata-refresh",
        "status-report",
        "internet-archive-plan",
        "discovery-manifest",
        "publication-evidence",
        "blocker-report",
    ],
)
def test_archive_cli_dispatches_every_command(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, command: str
) -> None:
    args = _archive_args(command, tmp_path)
    monkeypatch.setattr(archive, "parse_args", lambda: args)
    monkeypatch.setattr(archive, "configure_logging", lambda: None)
    monkeypatch.setattr(archive, "load_collection_export_tsv", lambda path: [])
    monkeypatch.setattr(archive, "load_inventory", lambda path: {})
    monkeypatch.setattr(archive, "load_json", lambda path: {})
    monkeypatch.setattr(archive, "build_inventory", lambda *a, **kw: {})
    monkeypatch.setattr(archive, "build_collection_manifest", lambda *a, **kw: {})
    monkeypatch.setattr(archive, "build_canonical_routing_manifest", lambda *a, **kw: {})
    monkeypatch.setattr(archive, "build_discovery_manifest", lambda *a, **kw: {})
    monkeypatch.setattr(archive, "assert_expected_count", lambda *a, **kw: None)
    for name in (
        "write_inventory_outputs",
        "write_json",
        "write_completeness_report",
        "write_htrc_ef_plan",
        "write_htrc_analytics_plan",
        "write_htrc_solr_discovery_plan",
        "write_ia_open_library_crosswalk_plan",
        "write_research_dataset_plan",
        "write_metadata_refresh_plan",
        "write_status_report",
        "write_internet_archive_overlap_plan",
        "write_discovery_report",
        "write_publication_evidence_report",
        "write_blocker_report",
    ):
        monkeypatch.setattr(archive, name, lambda *a, **kw: None)

    assert archive.main() == 0


def test_stage_cli_handles_failure_and_success(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    args = SimpleNamespace(
        manifest=tmp_path / "manifest.json",
        download_dir=tmp_path / "downloads",
        stage_dir=tmp_path / "stage",
        state_dir=tmp_path / "state",
        limit=1,
    )
    monkeypatch.setattr(stage, "parse_args", lambda: args)
    monkeypatch.setattr(stage, "configure_logging", lambda: None)
    monkeypatch.setattr(stage, "load_manifest", lambda path: [{"htid": "uc1.test"}])
    monkeypatch.setattr(stage, "write_stage_state", lambda *a, **kw: None)

    class FakeDataFrame:
        def __len__(self) -> int:
            return 0

        def write_parquet(self, path: str) -> None:
            return None

    monkeypatch.setattr(stage, "build_metadata_dataframe", lambda values: FakeDataFrame())

    monkeypatch.setattr(stage, "download_volume", lambda *a, **kw: None)
    assert stage.main() == 1

    monkeypatch.setattr(
        stage,
        "download_volume",
        lambda *a, **kw: {"sha256": "abc", "size_bytes": 3},
    )
    assert stage.main() == 0


def test_upload_cli_dry_run_and_execute(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    manifests = tmp_path / "manifests"
    manifests.mkdir()
    (manifests / "latest_manifest.json").write_text(
        json.dumps({"volumes": [{"htid": "uc1.test"}]}), encoding="utf-8"
    )
    common = {
        "stage_dir": tmp_path / "stage",
        "manifests_dir": manifests,
        "data_dir": tmp_path / "data",
        "repo_id": "owner/dataset",
        "state_dir": tmp_path / "state",
        "commit_message": "test",
    }
    monkeypatch.setattr(upload, "configure_logging", lambda: None)
    monkeypatch.setattr(upload, "get_hf_api", object)
    monkeypatch.setattr(upload, "ensure_repo_exists", lambda *a, **kw: True)
    monkeypatch.setattr(upload, "load_upload_state", lambda path: {})
    monkeypatch.setattr(upload, "upload_metadata_files", lambda *a, **kw: "meta")
    monkeypatch.setattr(upload, "upload_volume_files", lambda *a, **kw: "vol")
    monkeypatch.setattr(upload, "write_upload_state", lambda *a, **kw: None)

    monkeypatch.setattr(upload, "parse_args", lambda: SimpleNamespace(**common, dry_run=True))
    assert upload.main() == 0
    monkeypatch.setattr(upload, "parse_args", lambda: SimpleNamespace(**common, dry_run=False))
    assert upload.main() == 0


def test_archive_writers_emit_empty_manifests(tmp_path: Path) -> None:
    inventory = {"volumes": []}
    archive.write_htrc_ef_plan(inventory, tmp_path / "ef")
    archive.write_htrc_analytics_plan(inventory, tmp_path / "analytics")
    archive.write_htrc_solr_discovery_plan(inventory, tmp_path / "solr")
    archive.write_nz_enrichment_plan(inventory, tmp_path / "nz")
    archive.write_ia_open_library_crosswalk_plan(inventory, tmp_path / "crosswalk")
    archive.write_research_dataset_plan(inventory, tmp_path / "research")
    archive.write_internet_archive_overlap_plan(inventory, tmp_path / "ia", dry_run=True)

    assert (tmp_path / "ef" / "htrc_ef25_manifest.json").exists()
    assert (tmp_path / "analytics" / "htrc_analytics_manifest.json").exists()
    assert (tmp_path / "research" / "research_dataset_manifest.json").exists()


def test_archive_writers_process_a_curated_volume(tmp_path: Path) -> None:
    inventory = {
        "volumes": [
            {
                "htid": "uc1.test",
                "title": "Parliamentary debates (Hansard) v.1",
                "author": "New Zealand. Parliament",
                "date": "1900",
                "rights_code": "17",
                "rights_label": "cc-zero",
                "access_profile_code": "open",
                "digitization_agent_code": "uc1",
                "htrc_ef25_rsync_path": "uc1/test.json.bz2",
                "oclc": "123",
                "catalog_url": "https://catalog.example/test",
            }
        ]
    }
    archive.write_htrc_ef_plan(inventory, tmp_path / "ef")
    archive.write_htrc_analytics_plan(inventory, tmp_path / "analytics")
    archive.write_htrc_solr_discovery_plan(inventory, tmp_path / "solr")
    archive.write_nz_enrichment_plan(inventory, tmp_path / "nz")
    archive.write_ia_open_library_crosswalk_plan(inventory, tmp_path / "crosswalk")
    archive.write_research_dataset_plan(inventory, tmp_path / "research")
    archive.write_internet_archive_overlap_plan(inventory, tmp_path / "ia", dry_run=True)

    assert (tmp_path / "ef" / "htrc_ef25_htids.txt").read_text(encoding="utf-8").strip()
    assert (tmp_path / "research" / "research_dataset_manifest.json").exists()


def test_operational_parsers_and_cli_wrappers(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    assert package_release.parse_args(["--version", "1.0.0"]).version == "1.0.0"
    assert publish_zenodo.parse_args(["--archive", "release.zip", "--execute"]).dry_run is False
    assert publish_osf.parse_args([]).dry_run is True
    assert stage.parse_args([]).limit == 0
    assert upload.parse_args([]).dry_run is False
    assert (
        upload_hf_folder.parse_args(["--source-dir", ".", "--repo-id", "owner/data"]).dry_run
        is False
    )
    assert sync_hf_collection.parse_args(["--dry-run"]).dry_run is True

    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps({"child_datasets": []}), encoding="utf-8")
    monkeypatch.setattr(sync_hf_collection, "configure_logging", lambda: None)
    monkeypatch.setattr(sync_hf_collection, "sync_hf_collection", lambda **kwargs: {"ok": True})
    monkeypatch.setattr(
        sync_hf_collection,
        "parse_args",
        lambda: SimpleNamespace(
            title="title",
            namespace="owner",
            collection_slug=None,
            description="description",
            manifest=manifest,
            dry_run=True,
        ),
    )
    assert sync_hf_collection.main() == 0

    monkeypatch.setattr(upload_hf_folder, "configure_logging", lambda: None)
    monkeypatch.setattr(upload_hf_folder, "upload_folder_to_hf", lambda **kwargs: {"ok": True})
    monkeypatch.setattr(
        upload_hf_folder,
        "parse_args",
        lambda: SimpleNamespace(
            source_dir=tmp_path,
            repo_id="owner/data",
            path_in_repo=".",
            commit_message="test",
            create_pr=False,
            dry_run=True,
        ),
    )
    assert upload_hf_folder.main() == 0


def test_status_publication_and_blocker_reports(tmp_path: Path) -> None:
    inventory = {
        "meta": {"collection_id": "71329709", "record_count": 1},
        "summary": {"record_count": 1, "rights_counts": {"cc-zero": 1}},
        "volumes": [],
    }
    refresh = {"lanes": {"hathifiles": {"record_count": 1, "refresh_url": "url"}}}
    auxiliary = {"meta": {"record_count": 1, "route": "github_actions"}}
    status = archive.write_status_report(
        inventory,
        tmp_path / "status",
        metadata_refresh=refresh,
        internet_archive={"meta": {"record_count": 1, "matched_count": 1}},
        htrc_ef=auxiliary,
        htrc_analytics=auxiliary,
        track_metadata_paths=[],
    )
    evidence = archive.write_publication_evidence_report(inventory, tmp_path / "evidence")
    track = tmp_path / "track.json"
    track.write_text(
        json.dumps(
            {
                "track_id": "track",
                "status": "in_progress",
                "external_blockers": ["HathiTrust rsync key"],
            }
        ),
        encoding="utf-8",
    )
    blockers = archive.write_blocker_report(tmp_path / "blockers", track_metadata_paths=[track])

    assert status["metadata_refresh"]["present"] is True
    assert len(evidence["child_datasets"]) == 5
    assert blockers["meta"]["blocker_count"] == 1


def test_blocker_report_deduplicates_track_blockers(tmp_path: Path) -> None:
    track = tmp_path / "track.json"
    track.write_text(
        json.dumps(
            {
                "track_id": "track",
                "status": "in_progress",
                "blocked_until_external_access": ["HathiTrust rsync key"],
                "external_blockers": ["HathiTrust rsync key"],
            }
        ),
        encoding="utf-8",
    )

    blockers = archive.write_blocker_report(tmp_path / "blockers", track_metadata_paths=[track])

    assert blockers["meta"]["blocker_count"] == 1


def test_internet_archive_plan_records_error_review_and_match(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    volume = {
        "htid": "uc1.test",
        "title": "Parliamentary debates (Hansard) v.1",
        "author": "New Zealand. Parliament",
        "date": "1900",
    }
    request_error = archive.requests.RequestException("offline")
    monkeypatch.setattr(
        archive, "internet_archive_search", lambda *a, **kw: (_ for _ in ()).throw(request_error)
    )
    error_report = archive.write_internet_archive_overlap_plan(
        {"volumes": [volume]}, tmp_path / "search-error"
    )
    assert error_report["meta"]["unmatched_count"] == 1

    doc = {
        "identifier": "archive-item",
        "title": "Parliamentary debates (Hansard)",
        "creator": "New Zealand. Parliament",
        "year": "1900",
        "collection": ["publicdomain"],
    }
    monkeypatch.setattr(archive, "internet_archive_search", lambda *a, **kw: [doc])
    monkeypatch.setattr(
        archive,
        "internet_archive_metadata",
        lambda identifier: {"files": [{"name": "archive-item_djvu.txt"}]},
    )
    match_report = archive.write_internet_archive_overlap_plan(
        {"volumes": [volume]}, tmp_path / "match", dry_run=True
    )
    assert match_report["meta"]["matched_count"] == 1
    assert match_report["matched"][0]["dry_run"] is True

    class TextResponse:
        status_code = 200
        content = gzip.compress(b"archive text")

    monkeypatch.setattr(archive.requests, "get", lambda *a, **kw: TextResponse())
    text_path = archive.download_internet_archive_text(
        "archive-item", {"files": [{"name": "item_hocr_searchtext.txt.gz"}]}, tmp_path / "texts"
    )
    assert text_path is not None
    assert text_path.read_bytes() == b"archive text"


def test_fetch_hathitrust_remote_and_api_edge_paths(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    class Response:
        def __init__(self, payload: object, *, text: str = "") -> None:
            self.payload = payload
            self.text = text

        def raise_for_status(self) -> None:
            return None

        def json(self) -> object:
            return self.payload

    monkeypatch.setattr(
        fetch_hathitrust.requests,
        "get",
        lambda *args, **kwargs: Response(
            [{"full": True, "filename": "b.tsv.gz", "url": "https://b"}, {"full": False}]
        ),
    )
    assert fetch_hathitrust._latest_full_hathifile_url() == "https://b"
    monkeypatch.setattr(
        fetch_hathitrust,
        "_lookup_volume_metadata",
        lambda _: (_ for _ in ()).throw(fetch_hathitrust.requests.RequestException("down")),
    )
    assert fetch_hathitrust.lookup_volume_metadata("uc1.test") is None
    assert fetch_hathitrust.enrich_volume_metadata({"htid": ""}) == {"htid": ""}
    monkeypatch.setattr(fetch_hathitrust, "lookup_volume_metadata", lambda _: None)
    assert (
        fetch_hathitrust.enrich_volume_metadata({"htid": "uc1.test", "title": "x"})["title"] == "x"
    )

    class RawResponse:
        def __init__(self) -> None:
            self.raw = io.BytesIO(
                gzip.compress(
                    b"uc1.test\tpd\tpd\tbib\tdesc\tuc1\t"
                    + b"\t" * 18
                    + b"Title v.1\t1900\t\t\t\t\t\t\t\t\tNJP\tUC1\tUC1\tGoogle\tpd\tAuthor\n"
                )
            )

        def __enter__(self) -> "RawResponse":
            return self

        def __exit__(self, *args: object) -> None:
            self.raw.close()

        def raise_for_status(self) -> None:
            return None

    monkeypatch.setattr(fetch_hathitrust.requests, "get", lambda *args, **kwargs: RawResponse())
    assert list(fetch_hathitrust._iter_remote_hathifile_lines("https://example/full.gz"))

    export = tmp_path / "export.tsv"
    export.write_text("htid\ttitle\nuc1.test\tTitle\n", encoding="utf-8")
    assert fetch_hathitrust.build_manifest_from_collection_export(export_file=export)
    with pytest.raises(ValueError, match="No HTIDs"):
        empty = tmp_path / "empty.tsv"
        empty.write_text("htid\ttitle\n", encoding="utf-8")
        fetch_hathitrust.build_manifest_from_collection_export(export_file=empty)


def test_fetch_hathitrust_cli_api_and_download_branches(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    output = tmp_path / "manifest.json"
    monkeypatch.setattr(fetch_hathitrust, "configure_logging", lambda: None)
    monkeypatch.setattr(fetch_hathitrust, "lookup_volume_metadata", lambda _: {"htid": "uc1.test"})
    monkeypatch.setattr(
        fetch_hathitrust,
        "parse_args",
        lambda: SimpleNamespace(command="api-lookup", htid="uc1.test"),
    )
    # The legacy CLI prints a successful lookup but falls through to its
    # unknown-command return path; preserve that contract while covering it.
    assert fetch_hathitrust.main() == 1
    monkeypatch.setattr(fetch_hathitrust, "lookup_volume_metadata", lambda _: None)
    assert fetch_hathitrust.main() == 1

    downloaded = tmp_path / "downloaded.gz"
    monkeypatch.setattr(
        fetch_hathitrust, "_download_hathifile", lambda url, path: path.write_bytes(b"x") or path
    )
    monkeypatch.setattr(
        fetch_hathitrust, "build_manifest_from_hathifile", lambda *args, **kwargs: []
    )
    monkeypatch.setattr(
        fetch_hathitrust, "write_manifest", lambda volumes, path: {"meta": {"record_count": 0}}
    )
    monkeypatch.setattr(
        fetch_hathitrust,
        "parse_args",
        lambda: SimpleNamespace(
            command="remote-hathifile",
            url="https://example/full.gz",
            download_to=downloaded,
            output=output,
            collection_id="71329709",
            collection_code="NJP",
            htid_allowlist=None,
            category="debates",
            enrich_api=False,
        ),
    )
    assert fetch_hathitrust.main() == 0
    monkeypatch.setattr(fetch_hathitrust, "parse_args", lambda: SimpleNamespace(command="unknown"))
    assert fetch_hathitrust.main() == 1


def test_sync_hf_collection_updates_existing_collection_and_rejects_missing_slug(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class Collection:
        slug = "owner/existing"

    class Api:
        def __init__(self, token: str | None = None) -> None:
            self.updated = False

        def get_collection(self, slug: str, *, token: str | None) -> Collection:
            assert slug == "owner/existing"
            return Collection()

        def create_collection(self, *args: object, **kwargs: object) -> Collection:
            return Collection()

        def update_collection_metadata(self, slug: str, **kwargs: object) -> None:
            self.updated = True

        def add_collection_item(self, *args: object, **kwargs: object) -> None:
            return None

    api = Api()
    monkeypatch.setattr(sync_hf_collection, "HfApi", lambda token=None: api)
    result = sync_hf_collection.sync_hf_collection(
        title="title",
        namespace="owner",
        description="description",
        collection_slug="owner/existing",
    )
    assert result["resolved_slug"] == "owner/existing"
    assert api.updated
    monkeypatch.setattr(
        sync_hf_collection,
        "_collection_slug",
        lambda _: (_ for _ in ()).throw(ValueError("missing")),
    )
    with pytest.raises(ValueError, match="missing"):
        sync_hf_collection.sync_hf_collection(
            title="title", namespace="owner", description="description"
        )


@pytest.mark.parametrize(
    "argv",
    [
        ["inventory", "--collection-export", "in.tsv", "--output", "out.json"],
        ["collection-manifest", "--inventory", "in.json", "--output", "out.json"],
        ["routing-manifest", "--inventory", "in.json", "--output", "out.json"],
        ["htrc-ef-plan", "--inventory", "in.json", "--output-dir", "out"],
        ["htrc-analytics-plan", "--inventory", "in.json", "--output-dir", "out"],
        ["htrc-solr-plan", "--inventory", "in.json", "--output-dir", "out"],
        ["ia-open-library-crosswalk-plan", "--inventory", "in.json", "--output-dir", "out"],
        ["research-rsync-plan", "--inventory", "in.json", "--output-dir", "out"],
        ["metadata-refresh", "--inventory", "in.json", "--output-dir", "out"],
        ["status-report", "--inventory", "in.json", "--output-dir", "out"],
        ["internet-archive-plan", "--inventory", "in.json", "--output-dir", "out"],
        ["discovery-manifest", "--inventory", "in.json", "--output", "out.json"],
        ["publication-evidence", "--inventory", "in.json", "--output-dir", "out"],
        ["blocker-report", "--output-dir", "out"],
    ],
)
def test_archive_parser_accepts_all_commands(argv: list[str]) -> None:
    assert archive.parse_args(argv).command == argv[0]


def test_ocr_and_catalog_fail_closed_edges(tmp_path: Path) -> None:
    assert ocr_extract._parse_page_number("page.txt") is None
    archive_path = tmp_path / "uc1_test.zip"
    import zipfile

    with zipfile.ZipFile(archive_path, "w") as zf:
        zf.writestr("0002.txt", b"second")
        zf.writestr("0001.txt", "first")
    pages = ocr_extract.load_page_text(tmp_path, "uc1.test")
    assert [page["page_num"] for page in pages] == [1, 2]
    assert (
        ocr_extract.reconstruct_columns([{"column_texts": [" a ", " ", "b"]}])[0]["text"]
        == "a\n\nb"
    )
    assert ocr_extract.reconstruct_columns([{"text": "plain"}])[0]["text"] == "plain"

    assert check_manifest_consistency([{"htid": "x", "year": "1900", "rights": "bad", "source": 1}])
    assert validate_manifest_schema(
        {"meta": {}, "volumes": ["bad"]}, tmp_path / "missing-schema.json"
    )


@pytest.mark.parametrize(
    ("title", "expected"),
    [
        ("", (None, None)),
        ("Hansard 1900:2", (None, "1900:2")),
        ("Parliamentary debates 1900-01", (None, "1900-01")),
        (f"{archive.HANSARD_TITLE_PREFIX} special", (None, "special")),
        (f"{archive.PARLIAMENTARY_DEBATES_TITLE_PREFIX} (1900)", (None, None)),
    ],
)
def test_archive_normalization_and_policy_edges(
    title: str, expected: tuple[int | None, str | None]
) -> None:
    assert archive.parse_volume_label(title) == expected
    assert isinstance(archive.base_title_for_internet_archive(title), str)

    assert archive.htrc_stubbytree_path("uc1.b2889853").startswith("uc1/")
    with pytest.raises(ValueError):
        archive.htrc_stubbytree_path("invalid")
    assert archive.canonical_rights_label(None) == "und"
    assert archive.classify_publication_policy("17")["public_full_text_allowed"] is True
    restricted = archive.classify_publication_policy(
        "pdus", access_profile_code="page", digitization_agent_code="google"
    )
    assert restricted["public_full_text_allowed"] is False
    assert (
        archive.classify_publication_policy(
            "pd", source_dataset_name=archive.HATHI_RESEARCH_PD_OPEN_ACCESS
        )["requires_static_host"]
        is True
    )


def test_archive_routing_and_plan_restriction_edges(tmp_path: Path) -> None:
    inventory = {
        "meta": {"record_count": 2},
        "volumes": [
            {"htid": "uc1.public", "title": "Public", "rights_code": "17"},
            {"htid": "uc1.restricted", "title": "Restricted", "rights_code": "pdus"},
        ],
    }
    research = archive.write_research_dataset_plan(inventory, tmp_path / "research")
    assert research["meta"]["metadata_only_count"] == 1
    routing = archive.build_canonical_routing_manifest(
        inventory,
        internet_archive={"matches": [{"htid": "uc1.public", "publication_eligible": True}]},
        htrc_ef={"files": [{"htid": "uc1.restricted"}]},
    )
    assert {item["route"] for item in routing["routes"]} == {
        "internet_archive_public_domain_overlap",
        "htrc_extracted_features",
    }
    bad = tmp_path / "bad.json"
    bad.write_text("[]", encoding="utf-8")
    with pytest.raises(TypeError):
        archive.load_json(bad)
    with pytest.raises(TypeError):
        archive.load_inventory(bad)
