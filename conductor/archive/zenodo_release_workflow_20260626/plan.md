# Plan: Zenodo Release Workflow

## Phase 1: Workflow Creation
- [x] Task: Create .github/workflows/zenodo_release.yml c05adf8
- [x] Task: Wire package_release.py to build archive from git tag c05adf8
- [x] Task: Wire publish_zenodo.py to upload and publish c05adf8
- [x] Task: Add DOI capture and DATASET_CARD.md update step c05adf8
- [x] Task: Conductor - User Manual Verification Phase 1 c05adf8

## Phase 2: Secrets & Testing
- [x] Task: Document required secrets: ZENODO_TOKEN c05adf8
- [x] Task: Test workflow with sandbox Zenodo c05adf8
- [x] Task: Verify DOI is recorded correctly c05adf8
- [x] Task: Test production flag (dry-run first) c05adf8
- [x] Task: Conductor - User Manual Verification Phase 2 c05adf8

## Phase 3: Documentation
- [x] Task: Update README.md with Zenodo release instructions c05adf8
- [x] Task: Update DATASET_CARD.md Zenodo section with DOI c05adf8
- [x] Task: Add Zenodo DOI badge to README c05adf8
- [x] Task: Conductor - User Manual Verification Phase 3 c05adf8

## Deliverables Created
- .github/workflows/zenodo_release.yml
- Updated DATASET_CARD.md, README.md
- Zenodo release workflow and local validation coverage

## Local Evidence
- [2026-07-01] `pixi run -e dev pytest tests/test_zenodo_release_workflow.py tests/test_release_archival.py tests/test_version_consistency.py` passed.
- [2026-07-01] `pixi run -e dev quality` passed.
