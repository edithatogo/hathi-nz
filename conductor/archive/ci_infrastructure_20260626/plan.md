# Plan: CI Infrastructure & Resilience

## Phase 1: Codecov Integration
- [x] Task: Add Codecov action to ci.yml and hf_sync.yml workflows
- [x] Task: Create codecov.yml configuration with target thresholds
- [x] Task: Verify coverage uploads on push/PR
- [x] Task: Conductor - User Manual Verification Phase 1

## Phase 2: Tenacity Retry/Backoff
- [x] Task: Add tenacity to core dependencies
- [x] Task: Add retry decorators to fetch_hathitrust.py HTTP calls
- [x] Task: Add retry decorators to stage_hf_dataset.py download logic
- [x] Task: Add retry decorators to upload_hf_dataset.py Hub operations
- [x] Task: Write tests for retry behavior
- [x] Task: Conductor - User Manual Verification Phase 2

## Phase 3: CI Dead Config Cleanup
- [x] Task: Audit all Python version references across repo
- [x] Task: Remove or wire PYTHON_VERSION env var
- [x] Task: Align requires-python, target-version, ty python-version
- [x] Task: Conductor - User Manual Verification Phase 3

## Deliverables Created
- codecov.yml
- CI workflow updates (Codecov, version config)
- Tenacity retry wrappers in all HTTP scripts
- Updated pyproject.toml, pixi.toml
- Tests for retry behavior

## Local Evidence
- [2026-07-01] `pixi run -e dev pytest tests/test_code_quality_tooling.py` passed.
- [2026-07-01] `pixi run -e dev pytest tests/test_version.py tests/test_version_consistency.py tests/test_code_quality_tooling.py` passed.
- [2026-07-01] `pixi run -e dev test -- --cov --cov-report=term-missing --cov-report=xml --cov-fail-under=75` passed with 273 tests and 75.63% coverage.
- [2026-07-01] GitHub Actions run `28512319300` passed `lint`, `typecheck`, `test` (including Codecov OIDC upload), and `mutmut`.
- [2026-07-01] `pixi run -e dev pyright-check` and `pixi run -e dev pre-commit run --all-files` passed.
