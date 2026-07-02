# Specification: HathiTrust-NZ Multi-Source Archive (hathitrust_nz_multi_source_archive_20260702)

## 1. Summary

Turn HathiTrust-NZ into a collection-level archive. The collection links the
existing `edithatogo/corpus-nz-hathi` dataset with separate child datasets for
inventory metadata, Hathi Research Dataset full text, HTRC Extracted Features,
and HTRC Analytics outputs.

The archival process must run from GitHub Actions wherever practical. Large or
approval-bound full-text acquisition must run through a static rsync host, then
GitHub Actions may package and publish the staged outputs.

## 2. Source Model

- Hugging Face collection target: `edithatogo/hathitrust-nz`
- Existing compatibility dataset: `edithatogo/corpus-nz-hathi`
- New inventory dataset: `edithatogo/hathitrust-nz-inventory`
- New Research Dataset dataset: `edithatogo/hathitrust-nz-research-fulltext`
- New HTRC Extracted Features dataset: `edithatogo/hathitrust-nz-htrc-extracted-features`
- New HTRC Analytics dataset: `edithatogo/hathitrust-nz-htrc-analytics`
- Zenodo: one DOI-backed release stream per child dataset, linked from the collection manifest.

## 3. Seed Collection Inventory

The canonical seed remains HathiTrust Collection `71329709`.

- Dataset ID: `nz_parliamentary_debates_hansard`
- HathiTrust Collection: `71329709`
- Catalog record: `007119315`
- Source namespace: `uc1`
- Author: `New Zealand. Parliament`
- Documented span: 1854 to 1990
- Expected HTID count: 510
- Rights baseline: all 510 local export rows have rights code `17`
- Rights interpretation: HathiTrust rights docs define `17` as `cc-zero`, implying public-domain-equivalent redistribution.
- Normalization gap: 369 rows expose exact `v.N` labels; 141 rows need catalog or enumeration enrichment.

Expanded discovery must later include parliamentary/legal serials, government
reports, policy/statistics serials, NZ scholarly and cultural serials, and
Maori/Aotearoa materials. Discovery sources include Hathifiles, catalog records,
public collections, Bibliographic API lookups for known identifiers, and HTRC
Workset Builder or Extracted Features search.

## 4. Rights And Access Rules

Public HF/Zenodo archives may contain:

- Metadata, manifests, HTID lists, workset definitions, checksums, and generated derived metadata.
- Full text only when the volume is confirmed public-domain or Creative Commons and redistribution is allowed.
- HTRC Extracted Features 2.5 subset data, because it is an open, CC-BY-4.0, non-consumptive derived dataset.

Restricted handling:

- Hathi Research Dataset full text, including Google-digitized volumes, is not public-rehostable by default.
- HTRC Data Capsule outputs from restricted full text are represented publicly only as scripts, aggregate outputs, and reproducibility metadata.
- `pdus`, `ic`, `ic-world`, `und`, `supp`, Google-restricted, privacy-limited, or page-only records must fail closed for public full-text upload.

## 5. Acquisition Modes

GitHub Actions is responsible for:

- Inventory generation and source-specific manifest validation.
- Rights and redistribution classification.
- HTRC EF subset file-list generation and small direct rsync syncs.
- Packaging, validation, HF upload, Zenodo deposition, and DOI writeback.

The static rsync host is responsible for:

- Hathi Research Dataset full-text acquisition because approval is tied to a static IP and the rsync job can run for a day or more.
- Large HTRC EF subsets if GitHub runner disk or time limits are exceeded.

Required static-host configuration:

- `HATHI_RSYNC_HOST`
- `HATHI_RSYNC_MODULE`
- `HATHI_RSYNC_USER`
- `HATHI_STATIC_HOST_SSH_KEY`
- `HATHI_STATIC_HOST_STAGING_DIR`

## 6. Pipeline Requirements

- Replace stale `manifests/latest_manifest.json` use in the new archive path with generated source-specific manifests.
- Fail if the curated 510-row Hansard seed count drifts unexpectedly.
- Include dataset ID, access class, acquisition mode, source URL, source dataset name, rights code, digitization/access profile, and publish eligibility fields.
- Provide workflows for inventory sync, Research Dataset static-host sync, HTRC EF sync, and collection publication.
- Reuse existing HF/Zenodo clients where possible.

## 7. Test Plan

- Unit tests for HTID/path normalization, rights classification, dataset routing, and fail-closed publication decisions.
- Manifest tests proving the 510-row Hansard collection remains distinct from broad Hathifile search results.
- Workflow dry-run tests for HF and Zenodo publication without secrets.
- Integration smoke tests with a 1 to 3 volume public subset for Research Datasets and HTRC EF.
- Acceptance gate: no restricted full text is uploaded to HF or Zenodo; each child dataset has a manifest, dataset card, DOI status, source citation, and archive completeness report.

## 8. Planning Sources

- HathiTrust Research Datasets: https://www.hathitrust.org/member-libraries/resources-for-librarians/data-resources/research-datasets/
- Hathifiles Description: https://www.hathitrust.org/member-libraries/resources-for-librarians/data-resources/hathifiles/hathifiles-description/
- HathiTrust Rights Database: https://www.hathitrust.org/the-collection/preservation/rights-database/
- HTRC Extracted Features 2.5: https://htrc.atlassian.net/wiki/spaces/COM/pages/975306753
- HTRC Workset Toolkit: https://htrc.github.io/HTRC-WorksetToolkit/cli.html
