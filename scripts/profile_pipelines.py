#!/usr/bin/env python
"""Profile the HathiTrust metadata inventory and large manifest/checksum paths."""

import cProfile
import io
import pstats
import sys
from pathlib import Path

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent))

from rich.console import Console

console = Console()

# Base directory for this repo
BASE_DIR = Path(__file__).parent.parent


def profile_fetch_hathitrust():
    """Profile the fetch_hathitrust script."""
    console.print("[bold cyan]Profiling fetch_hathitrust...[/bold cyan]")

    profiler = cProfile.Profile()
    profiler.enable()

    try:
        from fetch_hathitrust import main as fetch_main

        console.print("[yellow]fetch_hathitrust imported (full run requires CLI args)[/yellow]")
    except ImportError as e:
        console.print(f"[red]Could not import fetch_hathitrust: {e}[/red]")

    profiler.disable()

    s = io.StringIO()
    ps = pstats.Stats(profiler, stream=s).sort_stats("cumulative")
    ps.print_stats(30)
    console.print(s.getvalue())

    output_path = BASE_DIR / "logs" / "profile_fetch_hathitrust.txt"
    output_path.parent.mkdir(exist_ok=True)
    output_path.write_text(s.getvalue())
    console.print(f"[green]Profile saved to {output_path}[/green]")


def profile_validate_catalog():
    """Profile the validate_catalog script."""
    console.print("[bold cyan]Profiling validate_catalog...[/bold cyan]")

    profiler = cProfile.Profile()
    profiler.enable()

    try:
        from validate_catalog import main as validate_main

        console.print("[yellow]validate_catalog imported (full run requires CLI args)[/yellow]")
    except ImportError as e:
        console.print(f"[red]Could not import validate_catalog: {e}[/red]")

    profiler.disable()

    s = io.StringIO()
    ps = pstats.Stats(profiler, stream=s).sort_stats("cumulative")
    ps.print_stats(30)
    console.print(s.getvalue())

    output_path = BASE_DIR / "logs" / "profile_validate_catalog.txt"
    output_path.parent.mkdir(exist_ok=True)
    output_path.write_text(s.getvalue())
    console.print(f"[green]Profile saved to {output_path}[/green]")


def profile_ocr_extract():
    """Profile the OCR extraction script."""
    console.print("[bold cyan]Profiling ocr_extract...[/bold cyan]")

    profiler = cProfile.Profile()
    profiler.enable()

    try:
        from ocr_extract import main as ocr_main

        console.print("[yellow]ocr_extract imported (full run requires CLI args)[/yellow]")
    except ImportError as e:
        console.print(f"[red]Could not import ocr_extract: {e}[/red]")

    profiler.disable()

    s = io.StringIO()
    ps = pstats.Stats(profiler, stream=s).sort_stats("cumulative")
    ps.print_stats(30)
    console.print(s.getvalue())

    output_path = BASE_DIR / "logs" / "profile_ocr_extract.txt"
    output_path.parent.mkdir(exist_ok=True)
    output_path.write_text(s.getvalue())
    console.print(f"[green]Profile saved to {output_path}[/green]")


def profile_package_release():
    """Profile the package_release script (manifest/checksum)."""
    console.print("[bold cyan]Profiling package_release...[/bold cyan]")

    profiler = cProfile.Profile()
    profiler.enable()

    try:
        from package_release import main as package_main

        console.print("[yellow]package_release imported (full run requires CLI args)[/yellow]")
    except ImportError as e:
        console.print(f"[red]Could not import package_release: {e}[/red]")

    profiler.disable()

    s = io.StringIO()
    ps = pstats.Stats(profiler, stream=s).sort_stats("cumulative")
    ps.print_stats(30)
    console.print(s.getvalue())

    output_path = BASE_DIR / "logs" / "profile_package_release.txt"
    output_path.parent.mkdir(exist_ok=True)
    output_path.write_text(s.getvalue())
    console.print(f"[green]Profile saved to {output_path}[/green]")


def main():
    """Run all profiling tasks."""
    console.print("[bold]Starting hathi-nz profiling[/bold]")

    # Ensure logs directory exists
    (BASE_DIR / "logs").mkdir(exist_ok=True)

    # Run profiles
    profile_fetch_hathitrust()
    profile_validate_catalog()
    profile_ocr_extract()
    profile_package_release()

    console.print("[bold green]Profiling complete![/bold green]")


if __name__ == "__main__":
    main()
