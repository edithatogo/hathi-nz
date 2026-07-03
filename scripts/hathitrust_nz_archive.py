"""Build source-specific HathiTrust-NZ archive manifests.

This module keeps the collection-level archive rules separate from the legacy
single-dataset sync path. The defaults are intentionally fail-closed: metadata
and derived manifests are publishable, but full text is only routed to public
archives when rights and source-dataset constraints are explicit.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import re
import sys
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import requests

from scripts.logging_utils import configure_logging

try:
    from _version import get_version
except ImportError:  # pragma: no cover

    def get_version() -> str:
        return "0.0.0"


HATHITRUST_NZ_COLLECTION_ID = "71329709"
HATHITRUST_NZ_COLLECTION_SLUG = "nz_parliamentary_debates_hansard"
HATHITRUST_NZ_EXPECTED_COUNT = 510
HATHITRUST_NZ_CATALOG_RECORD = "007119315"
HUGGING_FACE_COLLECTION = "edithatogo/hathitrust-nz"
PARLIAMENTARY_DEBATES_TITLE_PREFIX = "Parliamentary debates"

HF_COMPAT_DATASET_REPO = "edithatogo/corpus-nz-hathi"
HF_INVENTORY_REPO = "edithatogo/hathitrust-nz-inventory"
HF_RESEARCH_FULLTEXT_REPO = "edithatogo/hathitrust-nz-research-fulltext"
HF_HTRC_EF_REPO = "edithatogo/hathitrust-nz-htrc-extracted-features"
HF_HTRC_ANALYTICS_REPO = "edithatogo/hathitrust-nz-htrc-analytics"

HTRC_EF_VERSION = "2.5"
HTRC_EF_RSYNC_MODULE = "data.analytics.hathitrust.org::features-2025.04/"
INTERNET_ARCHIVE_SEARCH_URL = "https://archive.org/advancedsearch.php"
INTERNET_ARCHIVE_METADATA_URL = "https://archive.org/metadata/{identifier}"
INTERNET_ARCHIVE_DOWNLOAD_URL = "https://archive.org/download/{identifier}/{filename}"
HATHIFILE_LIST_URL = "https://www.hathitrust.org/files/hathifiles/hathi_file_list.json"
HATHI_BIBLIOGRAPHIC_API_URL = "https://share.hathitrust.org/api/volume/{htid}/json"
HATHI_OAI_FEED_URL = "https://www.hathitrust.org/member-libraries/resources-for-librarians/data-resources/oai-feed/"
HATHI_RESEARCH_PD_OPEN_ACCESS = "ht_text_pd_open_access"
HATHI_RESEARCH_PD_WORLD_OPEN_ACCESS = "ht_text_pd_world_open_access"
HATHI_RESEARCH_PD_WITH_GOOGLE = "ht_text_pd"
HATHI_RESEARCH_PD_WORLD_WITH_GOOGLE = "ht_text_pd_world"
HANSARD_TITLE_PREFIX = "Parliamentary debates (Hansard)"
PARLIAMENTARY_DEBATES_TITLE_PREFIX = "Parliamentary debates"

RIGHTS_LABELS = {
    "1": "pd",
    "2": "ic",
    "3": "opb",
    "4": "orph",
    "5": "und",
    "7": "ic-world",
    "9": "pdus",
    "10": "cc-by-nc-nd",
    "11": "cc-by-nc",
    "12": "cc-by-nc-sa",
    "13": "cc-by-nd",
    "14": "cc-by",
    "15": "cc-by-sa",
    "16": "orphcand",
    "17": "cc-zero",
    "18": "und-world",
    "19": "icus",
    "20": "cc-by-4.0",
    "21": "cc-by-sa-4.0",
    "22": "cc-by-nd-4.0",
    "23": "cc-by-nc-4.0",
    "24": "cc-by-nc-sa-4.0",
    "25": "cc-by-nc-nd-4.0",
    "26": "cc-zero-1.0",
    "27": "supp",
    "pd": "pd",
    "cc-zero": "cc-zero",
    "cc-zero-1.0": "cc-zero-1.0",
    "cc-by": "cc-by",
    "cc-by-4.0": "cc-by-4.0",
    "cc-by-sa": "cc-by-sa",
    "cc-by-sa-4.0": "cc-by-sa-4.0",
    "pdus": "pdus",
    "ic": "ic",
    "ic-world": "ic-world",
    "icus": "icus",
    "und": "und",
    "undetermined": "und",
    "supp": "supp",
    "suppressed": "supp",
}

FULL_TEXT_REHOSTABLE_RIGHTS = {
    "pd",
    "cc-zero",
    "cc-zero-1.0",
    "cc-by",
    "cc-by-4.0",
    "cc-by-sa",
    "cc-by-sa-4.0",
}
RESTRICTED_RIGHTS = {
    "ic",
    "ic-world",
    "icus",
    "pdus",
    "und",
    "supp",
    "opb",
    "orph",
    "orphcand",
    "und-world",
}
GOOGLE_RESTRICTED_DATASETS = {
    HATHI_RESEARCH_PD_WITH_GOOGLE,
    HATHI_RESEARCH_PD_WORLD_WITH_GOOGLE,
}
STATIC_RSYNC_DATASETS = {
    HATHI_RESEARCH_PD_OPEN_ACCESS,
    HATHI_RESEARCH_PD_WORLD_OPEN_ACCESS,
    HATHI_RESEARCH_PD_WITH_GOOGLE,
    HATHI_RESEARCH_PD_WORLD_WITH_GOOGLE,
}
INTERNET_ARCHIVE_TEXT_SUFFIXES = (
    "_djvu.txt",
    "_hocr_searchtext.txt.gz",
    "_djvu.xml",
)
SOURCE_POLICY_REGISTRY = {
    "hathitrust_research_dataset": {
        "display_name": "HathiTrust Research Dataset",
        "source_url": "https://www.hathitrust.org/member-libraries/resources-for-librarians/data-resources/research-datasets/",
        "permitted_artifacts": [
            "metadata",
            "manifests",
            "full_text",
            "ocr_text",
        ],
        "access_class": "approved_static_host",
        "default_acquisition_mode": "static_host_rsync",
        "publication_eligibility": {
            "hugging_face": "metadata_only_until_static_host_bundle_is_eligible",
            "zenodo": "metadata_only_until_static_host_bundle_is_eligible",
        },
        "source_priority": 10,
    },
    "hathifiles": {
        "display_name": "Hathifiles",
        "source_url": "https://www.hathitrust.org/member-libraries/resources-for-librarians/data-resources/hathifiles/",
        "permitted_artifacts": ["metadata", "manifests"],
        "access_class": "public_with_rate_limits",
        "default_acquisition_mode": "github_actions",
        "publication_eligibility": {
            "hugging_face": "public_metadata",
            "zenodo": "public_metadata",
        },
        "source_priority": 90,
    },
    "hathitrust_oai_pmh": {
        "display_name": "HathiTrust OAI-PMH",
        "source_url": "https://www.hathitrust.org/member-libraries/resources-for-librarians/data-resources/oai-feed/",
        "permitted_artifacts": ["metadata", "manifests"],
        "access_class": "public_with_rate_limits",
        "default_acquisition_mode": "github_actions",
        "publication_eligibility": {
            "hugging_face": "public_metadata",
            "zenodo": "public_metadata",
        },
        "source_priority": 80,
    },
    "hathitrust_bibliographic_api": {
        "display_name": "HathiTrust Bibliographic API",
        "source_url": "https://www.hathitrust.org/member-libraries/resources-for-librarians/data-resources/bibliographic-api/",
        "permitted_artifacts": ["metadata", "manifests"],
        "access_class": "public_with_rate_limits",
        "default_acquisition_mode": "github_actions",
        "publication_eligibility": {
            "hugging_face": "public_metadata",
            "zenodo": "public_metadata",
        },
        "source_priority": 85,
    },
    "htrc_solr_ef20": {
        "display_name": "HTRC Solr EF20",
        "source_url": "https://solr2.htrc.illinois.edu/solr-ef20/",
        "permitted_artifacts": ["metadata", "manifests", "derived_features"],
        "access_class": "public_with_rate_limits",
        "default_acquisition_mode": "github_actions",
        "publication_eligibility": {
            "hugging_face": "public_derived_features",
            "zenodo": "public_derived_features",
        },
        "source_priority": 70,
    },
    "htrc_extracted_features": {
        "display_name": "HTRC Extracted Features",
        "source_url": "https://htrc.atlassian.net/wiki/spaces/COM/pages/43295914/Extracted+Features+v.2.0",
        "permitted_artifacts": ["metadata", "manifests", "derived_features"],
        "access_class": "public_derived_features",
        "default_acquisition_mode": "github_actions",
        "publication_eligibility": {
            "hugging_face": "public_derived_features",
            "zenodo": "public_derived_features",
        },
        "source_priority": 60,
    },
    "htrc_analytics": {
        "display_name": "HTRC Analytics",
        "source_url": "https://analytics.hathitrust.org/",
        "permitted_artifacts": ["scripts", "aggregates", "reproducibility_metadata"],
        "access_class": "public_analytics_only",
        "default_acquisition_mode": "github_actions",
        "publication_eligibility": {
            "hugging_face": "public_scripts_aggregates_and_reproducibility_metadata",
            "zenodo": "public_scripts_aggregates_and_reproducibility_metadata",
        },
        "source_priority": 55,
    },
    "internet_archive": {
        "display_name": "Internet Archive",
        "source_url": "https://archive.org/",
        "permitted_artifacts": ["metadata", "manifests", "full_text", "ocr_text"],
        "access_class": "public_domain_overlap_only",
        "default_acquisition_mode": "github_actions",
        "publication_eligibility": {
            "hugging_face": "public_domain_overlap_only",
            "zenodo": "public_domain_overlap_only",
        },
        "source_priority": 65,
    },
    "open_library": {
        "display_name": "Open Library",
        "source_url": "https://openlibrary.org/",
        "permitted_artifacts": ["metadata", "manifests"],
        "access_class": "public_metadata",
        "default_acquisition_mode": "github_actions",
        "publication_eligibility": {
            "hugging_face": "public_metadata",
            "zenodo": "public_metadata",
        },
        "source_priority": 64,
    },
    "digitalnz": {
        "display_name": "DigitalNZ",
        "source_url": "https://digitalnz.org/",
        "permitted_artifacts": ["metadata", "manifests"],
        "access_class": "public_metadata",
        "default_acquisition_mode": "github_actions",
        "publication_eligibility": {
            "hugging_face": "public_metadata",
            "zenodo": "public_metadata",
        },
        "source_priority": 50,
    },
    "national_library_nz": {
        "display_name": "National Library NZ",
        "source_url": "https://natlib.govt.nz/",
        "permitted_artifacts": ["metadata", "manifests"],
        "access_class": "public_metadata",
        "default_acquisition_mode": "github_actions",
        "publication_eligibility": {
            "hugging_face": "public_metadata",
            "zenodo": "public_metadata",
        },
        "source_priority": 50,
    },
    "papers_past": {
        "display_name": "Papers Past",
        "source_url": "https://paperspast.natlib.govt.nz/",
        "permitted_artifacts": ["metadata", "manifests"],
        "access_class": "public_metadata",
        "default_acquisition_mode": "github_actions",
        "publication_eligibility": {
            "hugging_face": "public_metadata",
            "zenodo": "public_metadata",
        },
        "source_priority": 50,
    },
    "official_parliamentary_sources": {
        "display_name": "Official parliamentary sources",
        "source_url": "https://www.parliament.nz/",
        "permitted_artifacts": ["metadata", "manifests"],
        "access_class": "public_metadata",
        "default_acquisition_mode": "github_actions",
        "publication_eligibility": {
            "hugging_face": "public_metadata",
            "zenodo": "public_metadata",
        },
        "source_priority": 95,
    },
    "manual_evidence": {
        "display_name": "Manual evidence",
        "source_url": "",
        "permitted_artifacts": ["metadata", "manifests"],
        "access_class": "manual_review_only",
        "default_acquisition_mode": "manual",
        "publication_eligibility": {
            "hugging_face": "manual_review_only",
            "zenodo": "manual_review_only",
        },
        "source_priority": 5,
    },
}
INTERNET_ARCHIVE_SEARCH_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Codex HathiTrust-NZ archive planner)",
    "Accept": "application/json,text/plain,*/*",
}


def utc_now() -> str:
    """Return an ISO-8601 timestamp in UTC."""
    return datetime.now(UTC).isoformat()


def canonical_rights_label(rights_code: str | int | None) -> str:
    """Normalize a HathiTrust rights code or label."""
    value = "" if rights_code is None else str(rights_code).strip().lower()
    if not value:
        return "und"
    return RIGHTS_LABELS.get(value, value)


def source_policy_registry() -> dict[str, dict[str, Any]]:
    """Return a copy of the source policy registry."""
    return json.loads(json.dumps(SOURCE_POLICY_REGISTRY))


def source_policy_entry(source_id: str) -> dict[str, Any]:
    """Return one source policy entry or raise if it is unknown."""
    try:
        return source_policy_registry()[source_id]
    except KeyError as exc:  # pragma: no cover - defensive
        msg = f"Unknown source policy entry: {source_id}"
        raise KeyError(msg) from exc


def source_priority(source_id: str) -> int:
    """Return the routing priority for a source."""
    return int(source_policy_entry(source_id)["source_priority"])


def clean_htrc_htid(htid: str) -> str:
    """Return the HTRC Extracted Features-safe HTID filename stem."""
    return htid.strip().replace(":", "+").replace("/", "=")


def htrc_stubbytree_path(htid: str) -> str:
    """Return the HTRC EF 2.5 rsync path for an HTID.

    HTRC stores files under a namespace directory and a stubbytree shard made
    from every third character of the cleaned identifier suffix.
    """
    clean = clean_htrc_htid(htid)
    namespace, separator, suffix = clean.partition(".")
    if not separator or not namespace or not suffix:
        msg = f"HTID does not include a namespace separator: {htid!r}"
        raise ValueError(msg)
    shard = suffix[0::3]
    if not shard:
        msg = f"HTID does not include a usable suffix: {htid!r}"
        raise ValueError(msg)
    return f"{namespace}/{shard}/{clean}.json.bz2"


def parse_volume_label(title: str) -> tuple[int | None, str | None]:
    """Extract a sortable volume number and enumeration label from a title."""
    number: int | None = None
    label: str | None = None
    if not title:
        pass
    else:
        volume_match = re.search(r"\bv\.(\d+[A-Za-z]?)\b", title, flags=re.IGNORECASE)
        if volume_match:
            number_text = volume_match.group(1)
            number_match = re.match(r"\d+", number_text)
            number = int(number_match.group(0)) if number_match else None
            label = f"v.{number_text}"
        else:
            year_part_match = re.search(r"\b(18\d{2}|19\d{2})(?::(\d+))\b", title)
            if year_part_match:
                year = int(year_part_match.group(1))
                part = year_part_match.group(2)
                label = f"{year}:{part}"
            else:
                year_range_match = re.search(r"\b(18\d{2}|19\d{2})-(\d{2})\b", title)
                if year_range_match:
                    start = year_range_match.group(1)
                    end = year_range_match.group(2)
                    label = f"{start}-{end}"
                elif title.startswith(HANSARD_TITLE_PREFIX):
                    label = title[len(HANSARD_TITLE_PREFIX) :].strip(" -")
                elif title.startswith(PARLIAMENTARY_DEBATES_TITLE_PREFIX):
                    suffix = title[len(PARLIAMENTARY_DEBATES_TITLE_PREFIX) :].strip(" -")
                    if suffix and not (suffix.startswith("(") and suffix.endswith(")")):
                        label = suffix
    if label == "":
        label = None
    return number, label


def classify_publication_policy(
    rights_code: str | int | None,
    *,
    access_profile_code: str | None = None,
    digitization_agent_code: str | None = None,
    source_dataset_name: str | None = None,
    signed_google_agreement: bool = False,
) -> dict[str, Any]:
    """Classify public archive eligibility for one source record.

    Metadata and generated manifests remain publishable unless the caller later
    adds a stronger privacy flag. Full-text publication requires rehostable
    rights and must not pass through Google-restricted or page-only routes.
    """
    rights_label = canonical_rights_label(rights_code)
    source_name = (source_dataset_name or "").strip()
    source_name_lower = source_name.lower()
    access_profile = (access_profile_code or "").strip().lower()
    digitization_agent = (digitization_agent_code or "").strip().lower()

    reasons: list[str] = []
    requires_static_host = source_name_lower in STATIC_RSYNC_DATASETS
    google_restricted_source = source_name_lower in GOOGLE_RESTRICTED_DATASETS
    google_profile = "google" in access_profile or digitization_agent == "google"
    page_only_profile = "page" in access_profile

    if rights_label in RESTRICTED_RIGHTS:
        reasons.append(f"rights:{rights_label}")
    elif rights_label not in FULL_TEXT_REHOSTABLE_RIGHTS:
        reasons.append(f"rights-unmapped:{rights_label}")

    if google_restricted_source:
        reasons.append(f"source-dataset:{source_name}")
    if google_profile and not signed_google_agreement:
        reasons.append("google-digitized")
    if page_only_profile:
        reasons.append(f"access-profile:{access_profile}")

    public_full_text_allowed = not reasons
    if google_restricted_source:
        public_full_text_allowed = False

    if public_full_text_allowed:
        access_class = "public_full_text"
    elif rights_label in FULL_TEXT_REHOSTABLE_RIGHTS:
        access_class = "metadata_only_pending_source_permission"
    else:
        access_class = "metadata_only_restricted"

    return {
        "rights_label": rights_label,
        "access_class": access_class,
        "public_metadata_allowed": True,
        "public_full_text_allowed": public_full_text_allowed,
        "public_derived_allowed": True,
        "requires_static_host": requires_static_host,
        "requires_google_agreement": google_restricted_source or google_profile,
        "restriction_reason": ";".join(reasons) if reasons else "",
    }


def catalog_record_id(catalog_url: str) -> str:
    """Extract the catalog record ID from a HathiTrust catalog URL."""
    if not catalog_url:
        return ""
    return catalog_url.rstrip("/").rsplit("/", maxsplit=1)[-1]


def normalize_collection_export_row(
    row: dict[str, str],
    *,
    collection_id: str = HATHITRUST_NZ_COLLECTION_ID,
    collection_slug: str = HATHITRUST_NZ_COLLECTION_SLUG,
) -> dict[str, Any]:
    """Normalize a row from the HathiTrust collection export TSV."""
    htid = row.get("htitem_id", "").strip()
    title = row.get("title", "").strip()
    rights_code = row.get("rights", "").strip()
    source = htid.partition(".")[0]
    volume_number, enumeration = parse_volume_label(title)
    policy = classify_publication_policy(
        rights_code,
        source_dataset_name=HATHI_RESEARCH_PD_WORLD_OPEN_ACCESS,
    )
    clean_htid = clean_htrc_htid(htid)

    return {
        "dataset_id": collection_slug,
        "collection_id": collection_id,
        "collection_slug": collection_slug,
        "htid": htid,
        "htrc_clean_htid": clean_htid,
        "htrc_ef25_rsync_path": htrc_stubbytree_path(htid),
        "title": title,
        "author": row.get("author", "").strip(),
        "date": row.get("date", "").strip(),
        "volume_number": volume_number,
        "enumeration": enumeration,
        "enumeration_status": "parsed" if (volume_number is not None or enumeration is not None) else "needs_enrichment",
        "rights_code": rights_code,
        "rights_label": policy["rights_label"],
        "oclc": row.get("OCLC", "").strip(),
        "lccn": row.get("LCCN", "").strip(),
        "isbn": row.get("ISBN", "").strip(),
        "catalog_url": row.get("catalog_url", "").strip(),
        "catalog_record_id": catalog_record_id(row.get("catalog_url", "").strip()),
        "handle_url": row.get("handle_url", "").strip(),
        "source": source,
        "source_url": row.get("handle_url", "").strip() or row.get("catalog_url", "").strip(),
        "source_dataset_name": f"HathiTrust Collection {collection_id} export",
        "digitization_agent_code": "",
        "access_profile_code": "open",
        "acquisition_mode": "github_actions_inventory",
        "fulltext_acquisition_mode": "static_host_rsync",
        "htrc_ef_acquisition_mode": "github_actions_rsync_plan",
        "hf_collection": HUGGING_FACE_COLLECTION,
        "hf_dataset_repo": HF_INVENTORY_REPO,
        **policy,
    }


def load_collection_export_tsv(path: Path) -> list[dict[str, Any]]:
    """Load and normalize a HathiTrust collection export TSV."""
    with path.open("r", encoding="utf-8", newline="") as file:
        rows = list(csv.DictReader(file, delimiter="\t"))
    return [normalize_collection_export_row(row) for row in rows]


def summarize_inventory(volumes: list[dict[str, Any]]) -> dict[str, Any]:
    """Return count summaries used by acceptance gates."""
    rights_counts = Counter(str(volume.get("rights_label", "")) for volume in volumes)
    access_counts = Counter(str(volume.get("access_class", "")) for volume in volumes)
    parsed_volume_numbers = sum(1 for volume in volumes if isinstance(volume.get("volume_number"), int))
    parsed_enumerations = sum(1 for volume in volumes if str(volume.get("enumeration") or "").strip())
    parsed_labels = sum(
        1
        for volume in volumes
        if volume.get("enumeration_status") == "parsed"
    )
    needs_enrichment_count = len(volumes) - parsed_labels
    volume_numbers = [
        int(volume["volume_number"])
        for volume in volumes
        if isinstance(volume.get("volume_number"), int)
    ]
    return {
        "record_count": len(volumes),
        "rights_counts": dict(sorted(rights_counts.items())),
        "access_class_counts": dict(sorted(access_counts.items())),
        "label_parse": {
            "parsed": parsed_labels,
            "needs_enrichment": needs_enrichment_count,
        },
        "volume_number_parse": {
            "parsed": parsed_volume_numbers,
            "needs_enrichment": len(volumes) - parsed_volume_numbers,
            "min": min(volume_numbers) if volume_numbers else None,
            "max": max(volume_numbers) if volume_numbers else None,
        },
        "enumeration_parse": {
            "parsed": parsed_enumerations,
            "needs_enrichment": len(volumes) - parsed_enumerations,
        },
    }


def child_datasets() -> list[dict[str, Any]]:
    """Return the collection-level Hugging Face and Zenodo child dataset map."""
    return [
        {
            "dataset_id": "corpus-nz-hathi",
            "hf_repo_id": HF_COMPAT_DATASET_REPO,
            "role": "compatibility_dataset",
            "access_class": "public_full_text_where_confirmed",
            "zenodo_stream": "corpus-nz-hathi",
        },
        {
            "dataset_id": "hathitrust-nz-inventory",
            "hf_repo_id": HF_INVENTORY_REPO,
            "role": "collection_inventory",
            "access_class": "public_metadata",
            "zenodo_stream": "hathitrust-nz-inventory",
        },
        {
            "dataset_id": "hathitrust-nz-research-fulltext",
            "hf_repo_id": HF_RESEARCH_FULLTEXT_REPO,
            "role": "research_dataset_fulltext",
            "access_class": "metadata_only_until_static_host_bundle_is_eligible",
            "zenodo_stream": "hathitrust-nz-research-fulltext",
        },
        {
            "dataset_id": "hathitrust-nz-htrc-extracted-features",
            "hf_repo_id": HF_HTRC_EF_REPO,
            "role": "htrc_extracted_features_2_5_subset",
            "access_class": "public_derived_features",
            "zenodo_stream": "hathitrust-nz-htrc-extracted-features",
        },
        {
            "dataset_id": "hathitrust-nz-htrc-analytics",
            "hf_repo_id": HF_HTRC_ANALYTICS_REPO,
            "role": "htrc_analytics_outputs",
            "access_class": "public_scripts_aggregates_and_reproducibility_metadata",
            "zenodo_stream": "hathitrust-nz-htrc-analytics",
        },
    ]


def source_policy_summary() -> list[dict[str, Any]]:
    """Return the source policy registry as sorted manifest entries."""
    registry = source_policy_registry()
    return [
        {
            "source_id": source_id,
            **registry[source_id],
        }
        for source_id in sorted(registry, key=source_priority, reverse=True)
    ]


def metadata_refresh_record(
    volume: dict[str, Any],
    *,
    lane: str,
    source_id: str,
    refresh_url: str,
    refresh_mode: str,
    cursor_state: str = "",
) -> dict[str, Any]:
    """Build a deterministic metadata refresh record for one lane."""
    policy = classify_publication_policy(
        volume.get("rights_code"),
        access_profile_code=str(volume.get("access_profile_code", "")),
        digitization_agent_code=str(volume.get("digitization_agent_code", "")),
        source_dataset_name=str(volume.get("source_dataset_name", "")) or None,
    )
    source = source_policy_entry(source_id)
    return {
        "htid": volume.get("htid", ""),
        "title": volume.get("title", ""),
        "author": volume.get("author", ""),
        "rights_code": volume.get("rights_code", ""),
        "rights_label": policy["rights_label"],
        "access_class": policy["access_class"],
        "public_full_text_allowed": policy["public_full_text_allowed"],
        "source_lane": lane,
        "source_id": source_id,
        "source_display_name": source["display_name"],
        "source_url": source["source_url"],
        "refresh_url": refresh_url,
        "refresh_mode": refresh_mode,
        "cursor_state": cursor_state,
        "source_priority": source_priority(source_id),
    }


def write_metadata_refresh_plan(
    inventory: dict[str, Any],
    output_dir: Path,
    *,
    limit: int = 0,
    oai_cursor: str = "",
) -> dict[str, Any]:
    """Write metadata refresh manifests for the primary HathiTrust lanes."""
    volumes = list(inventory.get("volumes", []))
    if limit > 0:
        volumes = volumes[:limit]

    output_dir.mkdir(parents=True, exist_ok=True)
    hathifiles: list[dict[str, Any]] = []
    oai_pmh: list[dict[str, Any]] = []
    bibliographic_api: list[dict[str, Any]] = []

    for volume in volumes:
        hathifiles.append(
            metadata_refresh_record(
                volume,
                lane="hathifiles",
                source_id="hathifiles",
                refresh_url=HATHIFILE_LIST_URL,
                refresh_mode="inventory_and_rights_refresh",
            )
        )
        oai_pmh.append(
            metadata_refresh_record(
                volume,
                lane="oai_pmh",
                source_id="hathitrust_oai_pmh",
                refresh_url=HATHI_OAI_FEED_URL,
                refresh_mode="incremental_oai_cursor_refresh",
                cursor_state=oai_cursor,
            )
        )
        bibliographic_api.append(
            metadata_refresh_record(
                volume,
                lane="bibliographic_api",
                source_id="hathitrust_bibliographic_api",
                refresh_url=HATHI_BIBLIOGRAPHIC_API_URL.format(htid=volume.get("htid", "")),
                refresh_mode="known_identifier_enrichment",
            )
        )

    manifest = {
        "meta": {
            "generated_at": utc_now(),
            "source_dataset_name": "HathiTrust metadata refresh lanes",
            "record_count": len(volumes),
            "hf_dataset_repo": HF_INVENTORY_REPO,
            "acquisition_mode": "github_actions_metadata_refresh",
            "source_policy_version": len(source_policy_summary()),
        },
        "source_policy_registry": source_policy_summary(),
        "lanes": {
            "hathifiles": {
                "refresh_url": HATHIFILE_LIST_URL,
                "record_count": len(hathifiles),
                "records": hathifiles,
            },
            "oai_pmh": {
                "refresh_url": HATHI_OAI_FEED_URL,
                "record_count": len(oai_pmh),
                "requested_cursor": oai_cursor,
                "records": oai_pmh,
            },
            "bibliographic_api": {
                "refresh_url": "https://share.hathitrust.org/api/volume/{htid}/json",
                "record_count": len(bibliographic_api),
                "records": bibliographic_api,
            },
        },
    }
    write_json(output_dir / "metadata_refresh_manifest.json", manifest)
    write_json(
        output_dir / "hathifiles_refresh_manifest.json",
        {"meta": manifest["meta"], "records": hathifiles},
    )
    write_json(
        output_dir / "oai_pmh_refresh_manifest.json",
        {"meta": manifest["meta"], "records": oai_pmh},
    )
    write_json(
        output_dir / "bibliographic_api_refresh_manifest.json",
        {"meta": manifest["meta"], "records": bibliographic_api},
    )
    write_lines(
        output_dir / "metadata_refresh_report.md",
        [
            "# HathiTrust-NZ Metadata Refresh Plan",
            "",
            f"- Seed record count: `{len(volumes)}`.",
            f"- Hathifiles refresh records: `{len(hathifiles)}`.",
            f"- OAI-PMH refresh records: `{len(oai_pmh)}`.",
            f"- Bibliographic API refresh records: `{len(bibliographic_api)}`.",
            "- Hathifiles refreshes inventory and rights metadata.",
            "- OAI-PMH refreshes incremental catalog metadata using cursor state.",
            "- Bibliographic API refreshes known HTID enrichment for catalog normalization.",
        ],
    )
    return manifest


def discovery_families() -> list[dict[str, Any]]:
    """Return the broader NZ discovery families tracked for future expansion."""
    return [
        {
            "family_id": "parliamentary_and_legal",
            "title": "Parliamentary and legal serials",
            "status": "active_discovery",
            "public_archive_status": "mixed",
            "public_sources": [
                "Parliamentary Debates / Hansard",
                "Gazettes",
                "Statutes, Acts, and Ordinances",
            ],
            "restricted_sources": [
                "Records with page-only, suppressed, or Google-restricted access profiles",
            ],
            "source_inputs": [
                "HathiTrust collection exports",
                "Hathifiles",
                "HathiTrust Bibliographic API",
                "HathiTrust OAI feed",
                "HathiTrust catalog records",
                "HathiTrust Research Center extracted features 2.0/2.5",
            ],
            "acquisition_modes": [
                "github_actions_inventory",
                "github_actions_public_metadata_publish",
                "github_actions_derived_features",
                "static_host_rsync_for_restricted_research_datasets",
            ],
        },
        {
            "family_id": "government_and_policy",
            "title": "Government and policy serials",
            "status": "active_discovery",
            "public_archive_status": "mixed",
            "public_sources": [
                "Departmental reports",
                "Official statistics",
                "Commission reports",
                "Public works and education reports",
            ],
            "restricted_sources": [
                "Records with privacy-limited, suppressed, or Google-restricted profiles",
            ],
            "source_inputs": [
                "Hathifiles",
                "HathiTrust public collections",
                "HathiTrust Bibliographic API",
                "HathiTrust OAI feed",
                "Catalog record crosswalks",
                "Internet Archive public-domain overlap where provenance is explicit",
            ],
            "acquisition_modes": [
                "github_actions_inventory",
                "github_actions_public_metadata_publish",
                "github_actions_incremental_metadata_sync",
                "static_host_rsync_for_restricted_research_datasets",
            ],
        },
        {
            "family_id": "scholarly_and_cultural",
            "title": "NZ scholarly and cultural serials",
            "status": "active_discovery",
            "public_archive_status": "mixed",
            "public_sources": [
                "Journal and proceedings material with public rights",
                "Public-domain scholarly serials",
            ],
            "restricted_sources": [
                "Google-restricted or page-only serials",
            ],
            "source_inputs": [
                "Hathifiles",
                "HathiTrust catalog records",
                "Public collections",
                "HathiTrust Bibliographic API",
                "HathiTrust OAI feed",
                "HathiTrust Research Center extracted features 2.0/2.5",
            ],
            "acquisition_modes": [
                "github_actions_inventory",
                "github_actions_public_metadata_publish",
                "github_actions_derived_features",
                "static_host_rsync_for_restricted_research_datasets",
            ],
        },
        {
            "family_id": "maori_and_aotearoa",
            "title": "Māori / Aotearoa materials",
            "status": "active_discovery",
            "public_archive_status": "mixed",
            "public_sources": [
                "Public-domain dictionaries, histories, grammars, and missionary-era publications",
                "Public-domain newspapers and pamphlets",
            ],
            "restricted_sources": [
                "Privacy-limited, suppressed, or otherwise non-rehostable records",
            ],
            "source_inputs": [
                "Hathifiles",
                "HathiTrust catalog records",
                "HathiTrust Bibliographic API",
                "HathiTrust OAI feed",
                "HTRC Workset Builder and extracted features search",
                "HathiTrust Research Center Extracted Features v.2.0",
            ],
            "acquisition_modes": [
                "github_actions_inventory",
                "github_actions_public_metadata_publish",
                "github_actions_derived_features",
                "static_host_rsync_for_restricted_research_datasets",
            ],
        },
    ]


def build_discovery_manifest(inventory: dict[str, Any]) -> dict[str, Any]:
    """Build a broader NZ discovery manifest for future collection growth."""
    return {
        "meta": {
            "generated_at": utc_now(),
            "pipeline_version": get_version(),
            "collection_id": "hathitrust-nz",
            "hf_collection": HUGGING_FACE_COLLECTION,
            "seed_collection_id": inventory.get("meta", {}).get("collection_id"),
            "seed_record_count": inventory.get("meta", {}).get("record_count", 0),
        },
        "source_families": discovery_families(),
        "seed_summary": inventory.get("summary", {}),
        "discovery_notes": [
            "The seed Hansard set is the canonical entry point, but discovery extends to additional NZ source families.",
            "Internet Archive public-domain overlap is the interim full-text path until HathiTrust rsync access is available.",
            "Public metadata and manifests are GitHub-Actions-friendly; restricted full text remains static-host only until permission is explicit.",
            "HTRC derived features remain publication-safe as derived data, while raw full text follows HathiTrust redistribution rules.",
        ],
    }


def write_discovery_report(discovery: dict[str, Any], output: Path) -> None:
    """Write a concise Markdown discovery report."""
    lines = [
        "# HathiTrust-NZ Discovery Manifest",
        "",
        "- This manifest documents the broader NZ source families that should be discovered beyond the Hansard seed.",
        "- Internet Archive overlap is the interim full-text path until HathiTrust rsync access is restored.",
        "- Public metadata and derived manifests are publication-safe; restricted full text remains static-host only.",
        "",
        "## Families",
        "",
    ]
    for family in discovery.get("source_families", []):
        lines.extend(
            [
                f"### {family['title']}",
                "",
                f"- Family ID: `{family['family_id']}`",
                f"- Status: `{family['status']}`",
                f"- Public archive status: `{family['public_archive_status']}`",
                f"- Discovery inputs: {', '.join(family.get('source_inputs', []))}",
                f"- Acquisition modes: {', '.join(family.get('acquisition_modes', []))}",
                f"- Public sources: {', '.join(family.get('public_sources', []))}",
                f"- Restricted sources: {', '.join(family.get('restricted_sources', []))}",
                "",
            ]
        )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_inventory(
    volumes: list[dict[str, Any]],
    *,
    source_path: Path | None = None,
    expected_count: int = HATHITRUST_NZ_EXPECTED_COUNT,
) -> dict[str, Any]:
    """Build a source-specific collection inventory manifest."""
    summary = summarize_inventory(volumes)
    return {
        "meta": {
            "generated_at": utc_now(),
            "pipeline_version": get_version(),
            "source": "HathiTrust collection export",
            "source_path": source_path.as_posix() if source_path is not None else "",
            "collection_id": HATHITRUST_NZ_COLLECTION_ID,
            "collection_slug": HATHITRUST_NZ_COLLECTION_SLUG,
            "catalog_record_id": HATHITRUST_NZ_CATALOG_RECORD,
            "expected_record_count": expected_count,
            "record_count": len(volumes),
            "hf_collection": HUGGING_FACE_COLLECTION,
        },
        "summary": summary,
        "child_datasets": child_datasets(),
        "volumes": volumes,
    }


def assert_expected_count(inventory: dict[str, Any], expected_count: int) -> None:
    """Raise if the source-specific record count drifts unexpectedly."""
    actual_count = int(inventory.get("meta", {}).get("record_count", 0))
    if actual_count != expected_count:
        msg = f"Expected {expected_count} HathiTrust-NZ seed records, found {actual_count}"
        raise ValueError(msg)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    """Write deterministic pretty JSON."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=False) + "\n", encoding="utf-8")


