"""Tests for the Phase 3A MCP stdio server.

All tests are network-free, key-free, and do not start the blocking stdio loop.
Uses only public FastMCP interfaces: mcp.list_tools() and mcp.call_tool().

From the Phase 3A preflight, call_tool returns a two-element tuple:
    (list[TextContent], dict)
where tuple[0][0].text is the plain string the tool returned, and
tuple[1] is {'result': <return_value>}.
"""

from __future__ import annotations

import asyncio
from pathlib import Path

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _run(coro):
    """Run a coroutine synchronously, consistent with the existing test style."""
    return asyncio.run(coro)


def _text_from(call_result) -> str:
    """Extract the plain text string from a call_tool tuple result."""
    content_list, _structured = call_result
    return content_list[0].text


# ---------------------------------------------------------------------------
# 1. Import without starting stdio
# ---------------------------------------------------------------------------


def test_src_mcp_server_imports_without_starting_stdio():
    """Importing src.tools.mcp_server must not block or start the stdio loop."""
    import src.tools.mcp_server as srv
    assert hasattr(srv, "mcp")
    assert hasattr(srv, "main")


def test_paios_lite_mcp_server_imports_without_starting_stdio():
    """Importing paios_lite.tools.mcp_server must not block or start stdio."""
    import paios_lite.tools.mcp_server as delegator
    assert hasattr(delegator, "main")


# ---------------------------------------------------------------------------
# 2. Exactly five tools registered
# ---------------------------------------------------------------------------


def test_exactly_five_tools_registered():
    """Exactly five tools must be registered on the mcp server instance."""
    from src.tools.mcp_server import mcp
    tools = _run(mcp.list_tools())
    assert len(tools) == 5


# ---------------------------------------------------------------------------
# 3. Registered names are exactly the five locked names
# ---------------------------------------------------------------------------


_EXPECTED_TOOL_NAMES = {
    "read_project_context",
    "get_git_log",
    "search_notes",
    "create_plan",
    "render_actions",
}


def test_registered_tool_names_are_correct():
    """Registered tool names must match the five architecture-locked names exactly."""
    from src.tools.mcp_server import mcp
    tools = _run(mcp.list_tools())
    names = {t.name for t in tools}
    assert names == _EXPECTED_TOOL_NAMES


# ---------------------------------------------------------------------------
# 4. Input schemas reflect required parameters and defaults
# ---------------------------------------------------------------------------


def _schema_for(name: str):
    from src.tools.mcp_server import mcp
    tools = _run(mcp.list_tools())
    return next(t for t in tools if t.name == name).inputSchema


def test_read_project_context_schema_has_path():
    schema = _schema_for("read_project_context")
    assert "path" in schema.get("properties", {})
    assert "path" in schema.get("required", [])


def test_get_git_log_schema_has_path_and_n():
    schema = _schema_for("get_git_log")
    props = schema.get("properties", {})
    assert "path" in props
    assert "n" in props
    assert "path" in schema.get("required", [])


def test_search_notes_schema_has_query_and_path():
    schema = _schema_for("search_notes")
    props = schema.get("properties", {})
    assert "query" in props
    assert "path" in props
    required = schema.get("required", [])
    assert "query" in required
    assert "path" in required


def test_create_plan_schema_has_context():
    schema = _schema_for("create_plan")
    assert "context" in schema.get("properties", {})
    assert "context" in schema.get("required", [])


def test_render_actions_schema_has_plan():
    schema = _schema_for("render_actions")
    assert "plan" in schema.get("properties", {})
    assert "plan" in schema.get("required", [])


# ---------------------------------------------------------------------------
# 5. create_plan dispatch via call_tool
# ---------------------------------------------------------------------------


def test_create_plan_dispatch_succeeds():
    """create_plan called through call_tool returns a Plan block."""
    from src.tools.mcp_server import mcp
    result = _run(mcp.call_tool("create_plan", {"context": "Wire memory agent\nWrite tests"}))
    text = _text_from(result)
    assert "## Plan" in text
    assert "Wire memory agent" in text


