# Conductor Improvement Backlog

## Active candidates
- [ ] Validate conductor/learning-log.md entries against conductor/templates/learning-entry.schema.json in CI or local pre-commit checks.
- [ ] Add repository-scoped script to append learning candidates without automatic commit in CI failure paths.
- [ ] Capture registry/review/skills-feedback events into the backlog from failing submission workflows.
- [ ] Add phase-level retrospective notes for each Phase 1/2/3/4 run and record reviewer sign-off.
- [x] Migrate all scripts from stdlib logging to loguru (loguru is already a core dep but unused)
- [x] Create .pre-commit-config.yaml to match declared pre-commit dev dependency
- [x] Add pyright directly as dev dependency alongside ty for IDE integration
- [x] Add mutmut for mutation testing to validate test quality
- [ ] Add scalene for pipeline profiling (replace cProfile in profile_pipelines.py)
- [x] Integrate Codecov for coverage visibility (pytest-cov runs but results go nowhere)
- [x] Add tenacity for HTTP retry/backoff on HathiTrust and HF Hub calls
- [x] Remove orphaned PYTHON_VERSION: 3.14 env var from CI workflows
- [x] Align Python version config across requires-python, target-version, ty, and pixi
- [x] Raise coverage fail_under threshold from 60 to 75
- [x] Implement dynamic versioning with hatch-vcs to eliminate version drift
- [x] Add pydantic-settings for structured .env configuration loading
- [x] Verify and record public Zenodo publications for the HathiTrust-NZ child datasets, including DOI writeback into their dataset cards
- [x] Create OSF publication workflow for third publication target
- [x] Create Dockerfile for pixi-based reproducible pipeline execution
- [ ] Verify and commit pixi.lock for dependency reproducibility
- [ ] Populate `manifests/latest_manifest.json` and `data/` from the current HathiFile dump so the corpus reaches the full 510-volume archive target
- [ ] Harvest the 510 collection HTIDs from the HathiTrust collection page and feed them into the new HTID allowlist filter so the manifest matches the curated corpus exactly

## Skills touched by this workspace
- conductor-implement
- conductor-review
- conductor-track-new
- subagent orchestration (swarm / subagents.yaml)
- workspace-doctor
- track-status
- scripting (batch and PowerShell for workspace maintenance)

## Repo-local lesson hooks
- [ ] For each future workspace-level lesson that affects agent behavior, add a repo-local note here and promote only after review.
- [ ] Continue using local notes instead of writing into global skill directories unless explicitly approved.

## Historical Audit Findings (2026-06-26)

The following findings drove completed Conductor tracks and are retained as historical audit evidence, not active blockers:
- OSF integration, Zenodo workflow, pre-commit, Loguru, versioning, coverage, retry/backoff, Codecov, and containerization are implemented.
