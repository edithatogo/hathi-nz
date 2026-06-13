# Specification: Core Data Acquisition & Sync Pipeline (core_pipeline_20260613)

## 1. Overview & Context
This track implements the foundational raw data acquisition, inventory management, and publishing/sync pipeline for `hathi-nz`. 
Following the architectural patterns established in `corpus-law-nz` and `corpus-nz-hansard`, this repository focuses exclusively on:
1. **Cataloging & Volume Mapping:** Establishing a verified database/JSON representation of the 510 NZ Parliamentary Debates volumes (1854-1990) in HathiTrust Collection ID `71329709`.
2. **Hugging Face Live Sync:** Staging files in an organized directory structure and incrementally syncing them to the Hugging Face dataset repository under the `edithatogo` organization.
3. **Reproducibility & Open Science:** Preparing metadata sidecars for future Zenodo archive creation.
4. **Environment & Clean Code:** Leveraging `pixi` for Python 3.14 dependency management, Ruff for strict style checks, and `ty` for typing correctness.

All processing logic is kept separate from data, with common utilities structured to eventually integrate with the shared `nlp-policy-nz` library.

## 2. Directory Structure
```
hathi-nz/
├── conductor/               # Conductor configurations & tracks
├── data/
│   ├── raw/                 # Raw page scans / unmodified text files (Git ignored)
│   ├── processed/           # OCR processed and refined texts (Git ignored)
│   ├── metadata/            # Standardized volume-level sidecar JSON/YAML files
│   └── _state/              # Local tracking files (sync_state.json)
├── manifests/               # Dataset schemas and manifest files
│   ├── latest_manifest.json # Catalog of all volumes, hashes, and sizes
│   └── schema.json          # Schema constraints for volume records
├── scripts/                 # Ingestion, validation, and upload scripts
│   ├── fetch_hathitrust.py  # Crawling and volume mapping
│   ├── stage_hf_dataset.py  # Staging dataset structures
│   ├── upload_hf_dataset.py # Interfacing Hugging Face Hub APIs
│   └── validate_catalog.py  # Checking catalog formats and sizes
├── .github/
│   └── workflows/
│       └── hf_sync.yml      # Scheduled GitHub Actions pipeline
├── pixi.toml                # Environment dependencies for Python 3.14
└── pyproject.toml           # Ruff and type enforcement options
```

## 3. Detailed Components

### 3.1 Environment & Package Management (`pixi.toml`)
- Configure `pixi.toml` to build a environment using Python 3.14.
- Include core dependencies: `duckdb`, `polars`, `pyarrow`, `huggingface-hub`, `requests`, `pydantic`.
- Include development/validation dependencies: `pytest`, `pytest-cov`, `ruff`, `ty`.

### 3.2 Volume Enumeration & Mapping (`fetch_hathitrust.py`)
- Standardize HathiTrust crawler options.
- Support waypoint backup parsing (Wayback Machine page listings) and hathifile dump analysis.
- Produce `manifests/latest_manifest.json` as the source of truth catalog.

### 3.3 Incremental Sync Pipeline (`hf_sync.yml` & `upload_hf_dataset.py`)
- Sync should run daily via GitHub Actions schedule.
- Uses `huggingface_hub.snapshot_download` to fetch the current remote status.
- Compares remote hashes/files against the local manifest.
- Downloads new/missing volumes and publishes them back to the Hugging Face repository.

### 3.4 Strict Validation (`validate_catalog.py`)
- Uses Polars and PyArrow to validate that all structured catalog items conform to `manifests/schema.json`.
- Enforces checksum verification and data integrity checks.
