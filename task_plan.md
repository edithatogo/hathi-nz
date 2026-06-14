# Task Plan (From Preset: legal_nlp)

Mission: Build the core data acquisition and sync pipeline for corpus-nz-hathi, including HathiTrust volume inventory mapping, incremental Hugging Face sync via GitHub Actions, and strict metadata validation.

## Delegation
- **Oracle**: Architecture design, schema definitions, complex parsing logic
- **Junior**: Environment setup, ingestion scripts, GHA workflows, TDD implementation
- **Librarian**: Metadata mapping, documentation, dataset card, naming conventions
- **Quality_Validator**: Test verification, linting, type checking, coverage validation

## Track: core_pipeline_20260613

### Phase 1: Environment & Tooling Setup ✅
- [x] Task: Initialize pixi.toml and environment configuration for Python 3.14 (Junior)
- [x] Task: Configure pyproject.toml with strict Ruff linting, formatting, and 	y type checking rules (Junior)
- [x] Task: Conductor - User Manual Verification 'Phase 1: Environment & Tooling Setup' (Protocol in workflow.md)

### Phase 2: Catalog Inventory and Mapping ✅
- [x] Task: Write tests for HathiTrust volume enumeration and catalog mapping (Junior + Quality_Validator)
- [x] Task: Implement volume enumeration, hathifile parser, and catalog manifest generation in scripts/fetch_hathitrust.py (Junior + Oracle)
- [x] Task: Conductor - User Manual Verification 'Phase 2: Catalog Inventory and Mapping'

### Phase 3: Hugging Face Staging and Syncing Pipeline ✅
- [x] Task: Write tests for Hugging Face staging and upload logic (Junior)
- [x] Task: Implement staging (download + verify + parquet) and upload (HF API push) scripts (Junior)
- [x] Task: Conductor - User Manual Verification 'Phase 3: Hugging Face Staging and Syncing Pipeline'

### Phase 4: Automated Validation and GitHub Action Integration ✅
- [x] Task: Write tests for catalog schema and data integrity validation (Junior)
- [x] Task: Implement validation suite in scripts/validate_catalog.py (Junior)
- [x] Task: Configure the scheduled GitHub Actions workflow in .github/workflows/hf_sync.yml (Librarian)
- [x] Task: Conductor - User Manual Verification 'Phase 4: Automated Validation and GitHub Action Integration'

---
## Status: ✅ ALL PHASES COMPLETE

| Phase | Status | Key Deliverables |
|-------|--------|-----------------|
| **1** — Environment & Tooling | ✅ | pixi.toml, pyproject.toml, ci.yml, test infrastructure |
| **2** — Catalog Inventory | ✅ | fetch_hathitrust.py (8 fns, 51 tests), schema.json, manifests |
| **3** — Staging & Upload | ✅ | stage_hf_dataset.py, upload_hf_dataset.py (46 tests) |
| **4** — Validation & CI/CD | ✅ | validate_catalog.py (~35 tests), hf_sync.yml |

**98+ tests passing** | **ruff check 0 errors** | **ruff format clean** | **ty typecheck 0 errors**

