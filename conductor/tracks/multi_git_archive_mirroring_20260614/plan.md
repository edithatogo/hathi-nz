# Plan - Multi-Git and Multi-Archive Mirroring

## Phase 1: Git Remote Mirror Setup
- [x] Task: Write `.github/workflows/mirror_sync.yml` to support automated SSH mirroring to secondary Git remotes (GitLab/Codeberg).
- [!] Task: Configure repository secrets `GIT_MIRROR_URL` and `GIT_MIRROR_SSH_PRIVATE_KEY` on GitHub. Gated: requires external GitHub secret mutation.
- [!] Task: Verify successful manual and push triggers for mirror sync. Gated: requires external GitHub Actions trigger/account work.

## Phase 2: Zenodo & OSF Mirroring Integration
- [x] Task: Document Zenodo archival publication schema and script requirements.
- [x] Task: Design OSF optional mirror convenience policy matching sister Hansard/Legislation corpora.
- [ ] Task: Conductor - User Manual Verification 'Phase 2: Zenodo & OSF Mirroring Integration' (Protocol in workflow.md)

## Local Evidence
- [2026-06-14] Added `archive_strategy.md` with target matrix, Zenodo package requirements, OSF optional mirror policy, and explicit gate boundaries.
- [2026-06-14] Verified local source surfaces: `.github/workflows/mirror_sync.yml`, `.zenodo.json`, and `DATASET_CARD.md`.
