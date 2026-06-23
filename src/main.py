"""CLI entry point for PAIOS-Lite.

Usage:
    python -m paios_lite --context <path>
    python -m src.main --context <path>
"""

from __future__ import annotations

import argparse
import asyncio
import random
import sys
from pathlib import Path

import httpx
from google.adk.agents import SequentialAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import errors as genai_errors
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

_RETRIABLE_HTTP_CODES = frozenset({408, 429, 500, 502, 503, 504})
_MAX_PIPELINE_ATTEMPTS = 3
_INITIAL_RETRY_DELAY = 2.0
_MAX_RETRY_DELAY = 30.0

console = Console()


def _is_retriable(exc: Exception) -> bool:
    """Return True only for transient provider errors safe to retry."""
    if isinstance(exc, genai_errors.APIError):
        return exc.code in _RETRIABLE_HTTP_CODES
    if isinstance(exc, (httpx.TimeoutException, httpx.ConnectError)):
        return True
    return False


async def _run_pipeline(
    context_path: str,
    *,
    seen_authors: set[str] | None = None,
) -> dict[str, str]:
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
    progress_authors = seen_authors if seen_authors is not None else set()
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
            and author not in progress_authors
            and callable(checker)
            and checker()
        ):
            progress_authors.add(author)
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


async def _run_pipeline_with_retry(
    context_path: str,
    *,
    sleep_func=None,
    jitter_func=None,
) -> dict[str, str]:
    """Run the pipeline with exponential-backoff retry on transient provider errors."""
    if sleep_func is None:
        sleep_func = asyncio.sleep
    if jitter_func is None:
        jitter_func = random.uniform

    seen_authors: set[str] = set()

    for attempt in range(1, _MAX_PIPELINE_ATTEMPTS + 1):
        try:
            return await _run_pipeline(context_path, seen_authors=seen_authors)
        except Exception as exc:
            if not _is_retriable(exc):
                raise
            if attempt == _MAX_PIPELINE_ATTEMPTS:
                raise
            delay = min(
                _INITIAL_RETRY_DELAY * (2 ** (attempt - 1)) + jitter_func(0.0, 1.0),
                _MAX_RETRY_DELAY,
            )
            label = (
                f"HTTP {exc.code}"
                if isinstance(exc, genai_errors.APIError)
                else type(exc).__name__
            )
            console.print(
                f"[yellow]Transient provider failure ({label}), "
                f"attempt {attempt}/{_MAX_PIPELINE_ATTEMPTS}; "
                f"retrying in {delay:.1f}s.[/yellow]"
            )
            await sleep_func(delay)


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

    try:
        results = asyncio.run(_run_pipeline_with_retry(context_path))
    except (genai_errors.APIError, httpx.TimeoutException, httpx.ConnectError) as exc:
        label = (
            f"HTTP {exc.code}"
            if isinstance(exc, genai_errors.APIError)
            else type(exc).__name__
        )
        console.print(f"\n[red]Provider error:[/red] {label}")
        sys.exit(1)

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
