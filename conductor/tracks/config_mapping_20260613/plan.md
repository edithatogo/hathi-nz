# Plan: Dataset Mapping & Hugging Face Config Planning (config_mapping_20260613)

## Phase 1: Naming & Schema Mapping
- [x] Task: Write tests for metadata schema parser and naming rules.
- [x] Task: Define naming structures and write schema rules in `manifests/schema.json` and validate schemas.
- [x] Task: Conductor - User Manual Verification 'Phase 1: Naming & Schema Mapping' (Protocol in workflow.md) [bed1b0b]

## Phase 2: Configuration Catalog
- [x] Task: Write tests verifying dataset configuration loads properly via huggingface-hub.
- [x] Task: Implement the Hugging Face `DATASET_CARD.md` with structured YAML configurations for all planned subsets.
- [x] Task: Conductor - User Manual Verification 'Phase 2: Configuration Catalog' (Protocol in workflow.md) [bed1b0b]

## Local Evidence
- [2026-06-14] `tests/test_config_mapping.py` passes as part of the full local suite.
- [2026-07-01] `DATASET_CARD.md` frontmatter exposes both `debates` and `legislation` Hugging Face configs.
- [2026-07-01] `manifests/schema.json` includes standard `$schema` / `$id` metadata and preserves the subset-aware record shape.
