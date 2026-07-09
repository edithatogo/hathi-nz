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
MANIFEST_PATH = ROOT / "manifests" / "latest_manifest.json"
STATUS_REPORT_PATH = ROOT / "reports" / "status" / "status_report.json"
PUBLICATION_EVIDENCE_PATH = ROOT / "reports" / "publication_evidence" / "publication_evidence.json"
BLOCKER_REPORT_PATH = ROOT / "reports" / "blockers" / "blocker_report.json"

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
EXPECTED_VOLUMES_LINE = re.compile(r"\*\*Expected volumes\*\*\s*\|\s*(?P<count>\d+)")


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


def _dataset_card_expected_volumes(text: str) -> int | None:
    match = EXPECTED_VOLUMES_LINE.search(text)
    if match:
        return int(match.group("count"))
    return None


def _manifest_summary(text: str) -> dict[str, Any]:
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        return {"exists": False, "error": str(exc), "record_count": 0}
    meta = data.get("meta") if isinstance(data, dict) else {}
    volumes = data.get("volumes") if isinstance(data, dict) else []
    record_count = 0
    if isinstance(meta, dict) and isinstance(meta.get("record_count"), int):
        record_count = meta["record_count"]
    elif isinstance(volumes, list):
        record_count = len(volumes)
    return {
        "exists": True,
        "record_count": record_count,
        "generated_at": meta.get("generated_at") if isinstance(meta, dict) else None,
        "source": meta.get("source") if isinstance(meta, dict) else None,
    }


def _status_report_summary(text: str) -> dict[str, Any]:
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        return {"exists": False, "error": str(exc), "track_count": 0, "roadmap_complete": False}
    if not isinstance(data, dict):
        return {"exists": False, "error": "status report is not an object", "track_count": 0, "roadmap_complete": False}

    tracks = data.get("tracks", [])
    meta = data.get("meta", {})
    inventory = data.get("inventory", {})
    metadata_refresh = data.get("metadata_refresh", {})
    internet_archive = data.get("internet_archive", {})
    track_count = len(tracks) if isinstance(tracks, list) else 0
    complete = 0
    in_progress = 0
    pending = 0
    if isinstance(tracks, list):
        for track in tracks:
            if not isinstance(track, dict):
                continue
            status = str(track.get("status") or "").strip().lower()
            if status == "complete":
                complete += 1
            elif status == "in_progress":
                in_progress += 1
            else:
                pending += 1

    meta_record_count = meta.get("record_count", 0) if isinstance(meta, dict) else 0
    meta_generated_at = meta.get("generated_at") if isinstance(meta, dict) else None
    meta_hf_collection = meta.get("hf_collection") if isinstance(meta, dict) else None
    return {
        "exists": True,
        "generated_at": meta_generated_at,
        "hf_collection": meta_hf_collection,
        "record_count": meta_record_count,
        "track_count": track_count,
        "complete_track_count": complete,
        "in_progress_track_count": in_progress,
        "pending_track_count": pending,
        "roadmap_complete": in_progress == 0 and pending == 0,
        "inventory_record_count": inventory.get("record_count", 0) if isinstance(inventory, dict) else 0,
        "metadata_refresh_present": bool(metadata_refresh.get("present")) if isinstance(metadata_refresh, dict) else False,
        "internet_archive_present": bool(internet_archive.get("present")) if isinstance(internet_archive, dict) else False,
    }


def _publication_evidence_summary(text: str) -> dict[str, Any]:
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        return {"exists": False, "error": str(exc), "child_dataset_count": 0}
    if not isinstance(data, dict):
        return {"exists": False, "error": "publication evidence is not an object", "child_dataset_count": 0}
    child_datasets = data.get("child_datasets", [])
    child_dataset_count = len(child_datasets) if isinstance(child_datasets, list) else 0
    evidence_states = []
    if isinstance(child_datasets, list):
        for dataset in child_datasets:
            if not isinstance(dataset, dict):
                continue
            evidence_states.append(
                {
                    "dataset_id": dataset.get("dataset_id", ""),
                    "publication_state": dataset.get("publication_state", ""),
                    "route_evidence_count": len(dataset.get("route_evidence", []))
                    if isinstance(dataset.get("route_evidence", []), list)
                    else 0,
                    "blocked_route_count": len(dataset.get("blocked_routes", []))
                    if isinstance(dataset.get("blocked_routes", []), list)
                    else 0,
                }
            )
    meta = data.get("meta", {}) if isinstance(data.get("meta", {}), dict) else {}
    return {
        "exists": True,
        "generated_at": meta.get("generated_at"),
        "hf_collection": meta.get("hf_collection"),
        "record_count": meta.get("record_count", 0),
        "child_dataset_count": child_dataset_count,
        "evidence_states": evidence_states,
    }


