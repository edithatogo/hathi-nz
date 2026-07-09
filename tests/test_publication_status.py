"""Tests for the roadmap/publication status checker."""

from __future__ import annotations

import io
import json
import sys
from contextlib import redirect_stdout
from pathlib import Path
from typing import ClassVar

import pytest
import requests


def _repo_root(start: Path) -> Path:
    for candidate in (start, *start.parents):
        if (candidate / "pixi.toml").exists():
            return candidate
    return start.parents[1]


ROOT = _repo_root(Path(__file__).resolve())
sys.path.insert(0, str(ROOT / "scripts"))

import check_publication_status as check_publication_status_module  # noqa: E402
from check_publication_status import check_publication_status  # noqa: E402


def _hf_response() -> object:
    class Response:
        ok = True
        status_code = 200

        @staticmethod
        def json() -> dict[str, object]:
            return {
                "id": "edithatogo/corpus-nz-hathi",
                "sha": "abc123",
                "createdAt": "2026-06-14T12:16:55.000Z",
                "lastModified": "2026-06-15T09:03:08.000Z",
                "usedStorage": 1000000,
                "siblings": [
                    {"rfilename": ".gitattributes"},
                    {"rfilename": "metadata.parquet"},
                    {"rfilename": "data/raw/debates/sample.txt"},
                ],
            }

    return Response()


def _zenodo_response(matches: list[dict[str, object]]) -> object:
    class Response:
        status_code = 200

        @staticmethod
        def raise_for_status() -> None:
            return None

        @staticmethod
        def json() -> dict[str, object]:
            return {"hits": {"hits": matches}}

    return Response()


def _doi_response(url: str = "https://zenodo.org/records/123456") -> object:
    class Response:
        ok = True
        status_code = 200
        history: ClassVar[list[object]] = []

        @staticmethod
        def json() -> dict[str, object]:
            return {}

    response = Response()
    response.url = url
    return response


@pytest.mark.unit
def test_track_summary_counts_complete_in_progress_and_pending() -> None:
    text = """\
## [x] Track: One
## [~] Track: Two
## [ ] Track: Three
"""
    summary = check_publication_status_module._track_summary(text)

    assert summary["complete"] == 1
    assert summary["in_progress"] == 1
    assert summary["pending"] == 1
    assert summary["total"] == 3
    assert summary["all_complete"] is False


@pytest.mark.unit
def test_check_publication_status_reports_not_ready_when_zenodo_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        check_publication_status_module,
        "_text",
        lambda path: {
            check_publication_status_module.TRACKS_PATH: """\
## [x] Track: One
## [~] Track: Two
""",
            check_publication_status_module.MANIFEST_PATH: """\
{"meta": {"record_count": 0}, "volumes": []}
""",
            check_publication_status_module.DATASET_CARD_PATH: "For academic citation, use the Zenodo DOI once a public release is published and recorded here.",
        }[path],
    )

    def fake_get(url: str, timeout: int, params: dict[str, object] | None = None):  # type: ignore[no-untyped-def]
        if "huggingface.co/api/datasets" in url:
            return _hf_response()
        if "zenodo.org/api/records" in url:
            return _zenodo_response([])
        if "doi.org/10.5281/zenodo.123456" in url:
            return _doi_response()
        raise AssertionError(f"Unexpected URL: {url}")

    monkeypatch.setattr(check_publication_status_module.requests, "get", fake_get)

    report = check_publication_status()

    assert report["tracks"]["all_complete"] is False
    assert report["hugging_face"]["exists"] is True
    assert report["zenodo"]["match_count"] == 0
    assert report["ready"] is False


