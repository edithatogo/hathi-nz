"""Dynamic version resolution for hathi-nz.

Resolves the package version at runtime from (in priority order):
  1. ``git describe --tags`` (development / pixi environment)
  2. ``importlib.metadata.version("hathi-nz")`` (pip-installed package)
  3. The ``VERSION`` file at the repo root (CI fallback)
  4. ``"0.0.0"`` (ultimate fallback)

This eliminates hardcoded version strings scattered across scripts.
"""

from __future__ import annotations

import subprocess
from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as _md_version
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _git_describe() -> str | None:
    """Return ``git describe --tags --always`` output, or ``None`` on failure."""
    try:
        result = subprocess.run(  # noqa: S603, S607
            ["git", "describe", "--tags", "--always"],
            capture_output=True,
            text=True,
            cwd=ROOT,
            check=True,
        )
        return result.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError, OSError):
        return None


def _read_version_file() -> str | None:
    """Read the ``VERSION`` file if it exists."""
    version_file = ROOT / "VERSION"
    if version_file.exists():
        return version_file.read_text(encoding="utf-8").strip()
    return None


def _from_metadata() -> str | None:
    """Try ``importlib.metadata`` for installed packages."""
    try:
        return _md_version("hathi-nz")
    except PackageNotFoundError:
        return None


def _looks_like_version(s: str) -> bool:
    """Check if a string looks like a version (starts with digit or 'v' + digit)."""
    if not s:
        return False
    if s[0].isdigit():
        return True
    return len(s) > 1 and s[0] == "v" and s[1].isdigit()


def get_version() -> str:
    """Resolve the package version dynamically.

    Returns:
        A version string derived from git tags, package metadata,
        the VERSION file, or ``"0.0.0"`` as a last resort.

    """
    # 1. Git describe (preferred in development)
    if (git_version := _git_describe()) and _looks_like_version(git_version):
        return git_version

    # 2. VERSION file (CI fallback, also used by pixi)
    if file_version := _read_version_file():
        return file_version

    # 3. importlib.metadata (pip-installed)
    if md_version := _from_metadata():
        return md_version

    # 4. Ultimate fallback
    return "0.0.0"


__version__ = get_version()
