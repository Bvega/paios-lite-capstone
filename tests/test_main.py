"""Tests for src/main.py — _run_pipeline() orchestration and retry logic.

All tests make zero API or network calls and do not instantiate
real provider-backed agents.
"""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from google.genai import errors as genai_errors


_CONTEXT_PATH = "/fake/project/path"

_CANNED_STATE = {
    "memory_snapshot": "## Project Identity\nTest project.",
    "plan": "## Plan\n\nTask one.\n\n1 line(s) of context.\n",
    "research_notes": "## Research Notes\n\n0 task(s) researched.\n",
    "next_actions": "## Next Actions\n\n  1. Do something.\n\n1 action(s).\n",
}


async def _empty_async_gen():
    """Async generator that yields no events — simulates a completed pipeline run."""
    return
    yield  # makes this an async generator, not a coroutine


@pytest.fixture
def pipeline_run():
    """
    Patch all ADK infrastructure, execute _run_pipeline() once, and expose
    every mock and the final result for individual test assertions.
    """
    mock_mem_agent  = MagicMock(name="memory_agent_instance")
    mock_plan_agent = MagicMock(name="planner_agent_instance")
    mock_res_agent  = MagicMock(name="research_agent_instance")
    mock_exec_agent = MagicMock(name="executor_agent_instance")

    mock_pipeline = MagicMock(name="sequential_agent_instance")

    mock_session = MagicMock()
    mock_session.id = "sess-abc123"

    mock_final_session = MagicMock()
    mock_final_session.state = dict(_CANNED_STATE)

    mock_session_service = MagicMock()
    mock_session_service.create_session = AsyncMock(return_value=mock_session)
    mock_session_service.get_session    = AsyncMock(return_value=mock_final_session)

    mock_runner = MagicMock()
    mock_runner.run_async.return_value = _empty_async_gen()

    with (
        patch("src.main.memory_agent.build_agent",   return_value=mock_mem_agent)  as p_mem,
        patch("src.main.planner_agent.build_agent",  return_value=mock_plan_agent) as p_plan,
        patch("src.main.research_agent.build_agent", return_value=mock_res_agent)  as p_res,
        patch("src.main.executor_agent.build_agent", return_value=mock_exec_agent) as p_exec,
        patch("src.main.SequentialAgent",            return_value=mock_pipeline)   as p_seq,
        patch("src.main.InMemorySessionService",     return_value=mock_session_service) as p_svc,
        patch("src.main.Runner",                     return_value=mock_runner)     as p_runner,
    ):
        from src.main import _run_pipeline
        result = asyncio.run(_run_pipeline(_CONTEXT_PATH))

        yield {
            "result":               result,
            "mock_mem_agent":       mock_mem_agent,
            "mock_plan_agent":      mock_plan_agent,
            "mock_res_agent":       mock_res_agent,
            "mock_exec_agent":      mock_exec_agent,
            "mock_pipeline":        mock_pipeline,
            "mock_session":         mock_session,
            "mock_final_session":   mock_final_session,
            "mock_session_service": mock_session_service,
            "mock_runner":          mock_runner,
            "p_mem":    p_mem,
            "p_plan":   p_plan,
            "p_res":    p_res,
            "p_exec":   p_exec,
            "p_seq":    p_seq,
            "p_svc":    p_svc,
            "p_runner": p_runner,
        }


# ---------------------------------------------------------------------------
# 1. Every agent builder called exactly once
# ---------------------------------------------------------------------------


def test_pipeline_builds_all_four_agents(pipeline_run):
    """Each build_agent() factory is called exactly once."""
    pipeline_run["p_mem"].assert_called_once()
    pipeline_run["p_plan"].assert_called_once()
    pipeline_run["p_res"].assert_called_once()
    pipeline_run["p_exec"].assert_called_once()


# ---------------------------------------------------------------------------
# 2 + 3. SequentialAgent construction: name and agent order
# ---------------------------------------------------------------------------


def test_sequential_agent_receives_correct_name(pipeline_run):
    """SequentialAgent is constructed with name='paios_lite_pipeline'."""
    kwargs = pipeline_run["p_seq"].call_args.kwargs
    assert kwargs["name"] == "paios_lite_pipeline"


def test_sequential_agent_receives_agents_in_order(pipeline_run):
    """SequentialAgent sub_agents list is memory→planner→research→executor."""
    kwargs = pipeline_run["p_seq"].call_args.kwargs
    assert kwargs["sub_agents"] == [
        pipeline_run["mock_mem_agent"],
        pipeline_run["mock_plan_agent"],
        pipeline_run["mock_res_agent"],
        pipeline_run["mock_exec_agent"],
    ]


