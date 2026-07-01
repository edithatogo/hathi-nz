"""Report local roadmap completion and public publication status.

This script reports Conductor roadmap status alongside externally published
state so the repository can tell whether the roadmap is complete and whether
the published dataset is ready for release gating.
"""

from __future__ import annotations

import argparse
import json
import re
from collections.abc import Callable
from pathlib import Path
from typing import Any

import requests

ROOT = Path(__file__).resolve().parents[1]
TRACKS_PATH = ROOT / "conductor" / "tracks.md"
DATASET_CARD_PATH = ROOT / "DATASET_CARD.md"

get_settings: Callable[[], Any] | None = None
try:
    from config import get_settings as _get_settings
except ImportError:  # pragma: no cover
    pass
else:
    get_settings = _get_settings

TRACK_LINE = re.compile(r"^## \[(?P<status>[x~ ])\] Track: (?P<title>.+)$")
DOI_LINE = re.compile(
    r"For academic citation, use the Zenodo DOI \[(?P<doi>[^\]]+)\]\((?P<url>https://doi\.org/[^\)]+)\)\."
)
DOI_FALLBACK = re.compile(r"10\.5281/zenodo\.\d+")


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _hf_repo_id() -> str:
    if get_settings is not None:
        return get_settings().HF_REPO_ID
    return "edithatogo/corpus-nz-hathi"


def _track_summary(text: str) -> dict[str, Any]:
    summary = {"complete": 0, "in_progress": 0, "pending": 0, "titles": []}
    for line in text.splitlines():
        match = TRACK_LINE.match(line)
        if not match:
            continue
        status = match.group("status")
        title = match.group("title")
        summary["titles"].append(title)
        if status == "x":
            summary["complete"] += 1
        elif status == "~":
            summary["in_progress"] += 1
        else:
            summary["pending"] += 1
    summary["total"] = summary["complete"] + summary["in_progress"] + summary["pending"]
    summary["all_complete"] = summary["in_progress"] == 0 and summary["pending"] == 0
    return summary


def _dataset_card_doi(text: str) -> dict[str, str] | None:
    for line in text.splitlines():
        match = DOI_LINE.search(line)
        if match:
            return {"doi": match.group("doi"), "url": match.group("url")}
    fallback = DOI_FALLBACK.search(text)
    if fallback:
        doi = fallback.group(0)
        return {"doi": doi, "url": f"https://doi.org/{doi}"}
    return None


def _doi_resolves(doi_url: str) -> dict[str, Any]:
    try:
        response = requests.get(doi_url, timeout=30, allow_redirects=True)
    except requests.RequestException as exc:
        return {"resolves": False, "error": str(exc)}
    return {
        "resolves": response.ok and bool(response.url),
        "status_code": response.status_code,
        "final_url": response.url,
        "redirects": len(response.history),
    }


def _check_hugging_face(repo_id: str) -> dict[str, Any]:
    try:
        response = requests.get(
            f"https://huggingface.co/api/datasets/{repo_id}",
            timeout=30,
        )
    except requests.RequestException as exc:
        return {"repo_id": repo_id, "exists": False, "error": str(exc)}

    exists = response.ok
    payload: dict[str, Any] = {
        "repo_id": repo_id,
        "exists": exists,
        "status_code": response.status_code,
    }
    if exists:
        data = response.json()
        if isinstance(data, dict):
            payload["id"] = data.get("id")
            payload["sha"] = data.get("sha")
            payload["created_at"] = data.get("createdAt")
            payload["last_modified"] = data.get("lastModified")
    return payload


def _check_zenodo(query: str = "corpus-nz-hathi") -> dict[str, Any]:
    try:
        response = requests.get(
            "https://zenodo.org/api/records",
            params={"q": query, "size": 25},
            timeout=30,
        )
    except requests.RequestException as exc:
        return {"query": query, "match_count": 0, "matches": [], "error": str(exc)}

    response.raise_for_status()
    data = response.json()
    hits = data.get("hits", {}).get("hits", []) if isinstance(data, dict) else []
    matches: list[dict[str, Any]] = []
    for hit in hits:
        if not isinstance(hit, dict):
            continue
        title = str(hit.get("title") or hit.get("metadata", {}).get("title") or "")
        description = str(hit.get("metadata", {}).get("description") or "")
        if query.lower() in title.lower() or query.lower() in description.lower():
            matches.append(
                {
                    "title": title,
                    "doi": hit.get("doi"),
                    "status": hit.get("status"),
                    "created": hit.get("created"),
                    "updated": hit.get("updated"),
                }
            )
    return {"query": query, "match_count": len(matches), "matches": matches}


def check_publication_status() -> dict[str, Any]:
    tracks = _track_summary(_text(TRACKS_PATH))
    hugging_face = _check_hugging_face(_hf_repo_id())
    zenodo = _check_zenodo()
    dataset_card = _text(DATASET_CARD_PATH)
    card_doi = _dataset_card_doi(dataset_card)
    doi_status = _doi_resolves(card_doi["url"]) if card_doi is not None else None
    publication_ready = bool(
        hugging_face.get("exists")
        and card_doi is not None
        and doi_status is not None
        and doi_status.get("resolves")
    )
    ready = publication_ready
    return {
        "tracks": tracks,
        "hugging_face": hugging_face,
        "zenodo": zenodo,
        "dataset_card_doi": card_doi,
        "doi_status": doi_status,
        "roadmap_complete": tracks["all_complete"],
        "publication_ready": publication_ready,
        "ready": ready,
    }


def parse_args(args: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Report roadmap and publication status.")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit nonzero when the publication is not ready for release gating.",
    )
    return parser.parse_args(args)


def main(args: list[str] | None = None) -> int:
    ns = parse_args(args)
    report = check_publication_status()
    print(json.dumps(report, indent=2))
    if ns.strict and not report["ready"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
