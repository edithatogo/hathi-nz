# Conductor Improvement Backlog

## Active candidates
- [ ] Validate conductor/learning-log.md entries against conductor/templates/learning-entry.schema.json in CI or local pre-commit checks.
- [ ] Add repository-scoped script to append learning candidates without automatic commit in CI failure paths.
- [ ] Capture registry/review/skills-feedback events into the backlog from failing submission workflows.
- [ ] Add phase-level retrospective notes for each Phase 1/2/3/4 run and record reviewer sign-off.
- [ ] Migrate all scripts from stdlib logging to loguru (loguru is already a core dep but unused)
- [ ] Create .pre-commit-config.yaml to match declared pre-commit dev dependency
- [ ] Add pyright directly as dev dependency alongside ty for IDE integration
- [ ] Add mutmut for mutation testing to validate test quality
- [ ] Add scalene for pipeline profiling (replace cProfile in profile_pipelines.py)
- [ ] Integrate Codecov for coverage visibility (pytest-cov runs but results go nowhere)
- [ ] Add tenacity for HTTP retry/backoff on HathiTrust and HF Hub calls
- [ ] Remove orphaned PYTHON_VERSION: 3.14 env var from CI workflows
- [ ] Align Python version config across requires-python, target-version, ty, and pixi
- [ ] Raise coverage fail_under threshold from 60 to 75
- [ ] Implement dynamic versioning with hatch-vcs to eliminate version drift
- [ ] Add pydantic-settings for structured .env configuration loading
- [ ] Create Zenodo release GHA workflow (scripts exist, workflow missing)
- [ ] Create OSF publication workflow for third publication target
- [ ] Create Dockerfile for pixi-based reproducible pipeline execution
- [ ] Verify and commit pixi.lock for dependency reproducibility

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

## Comprehensive Audit Findings (2026-06-26)
- **OSF integration**: Missing entirely - no code, workflow, or metadata for OSF
- **Zenodo release workflow**: Missing - scripts exist but no GHA workflow
- **Pre-commit config**: Missing - dep declared but no .pre-commit-config.yaml
- **Loguru usage**: Not actually used - all scripts use stdlib logging
- **Versioning drift**: Hardcoded in 4 places with no single source of truth
- **Coverage threshold**: Only 60% - should be raised to 75%+
- **HTTP resilience**: No retry/backoff on any HTTP calls
- **CI dead config**: PYTHON_VERSION: 3.14 env var set but never consumed
- **No Codecov**: Coverage generated but not uploaded or tracked
- **No Docker**: No containerization for reproducible deployment