def _blocker_report_summary(text: str) -> dict[str, Any]:
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        return {"exists": False, "error": str(exc), "blocker_count": 0}
    if not isinstance(data, dict):
        return {"exists": False, "error": "blocker report is not an object", "blocker_count": 0}
    blockers = data.get("blockers", [])
    blocker_groups = data.get("blocker_groups", {})
    required_access = data.get("required_access", [])
    blocker_count = len(blockers) if isinstance(blockers, list) else 0
    group_count = len(blocker_groups) if isinstance(blocker_groups, dict) else 0
    required_access_count = len(required_access) if isinstance(required_access, list) else 0
    meta = data.get("meta", {}) if isinstance(data.get("meta", {}), dict) else {}
    return {
        "exists": True,
        "generated_at": meta.get("generated_at"),
        "track_count": meta.get("track_count", 0),
        "blocker_count": blocker_count,
        "group_count": group_count,
        "required_access_count": required_access_count,
    }


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
            payload["used_storage"] = data.get("usedStorage")
            siblings = data.get("siblings")
            if isinstance(siblings, list):
                payload["sibling_count"] = len(siblings)
                payload["data_file_count"] = sum(
                    1
                    for sibling in siblings
                    if isinstance(sibling, dict)
                    and str(sibling.get("rfilename") or "").strip() != ".gitattributes"
                )
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


def check_publication_status(
    *,
    status_report_path: Path | None = None,
    publication_evidence_path: Path | None = None,
    blocker_report_path: Path | None = None,
) -> dict[str, Any]:
    tracks = _track_summary(_text(TRACKS_PATH))
    hugging_face = _check_hugging_face(_hf_repo_id())
    zenodo = _check_zenodo()
    dataset_card = _text(DATASET_CARD_PATH)
    manifest = _manifest_summary(_text(MANIFEST_PATH)) if MANIFEST_PATH.exists() else {"exists": False, "record_count": 0}
    status_report_file = status_report_path or STATUS_REPORT_PATH
    status_report = _status_report_summary(_text(status_report_file)) if status_report_file.exists() else {"exists": False, "track_count": 0, "roadmap_complete": False}
    publication_evidence_file = publication_evidence_path or PUBLICATION_EVIDENCE_PATH
    publication_evidence = (
        _publication_evidence_summary(_text(publication_evidence_file))
        if publication_evidence_file.exists()
        else {"exists": False, "child_dataset_count": 0, "evidence_states": []}
    )
    blocker_report_file = blocker_report_path or BLOCKER_REPORT_PATH
    blocker_report = (
        _blocker_report_summary(_text(blocker_report_file))
        if blocker_report_file.exists()
        else {"exists": False, "blocker_count": 0}
    )
    expected_volumes = _dataset_card_expected_volumes(dataset_card)
    card_doi = _dataset_card_doi(dataset_card)
    doi_status = _doi_resolves(card_doi["url"]) if card_doi is not None else None
    hf_has_files = hugging_face.get("data_file_count", 0) > 0
    manifest_complete = bool(manifest.get("record_count", 0))
    if expected_volumes is not None:
        manifest_complete = manifest_complete and manifest.get("record_count") == expected_volumes
    evidence_complete = True
    if publication_evidence.get("exists"):
        evidence_complete = publication_evidence.get("child_dataset_count", 0) >= 5
    blockers_complete = bool(blocker_report.get("exists")) and blocker_report.get("blocker_count", 0) == 0
    publication_ready = bool(
        hugging_face.get("exists")
        and hf_has_files
        and card_doi is not None
        and doi_status is not None
        and doi_status.get("resolves")
        and manifest_complete
        and evidence_complete
        and blockers_complete
    )
    roadmap_complete = status_report["roadmap_complete"] if status_report.get("exists") else tracks["all_complete"]
    ready = publication_ready and roadmap_complete
    return {
        "tracks": tracks,
        "hugging_face": hugging_face,
        "zenodo": zenodo,
        "manifest": manifest,
        "status_report": status_report,
        "publication_evidence": publication_evidence,
        "blocker_report": blocker_report,
        "expected_volumes": expected_volumes,
        "dataset_card_doi": card_doi,
        "doi_status": doi_status,
        "roadmap_complete": roadmap_complete,
        "publication_ready": publication_ready,
        "ready": ready,
    }


def parse_args(args: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Report roadmap and publication status.")
    parser.add_argument(
        "--status-report",
        type=Path,
        default=STATUS_REPORT_PATH,
        help="Optional path to the generated status_report.json snapshot.",
    )
    parser.add_argument(
        "--publication-evidence",
        type=Path,
        default=PUBLICATION_EVIDENCE_PATH,
        help="Optional path to the generated publication_evidence.json snapshot.",
    )
    parser.add_argument(
        "--blocker-report",
        type=Path,
        default=BLOCKER_REPORT_PATH,
        help="Optional path to the generated blocker_report.json snapshot.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit nonzero when the publication is not ready for release gating.",
    )
    return parser.parse_args(args)


def main(args: list[str] | None = None) -> int:
    ns = parse_args(args)
    report = check_publication_status(
        status_report_path=ns.status_report,
        publication_evidence_path=ns.publication_evidence,
        blocker_report_path=ns.blocker_report,
    )
    print(json.dumps(report, indent=2))
    if ns.strict and not report["ready"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
