# Specification: Zenodo Release Workflow

## 1. Overview
Scripts (package_release.py, publish_zenodo.py) and metadata (.zenodo.json) exist, but no GitHub Actions workflow automates Zenodo publication. This track wires them together.

## 2. Components

### 2.1 Release Workflow
- Create .github/workflows/zenodo_release.yml:
  - Trigger: on release published or manual dispatch with version input
  - Step 1: Run package_release.py to build archive
  - Step 2: Run publish_zenodo.py to upload
  - Step 3: Record DOI and update DATASET_CARD.md

### 2.2 Secrets
- ZENODO_TOKEN for Zenodo API
- ZENODO_SANDBOX toggle

### 2.3 Versioning Alignment
- Use check_version_consistency.py as pre-flight gate

## 3. Acceptance Criteria
- Workflow can be triggered manually with version parameter
- Package built, validated, uploaded to Zenodo (sandbox)
- DOI captured and recorded in DATASET_CARD.md
- Production flag switches between sandbox and production
