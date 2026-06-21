"""CLI entry point for PAIOS-Lite.

Usage:
    python -m paios_lite --context <path>
    python -m src.main --context <path>
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from rich.console import Console
from rich.markdown import Markdown
from rich.rule import Rule

console = Console()


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="paios_lite",
        description="PAIOS-Lite: project continuity assistant",
    )
    parser.add_argument(
        "--context",
        required=True,
        metavar="PATH",
        help="Path to the project directory or context file to analyse.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = _parse_args(argv)
    context_path = args.context

    if not Path(context_path).exists():
        console.print(f"[red]Error:[/red] path does not exist: {context_path}")
        sys.exit(1)

    console.print(Rule("[bold cyan]PAIOS-Lite[/bold cyan]"))
    console.print(f"[dim]Context:[/dim] {context_path}")
    console.print()

    console.print("[cyan]\\[Memory Agent][/cyan] Reading project context…")

    # Import here so a missing .env produces a clear error before rich output
    from src.agents.memory_agent import run as memory_run  # noqa: PLC0415

    try:
        snapshot = memory_run(context_path)
    except EnvironmentError as exc:
        console.print(f"\n[red]Configuration error:[/red] {exc}")
        sys.exit(1)

    console.print()
    console.print(Rule("[bold cyan]Memory Snapshot[/bold cyan]"))
    console.print(Markdown(snapshot))
    console.print(Rule())


if __name__ == "__main__":
    main()
