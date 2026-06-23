"""MCP stdio server for PAIOS-Lite.

Exposes the five existing local tool functions via FastMCP with stdio
transport. All tool logic lives in the original tool modules; this module
only registers wrappers and sanitises error messages for external clients.

Start command (stdio transport, default):
    python -m paios_lite.tools.mcp_server
"""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from src.tools.context_reader import (
    get_git_log as _get_git_log,
    read_project_context as _read_project_context,
)
from src.tools.note_searcher import search_notes as _search_notes
from src.tools.plan_tools import create_plan as _create_plan
from src.tools.plan_tools import render_actions as _render_actions

mcp = FastMCP("paios-lite")

_SAFE_PATH_ERROR = "Invalid or inaccessible project path"


@mcp.tool()
def read_project_context(path: str) -> str:
    """Return a structured text summary of the project at the given path."""
    try:
        return _read_project_context(path)
    except (ValueError, OSError):
        raise ValueError(_SAFE_PATH_ERROR) from None


@mcp.tool()
def get_git_log(path: str, n: int = 10) -> str:
    """Return the last n git commit one-liners from the repository at path."""
    try:
        return _get_git_log(path, n)
    except (ValueError, OSError):
        raise ValueError(_SAFE_PATH_ERROR) from None


@mcp.tool()
def search_notes(query: str, path: str) -> str:
    """Search Markdown files at path for lines matching query."""
    try:
        return _search_notes(query, path)
    except (ValueError, OSError):
        raise ValueError(_SAFE_PATH_ERROR) from None


@mcp.tool()
def create_plan(context: str) -> str:
    """Wrap free-text context into a structured Plan block."""
    return _create_plan(context)


@mcp.tool()
def render_actions(plan: str) -> str:
    """Render a plan string into a numbered Next Actions block."""
    return _render_actions(plan)


def main() -> None:
    """Start the MCP server using stdio transport."""
    mcp.run()
