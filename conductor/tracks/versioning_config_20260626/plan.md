# Plan: Dynamic Versioning & Configuration

## Phase 1: Dynamic Versioning
- [~] Task: Add hatch-vcs build dependency to pyproject.toml
- [x] Task: Replace hardcoded version with dynamic = ["version"]
- [x] Task: Remove VERSION file; add git tag for initial version
- [x] Task: Replace PIPELINE_VERSION with importlib.metadata.version()
- [ ] Task: Conductor - User Manual Verification Phase 1

## Phase 2: pydantic-settings
- [x] Task: Add pydantic-settings to core dependencies
- [x] Task: Create scripts/config.py with Settings class
- [ ] Task: Wire into upload_hf_dataset.py
- [ ] Task: Wire into publish_zenodo.py
- [ ] Task: Wire into fetch_hathitrust.py
- [x] Task: Write tests for Settings class
- [ ] Task: Conductor - User Manual Verification Phase 2

## Deliverables Created
- scripts/config.py
- Updated pyproject.toml (hatch-vcs, dynamic version)
- Updated scripts (version from importlib.metadata)
- Tests for config loading