def write_lines(path: Path, lines: list[str]) -> None:
    """Write newline-terminated text lines."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")


def load_inventory(path: Path) -> dict[str, Any]:
    """Load an inventory manifest."""
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        msg = f"Inventory at {path} is not a JSON object"
        raise TypeError(msg)
    return data


def write_inventory_outputs(
    inventory: dict[str, Any],
    *,
    output: Path,
    htids_output: Path | None = None,
) -> None:
    """Write the inventory JSON and optional HTID allowlist."""
    write_json(output, inventory)
    if htids_output is not None:
        htids = [str(volume["htid"]) for volume in inventory.get("volumes", [])]
        write_lines(htids_output, htids)


def write_htrc_ef_plan(
    inventory: dict[str, Any],
    output_dir: Path,
    *,
    limit: int = 0,
) -> dict[str, Any]:
    """Write HTRC EF rsync allowlists and a manifest."""
    volumes = list(inventory.get("volumes", []))
    if limit > 0:
        volumes = volumes[:limit]

    rsync_paths = [str(volume["htrc_ef25_rsync_path"]) for volume in volumes]
    htids = [str(volume["htid"]) for volume in volumes]
    output_dir.mkdir(parents=True, exist_ok=True)
    write_lines(output_dir / "htrc_ef25_htids.txt", htids)
    write_lines(output_dir / "htrc_ef25_files.txt", rsync_paths)

    manifest = {
        "meta": {
            "generated_at": utc_now(),
            "source_dataset_name": f"HTRC Extracted Features {HTRC_EF_VERSION}",
            "source_url": "https://analytics.hathitrust.org/",
            "rsync_module": HTRC_EF_RSYNC_MODULE,
            "record_count": len(volumes),
            "limited": limit > 0,
            "license": "CC-BY-4.0",
            "hf_dataset_repo": HF_HTRC_EF_REPO,
            "acquisition_mode": "github_actions_rsync_or_static_host_staging",
        },
        "files": [
            {"htid": htid, "rsync_path": path}
            for htid, path in zip(htids, rsync_paths, strict=True)
        ],
    }
    write_json(output_dir / "htrc_ef25_manifest.json", manifest)
    write_lines(
        output_dir / "rsync_htrc_ef25_subset.sh",
        [
            "#!/usr/bin/env bash",
            "set -euo pipefail",
            'DEST_DIR="${1:-htrc_ef25_subset}"',
            'mkdir -p "$DEST_DIR"',
            (f'rsync -av --files-from="htrc_ef25_files.txt" "{HTRC_EF_RSYNC_MODULE}" "$DEST_DIR/"'),
        ],
    )
    return manifest


def write_research_dataset_plan(
    inventory: dict[str, Any],
    output_dir: Path,
    *,
    source_dataset_name: str = HATHI_RESEARCH_PD_WORLD_OPEN_ACCESS,
    limit: int = 0,
) -> dict[str, Any]:
    """Write a static-host acquisition plan for Hathi Research Datasets."""
    volumes = list(inventory.get("volumes", []))
    if limit > 0:
        volumes = volumes[:limit]

    eligible: list[dict[str, Any]] = []
    metadata_only: list[dict[str, Any]] = []
    for volume in volumes:
        policy = classify_publication_policy(
            volume.get("rights_code"),
            access_profile_code=str(volume.get("access_profile_code", "")),
            digitization_agent_code=str(volume.get("digitization_agent_code", "")),
            source_dataset_name=source_dataset_name,
        )
        record = {
            "htid": volume["htid"],
            "title": volume.get("title", ""),
            "rights_code": volume.get("rights_code", ""),
            "rights_label": policy["rights_label"],
            "source_dataset_name": source_dataset_name,
            **policy,
        }
        if policy["public_full_text_allowed"]:
            eligible.append(record)
        else:
            metadata_only.append(record)

    output_dir.mkdir(parents=True, exist_ok=True)
    write_lines(output_dir / "research_dataset_eligible_htids.txt", [r["htid"] for r in eligible])
    write_lines(
        output_dir / "research_dataset_metadata_only_htids.txt", [r["htid"] for r in metadata_only]
    )

    manifest = {
        "meta": {
            "generated_at": utc_now(),
            "source_dataset_name": source_dataset_name,
            "source_url": "https://www.hathitrust.org/member-libraries/resources-for-librarians/data-resources/research-datasets/",
            "record_count": len(volumes),
            "eligible_full_text_count": len(eligible),
            "metadata_only_count": len(metadata_only),
            "requires_static_host": True,
            "acquisition_mode": "static_host_rsync_then_actions_publish_staged_bundle",
            "hf_dataset_repo": HF_RESEARCH_FULLTEXT_REPO,
        },
        "static_host_contract": {
            "required_secrets": [
                "HATHI_STATIC_HOST_SSH_KEY",
            ],
            "required_variables": [
                "HATHI_RSYNC_HOST",
                "HATHI_RSYNC_MODULE",
                "HATHI_RSYNC_USER",
                "HATHI_STATIC_HOST_STAGING_DIR",
            ],
            "github_actions_role": (
                "Pull pre-approved staged bundles from the static host; do not "
                "download Hathi Research Dataset full text directly from GitHub runners."
            ),
        },
        "eligible_full_text": eligible,
        "metadata_only": metadata_only,
    }
    write_json(output_dir / "research_dataset_manifest.json", manifest)
    write_lines(
        output_dir / "static_host_staging_contract.sh",
        [
            "#!/usr/bin/env bash",
            "set -euo pipefail",
            ': "${HATHI_RSYNC_MODULE:?Set approved Hathi rsync module on static host}"',
            ': "${HATHI_STATIC_HOST_STAGING_DIR:?Set local staging dir on static host}"',
            'mkdir -p "$HATHI_STATIC_HOST_STAGING_DIR/research_datasets"',
            "# Use research_dataset_eligible_htids.txt as the allowlist for approved acquisition.",
            "# Dataset-specific path mapping is supplied by the approved Hathi Research Dataset endpoint.",
        ],
    )
    return manifest


def base_title_for_internet_archive(title: str) -> str:
    """Return a conservative title query for Archive.org search."""
    if not title:
        return ""

    if title.startswith(HANSARD_TITLE_PREFIX):
        return HANSARD_TITLE_PREFIX

    if title.startswith(PARLIAMENTARY_DEBATES_TITLE_PREFIX):
        return PARLIAMENTARY_DEBATES_TITLE_PREFIX

    _, label = parse_volume_label(title)
    if label and title.endswith(label):
        base = title[: -len(label)].strip(" :-")
        if base:
            return base
    return title


def internet_archive_search(query: str, *, rows: int = 5) -> list[dict[str, Any]]:
    """Search Archive.org and return raw docs."""
    params = {
        "q": query,
        "fl[]": ["identifier", "title", "creator", "year", "collection", "publicdate"],
        "rows": rows,
        "output": "json",
    }
    response = requests.get(
        INTERNET_ARCHIVE_SEARCH_URL,
        params=params,
        headers=INTERNET_ARCHIVE_SEARCH_HEADERS,
        timeout=60,
    )
    response.raise_for_status()
    payload = response.json()
    return list(payload.get("response", {}).get("docs", []))


def internet_archive_metadata(identifier: str) -> dict[str, Any]:
    """Fetch Archive.org metadata for a single item identifier."""
    response = requests.get(
        INTERNET_ARCHIVE_METADATA_URL.format(identifier=identifier),
        headers=INTERNET_ARCHIVE_SEARCH_HEADERS,
        timeout=60,
    )
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, dict):
        msg = f"Archive.org metadata for {identifier} is not an object"
        raise TypeError(msg)
    return payload


def internet_archive_text_candidates(metadata: dict[str, Any]) -> list[str]:
    """Return downloadable text-like files for a metadata record."""
    files = metadata.get("files", [])
    candidates: list[str] = []
    for file_entry in files:
        if not isinstance(file_entry, dict):
            continue
        name = str(file_entry.get("name", ""))
        if not name:
            continue
        if name.endswith(INTERNET_ARCHIVE_TEXT_SUFFIXES):
            candidates.append(name)
    prioritized: list[str] = []
    for suffix in INTERNET_ARCHIVE_TEXT_SUFFIXES:
        prioritized.extend(sorted(name for name in candidates if name.endswith(suffix)))
    return list(dict.fromkeys(prioritized))


def internet_archive_best_match(volume: dict[str, Any], docs: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Pick a conservative Archive.org match for a HathiTrust record."""
    title = str(volume.get("title", "")).strip()
    author = str(volume.get("author", "")).strip()
    title_query = base_title_for_internet_archive(title)
    title_lower = title_query.lower()
    author_lower = author.lower()

    for doc in docs:
        doc_title = str(doc.get("title", "")).strip()
        doc_creator = str(doc.get("creator", "")).strip()
        doc_title_lower = doc_title.lower()
        doc_creator_lower = doc_creator.lower()
        if title_lower and title_lower not in doc_title_lower:
            continue
        if author_lower and author_lower not in doc_creator_lower:
            continue
        return doc
    return None


