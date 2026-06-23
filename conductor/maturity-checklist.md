# Maturity & Dependency Checklist: hathi-nz

> Generated from analysis of `pyproject.toml`, `pixi.toml`, `.github/workflows/`, `conductor/tech-stack.md`.

| Category | Status | Rationale |
|---|---|---|
| Python environment manager (`pixi`) | **required** | Active — `pixi.toml` drives all CI tasks. No `uv`. **Inconsistency:** CI workflows (`ci.yml`, `hf_sync.yml`) define `PYTHON_VERSION: "3.14"` but never read it; pixi resolves from `python = ">=3.11"` in `pixi.toml` and `requires-python = ">=3.11"` in `pyproject.toml`. `ty` targets 3.11. The 3.14 env var is dead config. |
| Python lint/format (`ruff`) | **required** | Fully configured — `[tool.ruff]` with 40+ lint rules, py311 target, strict per-file ignores. Runs in CI (`pixi run lint`, `pixi run format-check`). |
| Python type checking (`ty`/`pyright`) | **required** | `ty` in dev deps, `[tool.ty.environment]` with `python-version = "3.11"`, `[tool.ty.rules] all = "error"`. Runs in CI (`pixi run typecheck`). |
| Python logging (`loguru`) | **required** | `loguru>=0.7.2` in core dependencies. `[tool.legal_nz] logging = "loguru"`. |
| Python CLI UX (`typer`/`rich`) | **deferred** | Entry points (`hathi-nz`, `nz-hathi-corpus`) point to `scripts.cli:main` but no typer/rich dependency. CLI parsing is ad-hoc. Worth adding when the CLI surface grows; current scripts are pipeline-focused, not interactive. |
| Config/env loading (`pydantic-settings`) | **optional** | `.env` / `.env.local` exist but no `pydantic-settings` dependency. `pydantic>=2.0.0` is present so the dep is low-cost. Recommend adding once config loading becomes non-trivial. |
| Boundary validation (`pydantic v2`) | **required** | `pydantic>=2.0.0` in core dependencies. Used for data model validation across the corpus pipeline. |
| Hot record serialization (`msgspec`) | **deferred** | Not currently used. Polars + PyArrow + JSON Schema cover current serialization needs. `msgspec` could accelerate hot-path encoding of validated records if performance bottlenecks emerge. |
| DataFrames (`polars`) | **required** | `polars>=1.41.2` in core dependencies. Central to data normalization and text parsing. |
| Query validation (`duckdb`) | **required** | `duckdb>=1.5.3` in core dependencies. Powers structured catalog querying and metadata assembly. |
| Columnar data (`pyarrow`/Parquet) | **required** | `pyarrow>=21.0.0` in core dependencies. Used for Parquet serialization and low-level dataset I/O. |
| JSON Schema (`jsonschema`) | **required** | `jsonschema>=4.26.0` in core dependencies. Validates manifest and catalog structure against Draft 2020-12 schemas in `manifests/schema.json`. |
| HTTP clients (`httpx`/`requests`) | **required** | `requests>=2.34.2` in core dependencies. Used for HathiTrust Catalog API and Data API calls. `httpx` (async) not needed given the batch-oriented pipeline. |
| Retry/backoff (`tenacity`) | **optional** | Not yet a dependency. HathiTrust HTTP calls would benefit from retry logic. Recommend adding when resilience requirements are formalised. |
| HTML parsing (`beautifulsoup4`/`selectolax`) | **optional** | Not currently in deps. May become relevant if HathiTrust page-level parsing is required beyond the current API-driven approach. |
| Terminal UI (`rich`) | **deferred** | Not in deps. Would improve CLI output (progress bars, styled tables) but the current pipeline output is log-driven via loguru. Defer until CLI interactivity is prioritised. |
| Checksums / manifests | **required** | `manifests/` directory exists with `latest_manifest.json` and `schema.json`. SHA-256 checksums are explicitly referenced in `.zenodo.json` methodology. |
| Local vector store (`lancedb`) | **not_applicable** | This is a corpus acquisition and publication pipeline. No local vector search use case. |
| Service vector DB (`qdrant`) | **not_applicable** | Same rationale as lancedb. No vector DB service integration planned or relevant. |
| RAG orchestration (`haystack`) | **not_applicable** | Corpus pipeline, not a RAG application. Downstream consumers may use this dataset for RAG, but that concern lives outside this subrepo. |
| HF publication (`huggingface_hub`/`datasets`) | **required** | `huggingface-hub>=1.18.0` in core dependencies. `hf_sync.yml` workflow uploads to Hugging Face Hub daily. Dataset existence implied by `.zenodo.json` related identifier. |
| Archive / DOI (`Zenodo`/OSF) | **required** | `.zenodo.json` at repo root with full Zenodo deposition metadata. Tech-stack mentions Zenodo API tooling. Release workflow (`release-zenodo.yml`) exists at the monorepo level. |

## Key Inconsistencies

| Issue | Detail |
|---|---|
| CI `PYTHON_VERSION: "3.14"` | Set in `ci.yml` and `hf_sync.yml` as an env var but **never consumed** — no step reads it. pixi resolves Python from `pixi.toml` (`>=3.11`). `pyproject.toml` says `>=3.11`, `ty` targets 3.11, `ruff` targets py311. The 3.14 env var is orphaned configuration. |
| Tech-stack claims 3.14 | `conductor/tech-stack.md` states "Python 3.14: Bleeding-edge Python runtime" but no config enforces 3.14. If 3.14 is desired, `requires-python`, `target-version`, `ty python-version`, and pixi pin must all be updated. |
| No committed lock file | `pixi.toml` has no lock file committed. This means CI and local environments can resolve differently over time, reducing reproducibility. |
| No Dockerfile | No Docker image for production runs. Not blocking (pixi + CI handle this) but notable if containerised deployment is ever needed. |