# ---------------------------------------------------------------------------
# 4. Session initial state
# ---------------------------------------------------------------------------


def test_session_created_with_project_path_in_state(pipeline_run):
    """Session is created with state={'project_path': context_path} exactly."""
    pipeline_run["mock_session_service"].create_session.assert_awaited_once()
    kwargs = pipeline_run["mock_session_service"].create_session.call_args.kwargs
    assert kwargs["state"] == {"project_path": _CONTEXT_PATH}


# ---------------------------------------------------------------------------
# 5 + 6. Single Runner wired to pipeline with correct app_name and session_service
# ---------------------------------------------------------------------------


def test_one_runner_created_for_pipeline(pipeline_run):
    """Exactly one Runner is created, wired to the pipeline with correct args."""
    pipeline_run["p_runner"].assert_called_once_with(
        agent=pipeline_run["mock_pipeline"],
        app_name="paios_lite",
        session_service=pipeline_run["mock_session_service"],
    )


# ---------------------------------------------------------------------------
# 7. Runner.run_async arguments
# ---------------------------------------------------------------------------


def test_runner_run_async_called_exactly_once(pipeline_run):
    """runner.run_async() is called exactly once."""
    pipeline_run["mock_runner"].run_async.assert_called_once()


def test_runner_run_async_called_with_correct_user_id(pipeline_run):
    """runner.run_async() receives user_id='cli_user'."""
    kwargs = pipeline_run["mock_runner"].run_async.call_args.kwargs
    assert kwargs["user_id"] == "cli_user"


def test_runner_run_async_called_with_correct_session_id(pipeline_run):
    """runner.run_async() receives the session id returned by create_session."""
    kwargs = pipeline_run["mock_runner"].run_async.call_args.kwargs
    assert kwargs["session_id"] == pipeline_run["mock_session"].id


def test_runner_run_async_trigger_message_is_user_role_content(pipeline_run):
    """runner.run_async() new_message is a user-role Content with one non-empty part."""
    from google.genai import types as genai_types
    kwargs = pipeline_run["mock_runner"].run_async.call_args.kwargs
    msg = kwargs["new_message"]
    assert isinstance(msg, genai_types.Content)
    assert msg.role == "user"
    assert len(msg.parts) == 1
    assert msg.parts[0].text


def test_runner_run_async_trigger_message_text_matches_constant(pipeline_run):
    """new_message text exactly matches src.main._TRIGGER_MESSAGE."""
    from src.main import _TRIGGER_MESSAGE
    kwargs = pipeline_run["mock_runner"].run_async.call_args.kwargs
    assert kwargs["new_message"].parts[0].text == _TRIGGER_MESSAGE


# ---------------------------------------------------------------------------
# 8. Event stream consumed to completion
# ---------------------------------------------------------------------------


def test_event_stream_consumed_to_completion():
    """The async for loop iterates all events; the generator is fully exhausted."""
    exhausted_flag = []

    async def _two_event_gen():
        yield MagicMock()
        yield MagicMock()
        exhausted_flag.append(True)

    mock_session = MagicMock()
    mock_session.id = "sess-count"
    mock_final = MagicMock()
    mock_final.state = {}

    mock_svc = MagicMock()
    mock_svc.create_session = AsyncMock(return_value=mock_session)
    mock_svc.get_session    = AsyncMock(return_value=mock_final)

    mock_runner = MagicMock()
    mock_runner.run_async.return_value = _two_event_gen()

    with (
        patch("src.main.memory_agent.build_agent",   return_value=MagicMock()),
        patch("src.main.planner_agent.build_agent",  return_value=MagicMock()),
        patch("src.main.research_agent.build_agent", return_value=MagicMock()),
        patch("src.main.executor_agent.build_agent", return_value=MagicMock()),
        patch("src.main.SequentialAgent",            return_value=MagicMock()),
        patch("src.main.InMemorySessionService",     return_value=mock_svc),
        patch("src.main.Runner",                     return_value=mock_runner),
    ):
        from src.main import _run_pipeline
        asyncio.run(_run_pipeline(_CONTEXT_PATH))

    assert exhausted_flag == [True], "Event generator was not fully consumed"


# ---------------------------------------------------------------------------
# 9. Explicit order log: stream exhausted before get_session
# ---------------------------------------------------------------------------


