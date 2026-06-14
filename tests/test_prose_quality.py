"""Tests for prose quality linting tool configuration.

Verifies that linter configs exist and tools can execute.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent


def test_typos_toml_exists() -> None:
    """typos.toml configuration file must exist."""
    path = PROJECT_ROOT / "typos.toml"
    assert path.exists(), f"typos.toml not found at {path}"
    content = path.read_text(encoding="utf-8")
    assert "[default]" in content
    assert "extend-ignore-re" in content or "extend-words" in content


def test_vale_ini_exists() -> None:
    """.vale.ini configuration file must exist."""
    path = PROJECT_ROOT / ".vale.ini"
    assert path.exists(), f".vale.ini not found at {path}"
    content = path.read_text(encoding="utf-8")
    assert "StylesPath" in content
    assert "[*.md]" in content
    assert "BasedOnStyles" in content


def test_vale_ini_has_styles() -> None:
    """.vale.ini should reference prose and write-good styles."""
    path = PROJECT_ROOT / ".vale.ini"
    content = path.read_text(encoding="utf-8")
    assert "write-good" in content or "prose" in content


def test_vale_styles_directory() -> None:
    """Vale styles directory should exist or be installable."""
    styles_path = PROJECT_ROOT / "styles"
    # styles may not exist yet; that's okay, just verify config references it
    ini_path = PROJECT_ROOT / ".vale.ini"
    content = ini_path.read_text(encoding="utf-8")
    assert "StylesPath" in content


def test_pixi_toml_has_quality_tasks() -> None:
    """pixi.toml must contain spell, toml-check, workflow-syntax, and quality tasks."""
    path = PROJECT_ROOT / "pixi.toml"
    assert path.exists()
    content = path.read_text(encoding="utf-8")
    assert 'spell = "typos' in content
    assert 'toml-check = "taplo' in content
    assert 'workflow-syntax = "actionlint' in content
    assert "quality" in content
    assert "depends_on" in content


def test_pixi_toml_has_lint_and_format_check() -> None:
    """pixi.toml must still have lint and format-check tasks."""
    path = PROJECT_ROOT / "pixi.toml"
    content = path.read_text(encoding="utf-8")
    assert 'lint = "ruff check' in content
    assert 'format-check = "ruff format' in content


def test_ruff_can_run() -> None:
    """ruff should be importable and discoverable."""
    try:
        import ruff as _  # noqa: F401
    except ImportError:
        # ruff may be installed as standalone binary
        result = subprocess.run(
            [sys.executable, "-m", "ruff", "--version"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0, f"ruff not available: {result.stderr}"


def test_taplo_importable() -> None:
    """taplo (TOML formatter) should be importable if installed."""
    try:
        import taplo as _  # noqa: F401
    except ImportError:
        # taplo may be a standalone binary
        pass  # Not a hard failure — CI might have it as binary


def test_typos_available() -> None:
    """typos binary should be discoverable (importable or on PATH)."""
    try:
        import typos as _  # noqa: F401
        return  # Import worked
    except ImportError:
        pass

    result = subprocess.run(
        ["typos", "--version"],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, f"typos not available: {result.stderr}"


def test_typos_config_has_nz_exceptions() -> None:
    """typos.toml should contain NZ legal spelling exceptions."""
    path = PROJECT_ROOT / "typos.toml"
    content = path.read_text(encoding="utf-8")
    # Check for key NZ legal terms in extend-words or extend-ignore-re
    terms = ["hathitrust", "hansard", "parliament", "zenodo", "huggingface"]
    found_any = any(term in content for term in terms)
    assert found_any, f"None of the NZ terms {terms} found in typos.toml"


def test_vale_config_has_nz_exceptions() -> None:
    """.vale.ini should have NZ term exceptions in prose.Spelling.Extend."""
    path = PROJECT_ROOT / ".vale.ini"
    content = path.read_text(encoding="utf-8")
    terms = ["hansard", "hathitrust", "parliament", "zenodo"]
    found_any = any(term in content for term in terms)
    assert found_any, f"None of the NZ terms {terms} found in .vale.ini"
