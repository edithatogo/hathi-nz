# Plan: Dynamic Versioning & Configuration

## Phase 1: Dynamic Versioning
- [x] Task: Add hatch-vcs build dependency to pyproject.toml
- [x] Task: Replace hardcoded version with dynamic = ["version"]
- [x] Task: Remove VERSION file; add git tag for initial version
- [x] Task: Replace PIPELINE_VERSION with importlib.metadata.version()
- [ ] Task: Conductor - User Manual Verification Phase 1

## Phase 2: pydantic-settings
- [x] Task: Add pydantic-settings to core dependencies
- [x] Task: Create scripts/config.py with Settings class
- [x] Task: Wire into upload_hf_dataset.py
- [x] Task: Wire into publish_zenodo.py
- [x] Task: Wire into fetch_hathitrust.py
- [x] Task: Write tests for Settings class
- [ ] Task: Conductor - User Manual Verification Phase 2

## Deliverables Created
- scripts/config.py
- Updated pyproject.toml (hatch-vcs, dynamic version)
- Updated scripts (version from importlib.metadata)
- Tests for config loading

## Phase: Review Fixes
- [x] Task: Apply review suggestions c6b2d48

## Local Evidence
- [2026-07-01] `pixi run -e dev pytest tests/test_version.py tests/test_version_consistency.py` passed.
- [2026-07-01] `pixi run -e dev pyright-check` and `pixi run -e dev pre-commit run --all-files` passed.
- [2026-07-01] `pixi run -e dev test -- --cov --cov-report=term-missing --cov-report=xml --cov-fail-under=75` passed with 272 tests and 75.96% coverage.
