# Plan: HathiTrust-NZ Multi-Source Archive (hathitrust_nz_multi_source_archive_20260702)

## Phase 1: Track Bootstrap And Inventory

- [x] Task: Create Conductor track artifacts for the multi-source archive.
- [x] Task: Generate a source-specific Hansard inventory from `data/hathi_collection_export_71329709.tsv`.
- [x] Task: Add a 510-record count gate so broad Hathifile manifests cannot silently replace the curated seed.
- [x] Task: Commit seed manifests under `manifests/hathitrust-nz/`.
- [x] Task: Create GitHub issue `Track: HathiTrust-NZ collection architecture and inventory` (#13).
- [ ] Task: Conductor - User Manual Verification 'Phase 1: Track Bootstrap And Inventory' (Protocol in workflow.md)

## Phase 2: Rights And Publication Routing

- [x] Task: Implement fail-closed rights and redistribution classifier.
- [x] Task: Add fields for dataset ID, source URL, source dataset name, rights code, access profile, acquisition mode, and publish eligibility.
- [x] Task: Add tests for public `17` / `cc-zero`, restricted rights, Google-restricted routes, and HTRC EF path generation.
- [x] Task: Create GitHub issue `Track Task: Implement rights and redistribution classifier` (#15).
- [ ] Task: Conductor - User Manual Verification 'Phase 2: Rights And Publication Routing' (Protocol in workflow.md)

## Phase 3: Static-Host Research Dataset Acquisition

- [x] Task: Add static-host Research Dataset plan generation and allowlist outputs.
- [x] Task: Add GitHub Actions workflow that pulls only from a configured static host.
- [x] Task: Require `HATHI_RSYNC_HOST`, `HATHI_RSYNC_MODULE`, `HATHI_RSYNC_USER`, `HATHI_STATIC_HOST_SSH_KEY`, and `HATHI_STATIC_HOST_STAGING_DIR`.
- [x] Task: Create GitHub issue `Track Task: Add static-host rsync acquisition for Hathi Research Datasets` (#16).
- [ ] Task: Conductor - User Manual Verification 'Phase 3: Static-Host Research Dataset Acquisition' (Protocol in workflow.md)

## Phase 4: HTRC Extracted Features And Analytics

- [x] Task: Add HTRC EF 2.5 stubbytree path generation and file-list manifests.
- [x] Task: Add HTRC EF GitHub Actions workflow with smoke-limit and opt-in rsync execution.
- [x] Task: Add HTRC Analytics child dataset card and collection publication placeholder.
- [x] Task: Create GitHub issue `Track Task: Add HTRC Extracted Features subset acquisition` (#17).
- [ ] Task: Conductor - User Manual Verification 'Phase 4: HTRC Extracted Features And Analytics' (Protocol in workflow.md)

## Phase 5: Hugging Face Collection And Child Datasets

- [x] Task: Add generic HF folder uploader for source-specific archive artifacts.
- [x] Task: Add HF collection sync helper for linking child dataset repos.
- [x] Task: Add collection publication workflow with optional HF manifest and collection mutation steps.
- [x] Task: Create GitHub issue `Track Task: Publish HathiTrust-NZ child datasets to Hugging Face collection` (#18).
- [ ] Task: Conductor - User Manual Verification 'Phase 5: Hugging Face Collection And Child Datasets' (Protocol in workflow.md)

## Phase 6: Zenodo Per-Dataset Release Streams

- [x] Task: Add child dataset cards with DOI writeback placeholders.
- [x] Task: Add per-child Zenodo metadata records.
- [x] Task: Add collection publication workflow loop for per-dataset Zenodo depositions.
- [x] Task: Create GitHub issue `Track Task: Publish per-dataset Zenodo DOI releases` (#19).
- [ ] Task: Conductor - User Manual Verification 'Phase 6: Zenodo Per-Dataset Release Streams' (Protocol in workflow.md)

## Phase 7: Validation And Archive Completeness

- [x] Task: Add unit tests for archive routing and publication decisions.
- [x] Task: Add generated archive completeness report.
- [x] Task: Run workflow syntax validation after all workflow files are present.
- [x] Task: Run GitHub Actions dry-run validation for inventory, Research Dataset, HTRC EF, and collection publication workflows.
- [x] Task: Create GitHub issue `Track Task: Validate Actions, status reports, and archive completeness` (#20).
- [ ] Task: Conductor - User Manual Verification 'Phase 7: Validation And Archive Completeness' (Protocol in workflow.md)

## Phase 8: Expanded NZ Discovery

- [x] Task: Create GitHub issue `Track Task: Build NZ Hathifiles and catalog discovery manifest` (#14).
- [x] Task: Expand beyond Hansard into parliamentary/legal, government/policy, scholarly/cultural, and Maori/Aotearoa targets.
- [x] Task: Document public versus restricted status for each expanded source family.
- [x] Task: Add Internet Archive overlap fallback for interim public-domain full-text mirroring.
- [x] Task: Emit `manifests/hathitrust-nz/nz_discovery_manifest.{json,md}` from the archive planner.
- [ ] Task: Conductor - User Manual Verification 'Phase 8: Expanded NZ Discovery' (Protocol in workflow.md)

## Acceptance Gates

- [x] No restricted full text is uploaded to Hugging Face or Zenodo.
- [x] Each child dataset has a manifest, dataset card, DOI status, source citation, and completeness report.
- [x] Interim public-domain full text can be mirrored from Internet Archive while HathiTrust rsync access is unavailable.
- [x] GitHub Actions dry-run paths pass without publication secrets.
- [x] HF publication requires `HF_TOKEN` and Zenodo publication requires `ZENODO_TOKEN` or `ZENODO_SANDBOX_TOKEN`.
- [x] Research Dataset full text is acquired only through the configured static host.

## Validation Evidence

- [2026-07-02] `pixi run -e dev ruff check .` passed.
- [2026-07-02] `pixi run -e dev pytest tests/ -q` passed: 342 tests.
- [2026-07-02] `pixi run -e dev actionlint <explicit workflow files>` passed for all workflows.
- [2026-07-02] `pixi run -e dev pyright scripts/` passed.
- [2026-07-03] `pixi run -e dev ty check scripts/ --exclude scripts/config.py` passed after fixing the optional OSF client import typing.
- [2026-07-02] GitHub Actions dry-run inventory sync passed: https://github.com/edithatogo/hathi-nz/actions/runs/28592206845
- [2026-07-02] GitHub Actions dry-run Research Dataset sync passed: https://github.com/edithatogo/hathi-nz/actions/runs/28592209485
- [2026-07-02] GitHub Actions dry-run HTRC EF sync passed: https://github.com/edithatogo/hathi-nz/actions/runs/28592211892
- [2026-07-02] GitHub Actions dry-run collection publish passed: https://github.com/edithatogo/hathi-nz/actions/runs/28592215328
- [2026-07-03] Child HF dataset artifacts uploaded before collection sync failed: https://github.com/edithatogo/hathi-nz/actions/runs/28598245910
- [2026-07-03] HF child dataset repo SHAs after upload:
  - `edithatogo/hathitrust-nz-inventory`: `e6ab8b479a855b31d6edd642cc3dc2599787baf6`
  - `edithatogo/hathitrust-nz-research-fulltext`: `ba1debe3fe5de591217201b6bb442a82817f9ed6`
  - `edithatogo/hathitrust-nz-htrc-extracted-features`: `dcd558640b20625f85138cbe35f57ca2e70051e0`
  - `edithatogo/hathitrust-nz-htrc-analytics`: `e61e3c3f593220e0d7b815c3bd70e09df490e7b0`
- [2026-07-03] HF collection creation remains blocked by `HF_TOKEN` scope: Hugging Face returned `403 Forbidden` for `POST /api/collections` in https://github.com/edithatogo/hathi-nz/actions/runs/28598245910.
- [2026-07-03] Zenodo sandbox publication remains blocked by `ZENODO_SANDBOX_TOKEN` scope or account state: Zenodo returned `403 Permission denied` for deposition creation in https://github.com/edithatogo/hathi-nz/actions/runs/28598586986.
- [2026-07-03] Hathi Research Dataset full-text acquisition remains blocked by missing static-host GitHub variables/secrets: `HATHI_RSYNC_HOST`, `HATHI_RSYNC_MODULE`, `HATHI_RSYNC_USER`, `HATHI_STATIC_HOST_STAGING_DIR`, and `HATHI_STATIC_HOST_SSH_KEY`.
