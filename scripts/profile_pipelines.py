#!/usr/bin/env python
"""Profile the HathiTrust metadata inventory and large manifest/checksum paths."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from textwrap import dedent

from rich.console import Console

console = Console()

BASE_DIR = Path(__file__).parent.parent
LOGS_DIR = BASE_DIR / "logs"

PROFILE_TARGETS = (
    ("fetch_hathitrust", "fetch_hathitrust.py"),
    ("validate_catalog", "validate_catalog.py"),
    ("ocr_extract", "ocr_extract.py"),
    ("package_release", "package_release.py"),
)


def _write_profile_wrapper(module_name: str) -> Path:
    """Create a tiny wrapper script to profile a module import path."""
    LOGS_DIR.mkdir(exist_ok=True)
    fd, raw_path = tempfile.mkstemp(prefix=f"profile_{module_name}_", suffix=".py")
    os.close(fd)
    wrapper_path = Path(raw_path)
    wrapper_path.write_text(
        dedent(
            f"""
            from scripts import {module_name} as _target


            def main() -> None:
                _ = _target  # Import for profiling side effects.


            if __name__ == "__main__":
                main()
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )
    return wrapper_path


def profile_with_scalene(module_name: str) -> Path:
    """Run Scalene against a lightweight wrapper for a script module."""
    console.print(f"[bold cyan]Profiling {module_name} with Scalene...[/bold cyan]")
    output_path = LOGS_DIR / f"profile_{module_name}.txt"
    wrapper_path = _write_profile_wrapper(module_name)
    try:
        subprocess.run(
            [
                sys.executable,
                "-m",
                "scalene",
                "run",
                "--outfile",
                str(output_path),
                "--reduced-profile",
                str(wrapper_path),
            ],
            check=True,
        )
    finally:
        wrapper_path.unlink(missing_ok=True)

    console.print(f"[green]Profile saved to {output_path}[/green]")
    return output_path


def parse_args(args: list[str] | None = None) -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(description="Profile core pipeline scripts with Scalene.")
    parser.add_argument(
        "--target",
        choices=[name for name, _ in PROFILE_TARGETS] + ["all"],
        default="all",
        help="Which pipeline script to profile.",
    )
    return parser.parse_args(args)


def main(args: list[str] | None = None) -> int:
    """Run the requested profiling tasks."""
    parsed = parse_args(args)
    LOGS_DIR.mkdir(exist_ok=True)

    targets = PROFILE_TARGETS
    if parsed.target != "all":
        targets = tuple(target for target in PROFILE_TARGETS if target[0] == parsed.target)

    for module_name, _script_file in targets:
        profile_with_scalene(module_name)

    console.print("[bold green]Profiling complete![/bold green]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
