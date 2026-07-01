# Specification: Dynamic Versioning & Configuration

## 1. Overview
Eliminate version drift by deriving version from git tags, and add structured config loading via pydantic-settings.

## 2. Components

### 2.1 Dynamic Versioning with hatch-vcs
- Add hatch-vcs as build dependency
- Remove hardcoded version from pyproject.toml
- Remove VERSION file; derive from git tag
- Replace PIPELINE_VERSION constants with importlib.metadata

### 2.2 pydantic-settings
- Add pydantic-settings to core dependencies
- Create scripts/config.py with Settings class
- Wire into upload_hf_dataset.py, publish_zenodo.py, fetch_hathitrust.py
- Support .env auto-loading

## 3. Acceptance Criteria
- pip install -e . derives version from git tag
- No version hardcoded in any script or config file
- Settings class loads from .env automatically
- All scripts use Settings instead of os.environ
