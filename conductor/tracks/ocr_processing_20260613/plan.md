# Plan: Layout-Aware OCR & Progressive Text Extraction (ocr_processing_20260613)

## Phase 1: Text Ingestion & Cleaning
- [~] Task: Write tests for raw text cleanup (e.g. de-hyphenation, header pruning) using mock inputs.
- [~] Task: Implement the text-cleaning utility script using the shared utilities from `nlp-policy-nz`.
- [ ] Task: Conductor - User Manual Verification 'Phase 1: Text Ingestion & Cleaning' (Protocol in workflow.md)

## Phase 2: Layout Parsing & Extraction
- [ ] Task: Write tests for multi-column page reconstruction and order sorting.
- [ ] Task: Implement layout-aware text extraction pipeline in `scripts/ocr_extract.py`.
- [ ] Task: Conductor - User Manual Verification 'Phase 2: Layout Parsing & Extraction' (Protocol in workflow.md)
