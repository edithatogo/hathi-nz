# HathiTrust-NZ Multi-Source Archive Track

- Track ID: `hathitrust_nz_multi_source_archive_20260702`
- Status: `in_progress`
- Seed collection: HathiTrust Collection `71329709`
- HF collection target: `edithatogo/hathitrust-nz-6a472b1e3de68381856b31f9`
- Existing compatibility dataset: `edithatogo/corpus-nz-hathi`
- New child datasets:
  - `edithatogo/hathitrust-nz-inventory`
  - `edithatogo/hathitrust-nz-research-fulltext`
  - `edithatogo/hathitrust-nz-htrc-extracted-features`
  - `edithatogo/hathitrust-nz-htrc-analytics`

## Current Repo Implementation

- Source-specific inventory builder: `scripts/hathitrust_nz_archive.py`
- Interim Internet Archive overlap planner: `scripts/hathitrust_nz_archive.py`
- Generic child dataset uploader: `scripts/upload_hf_folder.py`
- HF collection sync helper: `scripts/sync_hf_collection.py`
- GitHub Actions:
  - `.github/workflows/inventory_sync.yml`
  - `.github/workflows/research_dataset_sync.yml`
  - `.github/workflows/htrc_ef_sync.yml`
  - `.github/workflows/collection_publish.yml`
- Seed manifests: `manifests/hathitrust-nz/`

## External Gates

- `HF_TOKEN` must exist for HF dataset and collection publication.
- `ZENODO_TOKEN` or `ZENODO_SANDBOX_TOKEN` must exist for DOI publication.
- Static-host variables and SSH key are required before Hathi Research Dataset full text can be pulled into Actions.
- Restricted or Google-constrained full text must not be uploaded without explicit redistribution approval for the exact publication target.

## GitHub Issues

- #13: Track: HathiTrust-NZ collection architecture and inventory
- #14: Track Task: Build NZ Hathifiles and catalog discovery manifest
- #15: Track Task: Implement rights and redistribution classifier
- #16: Track Task: Add static-host rsync acquisition for Hathi Research Datasets
- #17: Track Task: Add HTRC Extracted Features subset acquisition
- #18: Track Task: Publish HathiTrust-NZ child datasets to Hugging Face collection
- #19: Track Task: Publish per-dataset Zenodo DOI releases
- #20: Track Task: Validate Actions, status reports, and archive completeness
