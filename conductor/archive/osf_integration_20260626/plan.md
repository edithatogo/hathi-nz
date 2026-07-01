# Plan: OSF Integration

## Phase 1: OSF Client Library
- [x] Task: Add osfclient to core dependencies dc09715
- [x] Task: Create .osf.json with OSF metadata dc09715
- [x] Task: Implement scripts/publish_osf.py dc09715
- [x] Task: Add dry-run mode dc09715
- [x] Task: Write tests with mocked OSF API dc09715
- [x] Task: Conductor - User Manual Verification Phase 1 dc09715

## Phase 2: GitHub Actions Workflow
- [x] Task: Create .github/workflows/osf_sync.yml dc09715
- [x] Task: Document OSF_TOKEN and OSF_PROJECT_ID secrets dc09715
- [x] Task: Wire into existing release process dc09715
- [x] Task: Conductor - User Manual Verification Phase 2 dc09715

## Phase 3: Documentation & Badges
- [x] Task: Update README.md with OSF target and badge dc09715
- [x] Task: Update DATASET_CARD.md with OSF mirror info dc09715
- [x] Task: Add OSF to corpus-family table in README dc09715
- [x] Task: Conductor - User Manual Verification Phase 3 dc09715

## Deliverables Created
- scripts/publish_osf.py
- .osf.json
- .github/workflows/osf_sync.yml
- Updated README.md, DATASET_CARD.md
- Tests for OSF publication

## Local Evidence
- [2026-07-01] `pixi install -e dev` completed and installed `osfclient` into the dev environment.
- [2026-07-01] `pixi run -e dev pytest tests/test_osf_integration.py tests/test_config.py` passed.
- [2026-07-01] `pixi run -e dev pytest` passed with 278 tests and 75.00% coverage.
- [2026-07-01] `pixi run -e dev lint`, `pixi run -e dev format-check`, and `pixi run -e dev quality` passed.
- [2026-07-01] `pixi run -e dev pyright-check` passed.
