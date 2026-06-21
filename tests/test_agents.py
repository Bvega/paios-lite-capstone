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
