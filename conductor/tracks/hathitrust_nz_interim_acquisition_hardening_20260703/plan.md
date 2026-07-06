# Plan: HathiTrust-NZ Interim Acquisition Hardening (hathitrust_nz_interim_acquisition_hardening_20260703)

## Phase 1: Track Bootstrap And Governance

- [x] Task: Create Conductor track artifacts for interim acquisition hardening.
- [x] Task: Create GitHub parent issue `Track: HathiTrust-NZ interim acquisition and provenance hardening` (#21).
- [x] Task: Cross-link this track from `hathitrust_nz_multi_source_archive_20260702` without replacing the existing blocker evidence.
- [x] Task: Define implementation issue set for source policy, metadata refresh, IA acquisition, HTRC EF, NZ enrichment, publication gates, and completeness reporting (#22-#28).
- [ ] Task: Conductor - User Manual Verification 'Phase 1: Track Bootstrap And Governance' (Protocol in workflow.md)

## Phase 2: Source Policy Registry

- [ ] Task: Add a machine-readable source policy registry for HathiTrust, Hathifiles, OAI-PMH, Bibliographic API, HTRC Solr EF20, HTRC Extracted Features, HTRC Analytics, Internet Archive, Open Library, DigitalNZ, National Library NZ, Papers Past, official parliamentary sources, static rsync staging, and manual evidence.
- [ ] Task: Add policy fields for permitted artifact classes, licence evidence, access class, acquisition mode, publication eligibility, and source priority.
- [ ] Task: Add fail-closed routing for unknown, restricted, legally ambiguous, or manual-review-only source classes.
- [ ] Task: Add unit tests for policy loading, source priority ordering, and publication eligibility decisions.
- [ ] Task: Create GitHub issue `Track Task: Add HathiTrust-NZ source policy registry` (#22).
- [ ] Task: Conductor - User Manual Verification 'Phase 2: Source Policy Registry' (Protocol in workflow.md)

## Phase 3: Metadata Refresh And Discovery Lanes

- [ ] Task: Add or extend Hathifiles refresh outputs for broad NZ inventory, rights, access profile, and digitization profile.
- [ ] Task: Add OAI-PMH incremental metadata refresh with cursor state, retry/backoff, and dry-run output.
- [ ] Task: Add Bibliographic API enrichment for known HTIDs, OCLC records, catalog IDs, creator/title/year normalization, and enumeration gaps.
- [ ] Task: Add HTRC EF Solr discovery/workset candidate generation for NZ-relevant records.
- [ ] Task: Add IA/Open Library crosswalk enrichment for identifiers, creators, titles, years, OCLC, and evidence URLs.
- [ ] Task: Add optional NZ enrichment manifest lanes for DigitalNZ, National Library NZ, Papers Past, and official parliamentary sources.
- [ ] Task: Keep the 510-record Hansard seed distinct from broad NZ discovery outputs.
- [ ] Task: Add tests for manifest separation, cursor state, enrichment merge precedence, and discovery count drift.
- [ ] Task: Create GitHub issue `Track Task: Add metadata refresh lanes for HathiTrust-NZ` (#23).
- [ ] Task: Conductor - User Manual Verification 'Phase 3: Metadata Refresh And Discovery Lanes' (Protocol in workflow.md)

## Phase 4: Internet Archive Interim Full-Text Acquisition

- [ ] Task: Harden IA matching with confidence scores, evidence fields, and no first-result fallback.
- [ ] Task: Add Open Library and IA metadata crosswalk evidence before full-text acquisition.
- [ ] Task: Emit IA overlap manifest, matched HTID list, IA identifier list, provenance ledger, source evidence report, checksum/file manifest, and manual review queue.
- [ ] Task: Download only public-domain or redistributable IA text/OCR artifacts under GitHub Actions or artifact staging paths, not git.
- [ ] Task: Route weak, ambiguous, or conflicting matches to manual review and block publication.
- [ ] Task: Add quality metrics for OCR/text availability, file size, checksum, source timestamp, and candidate confidence.
- [ ] Task: Add scheduled IA smoke workflow with small record limits and dry-run defaults.
- [ ] Task: Add tests for strict matches, title-only ambiguity, creator mismatches, checksum generation, provenance output, and review queue output.
- [ ] Task: Create GitHub issue `Track Task: Harden Internet Archive interim acquisition` (#24).
- [ ] Task: Conductor - User Manual Verification 'Phase 4: Internet Archive Interim Full-Text Acquisition' (Protocol in workflow.md)

## Phase 5: HTRC Extracted Features And Analytics Outputs

- [ ] Task: Add HTRC EF 2.0 and 2.5 source metadata into the source policy and discovery manifests.
- [ ] Task: Use HTRC EF Solr candidate results to build reproducible NZ worksets.
- [ ] Task: Acquire open HTRC Extracted Features subsets when runner size and source policy permit.
- [ ] Task: Route large HTRC EF subsets through static-host staging when GitHub runner limits are exceeded.
- [ ] Task: Publish HTRC Analytics outputs as scripts, aggregate results, workset definitions, and reproducibility metadata only.
- [ ] Task: Add tests for EF path generation, workset generation, analytics-only routing, and static-host fallback decisions.
- [ ] Task: Create GitHub issue `Track Task: Add HTRC EF and Analytics interim outputs` (#25).
- [ ] Task: Conductor - User Manual Verification 'Phase 5: HTRC Extracted Features And Analytics Outputs' (Protocol in workflow.md)

## Phase 6: Source Priority Routing And Rights Gates

- [ ] Task: Merge source policy, rights classifier, IA evidence, HTRC evidence, and HathiTrust metadata into a canonical routing manifest.
- [ ] Task: Prefer official HathiTrust Research Dataset full text when static-host rsync is available.
- [ ] Task: Prefer IA public-domain overlap while HathiTrust full text is unavailable.
- [ ] Task: Prefer HTRC EF or analytics-only routes when full text is restricted or unavailable.
- [ ] Task: Preserve metadata-only routes for uncertain, restricted, page-only, or manually reviewed records.
- [ ] Task: Add tests that publication fails closed when rights, source policy, or provenance evidence is incomplete.
- [ ] Task: Create GitHub issue `Track Task: Add source-priority routing and rights gates` (#26).
- [ ] Task: Conductor - User Manual Verification 'Phase 6: Source Priority Routing And Rights Gates' (Protocol in workflow.md)

## Phase 7: GitHub Actions Orchestration

- [ ] Task: Add or update workflows for source policy validation, metadata refresh, IA overlap smoke, HTRC EF sync, completeness reporting, and collection publication.
- [ ] Task: Ensure every routine workflow supports dry-run execution without secrets.
- [ ] Task: Ensure publication jobs require explicit `HF_TOKEN`, `ZENODO_TOKEN` or `ZENODO_SANDBOX_TOKEN`, and static-host secrets where needed.
- [ ] Task: Keep static rsync acquisition on the configured host and have Actions consume staged bundles or manifests.
- [ ] Task: Add workflow tests and `actionlint` coverage for changed workflows.
- [ ] Task: Create GitHub issue `Track Task: Wire interim acquisition GitHub Actions` (#27).
- [ ] Task: Conductor - User Manual Verification 'Phase 7: GitHub Actions Orchestration' (Protocol in workflow.md)

## Phase 8: Publication Evidence And Completeness Dashboard

- [ ] Task: Extend completeness reports with counts for known, public, enriched, IA-matched, IA-downloaded, HTRC EF-available, review-required, HF-published, and Zenodo-deposited records.
- [ ] Task: Add dataset-card sections that identify official HathiTrust, IA interim, HTRC EF, analytics-only, metadata-only, and blocked routes.
- [ ] Task: Add DOI/HF status writeback for interim-source child dataset artifacts.
- [x] Task: Synchronize GitHub issues, project fields, and redundancy-label taxonomy with blocker status and completion evidence.
- [ ] Task: Add tests for completeness report counters and dataset-card status rendering.
- [ ] Task: Create GitHub issue `Track Task: Add completeness dashboard and publication evidence` (#28).
- [ ] Task: Conductor - User Manual Verification 'Phase 8: Publication Evidence And Completeness Dashboard' (Protocol in workflow.md)

## Acceptance Gates

- [ ] No restricted full text is committed or uploaded to public publication targets.
- [ ] IA full text is published only after strict source-policy, rights, and provenance gates pass.
- [ ] Weak matches are visible in a manual review queue and excluded from publication bundles.
- [ ] Official HathiTrust full text supersedes IA interim text once rsync/static-host access is available.
- [ ] HTRC Analytics outputs remain non-consumptive unless rights allow broader publication.
- [ ] GitHub Actions dry-runs pass without secrets.
- [ ] Publication workflows fail clearly when required HF, Zenodo, or static-host credentials are absent.
- [ ] Completeness reports expose what remains unarchived and why.

## Validation Plan

- [ ] Run targeted unit tests for source policy, matching, routing, provenance, checksums, and completeness counters.
- [ ] Run workflow dry-run tests for metadata refresh, IA overlap, HTRC EF sync, and collection publish.
- [ ] Run `pixi run -e dev ruff check .`.
- [ ] Run `pixi run -e dev pytest tests/ -q`.
- [ ] Run `pixi run -e dev actionlint` for changed workflows.
- [ ] Run `git diff --check`.