def test_event_stream_exhausted_before_get_session():
    """Generator completion is logged before get_session() is called."""
    order_log: list[str] = []

    async def _tracking_gen():
        yield MagicMock()
        order_log.append("generator_exhausted")

    mock_session = MagicMock()
    mock_session.id = "sess-order"

    async def _tracking_get_session(**kwargs):
        order_log.append("get_session_called")
        final = MagicMock()
        final.state = {}
        return final

    mock_svc = MagicMock()
    mock_svc.create_session = AsyncMock(return_value=mock_session)
    mock_svc.get_session    = AsyncMock(side_effect=_tracking_get_session)

    mock_runner = MagicMock()
    mock_runner.run_async.return_value = _tracking_gen()

    with (
        patch("src.main.memory_agent.build_agent",   return_value=MagicMock()),
        patch("src.main.planner_agent.build_agent",  return_value=MagicMock()),
        patch("src.main.research_agent.build_agent", return_value=MagicMock()),
        patch("src.main.executor_agent.build_agent", return_value=MagicMock()),
        patch("src.main.SequentialAgent",            return_value=MagicMock()),
        patch("src.main.InMemorySessionService",     return_value=mock_svc),
        patch("src.main.Runner",                     return_value=mock_runner),
    ):
        from src.main import _run_pipeline
        asyncio.run(_run_pipeline(_CONTEXT_PATH))

    assert order_log == ["generator_exhausted", "get_session_called"]


# ---------------------------------------------------------------------------
# 10. Final session read with correct identifiers
# ---------------------------------------------------------------------------


def test_final_session_get_session_called_once(pipeline_run):
    """get_session() is awaited exactly once after run_async completes."""
    pipeline_run["mock_session_service"].get_session.assert_awaited_once()


def test_final_session_read_with_correct_identifiers(pipeline_run):
    """get_session() is called with correct app_name, user_id, and session_id."""
    kwargs = pipeline_run["mock_session_service"].get_session.call_args.kwargs
    assert kwargs["app_name"] == "paios_lite"
    assert kwargs["user_id"] == "cli_user"
    assert kwargs["session_id"] == pipeline_run["mock_session"].id


# ---------------------------------------------------------------------------
# 11. Returns all four state values
# ---------------------------------------------------------------------------


def test_run_pipeline_returns_memory_snapshot(pipeline_run):
    """_run_pipeline() returns the memory_snapshot from session state."""
    assert pipeline_run["result"]["memory_snapshot"] == _CANNED_STATE["memory_snapshot"]


def test_run_pipeline_returns_plan(pipeline_run):
    """_run_pipeline() returns the plan from session state."""
    assert pipeline_run["result"]["plan"] == _CANNED_STATE["plan"]


def test_run_pipeline_returns_research_notes(pipeline_run):
    """_run_pipeline() returns the research_notes from session state."""
    assert pipeline_run["result"]["research_notes"] == _CANNED_STATE["research_notes"]


def test_run_pipeline_returns_next_actions(pipeline_run):
    """_run_pipeline() returns the next_actions from session state."""
    assert pipeline_run["result"]["next_actions"] == _CANNED_STATE["next_actions"]


# ---------------------------------------------------------------------------
# 12. Missing state keys use the four exact fallback strings
# ---------------------------------------------------------------------------


def test_run_pipeline_missing_keys_return_fallback_strings():
    """All four keys return their approved fallback strings when absent from state."""
    mock_session = MagicMock()
    mock_session.id = "sess-empty"
    mock_final = MagicMock()
    mock_final.state = {}  # no output keys written by agents

    mock_svc = MagicMock()
    mock_svc.create_session = AsyncMock(return_value=mock_session)
    mock_svc.get_session    = AsyncMock(return_value=mock_final)

    mock_runner = MagicMock()
    mock_runner.run_async.return_value = _empty_async_gen()

    with (
        patch("src.main.memory_agent.build_agent",   return_value=MagicMock()),
        patch("src.main.planner_agent.build_agent",  return_value=MagicMock()),
        patch("src.main.research_agent.build_agent", return_value=MagicMock()),
        patch("src.main.executor_agent.build_agent", return_value=MagicMock()),
        patch("src.main.SequentialAgent",            return_value=MagicMock()),
        patch("src.main.InMemorySessionService",     return_value=mock_svc),
        patch("src.main.Runner",                     return_value=mock_runner),
    ):
        from src.main import _run_pipeline
        result = asyncio.run(_run_pipeline(_CONTEXT_PATH))

    assert result["memory_snapshot"]  == "(Memory Agent produced no output.)"
    assert result["plan"]             == "(Planner Agent produced no output.)"
    assert result["research_notes"]   == "(Research Agent produced no output.)"
    assert result["next_actions"]     == "(Executor Agent produced no output.)"


