# Specification: OSF Integration

## 1. Overview
Add OSF as a third publication target for corpus-nz-hathi, providing additional redundancy alongside Hugging Face and Zenodo.

## 2. Components

### 2.1 OSF API Client
- Use osfclient PyPI package for OSF API interaction
- Create scripts/publish_osf.py with operations:
  - Project creation (or use existing OSF project)
  - File/folder upload to OSF storage
  - Version tracking
  - Dry-run mode

### 2.2 OSF Metadata
- Create .osf.json with metadata: title, description, tags, category
- Map .zenodo.json fields to OSF metadata schema

### 2.3 GitHub Actions Workflow
- Create .github/workflows/osf_sync.yml
- Uses OSF_TOKEN and OSF_PROJECT_ID secrets

### 2.4 Documentation
- Update README.md with OSF publication target
- Add OSF badge to README

## 3. Acceptance Criteria
- scripts/publish_osf.py can upload release archives to OSF
- .github/workflows/osf_sync.yml exists and runs
- README documents OSF as publication target
- Dry-run mode works without authentication
