# Plan: Core Data Acquisition & Sync Pipeline (core_pipeline_20260613)

This plan implements the core pipeline following the Test-Driven Development (TDD) and Phase Completion Verification guidelines.

## Phase 1: Environment & Tooling Setup
- [ ] Task: Initialize `pixi.toml` and environment configuration for Python 3.14, including Polars, PyArrow, DuckDB, requests, and huggingface-hub.
- [ ] Task: Configure `pyproject.toml` with strict Ruff linting, formatting, and `ty` type checking rules.
- [ ] Task: Conductor - User Manual Verification 'Phase 1: Environment & Tooling Setup' (Protocol in workflow.md)

## Phase 2: Catalog Inventory and Mapping
- [ ] Task: Write tests for HathiTrust volume enumeration and catalog mapping.
- [ ] Task: Implement volume enumeration, Wayback page listing parser, and catalog manifest generation in `scripts/fetch_hathitrust.py`.
- [ ] Task: Conductor - User Manual Verification 'Phase 2: Catalog Inventory and Mapping' (Protocol in workflow.md)

## Phase 3: Hugging Face Staging and Syncing Pipeline
- [ ] Task: Write tests for Hugging Face snapshot restoration, staging, and upload logic.
- [ ] Task: Implement snapshot download, staging, and dataset upload logic in `scripts/stage_hf_dataset.py` and `scripts/upload_hf_dataset.py`.
- [ ] Task: Conductor - User Manual Verification 'Phase 3: Hugging Face Staging and Syncing Pipeline' (Protocol in workflow.md)

## Phase 4: Automated Validation and GitHub Action Integration
- [ ] Task: Write tests for catalog schema and data integrity validation.
- [ ] Task: Implement validation suite in `scripts/validate_catalog.py` using Polars and `jsonschema`.
- [ ] Task: Configure the scheduled GitHub Actions workflow in `.github/workflows/hf_sync.yml` to run the daily sync and validate steps.
- [ ] Task: Conductor - User Manual Verification 'Phase 4: Automated Validation and GitHub Action Integration' (Protocol in workflow.md)