@pytest.mark.unit
def test_check_publication_status_reports_ready_when_doi_resolves(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        check_publication_status_module,
        "_text",
        lambda path: {
            check_publication_status_module.TRACKS_PATH: """\
## [x] Track: One
""",
            check_publication_status_module.MANIFEST_PATH: """\
{"meta": {"record_count": 510}, "volumes": [{"htid": "uc1.b2889853"}]}
""",
            check_publication_status_module.DATASET_CARD_PATH: (
                "For academic citation, use the Zenodo DOI [10.5281/zenodo.123456](https://doi.org/10.5281/zenodo.123456)."
            ),
        }[path],
    )

    monkeypatch.setattr(
        check_publication_status_module,
        "_check_hugging_face",
        lambda repo_id: {
            "repo_id": repo_id,
            "exists": True,
            "status_code": 200,
            "data_file_count": 2,
        },
    )
    monkeypatch.setattr(
        check_publication_status_module,
        "_check_zenodo",
        lambda query="corpus-nz-hathi": {
            "query": query,
            "match_count": 0,
            "matches": [],
        },
    )
    monkeypatch.setattr(
        check_publication_status_module,
        "_doi_resolves",
        lambda doi_url: {
            "resolves": True,
            "status_code": 200,
            "final_url": doi_url,
            "redirects": 1,
        },
    )

    report = check_publication_status()

    assert report["dataset_card_doi"] == {
        "doi": "10.5281/zenodo.123456",
        "url": "https://doi.org/10.5281/zenodo.123456",
    }
    assert report["roadmap_complete"] is True
    assert report["doi_status"]["resolves"] is True
    assert report["tracks"]["all_complete"] is True


