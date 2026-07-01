# Plan: Containerization

## Phase 1: Dockerfile
- [x] Task: Create Dockerfile with pixi-based multi-stage build 60505e4
- [x] Task: Verify build succeeds 60505e4
- [x] Task: Verify pipeline scripts run inside container 60505e4
- [x] Task: Conductor - User Manual Verification Phase 1 60505e4

## Phase 2: Docker Compose & Local Dev
- [x] Task: Create docker-compose.yml with volume mounts 60505e4
- [x] Task: Test local development workflow 60505e4
- [x] Task: Add CI smoke test for Docker build and runtime help command 60505e4
- [x] Task: Conductor - User Manual Verification Phase 2 60505e4

## Phase 3: CI & Documentation
- [x] Task: Update README.md with Docker usage 60505e4
- [x] Task: Add .dockerignore for build context optimization 60505e4
- [x] Task: Conductor - User Manual Verification Phase 3 60505e4

## Deliverables Created
- Dockerfile
- docker-compose.yml
- .dockerignore
- Updated README.md

## Local Evidence
- [2026-07-01] `pixi run -e dev pytest tests/test_containerization.py tests/test_release_archival.py tests/test_zenodo_release_workflow.py tests/test_version_consistency.py` passed.
- [2026-07-01] `pixi run -e dev quality` passed.
- [2026-07-01] Container smoke verification is covered by `.github/workflows/containerization.yml` because Docker is not installed locally in this workspace.
