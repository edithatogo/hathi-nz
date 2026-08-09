# Plan: HathiTrust-NZ Interim Acquisition Hardening (hathitrust_nz_interim_acquisition_hardening_20260703)

## Phase 1: Track Bootstrap And Governance

- [x] Task: Create Conductor track artifacts for interim acquisition hardening.
- [x] Task: Create GitHub parent issue `Track: HathiTrust-NZ interim acquisition and provenance hardening` (#21).
- [x] Task: Cross-link this track from `hathitrust_nz_multi_source_archive_20260702` without replacing the existing blocker evidence.
- [x] Task: Define implementation issue set for source policy, metadata refresh, IA acquisition, HTRC EF, NZ enrichment, publication gates, and completeness reporting (#22-#30).
- [ ] Task: Conductor - User Manual Verification 'Phase 1: Track Bootstrap And Governance' (Protocol in workflow.md)

## Phase 2: Source Policy Registry

- [x] Task: Add a machine-readable source policy registry for HathiTrust, Hathifiles, OAI-PMH, Bibliographic API, HTRC Solr EF20, HTRC Extracted Features, HTRC Analytics, Internet Archive, Open Library, DigitalNZ, National Library NZ, Papers Past, official parliamentary sources, static rsync staging, and manual evidence.
- [x] Task: Add policy fields for permitted artifact classes, licence evidence, access class, acquisition mode, publication eligibility, and source priority.
- [x] Task: Add fail-closed routing for unknown, restricted, legally ambiguous, or manual-review-only source classes.
- [x] Task: Add unit tests for policy loading, source priority ordering, and publication eligibility decisions.
- [x] Task: Create GitHub issue `Track Task: Add HathiTrust-NZ source policy registry` (#22).
- [ ] Task: Conductor - User Manual Verification 'Phase 2: Source Policy Registry' (Protocol in workflow.md)

## Phase 3: Metadata Refresh And Discovery Lanes

- [x] Task: Add or extend Hathifiles refresh outputs for broad NZ inventory, rights, access profile, and digitization profile.
- [x] Task: Add OAI-PMH incremental metadata refresh with cursor state, retry/backoff, and dry-run output.
- [x] Task: Add Bibliographic API enrichment for known HTIDs, OCLC records, catalog IDs, creator/title/year normalization, and enumeration gaps.
- [x] Task: Add HTRC EF Solr discovery/workset candidate generation for NZ-relevant records.
- [x] Task: Add IA/Open Library crosswalk enrichment for identifiers, creators, titles, years, OCLC, and evidence URLs.
- [x] Task: Add optional NZ enrichment manifest lanes for DigitalNZ, National Library NZ, Papers Past, and official parliamentary sources.
- [x] Task: Keep the 510-record Hansard seed distinct from broad NZ discovery outputs.
- [x] Task: Add tests for manifest separation, cursor state, enrichment merge precedence, and discovery count drift.
- [x] Task: Create GitHub issue `Track Task: Add metadata refresh lanes for HathiTrust-NZ` (#23).
- [ ] Task: Conductor - User Manual Verification 'Phase 3: Metadata Refresh And Discovery Lanes' (Protocol in workflow.md)

## Phase 4: Internet Archive Interim Full-Text Acquisition

- [x] Task: Harden IA matching with confidence scores, evidence fields, and no first-result fallback.
- [x] Task: Add Open Library and IA metadata crosswalk evidence before full-text acquisition.
- [x] Task: Emit IA overlap manifest, matched HTID list, IA identifier list, provenance ledger, source evidence report, checksum/file manifest, and manual review queue.
- [x] Task: Download only public-domain or redistributable IA text/OCR artifacts under GitHub Actions or artifact staging paths, not git.
- [x] Task: Route weak, ambiguous, or conflicting matches to manual review and block publication.
- [x] Task: Add quality metrics for OCR/text availability, file size, checksum, source timestamp, and candidate confidence.
- [x] Task: Add scheduled IA smoke workflow with small record limits and dry-run defaults.
- [x] Task: Add tests for strict matches, title-only ambiguity, creator mismatches, checksum generation, provenance output, and review queue output.
- [x] Task: Create GitHub issue `Track Task: Harden Internet Archive interim acquisition` (#24).
- [ ] Task: Conductor - User Manual Verification 'Phase 4: Internet Archive Interim Full-Text Acquisition' (Protocol in workflow.md)

## Phase 5: HTRC Extracted Features And Analytics Outputs

- [x] Task: Add HTRC EF 2.0 and 2.5 source metadata into the source policy and discovery manifests.
- [x] Task: Use HTRC EF Solr candidate results to build reproducible NZ worksets.
- [x] Task: Acquire open HTRC Extracted Features subsets when runner size and source policy permit.
- [x] Task: Route large HTRC EF subsets through static-host staging when GitHub runner limits are exceeded.
- [x] Task: Publish HTRC Analytics outputs as scripts, aggregate results, workset definitions, and reproducibility metadata only.
- [x] Task: Add tests for EF path generation, workset generation, analytics-only routing, and static-host fallback decisions.
- [x] Task: Create GitHub issue `Track Task: Add HTRC EF and Analytics interim outputs` (#25).
- [ ] Task: Conductor - User Manual Verification 'Phase 5: HTRC Extracted Features And Analytics Outputs' (Protocol in workflow.md)

## Phase 6: Source Priority Routing And Rights Gates

- [x] Task: Merge source policy, rights classifier, IA evidence, HTRC evidence, and HathiTrust metadata into a canonical routing manifest.
- [x] Task: Prefer official HathiTrust Research Dataset full text when static-host rsync is available.
- [x] Task: Prefer IA public-domain overlap while HathiTrust full text is unavailable.
- [x] Task: Prefer HTRC EF or analytics-only routes when full text is restricted or unavailable.
- [x] Task: Preserve metadata-only routes for uncertain, restricted, page-only, or manually reviewed records.
- [x] Task: Add tests that publication fails closed when rights, source policy, or provenance evidence is incomplete.
- [x] Task: Create GitHub issue `Track Task: Add source-priority routing and rights gates` (#26).
- [ ] Task: Conductor - User Manual Verification 'Phase 6: Source Priority Routing And Rights Gates' (Protocol in workflow.md)

## Phase 7: GitHub Actions Orchestration

- [x] Task: Add or update workflows for source policy validation, metadata refresh, IA overlap smoke, HTRC EF sync, completeness reporting, and collection publication.
- [x] Task: Ensure every routine workflow supports dry-run execution without secrets.
- [x] Task: Ensure publication jobs require explicit `HF_TOKEN`, `ZENODO_TOKEN` or `ZENODO_SANDBOX_TOKEN`, and static-host secrets where needed.
- [x] Task: Keep static rsync acquisition on the configured host and have Actions consume staged bundles or manifests.
- [x] Task: Add workflow tests and `actionlint` coverage for changed workflows.
- [x] Task: Create GitHub issue `Track Task: Wire interim acquisition GitHub Actions` (#29).
- [ ] Task: Conductor - User Manual Verification 'Phase 7: GitHub Actions Orchestration' (Protocol in workflow.md)

## Phase 8: Publication Evidence And Completeness Dashboard

- [x] Task: Extend completeness reports with counts for known, public, enriched, IA-matched, IA-downloaded, HTRC EF-available, review-required, HF-published, and Zenodo-deposited records.
- [x] Task: Add dataset-card sections that identify official HathiTrust, IA interim, HTRC EF, analytics-only, metadata-only, and blocked routes.
- [x] Task: Add DOI/HF status writeback for interim-source child dataset artifacts.
- [x] Task: Synchronize GitHub issues, project fields, and redundancy-label taxonomy with blocker status and completion evidence.
- [x] Task: Add tests for completeness report counters and dataset-card status rendering.
- [x] Task: Create GitHub issue `Track Task: Add completeness dashboard and publication evidence` (#30).
- [ ] Task: Conductor - User Manual Verification 'Phase 8: Publication Evidence And Completeness Dashboard' (Protocol in workflow.md)

## Acceptance Gates

- [x] No restricted full text is committed or uploaded to public publication targets.
- [x] IA full text is published only after strict source-policy, rights, and provenance gates pass.
- [x] Weak matches are visible in a manual review queue and excluded from publication bundles.
- [ ] Official HathiTrust full text supersedes IA interim text once rsync/static-host access is available.
- [x] HTRC Analytics outputs remain non-consumptive unless rights allow broader publication.
- [x] GitHub Actions dry-runs pass without secrets.
- [x] Publication workflows fail clearly when required HF, Zenodo, or static-host credentials are absent.
- [x] Completeness reports expose what remains unarchived and why.

## Validation Plan

- [x] Run targeted unit tests for source policy, matching, routing, provenance, checksums, and completeness counters.
- [x] Run workflow dry-run tests for metadata refresh, IA overlap, HTRC EF sync, and collection publish.
- [x] Run `pixi run -e dev ruff check .`.
- [x] Run `pixi run -e dev pytest tests/ -q`.
- [x] Run `pixi run -e dev actionlint` for changed workflows.
- [x] Run `git diff --check`.

## Current External Gate

- Official HathiTrust Research Dataset full-text acquisition remains blocked until
  the approved static-host endpoint, module, user, staging directory, and SSH key
  are supplied. Interim metadata and fail-closed routing remain operational.
- Repository-side status, publication-evidence, and blocker reports are now
  materialized under `reports/`; no new source credentials were used.
- No-secret smoke workflows passed on 2026-07-15 for inventory, IA fallback,
  HTRC EF planning, and Internet Archive matching.
- Full quality validation passed on 2026-07-15: 446 tests, 90.10% coverage,
  Ruff, strict Pyright, typos, Taplo, Actionlint, CodeQL, and the security gate.
- Current hosted validation passed on 2026-07-15 at commit `32461e8`: CI,
  Docs, Containerization Smoke Test, CodeQL, Security Gate, and Mirror Sync.
- [2026-07-21] GitHub Actions Internet Archive full-seed smoke run succeeded:
  run `29825993206` matched 405 of 510 records, routed 105 to manual review,
  and downloaded no full text (`dry_run=true`). The durable overlap evidence
  is preserved under `reports/internet_archive/`.
