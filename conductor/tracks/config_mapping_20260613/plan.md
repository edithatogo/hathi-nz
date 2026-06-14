# Plan: Dataset Mapping & Hugging Face Config Planning (config_mapping_20260613)

## Phase 1: Naming & Schema Mapping
- [x] Task: Write tests for metadata schema parser and naming rules.
- [x] Task: Define naming structures and write schema rules in `manifests/schema.json` and validate schemas.
- [ ] Task: Conductor - User Manual Verification 'Phase 1: Naming & Schema Mapping' (Protocol in workflow.md)

## Phase 2: Configuration Catalog
- [x] Task: Write tests verifying dataset configuration loads properly via huggingface-hub.
- [x] Task: Implement the Hugging Face `DATASET_CARD.md` with structured YAML configurations for all planned subsets.
- [ ] Task: Conductor - User Manual Verification 'Phase 2: Configuration Catalog' (Protocol in workflow.md)

## Local Evidence
- [2026-06-14] `tests/test_config_mapping.py` passes as part of the full local suite.
- [2026-06-14] `DATASET_CARD.md` frontmatter includes the default `debates` Hugging Face config.
- [2026-06-14] `manifests/schema.json` accepts category/subset HTID fixtures used by config mapping tests.
