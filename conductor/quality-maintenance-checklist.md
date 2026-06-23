# Quality & Maintenance Tooling Baseline — hathi-nz

| Tool            | Classification | Status       |
|-----------------|----------------|--------------|
| Vale            | Required       | Present      |
| Markdown style  | Required       | Missing      |
| Renovate        | Required       | Missing      |
| Codecov         | Conditional    | Missing      |
| Scalene         | Conditional    | Missing      |

## Notes

- **Vale**: `.vale.ini` present with write-good extension — good shape.
- **Markdown style**: `.markdownlint.json` missing — created from root template.
- **Renovate**: `renovate.json` missing — created from `cli-legislation-nz` reference.
- **Codecov** (conditional): CI runs `--cov` and `pytest-cov` is in dev deps, so coverage is already generated. Codecov upload step could be added for visibility but is not currently wired.
- **Scalene** (conditional): No `[tool.scalene]` in `pyproject.toml`; no Scalene invocation in CI. Not currently used.
