# Plan: Zenodo Release Archival Automation (release_archival_20260613)

## Phase 1: Archive Packaging & Validation
- [x] Task: Write tests for release packager (verifying file listings and JSON schema validations).
- [x] Task: Implement package construction and `.zenodo.json` verification inside `scripts/package_release.py`.
- [x] Task: Conductor - User Manual Verification 'Phase 1: Archive Packaging & Validation' (Protocol in workflow.md) [ac19f96]

## Phase 2: Zenodo Upload Pipeline
- [x] Task: Write tests for Zenodo API client operations using mock API targets.
- [x] Task: Implement automated Zenodo deposition upload and publication script in `scripts/publish_zenodo.py`.
- [x] Task: Conductor - User Manual Verification 'Phase 2: Zenodo Upload Pipeline' (Protocol in workflow.md) [ac19f96]

## Local Evidence
- [2026-06-14] Added `scripts/package_release.py`, `scripts/publish_zenodo.py`, and `tests/test_release_archival.py`.
- [2026-06-14] `tests/test_release_archival.py` passes and the full local suite passes.
- [2026-06-14] Actual Zenodo deposition creation, file upload, and publication remain gated external-account actions.
- [2026-07-01] `pixi run -e dev pytest tests/test_release_archival.py -q` passed.
- [2026-07-01] `pixi run -e dev quality` passed.
- [2026-07-01] Added DOI writeback to `DATASET_CARD.md` after publication and regression coverage for the update path.