# ---------------------------------------------------------------------------
# 13. get_session() returning None raises RuntimeError
# ---------------------------------------------------------------------------


def test_run_pipeline_raises_when_get_session_returns_none():
    """RuntimeError is raised if get_session() returns None after pipeline execution."""
    mock_session = MagicMock()
    mock_session.id = "sess-none"

    mock_svc = MagicMock()
    mock_svc.create_session = AsyncMock(return_value=mock_session)
    mock_svc.get_session    = AsyncMock(return_value=None)

    mock_runner = MagicMock()
    mock_runner.run_async.return_value = _empty_async_gen()

    with (
        patch("src.main.memory_agent.build_agent",   return_value=MagicMock()),
        patch("src.main.planner_agent.build_agent",  return_value=MagicMock()),
        patch("src.main.research_agent.build_agent", return_value=MagicMock()),
        patch("src.main.executor_agent.build_agent", return_value=MagicMock()),
        patch("src.main.SequentialAgent",            return_value=MagicMock()),
        patch("src.main.InMemorySessionService",     return_value=mock_svc),
        patch("src.main.Runner",                     return_value=mock_runner),
    ):
        from src.main import _run_pipeline
        with pytest.raises(RuntimeError, match="Pipeline session could not be reloaded"):
            asyncio.run(_run_pipeline(_CONTEXT_PATH))


# ---------------------------------------------------------------------------
# Helpers for Phase 2G event-based progress tests
# ---------------------------------------------------------------------------


def _make_final_event(author: str) -> MagicMock:
    """Return a mock event whose is_final_response() returns True."""
    event = MagicMock()
    event.author = author
    event.is_final_response = MagicMock(return_value=True)
    return event


def _make_non_final_event(author: str) -> MagicMock:
    """Return a mock event whose is_final_response() returns False."""
    event = MagicMock()
    event.author = author
    event.is_final_response = MagicMock(return_value=False)
    return event


def _run_pipeline_with_events(*events) -> list:
    """
    Run _run_pipeline with a controlled set of mock events.
    Patches console so no real output is produced.
    Returns the console.print call_args_list for assertion.
    """
    async def _gen():
        for e in events:
            yield e

    mock_session = MagicMock()
    mock_session.id = "sess-progress"
    mock_final = MagicMock()
    mock_final.state = {}

    mock_svc = MagicMock()
    mock_svc.create_session = AsyncMock(return_value=mock_session)
    mock_svc.get_session    = AsyncMock(return_value=mock_final)

    mock_runner = MagicMock()
    mock_runner.run_async.return_value = _gen()

    mock_console = MagicMock()

    with (
        patch("src.main.memory_agent.build_agent",   return_value=MagicMock()),
        patch("src.main.planner_agent.build_agent",  return_value=MagicMock()),
        patch("src.main.research_agent.build_agent", return_value=MagicMock()),
        patch("src.main.executor_agent.build_agent", return_value=MagicMock()),
        patch("src.main.SequentialAgent",            return_value=MagicMock()),
        patch("src.main.InMemorySessionService",     return_value=mock_svc),
        patch("src.main.Runner",                     return_value=mock_runner),
        patch("src.main.console",                    mock_console),
    ):
        from src.main import _run_pipeline
        asyncio.run(_run_pipeline(_CONTEXT_PATH))

    return mock_console.print.call_args_list


def _status_calls(call_args_list: list) -> list[str]:
    """Return the string args from console.print calls that contain the ✓ marker."""
    return [
        call.args[0]
        for call in call_args_list
        if call.args and isinstance(call.args[0], str) and "✓" in call.args[0]
    ]


# ---------------------------------------------------------------------------
# 14. Per-agent completion status: final-response events print exactly once
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("author,label", [
    ("memory_agent",   "Memory Agent"),
    ("planner_agent",  "Planner Agent"),
    ("research_agent", "Research Agent"),
    ("executor_agent", "Executor Agent"),
])
def test_final_event_prints_agent_completion_status(author, label):
    """A final-response event from a recognized author prints exactly one status line."""
    calls = _run_pipeline_with_events(_make_final_event(author))
    statuses = _status_calls(calls)
    assert len(statuses) == 1
    assert label in statuses[0]


