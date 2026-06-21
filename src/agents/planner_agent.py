"""Planner Agent for the PAIOS-Lite continuity pipeline."""

from __future__ import annotations

from google.adk.agents import LlmAgent

from src import config
from src.tools.plan_tools import create_plan


_INSTRUCTION = """\
You are the Planner Agent for PAIOS-Lite, a project continuity assistant.

The Memory Agent has already analyzed the project and produced this snapshot:

{memory_snapshot}

Your job is to produce an ordered task plan from that snapshot.

Steps:
1. Identify the most important tasks, blockers, and next milestones from the
   snapshot above. Limit the result to the 5 highest-priority items.
2. Call create_plan with those tasks as the context argument.
   Format each task on its own line:
       [N] PRIORITY  Description (est. Xh)
   Valid priorities: CRITICAL, HIGH, LOW, NICE-TO-HAVE
3. Return the complete output of create_plan as your final response.

Rules:
- Base tasks only on information present in the memory snapshot.
- Do not invent tasks or project facts.
- Do not reproduce the raw snapshot verbatim.
- If the snapshot reports nothing open, call create_plan with
  "No open tasks found."
"""


def build_agent() -> LlmAgent:
    """Build the Planner Agent using the currently configured LLM model."""
    return LlmAgent(
        name="planner_agent",
        model=config.get_llm_model(),
        description=(
            "Reads the memory snapshot and produces an ordered task plan."
        ),
        instruction=_INSTRUCTION,
        tools=[create_plan],
        output_key="plan",
    )
