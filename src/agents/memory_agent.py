"""Memory Agent — reads local project files and returns a structured snapshot.

Uses the Google ADK LlmAgent with the tool functions from src.tools.context_reader.
The LLM model is read from the environment at call time (never hardcoded here).
"""

from __future__ import annotations

import asyncio

from google.adk.agents import LlmAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types as genai_types

from src import config
from src.tools.context_reader import get_git_log, read_project_context

_APP_NAME = "paios_lite"
_USER_ID = "cli_user"

_INSTRUCTION = """\
You are the Memory Agent for PAIOS-Lite, a project continuity assistant.

Your only job is to examine the given project path using the available tools
and produce a concise, structured Memory Snapshot in Markdown.

Steps:
1. Call read_project_context with the provided path to inspect files and TODOs.
2. Call get_git_log with the same path to see recent commits.
3. Return a Memory Snapshot with exactly these sections:

## Project Identity
One or two sentences: what is this project and what does it do?

## Recent Activity
Summarize the last few git commits. If none, say so.

## Current State
What is complete, what is in progress, what is clearly blocked or missing.

## Open Items
Bullet list of TODO / FIXME markers or obvious gaps found in the context.
If none found, say "No open items detected."

## Key Files
Short table or list of the most important files and their role.

Rules:
- Be concise. Every line should be information a developer can act on.
- Do not invent details not present in the tool output.
- Do not include raw tool output verbatim — summarize it.
"""


async def _run_async(path: str) -> str:
    """Build and run the Memory Agent, returning the snapshot text."""
    agent = LlmAgent(
        name="memory_agent",
        model=config.get_llm_model(),
        description="Reads local project files and git history, returns a memory snapshot.",
        instruction=_INSTRUCTION,
        tools=[read_project_context, get_git_log],
    )

    session_service = InMemorySessionService()
    runner = Runner(
        agent=agent,
        app_name=_APP_NAME,
        session_service=session_service,
    )
    session = await session_service.create_session(
        app_name=_APP_NAME,
        user_id=_USER_ID,
    )

    prompt = (
        f"Analyze the project at this path: {path}\n\n"
        "Call read_project_context first, then get_git_log. "
        "Return the complete Memory Snapshot."
    )
    message = genai_types.Content(
        role="user",
        parts=[genai_types.Part(text=prompt)],
    )

    snapshot = "(Memory Agent produced no output.)"
    async for event in runner.run_async(
        user_id=_USER_ID,
        session_id=session.id,
        new_message=message,
    ):
        if event.is_final_response():
            if event.content and event.content.parts:
                text = event.content.parts[0].text
                if text:
                    snapshot = text

    return snapshot


def run(path: str) -> str:
    """Validate config, then run the Memory Agent against *path*.

    This is the public synchronous entry point called by main.py.
    """
    config.validate_config()
    return asyncio.run(_run_async(path))