# ---------------------------------------------------------------------------
# 15. Duplicate final-response events from the same author: no duplicates
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("author", [
    "memory_agent", "planner_agent", "research_agent", "executor_agent",
])
def test_duplicate_final_events_print_status_only_once(author):
    """Two final-response events from the same author produce exactly one status line."""
    calls = _run_pipeline_with_events(
        _make_final_event(author),
        _make_final_event(author),
    )
    statuses = _status_calls(calls)
    assert len(statuses) == 1


# ---------------------------------------------------------------------------
# 16. Non-final events do not trigger completion status
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("author", [
    "memory_agent", "planner_agent", "research_agent", "executor_agent",
])
def test_non_final_event_does_not_print_completion_status(author):
    """A non-final event from a recognized author does not print a status line."""
    calls = _run_pipeline_with_events(_make_non_final_event(author))
    statuses = _status_calls(calls)
    assert statuses == []


# ---------------------------------------------------------------------------
# 17. Unknown and authorless events are silently ignored
# ---------------------------------------------------------------------------


def test_unknown_author_does_not_print_completion_status():
    """A final-response event from an unrecognized author produces no status line."""
    calls = _run_pipeline_with_events(_make_final_event("some_other_agent"))
    statuses = _status_calls(calls)
    assert statuses == []


def test_event_without_author_does_not_print_completion_status():
    """An event with no author attribute produces no status line."""
    event = MagicMock(spec=[])  # spec=[] → accessing .author raises AttributeError
    calls = _run_pipeline_with_events(event)
    statuses = _status_calls(calls)
    assert statuses == []


# ---------------------------------------------------------------------------
# 18. main() output: continuity-brief panel and section title order
# ---------------------------------------------------------------------------


@pytest.fixture
def main_output():
    """
    Run main() with fully mocked infrastructure; capture all console.print calls.
    _run_pipeline is replaced with a fast coroutine returning _CANNED_STATE.
    No API key, no network call, no filesystem access.
    """
    mock_console = MagicMock()

    async def _fake_pipeline(path: str, *, seen_authors=None) -> dict:
        return dict(_CANNED_STATE)

    with (
        patch("src.main._run_pipeline", side_effect=_fake_pipeline),
        patch("src.main.config.validate_config"),
        patch("src.main.Path") as mock_path_cls,
        patch("src.main.console", mock_console),
    ):
        mock_path_cls.return_value.exists.return_value = True
        from src.main import main
        main(["--context", _CONTEXT_PATH])

    return mock_console.print.call_args_list


def test_main_prints_continuity_brief_panel(main_output):
    """main() prints exactly one Panel for the continuity brief."""
    from rich.panel import Panel
    panels = [
        c.args[0] for c in main_output
        if c.args and isinstance(c.args[0], Panel)
    ]
    assert len(panels) == 1


def test_main_panel_contains_continuity_brief_text(main_output):
    """The continuity-brief Panel's renderable contains the expected title text."""
    from rich.panel import Panel
    from rich.text import Text
    panels = [
        c.args[0] for c in main_output
        if c.args and isinstance(c.args[0], Panel)
    ]
    assert len(panels) == 1
    renderable = panels[0].renderable
    panel_text = renderable.plain if isinstance(renderable, Text) else str(renderable)
    assert "PAIOS-Lite Continuity Brief" in panel_text


def test_main_section_titles_in_correct_order(main_output):
    """Section Rule titles appear in order: Current State, Plan, Research Notes, Next Actions."""
    from rich.rule import Rule
    rule_titles = [
        c.args[0].title
        for c in main_output
        if c.args and isinstance(c.args[0], Rule) and getattr(c.args[0], "title", "")
    ]
    expected = ["Current State", "Plan", "Research Notes", "Next Actions"]
    positions = []
    for exp in expected:
        pos = next((i for i, t in enumerate(rule_titles) if exp in t), None)
        assert pos is not None, f"Section title '{exp}' not found in Rule titles: {rule_titles}"
        positions.append(pos)
    assert positions == sorted(positions), (
        f"Section titles not in expected order. Positions: {positions}, titles: {rule_titles}"
    )


# ===========================================================================
# Phase 3B — Retry/Backoff Tests
# ===========================================================================

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _api_err(code: int) -> genai_errors.APIError:
    """Construct a real APIError with the given HTTP status code."""
    return genai_errors.APIError(code, {})


def _client_err(code: int) -> genai_errors.ClientError:
    return genai_errors.ClientError(code, {})