def test_create_plan_empty_context_returns_placeholder():
    """create_plan with empty context returns the placeholder message."""
    from src.tools.mcp_server import mcp
    result = _run(mcp.call_tool("create_plan", {"context": ""}))
    text = _text_from(result)
    assert "## Plan" in text
    assert "no context provided" in text


# ---------------------------------------------------------------------------
# 6. render_actions dispatch via call_tool
# ---------------------------------------------------------------------------


def test_render_actions_dispatch_succeeds():
    """render_actions called through call_tool returns a Next Actions block."""
    from src.tools.mcp_server import mcp
    result = _run(mcp.call_tool("render_actions", {"plan": "- Run tests\n- Deploy app"}))
    text = _text_from(result)
    assert "## Next Actions" in text
    assert "Run tests" in text
    assert "Deploy app" in text


def test_render_actions_empty_plan_returns_placeholder():
    """render_actions with empty plan returns the placeholder message."""
    from src.tools.mcp_server import mcp
    result = _run(mcp.call_tool("render_actions", {"plan": ""}))
    text = _text_from(result)
    assert "## Next Actions" in text
    assert "no actions generated" in text


# ---------------------------------------------------------------------------
# 7. search_notes dispatch against a temporary Markdown project
# ---------------------------------------------------------------------------


def test_search_notes_dispatch_finds_match(tmp_path):
    """search_notes called through call_tool finds content in a temp directory."""
    (tmp_path / "notes.md").write_text("# Project\n\nTODO: implement feature X\n")
    from src.tools.mcp_server import mcp
    result = _run(mcp.call_tool("search_notes", {"query": "TODO", "path": str(tmp_path)}))
    text = _text_from(result)
    assert "TODO" in text


def test_search_notes_dispatch_no_match(tmp_path):
    """search_notes returns a no-match message when query is absent."""
    (tmp_path / "notes.md").write_text("# Project\nAll good here.\n")
    from src.tools.mcp_server import mcp
    result = _run(mcp.call_tool("search_notes", {"query": "xyzzy_absent_12345", "path": str(tmp_path)}))
    text = _text_from(result)
    assert "No matches" in text


# ---------------------------------------------------------------------------
# 8. read_project_context dispatch against a temporary project
# ---------------------------------------------------------------------------


def test_read_project_context_dispatch_single_file(tmp_path):
    """read_project_context returns content when called through call_tool."""
    md = tmp_path / "README.md"
    md.write_text("# Test Project\n\nA sample.\n")
    from src.tools.mcp_server import mcp
    result = _run(mcp.call_tool("read_project_context", {"path": str(md)}))
    text = _text_from(result)
    assert "README" in text
    assert "Test Project" in text


def test_read_project_context_dispatch_directory(tmp_path):
    """read_project_context returns a directory listing when called through call_tool."""
    (tmp_path / "README.md").write_text("# Temp\n")
    (tmp_path / "src").mkdir()
    from src.tools.mcp_server import mcp
    result = _run(mcp.call_tool("read_project_context", {"path": str(tmp_path)}))
    text = _text_from(result)
    assert "Project root" in text


# ---------------------------------------------------------------------------
# 9. get_git_log dispatch without a network call
# ---------------------------------------------------------------------------


def test_get_git_log_dispatch_returns_string(tmp_path):
    """get_git_log returns a string result; non-repo path returns graceful message."""
    from src.tools.mcp_server import mcp
    result = _run(mcp.call_tool("get_git_log", {"path": str(tmp_path)}))
    text = _text_from(result)
    assert isinstance(text, str)
    assert len(text) > 0


def test_get_git_log_dispatch_on_real_repo():
    """get_git_log called on the project repo returns commit lines."""
    from pathlib import Path
    project_root = str(Path(__file__).parent.parent.resolve())
    from src.tools.mcp_server import mcp
    result = _run(mcp.call_tool("get_git_log", {"path": project_root, "n": 3}))
    text = _text_from(result)
    assert isinstance(text, str)
    assert len(text) > 0


# ---------------------------------------------------------------------------
# 10. Invalid path: error reported, raw path not disclosed
# ---------------------------------------------------------------------------

_SENTINEL = "/nonexistent/__paios_sentinel_path_xyz_99999__"


