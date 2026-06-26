# Specification: Code Quality & Tooling Enhancement

## 1. Overview
Strengthen the code quality toolchain with additional validation, profiling, mutation testing, and IDE-friendly type checking.

## 2. Components

### 2.1 Pre-commit Configuration
- Create .pre-commit-config.yaml with hooks for ruff, ty, typos, taplo
- Pin versions to match dev dependencies
- Document pre-commit install in README

### 2.2 Pyright Direct Dependency
- Add pyright to dev dependencies alongside existing ty
- Create [tool.pyright] section mirroring [tool.ty] config

### 2.3 Mutation Testing (mutmut)
- Add mutmut to dev dependencies
- Configure [tool.mutmut] in pyproject.toml targeting scripts/
- Add CI job for mutation testing

### 2.4 Scalene Profiling
- Add scalene to dev dependencies
- Refactor scripts/profile_pipelines.py to use scalene
- Add scalene invocation to pixi.toml tasks

### 2.5 Coverage Threshold
- Raise fail_under from 60 to 75 in pyproject.toml

## 3. Acceptance Criteria
- pre-commit run --all-files passes
- pyright scripts/ and ty scripts/ both pass
- mutmut run produces baseline report
- Scalene profiling reports generated
- Coverage threshold enforced at 75%+
