"""Zenodo deposition client for prepared release archives.

Network-mutating operations are isolated behind explicit function calls and the
CLI defaults to dry-run behavior. Publication requires a token and
``--publish``; using it is an external-account gate.
"""

from __future__ import annotations

import argparse
import json
import os
import re
from collections.abc import Callable
from pathlib import Path
from typing import Any

import requests

get_settings: Callable[[], Any] | None = None
try:
    from config import get_settings as _get_settings
except ImportError:  # pragma: no cover
    pass
else:
    get_settings = _get_settings

ZENODO_API = "https://zenodo.org/api"
ZENODO_SANDBOX_API = "https://sandbox.zenodo.org/api"
ZENODO_DOI_SENTENCE = re.compile(r"For academic citation, use the Zenodo DOI .*?\.")


class ZenodoSession(requests.Session):
    """Requests session carrying the selected Zenodo API base URL."""

    base_url: str


def get_zenodo_api(token: str, sandbox: bool = True) -> ZenodoSession:
    """Return an authenticated Zenodo API session."""
    session = ZenodoSession()
    session.headers.update({"Authorization": f"Bearer {token}"})
    session.base_url = ZENODO_SANDBOX_API if sandbox else ZENODO_API
    return session


def _base_url(api: requests.Session) -> str:
    return str(getattr(api, "base_url", ZENODO_SANDBOX_API))


def create_deposition(api: requests.Session, metadata: dict[str, Any]) -> dict[str, Any]:
    """Create a Zenodo deposition with metadata."""
    response = api.post(
        f"{_base_url(api)}/deposit/depositions", json={"metadata": metadata}, timeout=60
    )
    response.raise_for_status()
    data = response.json()
    if not isinstance(data, dict):
        msg = "Zenodo create deposition response was not an object"
        raise TypeError(msg)
    return data


def upload_file(api: requests.Session, deposition_id: str, file_path: Path) -> dict[str, Any]:
    """Upload a file to an existing Zenodo deposition bucket."""
    deposition_response = api.get(
        f"{_base_url(api)}/deposit/depositions/{deposition_id}", timeout=60
    )
    deposition_response.raise_for_status()
    deposition = deposition_response.json()
    bucket = deposition.get("links", {}).get("bucket")
    if not bucket:
        msg = f"Zenodo deposition {deposition_id} did not include an upload bucket"
        raise ValueError(msg)

    with file_path.open("rb") as file:
        response = api.put(f"{bucket}/{file_path.name}", data=file, timeout=300)
    response.raise_for_status()
    data = response.json()
    if not isinstance(data, dict):
        msg = "Zenodo upload response was not an object"
        raise TypeError(msg)
    return data


def publish_deposition(api: requests.Session, deposition_id: str) -> dict[str, Any]:
    """Publish an existing Zenodo deposition."""
    response = api.post(
        f"{_base_url(api)}/deposit/depositions/{deposition_id}/actions/publish", timeout=60
    )
    response.raise_for_status()
    data = response.json()
    if not isinstance(data, dict):
        msg = "Zenodo publish response was not an object"
        raise TypeError(msg)
    return data


def _extract_publication_doi(publication: dict[str, Any]) -> str:
    """Return the DOI from a Zenodo publication response."""
    doi = publication.get("doi")
    if isinstance(doi, str) and doi.strip():
        return doi.strip()

    metadata = publication.get("metadata")
    if isinstance(metadata, dict):
        reserved = metadata.get("prereserve_doi")
        if isinstance(reserved, dict):
            reserved_doi = reserved.get("doi")
            if isinstance(reserved_doi, str) and reserved_doi.strip():
                return reserved_doi.strip()

    msg = "Zenodo publication response did not include a DOI"
    raise ValueError(msg)


def update_dataset_card_doi(card_path: Path, doi: str) -> bool:
    """Write the published Zenodo DOI back into the dataset card."""
    text = card_path.read_text(encoding="utf-8")
    doi_url = f"https://doi.org/{doi}"
    replacement = f"For academic citation, use the Zenodo DOI [{doi}]({doi_url})."
    updated_text, substitutions = ZENODO_DOI_SENTENCE.subn(replacement, text, count=1)
    if substitutions == 0:
        suffix = "\n" if text.endswith("\n") else "\n\n"
        updated_text = f"{text.rstrip()}{suffix}{replacement}\n"
    card_path.write_text(updated_text, encoding="utf-8")
    return True


def deposit(
    archive_path: Path,
    metadata: dict[str, Any],
    token: str,
    sandbox: bool = True,
    publish: bool = False,
    dataset_card_path: Path | None = Path("DATASET_CARD.md"),
) -> dict[str, Any]:
    """Create a deposition, upload an archive, and optionally publish it."""
    api = get_zenodo_api(token=token, sandbox=sandbox)
    deposition = create_deposition(api, metadata)
    deposition_id = str(deposition["id"])
    upload = upload_file(api, deposition_id, archive_path)
    result = {
        "deposition": deposition,
        "upload": upload,
        "published": False,
    }
    if publish:
        publication = publish_deposition(api, deposition_id)
        result["publication"] = publication
        result["published"] = True
        if dataset_card_path is not None:
            doi = _extract_publication_doi(publication)
            result["dataset_card_updated"] = update_dataset_card_doi(dataset_card_path, doi)
    return result


def parse_args(args: list[str] | None = None) -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(description="Publish a prepared release archive to Zenodo.")
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--metadata", type=Path, default=Path(".zenodo.json"))
    parser.add_argument("--dataset-card", type=Path, default=Path("DATASET_CARD.md"))
    parser.add_argument("--token-env", default="ZENODO_TOKEN")
    parser.add_argument("--sandbox", action="store_true", default=True)
    parser.add_argument(
        "--production", action="store_true", help="Use production Zenodo instead of sandbox."
    )
    parser.add_argument(
        "--publish", action="store_true", help="Publish after upload. External account gate."
    )
    parser.add_argument("--dry-run", action="store_true", default=True)
    parser.add_argument(
        "--execute", action="store_false", dest="dry_run", help="Execute API mutation."
    )
    return parser.parse_args(args)


def main() -> int:
    """CLI entry point."""
    args = parse_args()
    metadata = json.loads(args.metadata.read_text(encoding="utf-8"))
    sandbox = not args.production
    if args.dry_run:
        print(
            json.dumps(
                {
                    "dry_run": True,
                    "archive": args.archive.as_posix(),
                    "metadata": args.metadata.as_posix(),
                    "dataset_card": args.dataset_card.as_posix(),
                    "sandbox": sandbox,
                    "publish": args.publish,
                },
                indent=2,
            )
        )
        return 0

    token = os.environ.get(args.token_env)
    if not token and get_settings is not None:
        settings = get_settings()
        if args.token_env == "ZENODO_TOKEN" and settings.ZENODO_TOKEN:  # noqa: S105
            token = settings.ZENODO_TOKEN.get_secret_value()
    if not token:
        print(f"Missing token environment variable: {args.token_env}")
        return 2

    result = deposit(
        archive_path=args.archive,
        metadata=metadata,
        token=token,
        sandbox=sandbox,
        publish=args.publish,
        dataset_card_path=args.dataset_card,
    )
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
