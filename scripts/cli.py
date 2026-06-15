"""CLI-first dispatcher for repository maintenance scripts.

This module provides one stable console command for agents, humans, and CI.
Existing scripts remain the implementation source of truth; this dispatcher only
routes approved command names to those scripts.
"""

from __future__ import annotations

import argparse
import runpy
import sys
from collections.abc import Sequence
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = REPO_ROOT / "scripts"

COMMANDS: dict[str, str] = {'fetch': 'fetch_hathitrust.py', 'ocr': 'ocr_extract.py', 'package': 'package_release.py', 'publish-zenodo': 'publish_zenodo.py', 'stage': 'stage_hf_dataset.py', 'upload': 'upload_hf_dataset.py', 'validate': 'validate_catalog.py'}


def _script_path(name: str) -> Path:
    script = COMMANDS.get(name, name)
    if not script.endswith(".py"):
        script = f"{script}.py"
    path = SCRIPT_DIR / script
    if not path.is_file():
        available = ", ".join(sorted(COMMANDS))
        raise SystemExit(f"Unknown command or missing script: {name}. Available aliases: {available}")
    return path


def _run_script(path: Path, args: Sequence[str]) -> int:
    old_argv = sys.argv[:]
    try:
        sys.argv = [str(path), *args]
        runpy.run_path(str(path), run_name="__main__")
    finally:
        sys.argv = old_argv
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="CLI-first dispatcher for repository scripts.")
    parser.add_argument("command", nargs="?", help="Approved command alias or scripts/*.py name.")
    parser.add_argument("args", nargs=argparse.REMAINDER, help="Arguments passed to the selected script.")
    parser.add_argument("--list", action="store_true", help="List approved command aliases and exit.")
    ns = parser.parse_args(argv)
    if ns.list:
        for alias, script in sorted(COMMANDS.items()):
            print(f"{alias}	{script}")
        return 0
    if not ns.command:
        parser.error("command is required unless --list is used")
    return _run_script(_script_path(ns.command), ns.args)


if __name__ == "__main__":
    raise SystemExit(main())
