# Plan: Zenodo Release Archival Automation (release_archival_20260613)

## Phase 1: Archive Packaging & Validation
- [~] Task: Write tests for release packager (verifying file listings and JSON schema validations).
- [~] Task: Implement package construction and `.zenodo.json` verification inside `scripts/package_release.py`.
- [ ] Task: Conductor - User Manual Verification 'Phase 1: Archive Packaging & Validation' (Protocol in workflow.md)

## Phase 2: Zenodo Upload Pipeline
- [ ] Task: Write tests for Zenodo API client operations using mock API targets.
- [ ] Task: Implement automated Zenodo deposition upload and publication script in `scripts/publish_zenodo.py`.
- [ ] Task: Conductor - User Manual Verification 'Phase 2: Zenodo Upload Pipeline' (Protocol in workflow.md)