@pytest.mark.unit
def test_check_publication_status_uses_status_report_snapshot(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    status_report_path = tmp_path / "status_report.json"
    status_report_path.write_text(
        json.dumps(
            {
                "meta": {
                    "generated_at": "2026-07-03T00:00:00Z",
                    "hf_collection": "edithatogo/hathitrust-nz",
                    "record_count": 510,
                },
                "inventory": {"record_count": 510},
                "metadata_refresh": {"present": True},
                "internet_archive": {"present": True},
                "tracks": [
                    {"track_id": "one", "status": "complete"},
                    {"track_id": "two", "status": "in_progress"},
                ],
            }
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(
        check_publication_status_module,
        "_text",
        lambda path: {
            check_publication_status_module.TRACKS_PATH: """\
## [x] Track: One
""",
            check_publication_status_module.MANIFEST_PATH: """\
{"meta": {"record_count": 510}, "volumes": [{"htid": "uc1.b2889853"}]}
""",
            check_publication_status_module.DATASET_CARD_PATH: (
                "For academic citation, use the Zenodo DOI [10.5281/zenodo.123456](https://doi.org/10.5281/zenodo.123456)."
            ),
            status_report_path: status_report_path.read_text(encoding="utf-8"),
        }[path],
    )
    monkeypatch.setattr(check_publication_status_module.requests, "get", lambda *args, **kwargs: _hf_response())  # type: ignore[assignment]
    monkeypatch.setattr(
        check_publication_status_module,
        "_check_zenodo",
        lambda query="corpus-nz-hathi": {
            "query": query,
            "match_count": 0,
            "matches": [],
        },
    )
    monkeypatch.setattr(
        check_publication_status_module,
        "_doi_resolves",
        lambda doi_url: {
            "resolves": True,
            "status_code": 200,
            "final_url": doi_url,
            "redirects": 1,
        },
    )

    report = check_publication_status(status_report_path=status_report_path)

    assert report["status_report"]["exists"] is True
    assert report["status_report"]["track_count"] == 2
    assert report["status_report"]["roadmap_complete"] is False
    assert report["roadmap_complete"] is False
    assert report["ready"] is False


@pytest.mark.unit
def test_check_publication_status_uses_publication_evidence_snapshot(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    status_report_path = tmp_path / "status_report.json"
    publication_evidence_path = tmp_path / "publication_evidence.json"
    status_report_path.write_text(
        json.dumps(
            {
                "meta": {
                    "generated_at": "2026-07-03T00:00:00Z",
                    "hf_collection": "edithatogo/hathitrust-nz",
                    "record_count": 510,
                },
                "inventory": {"record_count": 510},
                "metadata_refresh": {"present": True},
                "internet_archive": {"present": True},
                "tracks": [{"track_id": "one", "status": "complete"}],
            }
        ),
        encoding="utf-8",
    )
    publication_evidence_path.write_text(
        json.dumps(
            {
                "meta": {
                    "generated_at": "2026-07-03T00:00:00Z",
                    "hf_collection": "edithatogo/hathitrust-nz",
                    "record_count": 510,
                },
                "child_datasets": [
                    {
                        "dataset_id": "hathitrust-nz-inventory",
                        "publication_state": "metadata_only",
                        "route_evidence": ["a", "b"],
                        "blocked_routes": ["c"],
                    },
                    {
                        "dataset_id": "hathitrust-nz-research-fulltext",
                        "publication_state": "metadata_only_until_static_host_bundle_is_eligible",
                        "route_evidence": ["a", "b"],
                        "blocked_routes": ["c"],
                    },
                    {
                        "dataset_id": "hathitrust-nz-htrc-extracted-features",
                        "publication_state": "public_derived_features",
                        "route_evidence": ["a", "b"],
                        "blocked_routes": ["c"],
                    },
                    {
                        "dataset_id": "hathitrust-nz-htrc-analytics",
                        "publication_state": "public_scripts_aggregates_and_reproducibility_metadata",
                        "route_evidence": ["a", "b"],
                        "blocked_routes": ["c"],
                    },
                    {
                        "dataset_id": "corpus-nz-hathi",
                        "publication_state": "public_full_text_where_confirmed",
                        "route_evidence": ["a", "b"],
                        "blocked_routes": ["c"],
                    },
                ],
            }
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(
        check_publication_status_module,
        "_text",
        lambda path: {
            check_publication_status_module.TRACKS_PATH: """\
## [x] Track: One
""",
            check_publication_status_module.MANIFEST_PATH: """\
{"meta": {"record_count": 510}, "volumes": [{"htid": "uc1.b2889853"}]}
""",
            check_publication_status_module.DATASET_CARD_PATH: (
                "For academic citation, use the Zenodo DOI [10.5281/zenodo.123456](https://doi.org/10.5281/zenodo.123456)."
            ),
            status_report_path: status_report_path.read_text(encoding="utf-8"),
            publication_evidence_path: publication_evidence_path.read_text(encoding="utf-8"),
        }[path],
    )
    monkeypatch.setattr(check_publication_status_module.requests, "get", lambda *args, **kwargs: _hf_response())  # type: ignore[assignment]
    monkeypatch.setattr(
        check_publication_status_module,
        "_check_zenodo",
        lambda query="corpus-nz-hathi": {
            "query": query,
            "match_count": 0,
            "matches": [],
        },
    )
    monkeypatch.setattr(
        check_publication_status_module,
        "_doi_resolves",
        lambda doi_url: {
            "resolves": True,
            "status_code": 200,
            "final_url": doi_url,
            "redirects": 1,
        },
    )

    report = check_publication_status(
        status_report_path=status_report_path,
        publication_evidence_path=publication_evidence_path,
    )

    assert report["publication_evidence"]["exists"] is True
    assert report["publication_evidence"]["child_dataset_count"] == 5
    assert report["publication_ready"] is True
    assert report["ready"] is True


@pytest.mark.unit
def test_strict_mode_allows_publication_ready_even_when_roadmap_is_incomplete(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        check_publication_status_module,
        "check_publication_status",
        lambda **kwargs: {
            "tracks": {"all_complete": False},
            "hugging_face": {"exists": True},
            "zenodo": {"match_count": 0},
            "manifest": {"record_count": 510},
            "expected_volumes": 510,
            "dataset_card_doi": {"doi": "10.5281/zenodo.123456"},
            "doi_status": {"resolves": True},
            "roadmap_complete": False,
            "publication_ready": True,
            "ready": True,
        },
    )
    buffer = io.StringIO()
    with redirect_stdout(buffer):
        exit_code = check_publication_status_module.main(["--strict"])

    payload = json.loads(buffer.getvalue())
    assert payload["ready"] is True
    assert exit_code == 0


@pytest.mark.unit
def test_strict_mode_blocks_when_status_report_is_not_complete(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    status_report_path = tmp_path / "status_report.json"
    status_report_path.write_text(
        json.dumps(
            {
                "meta": {"record_count": 510},
                "tracks": [{"track_id": "one", "status": "complete"}, {"track_id": "two", "status": "pending"}],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        check_publication_status_module,
        "check_publication_status",
        lambda **kwargs: {
            "tracks": {"all_complete": False},
            "status_report": {"exists": True, "roadmap_complete": False},
            "hugging_face": {"exists": True},
            "zenodo": {"match_count": 0},
            "manifest": {"record_count": 510},
            "expected_volumes": 510,
            "dataset_card_doi": {"doi": "10.5281/zenodo.123456"},
            "doi_status": {"resolves": True},
            "roadmap_complete": False,
            "publication_ready": True,
            "ready": False,
        },
    )
    buffer = io.StringIO()
    with redirect_stdout(buffer):
        exit_code = check_publication_status_module.main(["--strict", "--status-report", str(status_report_path)])

    payload = json.loads(buffer.getvalue())
    assert payload["status_report"]["exists"] is True
    assert payload["ready"] is False
    assert exit_code == 1


@pytest.mark.unit
def test_main_strict_exits_nonzero_when_not_ready(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        check_publication_status_module,
        "check_publication_status",
        lambda **kwargs: {
            "tracks": {"all_complete": False},
            "hugging_face": {"exists": True},
            "zenodo": {"match_count": 0},
            "manifest": {"record_count": 0},
            "expected_volumes": 510,
            "ready": False,
        },
    )
    buffer = io.StringIO()
    with redirect_stdout(buffer):
        exit_code = check_publication_status_module.main(["--strict"])

    payload = json.loads(buffer.getvalue())
    assert payload["ready"] is False
    assert exit_code == 1


@pytest.mark.unit
def test_publication_status_helper_parses_fallback_fields() -> None:
    card_text = """\
For academic citation, use the Zenodo DOI 10.5281/zenodo.987654.

**Expected volumes** | 510
"""

    assert check_publication_status_module._dataset_card_doi(card_text) == {
        "doi": "10.5281/zenodo.987654",
        "url": "https://doi.org/10.5281/zenodo.987654",
    }
    assert check_publication_status_module._dataset_card_expected_volumes(card_text) == 510

    manifest = check_publication_status_module._manifest_summary("{not-json")
    assert manifest["exists"] is False
    assert manifest["record_count"] == 0


@pytest.mark.unit
def test_check_hugging_face_and_zenodo_error_paths(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_get(url: str, timeout: int, params: dict[str, object] | None = None):  # type: ignore[no-untyped-def]
        if "huggingface.co/api/datasets" in url:
            msg = "connection reset"
            raise requests.RequestException(msg)
        if "zenodo.org/api/records" in url:
            return _zenodo_response(
                [
                    {
                        "title": "corpus-nz-hathi release",
                        "doi": "10.5281/zenodo.123456",
                        "status": "done",
                        "created": "2026-07-02T00:00:00",
                        "updated": "2026-07-02T00:00:00",
                    }
                ]
            )
        raise AssertionError(f"Unexpected URL: {url}")

    monkeypatch.setattr(check_publication_status_module.requests, "get", fake_get)

    hf = check_publication_status_module._check_hugging_face("edithatogo/corpus-nz-hathi")
    assert hf["exists"] is False
    assert "connection reset" in hf["error"]

    zenodo = check_publication_status_module._check_zenodo("corpus-nz-hathi")
    assert zenodo["match_count"] == 1
    assert zenodo["matches"][0]["doi"] == "10.5281/zenodo.123456"
