# Plan: Prose Linting & Documentation Quality (prose_quality_20260613)

## Phase 1: Lint Tooling Setup & Config
- [x] Task: Create `typos.toml` for spelling exceptions.
- [x] Task: Initialize `.vale.ini` configuration and install local Vale styles.
- [x] Task: Conductor - User Manual Verification 'Phase 1: Lint Tooling Setup & Config' (Protocol in workflow.md)

## Phase 2: Quality Command Integration
- [x] Task: Write automated test script to check that linters (`typos`, `taplo`, `actionlint`) can execute successfully.
- [x] Task: Integrate quality check tasks (`lint`, `format-check`, `spell`, `toml-check`, `workflow-syntax`) into the environment commands.
- [x] Task: Conductor - User Manual Verification 'Phase 2: Quality Command Integration' (Protocol in workflow.md)

## Local Evidence
- [2026-06-14] `tests/test_prose_quality.py` passes as part of the full local suite.
- [2026-06-14] `.vale.ini` includes local corpus vocabulary exceptions aligned with `typos.toml`.
