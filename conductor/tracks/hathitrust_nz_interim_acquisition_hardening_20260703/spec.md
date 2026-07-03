# Specification: HathiTrust-NZ Interim Acquisition Hardening

## Overview

This track implements interim acquisition and provenance hardening for the HathiTrust-NZ collection while official HathiTrust Research Dataset rsync access is pending. It complements `hathitrust_nz_multi_source_archive_20260702` by turning the recommended interim mechanisms into a tested, GitHub Actions-driven pipeline that can discover, stage, validate, and publish public-domain overlap content without storing large data locally.

The track keeps HathiTrust identifiers and rights metadata as the canonical collection spine. Internet Archive and other public sources are used only as interim content sources when they can be confidently matched to HathiTrust NZ records and when redistribution is safe. Restricted HathiTrust full text remains excluded from public Hugging Face and Zenodo uploads.

## Goals

- Use GitHub Actions as the default execution environment for discovery, metadata refresh, packaging, publication, and status reporting.
- Add a source policy registry that defines which sources may provide metadata, derived features, full text, OCR text, or only manual review evidence.
- Add conservative Internet Archive and Open Library overlap routing for public-domain full text until HathiTrust rsync access is available.
- Add HathiTrust metadata refresh lanes using Hathifiles, OAI-PMH, and the Bibliographic API.
- Add HTRC discovery and non-consumptive output lanes using HTRC EF Solr, Extracted Features 2.0 or 2.5, and HTRC Analytics outputs.
- Add optional NZ source enrichment lanes for DigitalNZ, National Library NZ, Papers Past, and official parliamentary sources where they overlap with HathiTrust NZ records.
- Add provenance, checksum, confidence, and manual review artifacts so weak matches cannot silently become published full text.
- Add source-priority routing so official HathiTrust sources supersede interim mirrors when available.
- Improve completeness reporting across known records, matched public records, downloaded content, validated content, published Hugging Face datasets, and Zenodo deposits.

## Functional Requirements

### Source Policy Registry

- Define a machine-readable registry for every acquisition source.
- Each source entry must include:
  - source ID and display name.
  - source URL and API endpoint family.
  - permitted artifact classes: metadata, manifest, full text, OCR text, derived features, aggregate analytics.
  - rights/licence requirements.
  - access class: public, public-with-rate-limits, approved-static-host, restricted, or manual-review-only.
  - default acquisition mode: GitHub Actions, static rsync host, manual staging, or disabled.
  - publication eligibility rules for Hugging Face and Zenodo.
- Direct Anna's Archive download automation is out of scope unless a future legal review explicitly approves it. The pipeline may record manually supplied bibliographic evidence, but must not automate downloads from legally ambiguous mirrors.

### Metadata Refresh Lanes

- Implement or formalize refresh jobs for:
  - Hathifiles inventory and rights/access metadata.
  - HathiTrust OAI-PMH incremental metadata.
  - HathiTrust Bibliographic API enrichment for known identifiers.
  - HTRC EF Solr discovery and workset candidate queries.
  - Internet Archive and Open Library crosswalk enrichment.
  - Optional DigitalNZ, National Library NZ, Papers Past, and official parliamentary source candidate metadata.
- Preserve the 510-record Hansard seed as a distinct curated collection, separate from broad NZ discovery candidates.
- Emit source-specific manifests and a merged canonical routing manifest.

### Interim Internet Archive Acquisition

- Match HathiTrust records to Internet Archive items only when title, creator, year, identifier, or catalog evidence meets a defined confidence threshold.
- Do not use first-result fallback matching.
- Download only public-domain or otherwise clearly redistributable text/OCR artifacts.
- Emit:
  - overlap manifest.
  - provenance ledger.
  - checksum and file-size manifest.
  - manual review queue for ambiguous candidates.
  - source evidence report.
- Fail closed for rights codes or source policies that do not permit public full-text redistribution.

### HTRC Extracted Features And Analytics

- Use HTRC EF Solr and Extracted Features manifests to build NZ workset candidates.
- Prefer Extracted Features 2.5 where available; support EF 2.0 discovery where necessary.
- Publish HTRC Extracted Features subsets as non-consumptive open artifacts when source licence and size permit.
- Publish HTRC Analytics outputs as scripts, aggregate metrics, reproducibility metadata, and workset definitions, not restricted full text.

### Source Priority And Publication Routing

- Prefer official HathiTrust Research Dataset full text once static-host rsync access is available.
- Use Internet Archive as interim content only for confidently matched public-domain overlap records.
- Prefer HTRC Extracted Features for non-consumptive analysis when full text is unavailable or restricted.
- Use metadata-only publication for restricted, uncertain, or unavailable content.
- Keep Hugging Face and Zenodo publication paths reusable from existing scripts.

### GitHub Actions

- All routine acquisition and publication work must be runnable from GitHub Actions.
- Large or long-running official Hathi rsync jobs may still run on a static host, with GitHub Actions consuming staged manifests or bundles.
- Workflows must support dry-run execution without secrets.
- Publication workflows must validate source policy and rights decisions before upload.

### Completeness And Evidence

- Generate a completeness dashboard/report with counts by source family and route:
  - known HathiTrust records.
  - public redistributable records.
  - metadata enriched records.
  - IA/Open Library matched records.
  - IA full-text downloaded records.
  - HTRC EF available records.
  - manual review required records.
  - Hugging Face published records.
  - Zenodo deposited records.
- Link reports back to Conductor, GitHub issues, and dataset cards.

## Non-Functional Requirements

- No restricted full text may be uploaded to Hugging Face, Zenodo, GitHub artifacts intended for publication, or committed repository paths.
- Large downloaded content must stay out of the git repository.
- All matching and rights decisions must be reproducible from committed manifests and source evidence.
- Acquisition scripts must be resumable, rate-limit aware, and safe to run repeatedly.
- Tests must cover matching, rights gates, publication routing, provenance output, checksum output, and workflow dry-run behavior.

## Acceptance Criteria

- A source policy registry exists and is used by acquisition and publication planning code.
- Internet Archive overlap acquisition emits a provenance ledger, checksum manifest, review queue, and completeness counters.
- Weak or ambiguous IA matches are routed to manual review and are not downloaded or published as trusted full text.
- Hathifiles, OAI-PMH, Bibliographic API, HTRC EF Solr, HTRC EF, IA/Open Library, and optional NZ enrichment sources are represented in source-specific manifests.
- GitHub Actions can dry-run discovery, IA overlap, HTRC EF, completeness, and collection publication without secrets.
- Full publication paths require the appropriate Hugging Face, Zenodo, and static-host secrets.
- Dataset cards and completeness reports describe which records are official HathiTrust, IA interim, HTRC EF, analytics-only, metadata-only, or blocked.
- The existing `hathitrust_nz_multi_source_archive_20260702` track remains compatible and does not lose its blocker evidence.

## Out Of Scope

- Automating direct downloads from Anna's Archive or similar legally ambiguous mirrors.
- Publishing restricted HathiTrust Research Dataset full text without explicit approval for the target publication platform.
- Treating broad NZ discovery candidates as part of the curated 510-record Hansard seed without explicit promotion.
- Local bulk archiving on the workstation.
