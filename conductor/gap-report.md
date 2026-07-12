# HathiTrust-NZ Gap Report

This report covers the remaining open work in this repository as of 2026-07-12.

## Already Archived

- Shared Code-Scanning Gate Rollout
- This rollout is complete and archived under `conductor/archive/shared_code_scanning_gate_rollout_20260707/`.

## Still Open

### HathiTrust-NZ Multi-Source Archive

Status: in progress

What remains:
- Resolve the remaining official HathiTrust rsync/static-host access blocker.
- Obtain or confirm the missing HathiTrust rsync/static-host variables and SSH key.
- Run the production collection publication workflow for the child dataset DOI streams.

What next:
- Validate the collection-level dataset structure.
- Continue source-specific manifest and publication routing work.
- Close the remaining track issues after publication evidence is complete.

### HathiTrust-NZ Interim Acquisition Hardening

Status: in progress

What remains:
- Resolve official HathiTrust rsync keys and static-host approval.
- Validate the interim routes against live IA/HTRC evidence as those source manifests become available.

What next:
- Finish the remaining manual verification and external issue-tracking steps.

### Historical Coverage Breadth Integration

Status: complete

What remains:
- None. The evidence-only bridge and validator are implemented.

What next:
- Write the taxonomy and reference policy first.
- Then implement the bridge output and validation checks.

## Practical Next Step

The only external blocker is HathiTrust static-host approval and credentials. HF collection access is working, and four production Zenodo child-dataset records are published with DOI writebacks; the release workflow's final push gate needs a small race-hardening fix before it can report success automatically.
