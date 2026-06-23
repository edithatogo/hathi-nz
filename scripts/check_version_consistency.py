from __future__ import annotations

import re
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?$")


def _text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def check_version_consistency() -> list[str]:
    failures: list[str] = []

    version_file = _text("VERSION").strip()
    if not SEMVER_RE.fullmatch(version_file):
        failures.append(f"VERSION is not SemVer-compatible: {version_file}")

    pyproject = tomllib.loads(_text("pyproject.toml"))
    pyproject_version = str(pyproject["project"]["version"])
    if pyproject_version != version_file:
        failures.append(
            "Version mismatch: pyproject.toml "
            f"{pyproject_version} != VERSION {version_file}"
        )

    pixi = tomllib.loads(_text("pixi.toml"))
    pixi_version = str(pixi["project"]["version"])
    if pixi_version != version_file:
        failures.append(
            "Version mismatch: pixi.toml "
            f"{pixi_version} != VERSION {version_file}"
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
