# Plan: Code Quality & Tooling Enhancement

## Phase 1: Pre-commit Configuration
- [ ] Task: Create .pre-commit-config.yaml with ruff, ty, typos, taplo hooks
- [ ] Task: Run pre-commit run --all-files and fix issues
- [ ] Task: Document pre-commit usage in README.md
- [ ] Task: Conductor - User Manual Verification Phase 1

## Phase 2: Pyright Direct Dependency
- [ ] Task: Add pyright to dev dependencies
- [ ] Task: Create [tool.pyright] config in pyproject.toml
- [ ] Task: Add pixi run pyright-check task
- [ ] Task: Conductor - User Manual Verification Phase 2

## Phase 3: Mutation Testing with mutmut
- [ ] Task: Add mutmut to dev dependencies
- [ ] Task: Configure [tool.mutmut] in pyproject.toml
- [ ] Task: Run baseline mutation test and record score
- [ ] Task: Conductor - User Manual Verification Phase 3

## Phase 4: Scalene Profiling
- [ ] Task: Add scalene to dev dependencies
- [ ] Task: Refactor scripts/profile_pipelines.py to use scalene
- [ ] Task: Add pixi tasks for pipeline profiling
- [ ] Task: Conductor - User Manual Verification Phase 4

## Phase 5: Coverage Threshold
- [ ] Task: Raise fail_under from 60 to 75 in pyproject.toml
- [ ] Task: Update CI workflow with --cov-fail-under=75
- [ ] Task: Conductor - User Manual Verification Phase 5

## Deliverables Created
- .pre-commit-config.yaml
- pyproject.toml updates (pyright, mutmut, coverage)
- pixi.toml updates (pyright, scalene, mutmut)
- Updated scripts/profile_pipelines.py
- CI workflow updates
