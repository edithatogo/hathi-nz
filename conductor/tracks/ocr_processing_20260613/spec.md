# Specification: Layout-Aware OCR & Progressive Text Extraction (ocr_processing_20260613)

## 1. Overview
HathiTrust NZ Parliamentary Debates and legal documents require advanced OCR post-processing and layout recovery. This track implements the text extraction pipeline, utilizing layout-aware OCR (e.g. layout-parser, PyMuPDF, or Nougat) and cleaning text via functions shared with `nlp-policy-nz`.

## 2. Shared Library Integration
- Reusable text cleaning routines (regex-based hyphen-joins, column alignment, header/footer removal) will be imported from the shared `nlp-policy-nz` library.
- Ensures identical tokenization and normalization across `corpus-law-nz`, `corpus-nz-hansard`, and `hathi-nz`.

## 3. Pipeline Stages
1. **Layout Detection:** Parse pages to distinguish headers, footers, columns, and page numbers.
2. **Text Extraction/OCR:** Run extraction engines on raw image assets or PDFs.
3. **Post-Processing Cleaning:** Fix spelling issues, join words hyphenated at line boundaries, and remove page headers/footers.
4. **Staging:** Output cleanly aligned text files to `data/processed/`.
