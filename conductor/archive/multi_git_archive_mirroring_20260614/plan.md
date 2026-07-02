# Plan - Multi-Git and Multi-Archive Mirroring

## Phase 1: Git Remote Mirror Setup
- [x] Task: Write `.github/workflows/mirror_sync.yml` to support automated SSH mirroring to secondary Git remotes (GitLab/Codeberg).
- [x] Task: Configure repository secrets `GIT_MIRROR_URL` and `GIT_MIRROR_SSH_PRIVATE_KEY` on GitHub. Gated: requires external GitHub secret mutation.
- [x] Task: Verify successful manual and push triggers for mirror sync. Gated: requires external GitHub Actions trigger/account work.

## Phase 2: Zenodo & OSF Mirroring Integration [checkpoint: 7cdcfc5]
- [x] Task: Document Zenodo archival publication schema and script requirements.
- [x] Task: Design OSF optional mirror convenience policy matching sister Hansard/Legislation corpora.
- [x] Task: Conductor - User Manual Verification 'Phase 2: Zenodo & OSF Mirroring Integration' (Protocol in workflow.md) 7cdcfc5

## Local Evidence
- [2026-06-14] Added `archive_strategy.md` with target matrix, Zenodo package requirements, OSF optional mirror policy, and explicit gate boundaries.
- [2026-06-14] Verified local source surfaces: `.github/workflows/mirror_sync.yml`, `.zenodo.json`, and `DATASET_CARD.md`.
- [2026-07-01] Updated `.github/workflows/mirror_sync.yml` to skip mirror sync when either `GIT_MIRROR_URL` or `GIT_MIRROR_SSH_PRIVATE_KEY` is missing.
- [2026-07-01] Added regression coverage in `tests/test_mirror_sync.py`; `pixi run -e dev pytest tests/test_mirror_sync.py -q` and `pixi run -e dev quality` passed.
- [2026-07-02] Configured GitHub mirror secret to target Codeberg, created the `edithatogo/hathi-nz` Codeberg repository, added the shared SSH key to Codeberg, and verified a successful `mirror_sync.yml` run.
- [2026-07-02] Archived the completed track under `conductor/archive/multi_git_archive_mirroring_20260614/` and marked the final phase verification task complete.
