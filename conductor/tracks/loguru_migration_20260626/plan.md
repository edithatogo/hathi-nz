# Plan: Loguru Migration

## Phase 1: Core Script Migration
- [ ] Task: Migrate scripts/fetch_hathitrust.py to loguru
- [ ] Task: Migrate scripts/stage_hf_dataset.py to loguru
- [ ] Task: Migrate scripts/upload_hf_dataset.py to loguru
- [ ] Task: Migrate scripts/validate_catalog.py to loguru
- [ ] Task: Migrate scripts/ocr_extract.py to loguru
- [ ] Task: Conductor - User Manual Verification Phase 1

## Phase 2: Test & Config Updates
- [ ] Task: Update test fixtures that mock logging to mock loguru
- [ ] Task: Add loguru handler config in each main() entry point
- [ ] Task: Verify all tests pass after migration
- [ ] Task: Verify consistent log format across all stages
- [ ] Task: Conductor - User Manual Verification Phase 2

## Deliverables Created
- Updated scripts (all 5 pipeline scripts + cli.py)
- Updated tests (test fixtures for loguru mocking)
- Consistent log format established
