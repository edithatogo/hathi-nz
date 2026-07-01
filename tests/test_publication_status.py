"""Tests for the roadmap/publication status checker."""

from __future__ import annotations

import io
import json
import sys
from contextlib import redirect_stdout
from pathlib import Path
from typing import ClassVar

import pytest


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
            check_publication_status_module.DATASET_CARD_PATH: (
                "For academic citation, use the Zenodo DOI [10.5281/zenodo.123456](https://doi.org/10.5281/zenodo.123456)."
            ),
        }[path],
    )

    def fake_get(
        url: str,
        timeout: int,
        params: dict[str, object] | None = None,
        allow_redirects: bool | None = None,
    ):  # type: ignore[no-untyped-def]
        if "huggingface.co/api/datasets" in url:
            return _hf_response()
        if "doi.org/10.5281/zenodo.123456" in url:
            return _doi_response()
        if "zenodo.org/api/records" in url:
            return _zenodo_response([])
        raise AssertionError(f"Unexpected URL: {url}")

    monkeypatch.setattr(check_publication_status_module.requests, "get", fake_get)

    report = check_publication_status()

    assert report["dataset_card_doi"] == {
        "doi": "10.5281/zenodo.123456",
        "url": "https://doi.org/10.5281/zenodo.123456",
    }
    assert report["roadmap_complete"] is True
    assert report["publication_ready"] is True
    assert report["doi_status"]["resolves"] is True
    assert report["ready"] is True


@pytest.mark.unit
def test_strict_mode_allows_publication_ready_even_when_roadmap_is_incomplete(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        check_publication_status_module,
        "check_publication_status",
        lambda: {
            "tracks": {"all_complete": False},
            "hugging_face": {"exists": True},
            "zenodo": {"match_count": 0},
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
def test_main_strict_exits_nonzero_when_not_ready(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        check_publication_status_module,
        "check_publication_status",
        lambda: {
            "tracks": {"all_complete": False},
            "hugging_face": {"exists": True},
            "zenodo": {"match_count": 0},
            "ready": False,
        },
    )
    buffer = io.StringIO()
    with redirect_stdout(buffer):
        exit_code = check_publication_status_module.main(["--strict"])

    payload = json.loads(buffer.getvalue())
    assert payload["ready"] is False
    assert exit_code == 1
