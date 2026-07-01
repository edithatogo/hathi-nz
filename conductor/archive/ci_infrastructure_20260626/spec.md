# Specification: CI Infrastructure & Resilience

## 1. Overview
Improve CI/CD infrastructure with coverage reporting, HTTP resilience, and configuration cleanup.

## 2. Components

### 2.1 Codecov Integration
- Add codecov-action to CI workflows
- Upload coverage reports from ci.yml and hf_sync.yml
- Configure Codecov status checks on PRs

### 2.2 Tenacity Retry/Backoff
- Add tenacity to core dependencies
- Wrap HathiTrust HTTP calls with retry logic
- HathiTrust ZIP downloads
- HathiTrust Data API lookups
- Hugging Face Hub uploads

### 2.3 CI Dead Config Cleanup
- Remove orphaned PYTHON_VERSION env var from CI workflows
- Align requires-python, target-version, ty python-version

## 3. Acceptance Criteria
- Codecov reports visible on PRs
- All HTTP calls have retry decorators
- No orphaned env vars in CI
- Python version config consistent across all files