def internet_archive_review_reason(volume: dict[str, Any], doc: dict[str, Any]) -> list[str]:
    """Return why a candidate needs manual review instead of auto-match."""
    reasons: list[str] = []
    title = base_title_for_internet_archive(str(volume.get("title", "")).strip()).lower()
    author = str(volume.get("author", "")).strip().lower()
    doc_title = str(doc.get("title", "")).strip().lower()
    doc_creator = str(doc.get("creator", "")).strip().lower()
    if title and title not in doc_title:
        reasons.append("title_mismatch")
    if author and author not in doc_creator:
        reasons.append("creator_mismatch")
    if not reasons:
        reasons.append("needs_manual_review")
    return reasons


def sha256_file(path: Path) -> str:
    """Return the SHA-256 checksum for a file."""
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def download_internet_archive_text(
    identifier: str,
    metadata: dict[str, Any],
    output_dir: Path,
) -> Path | None:
    """Download the best available text file from Archive.org."""
    candidates = internet_archive_text_candidates(metadata)
    if not candidates:
        return None

    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{identifier}.txt"
    for filename in candidates:
        response = requests.get(
            INTERNET_ARCHIVE_DOWNLOAD_URL.format(identifier=identifier, filename=filename),
            headers=INTERNET_ARCHIVE_SEARCH_HEADERS,
            timeout=120,
        )
        if response.status_code != 200:
            continue
        content = response.content
        if filename.endswith(".gz"):
            content = gzip.decompress(content)
        output_path.write_bytes(content)
        return output_path
    return None


