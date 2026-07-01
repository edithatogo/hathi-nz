from __future__ import annotations

import subprocess
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def _git_tag() -> str | None:
    """Return the latest git tag (e.g. ``v0.1.0``) or ``None``."""
    try:
        result = subprocess.run(  # noqa: S603, S607
            ["git", "describe", "--tags", "--abbrev=0"],
            capture_output=True,
            text=True,
            cwd=ROOT,
            check=True,
        )
        return result.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError, OSError):
        return None


def _strip_v_prefix(tag: str) -> str:
    """Strip a leading ``v`` from a tag (``v0.1.0`` → ``0.1.0``)."""
    return tag.removeprefix("v")


def check_version_consistency() -> list[str]:
    failures: list[str] = []

    # pyproject.toml uses dynamic versioning (hatch-vcs); skip static check
    # but verify the build-system is configured
    pyproject = tomllib.loads(_text("pyproject.toml"))
    build_sys = pyproject.get("build-system", {})
    if "hatch-vcs" not in build_sys.get("requires", []):
        failures.append("pyproject.toml build-system missing hatch-vcs dependency")

    # pixi.toml should not pin a version; the package version is derived from git tags.
    pixi = tomllib.loads(_text("pixi.toml"))
    project = pixi.get("project", {})
    if "version" in project:
        failures.append("pixi.toml project version must be omitted")

    # Git tag should be semver-like when present.
    git_tag = _git_tag()
    if git_tag:
        tag_version = _strip_v_prefix(git_tag)
        if not tag_version or not tag_version[0].isdigit():
            failures.append(f"Git tag is not version-like: {git_tag}")

    return failures


def main() -> int:
    failures = check_version_consistency()
    if failures:
        for f in failures:
            print(f"ERROR: {f}")
        return 1
    print("Version consistency checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
