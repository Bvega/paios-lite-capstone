"""Formatting tools for the Planner and Executor agents.

Both functions are pure standard-library Python — no LLM calls, no network
I/O, no filesystem access.
"""

from __future__ import annotations

import re

_MARKER_RE = re.compile(r'^(?:[-*]|\d+[.)])\s+')


def create_plan(context: str) -> str:
    """Wrap free-text context into a structured ## Plan block.

    Counts non-empty lines and appends a count footer. Returns a placeholder
    when context is empty or whitespace-only.
    """
    stripped = context.strip()
    if not stripped:
        return "## Plan\n\n(no context provided)\n"
    count = sum(1 for line in stripped.splitlines() if line.strip())
    return f"## Plan\n\n{stripped}\n\n{count} line(s) of context.\n"


def render_actions(plan: str) -> str:
    """Render a plan string into a numbered ## Next Actions block.

    Strips leading list markers (- / * / N. / N)) and renumbers items 1, 2, 3…
    in stable input order. Blank lines and lines that are empty after marker
    removal are ignored. Returns a placeholder when plan is empty or
    whitespace-only.
    """
    stripped = plan.strip()
    if not stripped:
        return "## Next Actions\n\n(no actions generated)\n"

    actions: list[str] = []
    for line in stripped.splitlines():
        text = line.strip()
        if not text:
            continue
        text = _MARKER_RE.sub("", text)
        if not text:
            continue
        actions.append(text)

    if not actions:
        return "## Next Actions\n\n(no actions generated)\n"

    items = "\n".join(f"  {i}. {action}" for i, action in enumerate(actions, 1))
    return f"## Next Actions\n\n{items}\n\n{len(actions)} action(s).\n"
