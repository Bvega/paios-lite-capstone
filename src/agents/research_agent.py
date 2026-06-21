"""Research Agent for the PAIOS-Lite continuity pipeline."""

from __future__ import annotations

from google.adk.agents import LlmAgent

from src import config
from src.tools.note_searcher import search_notes


_INSTRUCTION = """\
You are the Research Agent for PAIOS-Lite, a project continuity assistant.

The Memory Agent produced this project snapshot:

{memory_snapshot}

The Planner Agent produced this task plan:

{plan}

Project context path (use this as the path argument for all search_notes calls):

{project_path}

Your job is to search the project notes for context relevant to the
highest-priority tasks in the plan.

Steps:
1. Identify up to 3 CRITICAL or HIGH priority tasks from the plan.
2. For each task, derive a short keyword or phrase that captures its subject.
3. Call search_notes using that keyword and the project context path shown
   above.
4. Collect the results and produce a Research Notes block that links each
   finding to the task it supports.
5. Return the complete Research Notes block as your final response.

Format your response as:

## Research Notes

### <Task description>
<Search findings, or "No relevant notes found.">

N task(s) researched.

Rules:
- Call search_notes at most 5 times total.
- Use short, specific keywords derived from the task description.
- Do not call search_notes with an empty query.
- Always use the exact project context path shown above.
- If a search returns no results or an unsupported-file message, note it
  briefly and continue.
- Do not reproduce the memory snapshot or plan verbatim.
- Do not invent project facts.
"""


def build_agent() -> LlmAgent:
    """Build the Research Agent using the currently configured LLM model."""
    return LlmAgent(
        name="research_agent",
        model=config.get_llm_model(),
        description=(
            "Searches project notes for context relevant to high-priority tasks."
        ),
        instruction=_INSTRUCTION,
        tools=[search_notes],
        output_key="research_notes",
    )
