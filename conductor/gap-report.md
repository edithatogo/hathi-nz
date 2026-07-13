# HathiTrust-NZ Gap Report

This report covers the remaining open work in this repository as of 2026-07-13.

## Already Archived

- Shared Code-Scanning Gate Rollout
- This rollout is complete and archived under `conductor/archive/shared_code_scanning_gate_rollout_20260707/`.

## Still Open

### HathiTrust-NZ Multi-Source Archive

Status: in progress

What remains:
- Resolve the remaining official HathiTrust rsync/static-host access blocker.
- Obtain or confirm the missing HathiTrust rsync/static-host variables and SSH key.

What next:
- Run the official Research Dataset acquisition lane once static-host access is approved.
- Close the track after full-text evidence and CI release gates pass.

### HathiTrust-NZ Interim Acquisition Hardening

Status: in progress

What remains:
- Resolve official HathiTrust rsync keys and static-host approval.
- Validate the interim routes against live IA/HTRC evidence as those source manifests become available.

What next:
- Keep metadata-only and derived-feature routes active until official source evidence changes the routing decision.

### Historical Coverage Breadth Integration

Status: complete

What remains:
- None. The evidence-only bridge and validator are implemented.

What next:
- No further repository work is required for this track.

## Practical Next Step

The only archival-content blocker is HathiTrust static-host approval and credentials. HF collection access is working, four production Zenodo child-dataset records are published with DOI writebacks, the publication gate now checks all child DOIs, and CI formatting/type-check gates have been stabilized.
