# Product Guidelines: Hathi NZ Corpus

## 1. Data Organization & Directory Structure
To maintain compatibility and align with the other New Zealand legal-nlp repositories (like `corpus-law-nz` and `corpus-nz-hansard`), the data directory must be structured systematically:
- **`data/raw/`**: Contains raw, immutable files (e.g., page-level images or unprocessed text files as acquired from HathiTrust).
- **`data/processed/`**: Stages processed files (e.g., clean text, structured OCR transcripts, and layout-aware parses).
- **`data/metadata/`**: Holds volume-level and catalog metadata, keeping files tidy and queryable.
- **`data/_state/`**: Stores local synchronization state (e.g., last crawled date, volume list, and checksums).

## 2. Ingestion & Synchronization Mechanism
Following the pattern established in `corpus-law-nz`, the dataset is kept up-to-date incrementally using automated pipelines:
- **GitHub Actions Live Sync:** A scheduled workflow (`hf_sync.yml`) runs periodically.
- **State Restoration:** The workflow begins by restoring the current dataset snapshot from Hugging Face via `huggingface_hub.snapshot_download` into `data/`.
- **Incremental Fetching:** The script checks the HathiTrust catalog/data API for any new volumes or updates matching the collection ID (`71329709`), fetching only what is missing.
- **Manifest Generation:** Updates metadata sidecars, schemas, and a central `manifests/latest_manifest.json` detailing all volumes.
- **Hugging Face Publish:** Uploads the updated directory to the Hugging Face dataset repository under `edithatogo/` using a secure token.

## 3. Metadata Standards & Reproducibility
- **Standardized Sidecars:** Every volume or file group must be accompanied by a JSON/YAML metadata sidecar. This file records the original HathiTrust ID (`htid`), volume details, OCLC number, and original publication date.
- **Open Science & Citability:** Packaged releases will be registered on Zenodo with a `.zenodo.json` metadata description to mint persistent DOIs for academic citing.
- **Permissive Licensing:** Enforce CC-BY-4.0 or CC0 licensing for all extracted and clean texts where rights allow, ensuring global researcher accessibility.

## 4. Progressive Processing Pipeline
- **Phase 1 (Raw Transfer):** Focus entirely on automating volume discovery, downloading raw text/metadata, and publishing to Hugging Face.
- **Phase 2 (OCR & Refinement):** Integrate OCR enhancement and layout-aware extraction, utilizing shared processing scripts in `nlp-policy-nz` to avoid code duplication.
