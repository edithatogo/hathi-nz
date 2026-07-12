# Historical Coverage Breadth Integration Plan

## Phase 1: Define the HathiTrust Coverage Bridge

- [x] Task: Draft the HathiTrust-side coverage taxonomy for inventory, archive completeness, overlap, and gap-detection evidence.
- [x] Task: Define the bridge manifest shape that the Parliament repo can consume for cross-repo reconciliation.
- [x] Task: Specify the no-completeness-claim boundary rules and cross-repo reference policy.
- [ ] Task: Conductor - User Manual Verification 'Define the HathiTrust Coverage Bridge' (Protocol in workflow.md)

## Phase 2: Implement the Bridge Manifest and Checks

- [x] Task: Create the bridge manifest builder and schema for the HathiTrust evidence surface.
- [x] Task: Add docs that explain how the HathiTrust archive complements Parliament-side coverage reconciliation.
- [x] Task: Add checker coverage for bridge classification, overlap handling, and completeness-claim guardrails.
- [x] Task: Add unit tests for bridge validation and cross-repo reference integrity.
- [ ] Task: Conductor - User Manual Verification 'Implement the Bridge Manifest and Checks' (Protocol in workflow.md)

## Phase 3: Integrate with Parliament Coverage Reconciliation

- [x] Task: Add cross-repo references that point to the Parliament repo's historical coverage reconciliation track.
- [x] Task: Run the repo validation gates and verify the bridge remains evidence-only where required.
- [x] Task: Update track evidence with the final bridge manifest, checker results, and repository-boundary summary.
- [ ] Task: Conductor - User Manual Verification 'Integrate with Parliament Coverage Reconciliation' (Protocol in workflow.md)