def _call_path_tool_and_check_error(tool_name: str, args: dict, sentinel: str) -> None:
    """
    Call a path tool with an invalid sentinel path via call_tool.
    Handles both FastMCP behaviours:
      - raises an exception (sentinel absent from message required)
      - returns a result (sentinel absent from content required)
    In both cases the generic safe message must be present.
    """
    from src.tools.mcp_server import mcp

    async def _inner():
        try:
            result = await mcp.call_tool(tool_name, args)
            # call_tool did not raise — check the content for error indicators
            content_list, structured = result
            content_str = " ".join(item.text for item in content_list if hasattr(item, "text"))
            combined = content_str + str(structured)
            assert sentinel not in combined, "raw sentinel path leaked in result content"
            # FastMCP may surface the error in content text or as isError in structured
            has_error_marker = (
                "Invalid or inaccessible" in combined
                or structured.get("isError", False)
                or any(getattr(item, "isError", False) for item in content_list)
            )
            assert has_error_marker, f"no error marker found in result: {combined!r}"
        except Exception as exc:
            msg = str(exc)
            assert sentinel not in msg, f"raw sentinel path leaked in exception: {msg!r}"
            assert "Invalid or inaccessible" in msg, (
                f"safe error message absent from exception: {msg!r}"
            )

    asyncio.run(_inner())


def test_read_project_context_invalid_path_no_disclosure():
    """Invalid path to read_project_context: safe message, no path leak."""
    _call_path_tool_and_check_error(
        "read_project_context",
        {"path": _SENTINEL},
        _SENTINEL,
    )


def test_get_git_log_invalid_path_no_disclosure():
    """Invalid path to get_git_log: safe message, no path leak."""
    _call_path_tool_and_check_error(
        "get_git_log",
        {"path": _SENTINEL},
        _SENTINEL,
    )


def test_search_notes_invalid_path_no_disclosure():
    """Invalid path to search_notes: safe message, no path leak."""
    _call_path_tool_and_check_error(
        "search_notes",
        {"query": "anything", "path": _SENTINEL},
        _SENTINEL,
    )


# ---------------------------------------------------------------------------
# 11. Original local functions remain independently importable and callable
# ---------------------------------------------------------------------------


def test_original_read_project_context_unchanged(tmp_path):
    """The original read_project_context remains directly callable."""
    from src.tools.context_reader import read_project_context
    (tmp_path / "README.md").write_text("# Original\n")
    result = read_project_context(str(tmp_path))
    assert isinstance(result, str)
    assert "README" in result


def test_original_get_git_log_unchanged(tmp_path):
    """The original get_git_log remains directly callable."""
    from src.tools.context_reader import get_git_log
    result = get_git_log(str(tmp_path))
    assert isinstance(result, str)


def test_original_search_notes_unchanged(tmp_path):
    """The original search_notes remains directly callable."""
    from src.tools.note_searcher import search_notes
    (tmp_path / "notes.md").write_text("TODO: check this\n")
    result = search_notes("TODO", str(tmp_path))
    assert "TODO" in result


def test_original_create_plan_unchanged():
    """The original create_plan remains directly callable."""
    from src.tools.plan_tools import create_plan
    result = create_plan("Task one")
    assert "## Plan" in result
    assert "Task one" in result


def test_original_render_actions_unchanged():
    """The original render_actions remains directly callable."""
    from src.tools.plan_tools import render_actions
    result = render_actions("- Do something")
    assert "## Next Actions" in result
    assert "Do something" in result


# ---------------------------------------------------------------------------
# 12. Delegator exposes a callable entry point without running on import
# ---------------------------------------------------------------------------


def test_delegator_exposes_main_callable():
    """paios_lite.tools.mcp_server.main is callable without being invoked on import."""
    import paios_lite.tools.mcp_server as delegator
    assert callable(delegator.main)


def test_delegator_main_is_the_server_main():
    """The delegator's main reference is the same object as src.tools.mcp_server.main."""
    import paios_lite.tools.mcp_server as delegator
    from src.tools.mcp_server import main as server_main
    assert delegator.main is server_main
