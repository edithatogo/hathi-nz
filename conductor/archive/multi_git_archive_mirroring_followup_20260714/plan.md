# Plan - Multi-Git Mirroring Follow-up

## Phase 1: Workflow hardening
- [x] Add independently configured GitLab and Codeberg targets.
- [x] Add pinned-host-key and SSH URL fail-closed checks.
- [x] Mirror all branches and tags and report pushed target count.
- [x] Add regression tests for target configuration and safety gates.

## Phase 2: External verification
- [x] Verify Codeberg matches the canonical default branch.
- [x] Create/configure the GitLab repository and GitHub secrets.
- [x] Run the workflow with both targets and record successful ref checks.

## Completion evidence

- GitLab repository: `https://gitlab.com/edithatogo/hathi-nz`.
- GitLab deploy key registered with push access; private key stored in the
  `GITLAB_MIRROR_SSH_PRIVATE_KEY` GitHub secret.
- GitHub Actions run `29318445717` completed successfully with
  `mirror_targets_pushed=2`.
- GitLab and Codeberg both expose the branch
  `codex/hathi-structured-extraction-plan` at `7ae6986`, `master` at
  `74bc97fa`, and tag `v0.1.0` at `5e52d4dc`.

## Evidence

- 2026-07-14: prior Codeberg-only run `29314426756` succeeded with
  `mirror_targets_pushed=1`; current two-target evidence supersedes it.