def write_internet_archive_overlap_plan(
    inventory: dict[str, Any],
    output_dir: Path,
    *,
    limit: int = 0,
) -> dict[str, Any]:
    """Write an Archive.org overlap plan for interim full-text mirroring."""
    volumes = list(inventory.get("volumes", []))
    if limit > 0:
        volumes = volumes[:limit]

    output_dir.mkdir(parents=True, exist_ok=True)
    text_output_dir = output_dir / "texts"
    provenance_ledger: list[dict[str, Any]] = []
    review_queue: list[dict[str, Any]] = []
    checksum_rows: list[dict[str, Any]] = []
    matched: list[dict[str, Any]] = []
    unmatched: list[dict[str, Any]] = []

    for volume in volumes:
        title_query = base_title_for_internet_archive(str(volume.get("title", "")))
        author = str(volume.get("author", "")).strip()
        query_parts = [f'title:"{title_query}"']
        if author:
            query_parts.append(f'creator:"{author}"')
        query_parts.append("mediatype:texts")
        query = " AND ".join(query_parts)

        try:
            docs = internet_archive_search(query, rows=5)
        except requests.RequestException as exc:
            unmatched.append(
                {
                    "htid": volume["htid"],
                    "title": volume.get("title", ""),
                    "author": author,
                    "search_query": query,
                    "error": str(exc),
                }
            )
            continue

        best = internet_archive_best_match(volume, docs)
        if not best:
            unmatched.append(
                {
                    "htid": volume["htid"],
                    "title": volume.get("title", ""),
                    "author": author,
                    "search_query": query,
                    "error": "no_match",
                }
            )
            if docs:
                candidate = docs[0]
                review_queue.append(
                    {
                        "htid": volume["htid"],
                        "title": volume.get("title", ""),
                        "author": author,
                        "search_query": query,
                        "candidate_identifier": candidate.get("identifier", ""),
                        "candidate_title": candidate.get("title", ""),
                        "candidate_creator": candidate.get("creator", ""),
                        "candidate_year": candidate.get("year", ""),
                        "review_reasons": internet_archive_review_reason(volume, candidate),
                    }
                )
            provenance_ledger.append(
                {
                    "htid": volume["htid"],
                    "search_query": query,
                    "status": "unmatched",
                    "matched": False,
                    "candidate_count": len(docs),
                }
            )
            continue

        identifier = str(best.get("identifier", "")).strip()
        record: dict[str, Any] = {
            "htid": volume["htid"],
            "title": volume.get("title", ""),
            "author": author,
            "search_query": query,
            "archive_identifier": identifier,
            "archive_title": best.get("title", ""),
            "archive_creator": best.get("creator", ""),
            "archive_year": best.get("year", ""),
            "archive_collection": best.get("collection", []),
            "archive_publicdate": best.get("publicdate", ""),
            "archive_metadata_url": INTERNET_ARCHIVE_METADATA_URL.format(identifier=identifier),
            "archive_download_url": f"https://archive.org/download/{identifier}/",
        }

        try:
            metadata = internet_archive_metadata(identifier)
            record["archive_file_candidates"] = internet_archive_text_candidates(metadata)
            text_path = download_internet_archive_text(identifier, metadata, text_output_dir)
            if text_path is not None:
                record["text_path"] = text_path.as_posix()
                checksum = sha256_file(text_path)
                checksum_rows.append(
                    {
                        "htid": volume["htid"],
                        "archive_identifier": identifier,
                        "file_path": text_path.as_posix(),
                        "filename": text_path.name,
                        "size_bytes": text_path.stat().st_size,
                        "sha256": checksum,
                    }
                )
                record["sha256"] = checksum
        except requests.RequestException as exc:
            record["error"] = str(exc)
            unmatched.append(record)
            provenance_ledger.append(
                {
                    "htid": volume["htid"],
                    "search_query": query,
                    "status": "error",
                    "matched": False,
                    "error": str(exc),
                }
            )
            continue

        matched.append(record)
        provenance_ledger.append(
            {
                "htid": volume["htid"],
                "search_query": query,
                "status": "matched",
                "matched": True,
                "archive_identifier": identifier,
                "archive_metadata_url": record["archive_metadata_url"],
                "archive_download_url": record["archive_download_url"],
                "archive_title": record["archive_title"],
                "archive_creator": record["archive_creator"],
                "archive_year": record["archive_year"],
                "evidence": {
                    "title": base_title_for_internet_archive(str(volume.get("title", ""))),
                    "creator": str(volume.get("author", "")).strip(),
                },
            }
        )

    manifest = {
        "meta": {
            "generated_at": utc_now(),
            "source_dataset_name": "Internet Archive public-domain overlap",
            "source_url": "https://archive.org/",
            "record_count": len(volumes),
            "matched_count": len(matched),
            "unmatched_count": len(unmatched),
            "review_queue_count": len(review_queue),
            "checksum_count": len(checksum_rows),
            "hf_dataset_repo": HF_RESEARCH_FULLTEXT_REPO,
            "acquisition_mode": "internet_archive_public_metadata_and_text",
        },
        "matched": matched,
        "unmatched": unmatched,
        "review_queue": review_queue,
    }
    write_json(output_dir / "internet_archive_overlap_manifest.json", manifest)
    write_json(output_dir / "internet_archive_provenance_ledger.json", {"rows": provenance_ledger})
    write_json(output_dir / "internet_archive_checksum_manifest.json", {"files": checksum_rows})
    write_lines(
        output_dir / "internet_archive_overlap_htids.txt",
        [record["htid"] for record in matched],
    )
    write_lines(
        output_dir / "internet_archive_overlap_identifiers.txt",
        [record["archive_identifier"] for record in matched if record.get("archive_identifier")],
    )
    write_lines(
        output_dir / "internet_archive_review_queue_htids.txt",
        [entry["htid"] for entry in review_queue],
    )
    return manifest


