# Plan - Multi-Git Mirroring Follow-up

## Phase 1: Workflow hardening
- [x] Add independently configured GitLab and Codeberg targets.
- [x] Add pinned-host-key and SSH URL fail-closed checks.
- [x] Mirror all branches and tags and report pushed target count.
- [x] Add regression tests for target configuration and safety gates.

## Phase 2: External verification
- [x] Verify Codeberg matches the canonical default branch.
- [ ] Create/configure the GitLab repository and GitHub secrets.
- [ ] Run the workflow with both targets and record successful ref checks.

## Residual gate

GitLab repository creation, SSH key registration, and GitHub secret mutation
require external account access. The local implementation does not claim those
actions are complete.