def _server_err(code: int) -> genai_errors.ServerError:
    return genai_errors.ServerError(code, {})


def _run_retry(pipeline_side_effect, *, jitter: float = 0.0):
    """
    Exercise _run_pipeline_with_retry with a mocked _run_pipeline.

    Returns (result, sleep_delays, call_count) on success, or propagates the
    raised exception so the caller can use pytest.raises.
    """
    sleep_delays: list[float] = []

    async def _no_sleep(delay: float) -> None:
        sleep_delays.append(delay)

    pipeline_mock = AsyncMock(side_effect=pipeline_side_effect)

    from src.main import _run_pipeline_with_retry

    with patch("src.main._run_pipeline", pipeline_mock):
        result = asyncio.run(
            _run_pipeline_with_retry(
                _CONTEXT_PATH,
                sleep_func=_no_sleep,
                jitter_func=lambda _a, _b: jitter,
            )
        )

    return result, sleep_delays, pipeline_mock


# ---------------------------------------------------------------------------
# _is_retriable unit tests
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("code", [408, 429, 500, 502, 503, 504])
def test_is_retriable_returns_true_for_retriable_code(code):
    """_is_retriable() returns True for each retriable HTTP status code."""
    from src.main import _is_retriable
    assert _is_retriable(_api_err(code)) is True


@pytest.mark.parametrize("code", [400, 401, 403, 404])
def test_is_retriable_returns_false_for_non_retriable_code(code):
    """_is_retriable() returns False for non-retriable HTTP codes."""
    from src.main import _is_retriable
    assert _is_retriable(_api_err(code)) is False


def test_is_retriable_timeout_exception_is_retriable():
    """httpx.TimeoutException is retriable."""
    from src.main import _is_retriable
    assert _is_retriable(httpx.TimeoutException("timeout")) is True


def test_is_retriable_connect_error_is_retriable():
    """httpx.ConnectError is retriable."""
    from src.main import _is_retriable
    assert _is_retriable(httpx.ConnectError("refused")) is True


def test_is_retriable_value_error_is_not_retriable():
    """ValueError is not retriable."""
    from src.main import _is_retriable
    assert _is_retriable(ValueError("bad value")) is False


def test_is_retriable_environment_error_is_not_retriable():
    """EnvironmentError is not retriable."""
    from src.main import _is_retriable
    assert _is_retriable(EnvironmentError("missing key")) is False


def test_is_retriable_runtime_error_is_not_retriable():
    """Unknown RuntimeError is not retriable."""
    from src.main import _is_retriable
    assert _is_retriable(RuntimeError("unexpected")) is False


# ---------------------------------------------------------------------------
# _run_pipeline_with_retry behavioral tests
# ---------------------------------------------------------------------------


def test_retry_first_attempt_success_no_sleep():
    """First-attempt success: _run_pipeline called once, no sleep."""
    result, sleep_delays, mock = _run_retry([dict(_CANNED_STATE)])
    assert mock.call_count == 1
    assert sleep_delays == []
    assert result == dict(_CANNED_STATE)


def test_retry_429_then_success_two_attempts():
    """HTTP 429 on attempt 1, success on attempt 2: two calls, one sleep."""
    result, sleep_delays, mock = _run_retry(
        [_client_err(429), dict(_CANNED_STATE)],
    )
    assert mock.call_count == 2
    assert len(sleep_delays) == 1
    assert result == dict(_CANNED_STATE)


def test_retry_503_then_success_two_attempts():
    """HTTP 503 on attempt 1, success on attempt 2: two calls, one sleep."""
    result, sleep_delays, mock = _run_retry(
        [_server_err(503), dict(_CANNED_STATE)],
    )
    assert mock.call_count == 2
    assert len(sleep_delays) == 1


def test_retry_two_failures_then_success_three_attempts():
    """Two transient failures then success: three calls, two sleeps."""
    result, sleep_delays, mock = _run_retry(
        [_server_err(503), _server_err(502), dict(_CANNED_STATE)],
    )
    assert mock.call_count == 3
    assert len(sleep_delays) == 2
    assert result == dict(_CANNED_STATE)


