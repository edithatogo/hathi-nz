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

## Evidence

- 2026-07-14: `mirror_sync.yml` run `29314426756` succeeded with
  `mirror_targets_pushed=1`.
- Codeberg `master` remains at `74bc97fa`; the follow-up branch is at
  `4e7c8e7`; tag `v0.1.0` remains present.
- GitHub currently has the legacy `GIT_MIRROR_URL` and shared SSH key, plus
  pinned Codeberg/GitLab host keys. `GITLAB_MIRROR_URL` and
  `CODEBERG_MIRROR_URL` are not configured.
