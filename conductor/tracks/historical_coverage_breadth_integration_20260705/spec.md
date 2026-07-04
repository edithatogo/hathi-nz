# Historical Coverage Breadth Integration

## Overview

Build a HathiTrust-side Hansard coverage bridge that feeds cross-repo historical completeness work in `corpus-nz-hansard`. This track improves historical breadth by making the HathiTrust inventory, archive completeness, OCR/fulltext evidence, and overlap state explicit without claiming complete historical coverage.

This track is intentionally cross-repo:
- `hathi-nz` provides the HathiTrust inventory, archive completeness, and extraction evidence.
- `corpus-nz-hansard` provides the Parliament website inventory and cross-repo boundary rules.
- `corpus-law-nz` remains a boundary reference only and is not in scope for acquisition here.

## Functional Requirements

1. Define a HathiTrust-side coverage model for NZ Parliamentary Debates, archive inventory, and overlap evidence.
2. Add a machine-readable bridge manifest that can be consumed by the Parliament repo's historical coverage reconciliation layer.
3. Record which HathiTrust records are direct evidence, overlap evidence, or gap-detection evidence for historical Hansard completeness work.
4. Preserve explicit no-completeness-claim language so the bridge cannot be misread as complete historical Hansard coverage.
5. Add validation that cross-repo references point to the Parliament repo or adjacent boundary docs rather than to unsupported claims.
6. Update docs so the HathiTrust archive work is clearly situated as a companion source to Parliament coverage reconciliation.

## Non-Functional Requirements

- Keep outputs deterministic, hash-backed, and reproducible.
- Do not add bulk-acquisition assumptions that are not already supported by the repo.
- Do not claim the HathiTrust inventory is complete historical Hansard coverage.
- Keep the bridge artifact compatible with downstream cross-repo reconciliation checks.

## Acceptance Criteria

- The bridge manifest validates against its schema.
- The docs identify the Parliament repo as the integration target and keep boundaries explicit.
- Tests verify bridge classification, completeness-claim guardrails, and cross-repo reference integrity.
- The repo still distinguishes archive evidence from historical completeness assertions.

## Out of Scope

- Changing `corpus-nz-hansard` implementation directly in this track.
- Bulk acquisition from HathiTrust outside the existing HathiTrust project scope.
- Any legislation/Gazette acquisition work.
- Publishing a historical-completeness claim.
