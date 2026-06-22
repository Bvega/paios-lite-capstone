"""CLI entry point for PAIOS-Lite.

Usage:
    python -m paios_lite --context <path>
    python -m src.main --context <path>
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

from google.adk.agents import SequentialAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types as genai_types
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.rule import Rule
from rich.text import Text

from src import config
from src.agents import executor_agent, memory_agent, planner_agent, research_agent

_APP_NAME = "paios_lite"
_USER_ID = "cli_user"
_TRIGGER_MESSAGE = "Analyze the project and produce a memory snapshot."

_AGENT_LABELS: dict[str, str] = {
    "memory_agent":   "Memory Agent",
    "planner_agent":  "Planner Agent",
    "research_agent": "Research Agent",
    "executor_agent": "Executor Agent",
}

console = Console()


async def _run_pipeline(context_path: str) -> dict[str, str]:
    """Build and execute the four-agent pipeline; return all four state values."""
    pipeline = SequentialAgent(
        name="paios_lite_pipeline",
        sub_agents=[
            memory_agent.build_agent(),
            planner_agent.build_agent(),
            research_agent.build_agent(),
            executor_agent.build_agent(),
        ],
    )
    session_service = InMemorySessionService()
    runner = Runner(
        agent=pipeline,
        app_name=_APP_NAME,
        session_service=session_service,
    )
    session = await session_service.create_session(
        app_name=_APP_NAME,
        user_id=_USER_ID,
        state={"project_path": context_path},
    )
    message = genai_types.Content(
        role="user",
        parts=[genai_types.Part(text=_TRIGGER_MESSAGE)],
    )
    seen_authors: set[str] = set()
    async for event in runner.run_async(
        user_id=_USER_ID,
        session_id=session.id,
        new_message=message,
    ):
        author = getattr(event, "author", None)
        checker = getattr(event, "is_final_response", None)
        if (
            author
            and author in _AGENT_LABELS
            and author not in seen_authors
            and callable(checker)
            and checker()
        ):
            seen_authors.add(author)
            console.print(f"[green]✓[/green] {_AGENT_LABELS[author]} complete")
    final_session = await session_service.get_session(
        app_name=_APP_NAME,
        user_id=_USER_ID,
        session_id=session.id,
    )
    if final_session is None:
        raise RuntimeError(
            "Pipeline session could not be reloaded after execution."
        )
    return {
        "memory_snapshot": final_session.state.get(
            "memory_snapshot", "(Memory Agent produced no output.)"
        ),
        "plan": final_session.state.get(
            "plan", "(Planner Agent produced no output.)"
        ),
        "research_notes": final_session.state.get(
            "research_notes", "(Research Agent produced no output.)"
        ),
        "next_actions": final_session.state.get(
            "next_actions", "(Executor Agent produced no output.)"
        ),
    }


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

    try:
        config.validate_config()
    except EnvironmentError as exc:
        console.print(f"\n[red]Configuration error:[/red] {exc}")
        sys.exit(1)

    results = asyncio.run(_run_pipeline(context_path))

    console.print()
    header = Text(justify="center")
    header.append("PAIOS-Lite Continuity Brief")
    console.print(Panel(header))
    console.print()

    console.print(Rule("[bold cyan]Current State[/bold cyan]"))
    console.print(Markdown(results["memory_snapshot"]))
    console.print()
    console.print(Rule("[bold cyan]Plan[/bold cyan]"))
    console.print(Markdown(results["plan"]))
    console.print()
    console.print(Rule("[bold cyan]Research Notes[/bold cyan]"))
    console.print(Markdown(results["research_notes"]))
    console.print()
    console.print(Rule("[bold cyan]Next Actions[/bold cyan]"))
    console.print(Markdown(results["next_actions"]))
    console.print(Rule())


if __name__ == "__main__":
    main()
