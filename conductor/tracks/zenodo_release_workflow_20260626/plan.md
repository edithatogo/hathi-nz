# Plan: Zenodo Release Workflow

## Phase 1: Workflow Creation
- [~] Task: Create .github/workflows/zenodo_release.yml
- [ ] Task: Wire package_release.py to build archive from git tag
- [ ] Task: Wire publish_zenodo.py to upload and publish
- [ ] Task: Add DOI capture and DATASET_CARD.md update step
- [ ] Task: Conductor - User Manual Verification Phase 1

## Phase 2: Secrets & Testing
- [ ] Task: Document required secrets: ZENODO_TOKEN
- [ ] Task: Test workflow with sandbox Zenodo
- [ ] Task: Verify DOI is recorded correctly
- [ ] Task: Test production flag (dry-run first)
- [ ] Task: Conductor - User Manual Verification Phase 2

## Phase 3: Documentation
- [ ] Task: Update README.md with Zenodo release instructions
- [ ] Task: Update DATASET_CARD.md Zenodo section with DOI
- [ ] Task: Add Zenodo DOI badge to README
- [ ] Task: Conductor - User Manual Verification Phase 3

## Deliverables Created
- .github/workflows/zenodo_release.yml
- Updated DATASET_CARD.md, README.md
- First Zenodo deposition (sandbox verified)
