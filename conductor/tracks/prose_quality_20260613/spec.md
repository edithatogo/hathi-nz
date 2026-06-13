# Specification: Prose Linting & Documentation Quality (prose_quality_20260613)

## 1. Overview
This track integrates automated prose linters, spelling validators, and documentation style checks to ensure documentation remains clean, consistent, and error-free. It aligns with quality processes used in `corpus-nz-hansard` and `corpus-law-nz`.

## 2. Integrated Tools
- **Vale:** A prose linter to check readability, style guidelines, and correct grammar inside Markdown documentation.
- **typos:** Fast, source-code spellchecker to prevent spelling bugs in both code and markdown.
- **taplo:** TOML formatting and schema checking (e.g. for `pixi.toml` or `pyproject.toml`).
- **actionlint:** Direct syntax validation for GitHub Action workflows under `.github/workflows`.
- **Markdown & Mermaid styleguides:** Written in `conductor/code_styleguides/` to guide developers.

## 3. Configuration
- Vale will use `.vale.ini` checking for `*.md` files.
- `typos` will use a local `typos.toml` for exceptions.
- Integration into the master development execution commands.
