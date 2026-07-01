# Plan: Code Quality & Tooling Enhancement

## Phase 1: Pre-commit Configuration
- [x] Task: Create .pre-commit-config.yaml with ruff, ty, typos, taplo hooks
- [x] Task: Run pre-commit run --all-files and fix issues
- [x] Task: Document pre-commit usage in README.md
- [x] Task: Conductor - User Manual Verification Phase 1

## Phase 2: Pyright Direct Dependency
- [x] Task: Add pyright to dev dependencies
- [x] Task: Create [tool.pyright] config in pyproject.toml
- [x] Task: Add pixi run pyright-check task
- [x] Task: Conductor - User Manual Verification Phase 2

## Phase 3: Mutation Testing with mutmut
- [x] Task: Add mutmut to dev dependencies
- [x] Task: Configure [tool.mutmut] in pyproject.toml
- [x] Task: Run baseline mutation test and record score
- [x] Task: Conductor - User Manual Verification Phase 3

## Phase 4: Scalene Profiling
- [x] Task: Add scalene to dev dependencies
- [x] Task: Refactor scripts/profile_pipelines.py to use scalene
- [x] Task: Add pixi tasks for pipeline profiling
- [x] Task: Conductor - User Manual Verification Phase 4

## Phase 5: Coverage Threshold
- [x] Task: Raise fail_under from 60 to 75 in pyproject.toml
- [x] Task: Update CI workflow with --cov-fail-under=75
- [x] Task: Conductor - User Manual Verification Phase 5

## Deliverables Created
- .pre-commit-config.yaml
- pyproject.toml updates (pyright, mutmut, coverage)
- pixi.toml updates (pyright, scalene, mutmut)
- Updated scripts/profile_pipelines.py
- CI workflow updates

## Local Evidence
- [2026-07-01] `pixi run -e dev pre-commit run --all-files` passed.
- [2026-07-01] `pixi run -e dev test -- --cov --cov-report=term-missing --cov-fail-under=75` passed with 267 tests and 75.09% coverage.
- [2026-07-01] GitHub Actions run `28510971474` passed lint, typecheck, tests, and mutmut after the final hermeticity fixes.
