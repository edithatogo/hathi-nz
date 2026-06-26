# Plan: CI Infrastructure & Resilience

## Phase 1: Codecov Integration
- [ ] Task: Add Codecov action to ci.yml and hf_sync.yml workflows
- [ ] Task: Create codecov.yml configuration with target thresholds
- [ ] Task: Verify coverage uploads on push/PR
- [ ] Task: Conductor - User Manual Verification Phase 1

## Phase 2: Tenacity Retry/Backoff
- [ ] Task: Add tenacity to core dependencies
- [ ] Task: Add retry decorators to fetch_hathitrust.py HTTP calls
- [ ] Task: Add retry decorators to stage_hf_dataset.py download logic
- [ ] Task: Add retry decorators to upload_hf_dataset.py Hub operations
- [ ] Task: Write tests for retry behavior
- [ ] Task: Conductor - User Manual Verification Phase 2

## Phase 3: CI Dead Config Cleanup
- [ ] Task: Audit all Python version references across repo
- [ ] Task: Remove or wire PYTHON_VERSION env var
- [ ] Task: Align requires-python, target-version, ty python-version
- [ ] Task: Conductor - User Manual Verification Phase 3

## Deliverables Created
- codecov.yml
- CI workflow updates (Codecov, version config)
- Tenacity retry wrappers in all HTTP scripts
- Updated pyproject.toml, pixi.toml
- Tests for retry behavior