def build_collection_manifest(inventory: dict[str, Any]) -> dict[str, Any]:
    """Build the collection-level manifest linking child datasets."""
    summary = inventory.get("summary", {})
    return {
        "meta": {
            "generated_at": utc_now(),
            "pipeline_version": get_version(),
            "collection_id": "hathitrust-nz",
            "hf_collection": HUGGING_FACE_COLLECTION,
            "legacy_dataset_repo": HF_COMPAT_DATASET_REPO,
            "source_collection_id": inventory.get("meta", {}).get("collection_id"),
            "source_catalog_record_id": inventory.get("meta", {}).get("catalog_record_id"),
            "record_count": inventory.get("meta", {}).get("record_count", 0),
        },
        "summary": summary,
        "sources": [
            {
                "source_id": HATHITRUST_NZ_COLLECTION_SLUG,
                "source_type": "hathitrust_collection_export",
                "collection_id": HATHITRUST_NZ_COLLECTION_ID,
                "catalog_record_id": HATHITRUST_NZ_CATALOG_RECORD,
                "record_count": inventory.get("meta", {}).get("record_count", 0),
                "public_full_text_rule": (
                    "Only public-domain or Creative Commons records with no "
                    "Google/page/restricted profile are eligible for public full text."
                ),
            },
            {
                "source_id": "htrc_extracted_features_2_5",
                "source_type": "htrc_extracted_features",
                "license": "CC-BY-4.0",
                "rsync_module": HTRC_EF_RSYNC_MODULE,
            },
            {
                "source_id": "hathi_research_datasets",
                "source_type": "static_ip_rsync",
                "public_archive_rule": (
                    "Metadata is public; full text is staged only through the approved "
                    "static host and published only when rehost eligibility is explicit."
                ),
            },
            {
                "source_id": "internet_archive_public_domain_overlap",
                "source_type": "archive_org_public_metadata_and_text",
                "public_archive_rule": (
                    "Archive.org is the interim public-domain overlap source until HathiTrust "
                    "rsync access is restored; only public-domain overlap items with matching "
                    "title/creator evidence are admitted."
                ),
            },
        ],
        "source_policy_registry": source_policy_summary(),
        "child_datasets": child_datasets(),
    }