def test_retry_delay_follows_exponential_base():
    """Delays follow 2s and 4s exponential bases (with zero jitter)."""
    _run_retry(
        [_server_err(503), _server_err(502), dict(_CANNED_STATE)],
        jitter=0.0,
    )
    # Re-run inside test to capture delays
    sleep_delays: list[float] = []

    async def _no_sleep(d: float) -> None:
        sleep_delays.append(d)

    from src.main import _run_pipeline_with_retry

    pipeline_mock = AsyncMock(
        side_effect=[_server_err(503), _server_err(502), dict(_CANNED_STATE)]
    )
    with patch("src.main._run_pipeline", pipeline_mock):
        asyncio.run(
            _run_pipeline_with_retry(
                _CONTEXT_PATH,
                sleep_func=_no_sleep,
                jitter_func=lambda _a, _b: 0.0,
            )
        )

    assert len(sleep_delays) == 2
    assert sleep_delays[0] == pytest.approx(2.0)
    assert sleep_delays[1] == pytest.approx(4.0)


def test_retry_exhaustion_raises_original_exception():
    """Retry exhaustion (3 failures): three calls, two sleeps, original exception re-raised."""
    exc_instance = _server_err(503)

    sleep_delays: list[float] = []

    async def _no_sleep(d: float) -> None:
        sleep_delays.append(d)

    from src.main import _run_pipeline_with_retry

    pipeline_mock = AsyncMock(side_effect=[exc_instance, _server_err(503), exc_instance])

    with patch("src.main._run_pipeline", pipeline_mock):
        with pytest.raises(genai_errors.ServerError):
            asyncio.run(
                _run_pipeline_with_retry(
                    _CONTEXT_PATH,
                    sleep_func=_no_sleep,
                    jitter_func=lambda _a, _b: 0.0,
                )
            )

    assert pipeline_mock.call_count == 3
    assert len(sleep_delays) == 2


@pytest.mark.parametrize("code", [400, 401, 403, 404])
def test_retry_non_retriable_code_not_retried(code):
    """Non-retriable HTTP codes: called exactly once, no sleep."""
    sleep_delays: list[float] = []

    async def _no_sleep(d: float) -> None:
        sleep_delays.append(d)

    from src.main import _run_pipeline_with_retry

    pipeline_mock = AsyncMock(side_effect=[_client_err(code)])

    with patch("src.main._run_pipeline", pipeline_mock):
        with pytest.raises(genai_errors.ClientError):
            asyncio.run(
                _run_pipeline_with_retry(
                    _CONTEXT_PATH,
                    sleep_func=_no_sleep,
                    jitter_func=lambda _a, _b: 0.0,
                )
            )

    assert pipeline_mock.call_count == 1
    assert sleep_delays == []


def test_retry_timeout_then_success():
    """httpx.TimeoutException on attempt 1, success on attempt 2."""
    result, sleep_delays, mock = _run_retry(
        [httpx.TimeoutException("timeout"), dict(_CANNED_STATE)],
    )
    assert mock.call_count == 2
    assert len(sleep_delays) == 1
    assert result == dict(_CANNED_STATE)


def test_retry_connect_error_then_success():
    """httpx.ConnectError on attempt 1, success on attempt 2."""
    result, sleep_delays, mock = _run_retry(
        [httpx.ConnectError("refused"), dict(_CANNED_STATE)],
    )
    assert mock.call_count == 2
    assert len(sleep_delays) == 1


# ---------------------------------------------------------------------------
# Duplicate completion prevention via shared seen_authors
# ---------------------------------------------------------------------------


def test_seen_authors_shared_across_retry_attempts():
    """The same seen_authors set is passed to all retry attempts, preventing duplicate lines."""
    authors_per_attempt: list[set] = []

    async def _tracking_pipeline(path: str, *, seen_authors=None) -> dict:
        authors_per_attempt.append(seen_authors)
        if len(authors_per_attempt) == 1:
            # Simulate Memory Agent completing during the failed attempt
            seen_authors.add("memory_agent")
            raise genai_errors.ServerError(503, {})
        return dict(_CANNED_STATE)

    sleep_delays: list[float] = []

    async def _no_sleep(d: float) -> None:
        sleep_delays.append(d)

    from src.main import _run_pipeline_with_retry

    with patch("src.main._run_pipeline", side_effect=_tracking_pipeline):
        result = asyncio.run(
            _run_pipeline_with_retry(
                _CONTEXT_PATH,
                sleep_func=_no_sleep,
                jitter_func=lambda _a, _b: 0.0,
            )
        )

    assert len(authors_per_attempt) == 2
    # Same set object passed to both attempts
    assert authors_per_attempt[0] is authors_per_attempt[1]
    # Memory Agent still present in set at the second attempt → would not be printed again
    assert "memory_agent" in authors_per_attempt[1]
    assert result == dict(_CANNED_STATE)


