"""Tests for src/agents — construction-only, no API key required.

All tests verify agent wiring without making real LLM or network calls.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest

# ---------------------------------------------------------------------------
# Memory Agent — construction-only tests (no API key, no LLM call)
# ---------------------------------------------------------------------------


def test_memory_agent_build_agent_returns_llm_agent():
    """build_agent() returns an ADK LlmAgent instance."""
    from google.adk.agents import LlmAgent
    with patch("src.agents.memory_agent.config.get_llm_model", return_value="ollama/llama3.2"):
        from src.agents import memory_agent
        agent = memory_agent.build_agent()
    assert isinstance(agent, LlmAgent)


def test_memory_agent_name():
    """Agent name is exactly 'memory_agent'."""
    with patch("src.agents.memory_agent.config.get_llm_model", return_value="ollama/llama3.2"):
        from src.agents import memory_agent
        agent = memory_agent.build_agent()
    assert agent.name == "memory_agent"


def test_memory_agent_output_key_is_memory_snapshot():
    """output_key is exactly 'memory_snapshot'."""
    with patch("src.agents.memory_agent.config.get_llm_model", return_value="ollama/llama3.2"):
        from src.agents import memory_agent
        agent = memory_agent.build_agent()
    assert agent.output_key == "memory_snapshot"


def test_memory_agent_model_from_config():
    """Agent model comes from the patched config.get_llm_model()."""
    with patch("src.agents.memory_agent.config.get_llm_model", return_value="ollama/llama3.2"):
        from src.agents import memory_agent
        agent = memory_agent.build_agent()
    assert agent.model == "ollama/llama3.2"


def test_memory_agent_config_called_once_per_build():
    """config.get_llm_model() is called exactly once per build_agent() call."""
    mock_get_model = patch(
        "src.agents.memory_agent.config.get_llm_model", return_value="ollama/llama3.2"
    )
    with mock_get_model as mock:
        from src.agents import memory_agent
        memory_agent.build_agent()
    mock.assert_called_once()


def test_memory_agent_exactly_two_tools():
    """Exactly two tools are registered on the Memory Agent."""
    with patch("src.agents.memory_agent.config.get_llm_model", return_value="ollama/llama3.2"):
        from src.agents import memory_agent
        agent = memory_agent.build_agent()
    assert len(agent.tools) == 2


def test_memory_agent_tool_0_is_read_project_context():
    """First registered tool is read_project_context (wrapper-safe check)."""
    from src.tools.context_reader import read_project_context
    with patch("src.agents.memory_agent.config.get_llm_model", return_value="ollama/llama3.2"):
        from src.agents import memory_agent
        agent = memory_agent.build_agent()
    tool = agent.tools[0]
    assert getattr(tool, "func", tool) is read_project_context


def test_memory_agent_tool_1_is_get_git_log():
    """Second registered tool is get_git_log (wrapper-safe check)."""
    from src.tools.context_reader import get_git_log
    with patch("src.agents.memory_agent.config.get_llm_model", return_value="ollama/llama3.2"):
        from src.agents import memory_agent
        agent = memory_agent.build_agent()
    tool = agent.tools[1]
    assert getattr(tool, "func", tool) is get_git_log


def test_memory_agent_instruction_contains_project_path_placeholder():
    """Instruction contains the {project_path} session-state placeholder."""
    with patch("src.agents.memory_agent.config.get_llm_model", return_value="ollama/llama3.2"):
        from src.agents import memory_agent
        agent = memory_agent.build_agent()
    assert "{project_path}" in agent.instruction


def test_memory_agent_instruction_does_not_contain_downstream_placeholders():
    """Instruction must not depend on {plan}, {research_notes}, or {next_actions}."""
    with patch("src.agents.memory_agent.config.get_llm_model", return_value="ollama/llama3.2"):
        from src.agents import memory_agent
        agent = memory_agent.build_agent()
    assert "{plan}" not in agent.instruction
    assert "{research_notes}" not in agent.instruction
    assert "{next_actions}" not in agent.instruction


def test_memory_agent_build_agent_is_synchronous():
    """build_agent() returns synchronously and is not a coroutine."""
    import inspect
    with patch("src.agents.memory_agent.config.get_llm_model", return_value="ollama/llama3.2"):
        from src.agents import memory_agent
        result = memory_agent.build_agent()
    assert not inspect.iscoroutine(result)


def test_memory_agent_module_exposes_no_runner_or_event_loop():
    """Module must not expose run, _run_async, Runner, InMemorySessionService, or asyncio."""
    import src.agents.memory_agent as ma
    assert not hasattr(ma, "run")
    assert not hasattr(ma, "_run_async")
    assert not hasattr(ma, "Runner")
    assert not hasattr(ma, "InMemorySessionService")
    assert not hasattr(ma, "asyncio")
    assert not hasattr(ma, "run_async")
    assert not hasattr(ma, "run_until_complete")


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


# ---------------------------------------------------------------------------
# Research Agent — construction-only tests (no API key, no LLM call)
# ---------------------------------------------------------------------------


def test_research_agent_build_agent_returns_llm_agent():
    """build_agent() returns an ADK LlmAgent instance."""
    from google.adk.agents import LlmAgent
    with patch("src.agents.research_agent.config.get_llm_model", return_value="ollama/llama3.2"):
        from src.agents import research_agent
        agent = research_agent.build_agent()
    assert isinstance(agent, LlmAgent)


def test_research_agent_name():
    """Agent name is exactly 'research_agent'."""
    with patch("src.agents.research_agent.config.get_llm_model", return_value="ollama/llama3.2"):
        from src.agents import research_agent
        agent = research_agent.build_agent()
    assert agent.name == "research_agent"


def test_research_agent_output_key_is_research_notes():
    """output_key is exactly 'research_notes'."""
    with patch("src.agents.research_agent.config.get_llm_model", return_value="ollama/llama3.2"):
        from src.agents import research_agent
        agent = research_agent.build_agent()
    assert agent.output_key == "research_notes"


def test_research_agent_model_from_config():
    """Agent model comes from the patched config.get_llm_model()."""
    with patch("src.agents.research_agent.config.get_llm_model", return_value="ollama/llama3.2"):
        from src.agents import research_agent
        agent = research_agent.build_agent()
    assert agent.model == "ollama/llama3.2"


def test_research_agent_config_called_once_per_build():
    """config.get_llm_model() is called exactly once per build_agent() call."""
    mock_get_model = patch(
        "src.agents.research_agent.config.get_llm_model", return_value="ollama/llama3.2"
    )
    with mock_get_model as mock:
        from src.agents import research_agent
        research_agent.build_agent()
    mock.assert_called_once()


def test_research_agent_exactly_one_tool():
    """Exactly one tool is registered on the Research Agent."""
    with patch("src.agents.research_agent.config.get_llm_model", return_value="ollama/llama3.2"):
        from src.agents import research_agent
        agent = research_agent.build_agent()
    assert len(agent.tools) == 1


def test_research_agent_tool_is_search_notes():
    """The registered tool is search_notes (wrapper-safe check)."""
    from src.tools.note_searcher import search_notes
    with patch("src.agents.research_agent.config.get_llm_model", return_value="ollama/llama3.2"):
        from src.agents import research_agent
        agent = research_agent.build_agent()
    tool = agent.tools[0]
    tool_function = getattr(tool, "func", tool)
    assert tool_function is search_notes


def test_research_agent_instruction_contains_memory_snapshot_placeholder():
    """Instruction contains the {memory_snapshot} state placeholder."""
    with patch("src.agents.research_agent.config.get_llm_model", return_value="ollama/llama3.2"):
        from src.agents import research_agent
        agent = research_agent.build_agent()
    assert "{memory_snapshot}" in agent.instruction


def test_research_agent_instruction_contains_plan_placeholder():
    """Instruction contains the {plan} state placeholder."""
    with patch("src.agents.research_agent.config.get_llm_model", return_value="ollama/llama3.2"):
        from src.agents import research_agent
        agent = research_agent.build_agent()
    assert "{plan}" in agent.instruction


def test_research_agent_instruction_contains_project_path_placeholder():
    """Instruction contains the {project_path} state placeholder."""
    with patch("src.agents.research_agent.config.get_llm_model", return_value="ollama/llama3.2"):
        from src.agents import research_agent
        agent = research_agent.build_agent()
    assert "{project_path}" in agent.instruction


def test_research_agent_build_agent_is_synchronous():
    """build_agent() returns synchronously and is not a coroutine."""
    import inspect
    with patch("src.agents.research_agent.config.get_llm_model", return_value="ollama/llama3.2"):
        from src.agents import research_agent
        result = research_agent.build_agent()
    assert not inspect.iscoroutine(result)


def test_research_agent_module_exposes_no_runner_or_event_loop():
    """Module must not own Runner, InMemorySessionService, or asyncio."""
    import src.agents.research_agent as ra
    assert not hasattr(ra, "Runner")
    assert not hasattr(ra, "InMemorySessionService")
    assert not hasattr(ra, "asyncio")


# ---------------------------------------------------------------------------
# Executor Agent — construction-only tests (no API key, no LLM call)
# ---------------------------------------------------------------------------


def test_executor_agent_build_agent_returns_llm_agent():
    """build_agent() returns an ADK LlmAgent instance."""
    from google.adk.agents import LlmAgent
    with patch("src.agents.executor_agent.config.get_llm_model", return_value="ollama/llama3.2"):
        from src.agents import executor_agent
        agent = executor_agent.build_agent()
    assert isinstance(agent, LlmAgent)


def test_executor_agent_name():
    """Agent name is exactly 'executor_agent'."""
    with patch("src.agents.executor_agent.config.get_llm_model", return_value="ollama/llama3.2"):
        from src.agents import executor_agent
        agent = executor_agent.build_agent()
    assert agent.name == "executor_agent"


def test_executor_agent_output_key_is_next_actions():
    """output_key is exactly 'next_actions'."""
    with patch("src.agents.executor_agent.config.get_llm_model", return_value="ollama/llama3.2"):
        from src.agents import executor_agent
        agent = executor_agent.build_agent()
    assert agent.output_key == "next_actions"


def test_executor_agent_model_from_config():
    """Agent model comes from the patched config.get_llm_model()."""
    with patch("src.agents.executor_agent.config.get_llm_model", return_value="ollama/llama3.2"):
        from src.agents import executor_agent
        agent = executor_agent.build_agent()
    assert agent.model == "ollama/llama3.2"


def test_executor_agent_config_called_once_per_build():
    """config.get_llm_model() is called exactly once per build_agent() call."""
    mock_get_model = patch(
        "src.agents.executor_agent.config.get_llm_model", return_value="ollama/llama3.2"
    )
    with mock_get_model as mock:
        from src.agents import executor_agent
        executor_agent.build_agent()
    mock.assert_called_once()


def test_executor_agent_exactly_one_tool():
    """Exactly one tool is registered on the Executor Agent."""
    with patch("src.agents.executor_agent.config.get_llm_model", return_value="ollama/llama3.2"):
        from src.agents import executor_agent
        agent = executor_agent.build_agent()
    assert len(agent.tools) == 1


def test_executor_agent_tool_is_render_actions():
    """The registered tool is render_actions (wrapper-safe check)."""
    from src.tools.plan_tools import render_actions
    with patch("src.agents.executor_agent.config.get_llm_model", return_value="ollama/llama3.2"):
        from src.agents import executor_agent
        agent = executor_agent.build_agent()
    tool = agent.tools[0]
    tool_function = getattr(tool, "func", tool)
    assert tool_function is render_actions


def test_executor_agent_instruction_contains_plan_placeholder():
    """Instruction contains the {plan} state placeholder."""
    with patch("src.agents.executor_agent.config.get_llm_model", return_value="ollama/llama3.2"):
        from src.agents import executor_agent
        agent = executor_agent.build_agent()
    assert "{plan}" in agent.instruction


def test_executor_agent_instruction_contains_research_notes_placeholder():
    """Instruction contains the {research_notes} state placeholder."""
    with patch("src.agents.executor_agent.config.get_llm_model", return_value="ollama/llama3.2"):
        from src.agents import executor_agent
        agent = executor_agent.build_agent()
    assert "{research_notes}" in agent.instruction


def test_executor_agent_instruction_does_not_contain_memory_snapshot():
    """Instruction must not contain the {memory_snapshot} placeholder."""
    with patch("src.agents.executor_agent.config.get_llm_model", return_value="ollama/llama3.2"):
        from src.agents import executor_agent
        agent = executor_agent.build_agent()
    assert "{memory_snapshot}" not in agent.instruction


def test_executor_agent_build_agent_is_synchronous():
    """build_agent() returns synchronously and is not a coroutine."""
    import inspect
    with patch("src.agents.executor_agent.config.get_llm_model", return_value="ollama/llama3.2"):
        from src.agents import executor_agent
        result = executor_agent.build_agent()
    assert not inspect.iscoroutine(result)


def test_executor_agent_module_exposes_no_runner_or_event_loop():
    """Module must not own Runner, InMemorySessionService, or asyncio."""
    import src.agents.executor_agent as ea
    assert not hasattr(ea, "Runner")
    assert not hasattr(ea, "InMemorySessionService")
    assert not hasattr(ea, "asyncio")