def write_completeness_report(inventory: dict[str, Any], output: Path) -> None:
    """Write a concise Markdown archive completeness report."""
    summary = inventory.get("summary", {})
    parse = summary.get("volume_number_parse", {})
    label_parse = summary.get("label_parse", {})
    enumeration_parse = summary.get("enumeration_parse", {})
    lines = [
        "# HathiTrust-NZ Archive Completeness Report",
        "",
        f"- Source collection: HathiTrust Collection `{HATHITRUST_NZ_COLLECTION_ID}`.",
        f"- HF collection: `{HUGGING_FACE_COLLECTION}`.",
        f"- Seed record count: `{summary.get('record_count', 0)}`.",
        f"- Parsed numeric volume labels: `{parse.get('parsed', 0)}`.",
        f"- Parsed enumeration labels: `{enumeration_parse.get('parsed', 0)}`.",
        f"- Fully parsed seed labels: `{label_parse.get('parsed', 0)}`.",
        f"- Needs enumeration enrichment: `{label_parse.get('needs_enrichment', 0)}`.",
        "- Public full-text uploads fail closed when rights, source, or access profile is ambiguous.",
        "- Internet Archive public-domain overlap is the interim full-text path while HathiTrust rsync remains unavailable.",
        "- Hathi Research Dataset full text must be staged via the approved static rsync host once access is restored.",
        "- HTRC Extracted Features 2.5 subset acquisition uses rsync file allowlists.",
        "",
        "## Child Datasets",
        "",
    ]
    for dataset in child_datasets():
        lines.append(f"- `{dataset['dataset_id']}` -> `{dataset['hf_repo_id']}`")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args(args: list[str] | None = None) -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    inventory = subparsers.add_parser("inventory", help="Build seed collection inventory")
    inventory.add_argument("--collection-export", type=Path, required=True)
    inventory.add_argument("--output", type=Path, required=True)
    inventory.add_argument("--htids-output", type=Path)
    inventory.add_argument("--expected-count", type=int, default=HATHITRUST_NZ_EXPECTED_COUNT)
    inventory.add_argument("--fail-on-count-drift", action="store_true")

    collection = subparsers.add_parser("collection-manifest", help="Build collection manifest")
    collection.add_argument("--inventory", type=Path, required=True)
    collection.add_argument("--output", type=Path, required=True)
    collection.add_argument("--completeness-report", type=Path)

    htrc_ef = subparsers.add_parser("htrc-ef-plan", help="Build HTRC EF rsync plan")
    htrc_ef.add_argument("--inventory", type=Path, required=True)
    htrc_ef.add_argument("--output-dir", type=Path, required=True)
    htrc_ef.add_argument("--limit", type=int, default=0)

    research = subparsers.add_parser("research-rsync-plan", help="Build Research Dataset plan")
    research.add_argument("--inventory", type=Path, required=True)
    research.add_argument("--output-dir", type=Path, required=True)
    research.add_argument(
        "--source-dataset-name",
        default=HATHI_RESEARCH_PD_WORLD_OPEN_ACCESS,
        choices=sorted(STATIC_RSYNC_DATASETS),
    )
    research.add_argument("--limit", type=int, default=0)

    metadata_refresh = subparsers.add_parser(
        "metadata-refresh", help="Build HathiTrust metadata refresh manifests"
    )
    metadata_refresh.add_argument("--inventory", type=Path, required=True)
    metadata_refresh.add_argument("--output-dir", type=Path, required=True)
    metadata_refresh.add_argument("--limit", type=int, default=0)
    metadata_refresh.add_argument(
        "--oai-cursor",
        default="",
        help="Optional OAI-PMH cursor state to record in the manifest.",
    )

    ia = subparsers.add_parser(
        "internet-archive-plan", help="Build an Internet Archive overlap mirror plan"
    )
    ia.add_argument("--inventory", type=Path, required=True)
    ia.add_argument("--output-dir", type=Path, required=True)
    ia.add_argument("--limit", type=int, default=0)

    discovery = subparsers.add_parser("discovery-manifest", help="Build broader NZ discovery manifest")
    discovery.add_argument("--inventory", type=Path, required=True)
    discovery.add_argument("--output", type=Path, required=True)
    discovery.add_argument("--report", type=Path)

    return parser.parse_args(args)


