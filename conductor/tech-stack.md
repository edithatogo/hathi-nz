# Technology Stack: Hathi NZ Corpus

## 1. Runtime & Environment Management
- **Python 3.14:** Bleeding-edge Python runtime to leverage the latest language features and optimizations.
- **pixi:** High-performance package manager and environment resolver (Conda-compatible, Rust-powered) to enforce strict, reproducible environments across all developers and platforms.

## 2. Core Dependencies & Libraries
- **Data Engineering & Querying:**
  - **DuckDB:** Local analytics database for structured catalog querying and metadata assembly.
  - **Polars:** Fast DataFrame library for raw data normalization, text parsing, and manipulation.
  - **PyArrow:** Parquet serialization and low-level dataset interface.
- **Acquisition & Distribution APIs:**
  - **`huggingface-hub` (with Xet integration):** Interface for automated syncing, snapshots, and dataset uploads.
  - **`requests`:** Client library for interacting with HathiTrust Catalog and Data APIs.
  - **Zenodo API tooling:** For automated archive creation and deposition updates.
- **Shared NLP Utilities:**
  - **`nlp-policy-nz`**: Decoupled shared library containing reusable text processing, cleaning, and tokenization utilities.

## 3. Strict Tooling & Code Quality
- **Ruff:** Configured for maximum coverage—acting as linter, formatter, and import organizer with strict rules enabled (E, F, I, N, UP, B, SIM, A, ARG, C4, COM, etc.).
- **`ty`:** Strict static type runner/checker for Python typing compliance and type safety.
- **pytest:** Enforcing test-driven development (TDD) and coverage metrics.
