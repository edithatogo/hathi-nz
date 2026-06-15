# CLI-first entrypoints

Use `hathi-nz` before invoking repository scripts directly.

## Commands

- `hathi-nz --list` lists approved aliases.
- `hathi-nz <alias> -- <script-args>` dispatches to the existing script implementation.

## Approved aliases

- `fetch` -> `scripts/fetch_hathitrust.py`
- `ocr` -> `scripts/ocr_extract.py`
- `package` -> `scripts/package_release.py`
- `publish-zenodo` -> `scripts/publish_zenodo.py`
- `stage` -> `scripts/stage_hf_dataset.py`
- `upload` -> `scripts/upload_hf_dataset.py`
- `validate` -> `scripts/validate_catalog.py`

## Policy

Existing `scripts/*.py` files remain implementation modules. New automation, conductor tracks, and swarm prompts should call the package CLI first, then add a new alias here when a repeated workflow is needed.
