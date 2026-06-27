from __future__ import annotations

import re
import subprocess
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?$")


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

    # VERSION file is the source of truth for pixi/CI environments
    version_file = _text("VERSION").strip()
    if not SEMVER_RE.fullmatch(version_file):
        failures.append(f"VERSION is not SemVer-compatible: {version_file}")

    # pyproject.toml uses dynamic versioning (hatch-vcs); skip static check
    # but verify the build-system is configured
    pyproject = tomllib.loads(_text("pyproject.toml"))
    build_sys = pyproject.get("build-system", {})
    if "hatch-vcs" not in build_sys.get("requires", []):
        failures.append("pyproject.toml build-system missing hatch-vcs dependency")

    # pixi.toml must match VERSION file (pixi doesn't support dynamic versioning)
    pixi = tomllib.loads(_text("pixi.toml"))
    pixi_version = str(pixi["project"]["version"])
    if pixi_version != version_file:
        failures.append(f"Version mismatch: pixi.toml {pixi_version} != VERSION {version_file}")

    # Git tag should match VERSION (with optional 'v' prefix)
    git_tag = _git_tag()
    if git_tag:
        tag_version = _strip_v_prefix(git_tag)
        if tag_version != version_file:
            failures.append(
                f"Version mismatch: git tag {git_tag} (→{tag_version}) != VERSION {version_file}"
            )

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