# ---------------------------------------------------------------------------
# main() structural: single asyncio.run() call
# ---------------------------------------------------------------------------


def test_main_calls_asyncio_run_exactly_once():
    """main() must call asyncio.run() exactly once (single event loop)."""
    def _run_stub(coroutine):
        coroutine.close()
        return dict(_CANNED_STATE)

    run_mock = MagicMock(side_effect=_run_stub)

    with (
        patch("src.main.asyncio.run", run_mock),
        patch("src.main.config.validate_config"),
        patch("src.main.Path") as mock_path_cls,
        patch("src.main.console", MagicMock()),
    ):
        mock_path_cls.return_value.exists.return_value = True
        from src.main import main
        main(["--context", _CONTEXT_PATH])

    assert run_mock.call_count == 1


# ---------------------------------------------------------------------------
# main() terminal provider-error handling
# ---------------------------------------------------------------------------


def test_main_exits_1_on_provider_api_error_sanitized():
    """Terminal APIError: exit 1 with sanitized output (HTTP code, not raw message)."""
    exc = _server_err(503)
    raw_message = str(exc)
    mock_console = MagicMock()

    # Use a plain MagicMock (not AsyncMock) so patch() does not auto-promote
    # the target to a coroutine; raising synchronously keeps the except-block
    # under test without triggering unawaited-coroutine warnings.
    def _raise_immediately(*args, **kwargs):
        raise exc

    with (
        patch("src.main._run_pipeline_with_retry", MagicMock(side_effect=_raise_immediately)),
        patch("src.main.config.validate_config"),
        patch("src.main.Path") as mock_path_cls,
        patch("src.main.console", mock_console),
    ):
        mock_path_cls.return_value.exists.return_value = True
        from src.main import main
        with pytest.raises(SystemExit) as exc_info:
            main(["--context", _CONTEXT_PATH])

    assert exc_info.value.code == 1
    all_output = " ".join(str(c) for c in mock_console.print.call_args_list)
    assert "503" in all_output
    assert raw_message not in all_output


def test_main_exits_1_on_timeout_sanitized():
    """Terminal TimeoutException: exit 1 with sanitized output (class name, not message)."""
    exc = httpx.TimeoutException("internal timeout details")
    raw_message = "internal timeout details"
    mock_console = MagicMock()

    def _raise_immediately(*args, **kwargs):
        raise exc

    with (
        patch("src.main._run_pipeline_with_retry", MagicMock(side_effect=_raise_immediately)),
        patch("src.main.config.validate_config"),
        patch("src.main.Path") as mock_path_cls,
        patch("src.main.console", mock_console),
    ):
        mock_path_cls.return_value.exists.return_value = True
        from src.main import main
        with pytest.raises(SystemExit) as exc_info:
            main(["--context", _CONTEXT_PATH])

    assert exc_info.value.code == 1
    all_output = " ".join(str(c) for c in mock_console.print.call_args_list)
    assert "TimeoutException" in all_output
    assert raw_message not in all_output


# ---------------------------------------------------------------------------
# Compatibility: direct _run_pipeline callers remain unchanged
# ---------------------------------------------------------------------------


def test_run_pipeline_direct_call_without_seen_authors_compatible():
    """_run_pipeline(context_path) without seen_authors keyword still works."""
    mock_session = MagicMock()
    mock_session.id = "sess-compat"
    mock_final = MagicMock()
    mock_final.state = dict(_CANNED_STATE)

    mock_svc = MagicMock()
    mock_svc.create_session = AsyncMock(return_value=mock_session)
    mock_svc.get_session    = AsyncMock(return_value=mock_final)

    mock_runner = MagicMock()
    mock_runner.run_async.return_value = _empty_async_gen()

    with (
        patch("src.main.memory_agent.build_agent",   return_value=MagicMock()),
        patch("src.main.planner_agent.build_agent",  return_value=MagicMock()),
        patch("src.main.research_agent.build_agent", return_value=MagicMock()),
        patch("src.main.executor_agent.build_agent", return_value=MagicMock()),
        patch("src.main.SequentialAgent",            return_value=MagicMock()),
        patch("src.main.InMemorySessionService",     return_value=mock_svc),
        patch("src.main.Runner",                     return_value=mock_runner),
    ):
        from src.main import _run_pipeline
        result = asyncio.run(_run_pipeline(_CONTEXT_PATH))

    assert result["memory_snapshot"] == _CANNED_STATE["memory_snapshot"]
