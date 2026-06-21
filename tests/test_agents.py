"""Tests for src/agents/memory_agent.py.

Verifies agent wiring without making real LLM API calls.
ADK runner execution is mocked at the asyncio.run boundary so the test
suite runs with no API key and no network access.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

_SAMPLE_FILE = str(Path(__file__).parent.parent / "examples" / "sample_project_context.md")

# ---------------------------------------------------------------------------
# Config guard — must fire before any asyncio/ADK call
# ---------------------------------------------------------------------------


def test_memory_agent_raises_when_gemini_key_absent(monkeypatch):
    """EnvironmentError is raised before the LLM is called when the key is missing."""
    monkeypatch.setenv("LLM_MODEL", "gemini/gemini-2.0-flash-exp")
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)

    from src.agents import memory_agent

    with pytest.raises(EnvironmentError, match="GOOGLE_API_KEY"):
        memory_agent.run(_SAMPLE_FILE)


def test_memory_agent_raises_when_claude_key_absent(monkeypatch):
    """EnvironmentError is raised when Claude is selected but ANTHROPIC_API_KEY is missing."""
    monkeypatch.setenv("LLM_MODEL", "claude-3-5-haiku-20241022")
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    from src.agents import memory_agent

    with pytest.raises(EnvironmentError, match="ANTHROPIC_API_KEY"):
        memory_agent.run(_SAMPLE_FILE)


def test_memory_agent_config_called_before_llm(monkeypatch):
    """Config validation runs first; asyncio.run is never reached on failure."""
    monkeypatch.setenv("LLM_MODEL", "gemini/gemini-2.0-flash-exp")
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)

    call_order: list[str] = []

    from src import config
    original_validate = config.validate_config

    def recording_validate():
        call_order.append("validate")
        original_validate()

    with patch("src.agents.memory_agent.config.validate_config", side_effect=recording_validate):
        with patch("asyncio.run") as mock_run:
            from src.agents import memory_agent

            with pytest.raises(EnvironmentError):
                memory_agent.run(_SAMPLE_FILE)

            mock_run.assert_not_called()

    assert call_order == ["validate"]


# ---------------------------------------------------------------------------
# Happy path — mocked asyncio.run returns a canned snapshot
# ---------------------------------------------------------------------------

_CANNED_SNAPSHOT = (
    "## Project Identity\n"
    "Test project for PAIOS-Lite wiring verification.\n\n"
    "## Recent Activity\n"
    "No commits found.\n\n"
    "## Current State\n"
    "All complete.\n\n"
    "## Open Items\n"
    "No open items detected.\n\n"
    "## Key Files\n"
    "- sample_project_context.md — demo fixture\n"
)


def test_memory_agent_returns_snapshot_string(monkeypatch):
    """run() returns the text produced by the (mocked) ADK runner."""
    monkeypatch.setenv("LLM_MODEL", "ollama/llama3.2")
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    def _close_and_return(coro):
        coro.close()  # prevent "coroutine never awaited" RuntimeWarning
        return _CANNED_SNAPSHOT

    with patch("asyncio.run", side_effect=_close_and_return):
        from src.agents import memory_agent

        result = memory_agent.run(_SAMPLE_FILE)

    assert result == _CANNED_SNAPSHOT
    assert "## Project Identity" in result


def test_memory_agent_passes_path_to_async_runner(monkeypatch):
    """_run_async is awaited exactly once with _SAMPLE_FILE and its return value is surfaced."""
    monkeypatch.setenv("LLM_MODEL", "ollama/llama3.2")
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    mock_run_async = AsyncMock(return_value=_CANNED_SNAPSHOT)

    with patch("src.agents.memory_agent._run_async", mock_run_async):
        from src.agents import memory_agent

        result = memory_agent.run(_SAMPLE_FILE)

    mock_run_async.assert_awaited_once_with(_SAMPLE_FILE)
    assert result == _CANNED_SNAPSHOT


# ---------------------------------------------------------------------------
# Planner Agent — construction-only tests (no API key, no LLM call)
# ---------------------------------------------------------------------------


def test_planner_agent_build_agent_returns_llm_agent(monkeypatch):
    """build_agent() returns an ADK LlmAgent instance."""
    from google.adk.agents import LlmAgent
    with patch("src.agents.planner_agent.config.get_llm_model", return_value="ollama/llama3.2"):
        from src.agents import planner_agent
        agent = planner_agent.build_agent()
    assert isinstance(agent, LlmAgent)


def test_planner_agent_name(monkeypatch):
    """Agent name is exactly 'planner_agent'."""
    with patch("src.agents.planner_agent.config.get_llm_model", return_value="ollama/llama3.2"):
        from src.agents import planner_agent
        agent = planner_agent.build_agent()
    assert agent.name == "planner_agent"


def test_planner_agent_output_key_is_plan(monkeypatch):
    """output_key is exactly 'plan'."""
    with patch("src.agents.planner_agent.config.get_llm_model", return_value="ollama/llama3.2"):
        from src.agents import planner_agent
        agent = planner_agent.build_agent()
    assert agent.output_key == "plan"


def test_planner_agent_model_from_config(monkeypatch):
    """Agent model comes from the patched config.get_llm_model()."""
    with patch("src.agents.planner_agent.config.get_llm_model", return_value="ollama/llama3.2"):
        from src.agents import planner_agent
        agent = planner_agent.build_agent()
    assert agent.model == "ollama/llama3.2"


def test_planner_agent_config_called_once_per_build(monkeypatch):
    """config.get_llm_model() is called exactly once per build_agent() call."""
    mock_get_model = patch(
        "src.agents.planner_agent.config.get_llm_model", return_value="ollama/llama3.2"
    )
    with mock_get_model as mock:
        from src.agents import planner_agent
        planner_agent.build_agent()
    mock.assert_called_once()


def test_planner_agent_exactly_one_tool(monkeypatch):
    """Exactly one tool is registered on the Planner Agent."""
    with patch("src.agents.planner_agent.config.get_llm_model", return_value="ollama/llama3.2"):
        from src.agents import planner_agent
        agent = planner_agent.build_agent()
    assert len(agent.tools) == 1


def test_planner_agent_tool_is_create_plan(monkeypatch):
    """The registered tool is create_plan (wrapper-safe check)."""
    from src.tools.plan_tools import create_plan
    with patch("src.agents.planner_agent.config.get_llm_model", return_value="ollama/llama3.2"):
        from src.agents import planner_agent
        agent = planner_agent.build_agent()
    tool = agent.tools[0]
    tool_function = getattr(tool, "func", tool)
    assert tool_function is create_plan


def test_planner_agent_instruction_contains_memory_snapshot_placeholder(monkeypatch):
    """Instruction contains the literal {memory_snapshot} placeholder."""
    with patch("src.agents.planner_agent.config.get_llm_model", return_value="ollama/llama3.2"):
        from src.agents import planner_agent
        agent = planner_agent.build_agent()
    assert "{memory_snapshot}" in agent.instruction


def test_planner_agent_build_agent_is_synchronous(monkeypatch):
    """build_agent() returns synchronously and is not a coroutine."""
    import inspect
    with patch("src.agents.planner_agent.config.get_llm_model", return_value="ollama/llama3.2"):
        from src.agents import planner_agent
        result = planner_agent.build_agent()
    assert not inspect.iscoroutine(result)


def test_planner_agent_module_exposes_no_runner_or_event_loop():
    """Module must not own Runner, InMemorySessionService, or asyncio."""
    import src.agents.planner_agent as pa
    assert not hasattr(pa, "Runner")
    assert not hasattr(pa, "InMemorySessionService")
    assert not hasattr(pa, "asyncio")
