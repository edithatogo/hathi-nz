# Specification: Loguru Migration

## 1. Overview
loguru>=0.7.2 is declared as a core dependency but all scripts use stdlib logging. This track aligns implementation with declared intent.

## 2. Migration Scope

### 2.1 Files to Migrate
- scripts/fetch_hathitrust.py
- scripts/stage_hf_dataset.py
- scripts/upload_hf_dataset.py
- scripts/validate_catalog.py
- scripts/ocr_extract.py
- scripts/cli.py

### 2.2 Migration Pattern
Replace: import logging / logger = logging.getLogger(__name__)
With: from loguru import logger

### 2.3 Logging Configuration
- Replace logging.basicConfig() with loguru.configure()
- Use loguru structured format

### 2.4 Test Adjustments
- Update test fixtures that mock logging calls

## 3. Acceptance Criteria
- All scripts use from loguru import logger
- No stdlib logging imports remain in scripts/
- All tests pass
- Consistent log format across all pipeline stages
