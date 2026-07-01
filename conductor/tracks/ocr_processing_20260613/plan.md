# Plan: Layout-Aware OCR & Progressive Text Extraction (ocr_processing_20260613)

## Phase 1: Text Ingestion & Cleaning
- [x] Task: Write tests for raw text cleanup (e.g. de-hyphenation, header pruning) using mock inputs.
- [x] Task: Implement the text-cleaning utility script using the shared utilities from `nlp-policy-nz`.
- [x] Task: Conductor - User Manual Verification 'Phase 1: Text Ingestion & Cleaning' (Protocol in workflow.md) [62be971]

## Phase 2: Layout Parsing & Extraction
- [x] Task: Write tests for multi-column page reconstruction and order sorting.
- [x] Task: Implement layout-aware text extraction pipeline in `scripts/ocr_extract.py`.
- [x] Task: Conductor - User Manual Verification 'Phase 2: Layout Parsing & Extraction' (Protocol in workflow.md) [62be971]
