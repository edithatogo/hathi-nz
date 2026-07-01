# Plan: Loguru Migration

## Phase 1: Core Script Migration
- [x] Task: Migrate scripts/fetch_hathitrust.py to loguru 50140b9
- [x] Task: Migrate scripts/stage_hf_dataset.py to loguru 50140b9
- [x] Task: Migrate scripts/upload_hf_dataset.py to loguru 50140b9
- [x] Task: Migrate scripts/validate_catalog.py to loguru 50140b9
- [x] Task: Migrate scripts/ocr_extract.py to loguru 50140b9
- [x] Task: Conductor - User Manual Verification Phase 1 50140b9

## Phase 2: Test & Config Updates
- [x] Task: Update test fixtures that mock logging to mock loguru 50140b9
- [x] Task: Add loguru handler config in each main() entry point 50140b9
- [x] Task: Verify all tests pass after migration 50140b9
- [x] Task: Verify consistent log format across all stages 50140b9
- [x] Task: Conductor - User Manual Verification Phase 2 50140b9

## Deliverables Created
- Updated scripts (all 5 pipeline scripts + cli.py)
- Updated tests (test fixtures for loguru mocking)
- Consistent log format established

## Local Evidence
- [2026-07-01] `pixi run -e dev pytest tests/test_logging_utils.py tests/test_stage_hf_dataset.py tests/test_fetch_hathitrust.py tests/test_upload_hf_dataset.py tests/test_validate_catalog.py tests/test_ocr_extract.py` passed.
- [2026-07-01] `pixi run -e dev pytest` passed with 274 tests and 76.09% coverage.
- [2026-07-01] `pixi run -e dev pyright-check` passed.
- [2026-07-01] `pixi run -e dev lint` and `pixi run -e dev format-check` passed.
