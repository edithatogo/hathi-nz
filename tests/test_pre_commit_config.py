"""Tests for the repository pre-commit configuration."""

from __future__ import annotations

from pathlib import Path

CONFIG_PATH = Path(".pre-commit-config.yaml")
README_PATH = Path("README.md")


def test_pre_commit_config_exists_with_core_hooks() -> None:
    content = CONFIG_PATH.read_text(encoding="utf-8")

    assert "https://github.com/pre-commit/pre-commit-hooks" in content
    assert "id: check-merge-conflict" in content
    assert "id: end-of-file-fixer" in content
    assert "id: trailing-whitespace" in content
    assert "https://github.com/astral-sh/ruff-pre-commit" in content
    assert "id: ruff" in content
    assert "id: ruff-format" in content
    assert "repo: local" in content
    assert "id: ty-check" in content
    assert "entry: ty check" in content
    assert "https://github.com/crate-ci/typos" in content
    assert "id: typos" in content
    assert "https://github.com/ComPWA/taplo-pre-commit" in content
    assert "id: taplo-format" in content


def test_readme_documents_pre_commit_install() -> None:
    content = README_PATH.read_text(encoding="utf-8")

    assert "pre-commit install" in content
    assert "pre-commit run --all-files" in content
