# Plan: OSF Integration

## Phase 1: OSF Client Library
- [ ] Task: Add osfclient to core dependencies
- [ ] Task: Create .osf.json with OSF metadata
- [ ] Task: Implement scripts/publish_osf.py
- [ ] Task: Add dry-run mode
- [ ] Task: Write tests with mocked OSF API
- [ ] Task: Conductor - User Manual Verification Phase 1

## Phase 2: GitHub Actions Workflow
- [ ] Task: Create .github/workflows/osf_sync.yml
- [ ] Task: Document OSF_TOKEN and OSF_PROJECT_ID secrets
- [ ] Task: Wire into existing release process
- [ ] Task: Conductor - User Manual Verification Phase 2

## Phase 3: Documentation & Badges
- [ ] Task: Update README.md with OSF target and badge
- [ ] Task: Update DATASET_CARD.md with OSF mirror info
- [ ] Task: Add OSF to corpus-family table in README
- [ ] Task: Conductor - User Manual Verification Phase 3

## Deliverables Created
- scripts/publish_osf.py
- .osf.json
- .github/workflows/osf_sync.yml
- Updated README.md, DATASET_CARD.md
- Tests for OSF publication