def main() -> int:
    """CLI entry point."""
    configure_logging()
    args = parse_args()
    result = 2

    if args.command == "inventory":
        volumes = load_collection_export_tsv(args.collection_export)
        inventory = build_inventory(
            volumes,
            source_path=args.collection_export,
            expected_count=args.expected_count,
        )
        if args.fail_on_count_drift:
            assert_expected_count(inventory, args.expected_count)
        write_inventory_outputs(inventory, output=args.output, htids_output=args.htids_output)
        result = 0
    elif args.command == "collection-manifest":
        inventory = load_inventory(args.inventory)
        manifest = build_collection_manifest(inventory)
        write_json(args.output, manifest)
        if args.completeness_report is not None:
            write_completeness_report(inventory, args.completeness_report)
        result = 0
    elif args.command == "htrc-ef-plan":
        inventory = load_inventory(args.inventory)
        write_htrc_ef_plan(inventory, args.output_dir, limit=args.limit)
        result = 0
    elif args.command == "research-rsync-plan":
        inventory = load_inventory(args.inventory)
        write_research_dataset_plan(
            inventory,
            args.output_dir,
            source_dataset_name=args.source_dataset_name,
            limit=args.limit,
        )
        result = 0
    elif args.command == "metadata-refresh":
        inventory = load_inventory(args.inventory)
        write_metadata_refresh_plan(
            inventory,
            args.output_dir,
            limit=args.limit,
            oai_cursor=args.oai_cursor,
        )
        result = 0
    elif args.command == "internet-archive-plan":
        inventory = load_inventory(args.inventory)
        write_internet_archive_overlap_plan(inventory, args.output_dir, limit=args.limit)
        result = 0
    elif args.command == "discovery-manifest":
        inventory = load_inventory(args.inventory)
        discovery = build_discovery_manifest(inventory)
        write_json(args.output, discovery)
        if args.report is not None:
            write_discovery_report(discovery, args.report)
        result = 0

    return result


if __name__ == "__main__":
    raise SystemExit(main())
