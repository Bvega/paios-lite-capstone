"""Memory Agent for the PAIOS-Lite continuity pipeline."""

from __future__ import annotations

from google.adk.agents import LlmAgent

from src import config
from src.tools.context_reader import get_git_log, read_project_context


_INSTRUCTION = """\
You are the Memory Agent for PAIOS-Lite, a project continuity assistant.

Project path: {project_path}

Your only job is to examine the project at that path using the available tools
and produce a concise, structured Memory Snapshot in Markdown.

Steps:
1. Call read_project_context with {project_path} as the path argument to
   inspect files and TODO markers.
2. Call get_git_log with {project_path} as the path argument and n=10 to
   see recent commits.
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
- Call each tool at most once.
- If read_project_context returns an error, report it in ## Current State.
"""


def build_agent() -> LlmAgent:
    """Build the Memory Agent using the currently configured LLM model."""
    return LlmAgent(
        name="memory_agent",
        model=config.get_llm_model(),
        description=(
            "Reads project context and git history; produces a memory snapshot."
        ),
        instruction=_INSTRUCTION,
        tools=[read_project_context, get_git_log],
        output_key="memory_snapshot",
    )
