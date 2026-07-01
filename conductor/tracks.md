# Project Tracks

This file tracks all major tracks for the project. Each track has its own detailed plan in its respective folder.

---

## [x] Track: Build the core data acquisition and sync pipeline for hathi-nz
*Link: [./conductor/tracks/core_pipeline_20260613/](./conductor/tracks/core_pipeline_20260613/)*

## [x] Track: Prose Linting & Documentation Quality
*Link: [./conductor/tracks/prose_quality_20260613/](./conductor/tracks/prose_quality_20260613/)*

## [x] Track: Dataset Mapping & Hugging Face Config Planning
*Link: [./conductor/tracks/config_mapping_20260613/](./conductor/tracks/config_mapping_20260613/)*

## [x] Track: Layout-Aware OCR & Progressive Text Extraction
*Link: [./conductor/tracks/ocr_processing_20260613/](./conductor/tracks/ocr_processing_20260613/)*

## [~] Track: Multi-Git and Multi-Archive Mirroring Setup
*Link: [./conductor/tracks/multi_git_archive_mirroring_20260614/](./conductor/tracks/multi_git_archive_mirroring_20260614/)*

---

## [x] Track: Code Quality & Tooling Enhancement
*Link: [./conductor/archive/code_quality_enhancement_20260626/](./conductor/archive/code_quality_enhancement_20260626/)*
- Pre-commit config, mutmut, scalene, pyright direct dep, coverage threshold 75%

## [x] Track: CI Infrastructure & Resilience
*Link: [./conductor/archive/ci_infrastructure_20260626/](./conductor/archive/ci_infrastructure_20260626/)*
- Codecov, tenacity retry/backoff, CI dead config cleanup

## [x] Track: Dynamic Versioning & Configuration
*Link: [./conductor/archive/versioning_config_20260626/](./conductor/archive/versioning_config_20260626/)*
- hatch-vcs dynamic versioning, pydantic-settings config loading

## [ ] Track: Loguru Migration
*Link: [./conductor/tracks/loguru_migration_20260626/](./conductor/tracks/loguru_migration_20260626/)*
- Migrate from stdlib logging to loguru across all scripts

## [ ] Track: OSF Integration
*Link: [./conductor/tracks/osf_integration_20260626/](./conductor/tracks/osf_integration_20260626/)*
- OSF publication workflow for dataset mirroring

## [ ] Track: Zenodo Release Workflow
*Link: [./conductor/tracks/zenodo_release_workflow_20260626/](./conductor/tracks/zenodo_release_workflow_20260626/)*
- GHA workflow for automated Zenodo depositions with DOI minting

## [ ] Track: Containerization
*Link: [./conductor/tracks/containerization_20260626/](./conductor/tracks/containerization_20260626/)*
- Dockerfile for pixi-based reproducible pipeline execution

---

### Architecture Status (oracle, 2026-06-26)
- **core_pipeline**: ✅ All 4 phases complete (143 tests, 0 errors, 76% coverage)
- **code_quality_enhancement**: [ ] New - Tooling improvements identified in comprehensive audit
- **ci_infrastructure**: [ ] New - Resilience and CI/CD enhancements
- **versioning_config**: [ ] New - Dynamic versioning and config management
- **loguru_migration**: [ ] New - Align logging implementation with declared dependency
- **osf_integration**: [ ] New - Third publication target
- **zenodo_release_workflow**: [ ] New - GHA workflow for existing Zenodo scripts
- **containerization**: [ ] New - Docker deployment support
