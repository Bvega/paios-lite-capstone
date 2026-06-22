# Architecture — PAIOS-Lite

> Implemented: 2026-06-22 · Phase 2 HEAD: `3f2314a`
> Authority: `docs/ARCHITECTURE_LOCK.md`
> MCP stdio server: pending Phase 3

---

## Overview

PAIOS-Lite is a local CLI tool. One command reads a project context path,
runs a four-agent pipeline, and prints a structured continuity brief to the
terminal. Nothing is deployed. No state is persisted between runs.

```
User
 │
 ▼
CLI  python -m paios_lite --context <path>
     src/main.py · argparse · Rich terminal output
 │
 ▼  asyncio.run(_run_pipeline(context_path))
SequentialAgent  "paios_lite_pipeline"  [ADK orchestrator]
 │
 ├── Memory Agent    ──► read_project_context(path)    ──► memory_snapshot
 │                   ──► get_git_log(path, n=10)
 │
 ├── Planner Agent   ──► create_plan(context)          ──► plan
 │                       reads {memory_snapshot}
 │
 ├── Research Agent  ──► search_notes(query, path)     ──► research_notes
 │                       reads {memory_snapshot}, {plan}, {project_path}
 │
 └── Executor Agent  ──► render_actions(plan)          ──► next_actions
                         reads {plan}, {research_notes}
 │
 ▼
InMemorySessionService  (session state propagated between agents)
 │
 ▼
Rich continuity brief printed to stdout
```

---

## CLI Entry Point

File: `src/main.py`

`src/main.py` is the sole owner of:

- One `SequentialAgent` instance (`paios_lite_pipeline`)
- One `Runner` instance
- One `InMemorySessionService` instance
- One `asyncio` event loop (via `asyncio.run(_run_pipeline(...))`)

No agent file creates its own `Runner`, `InMemorySessionService`, or event loop.

The initial session state is `{"project_path": context_path}`. The pipeline
reads this value and agents append additional state keys via `output_key`.

The event loop is consumed by `async for event in runner.run_async(...)`.
Each event is inspected for `event.author` and `event.is_final_response()`;
when a known agent emits its final response for the first time, a progress
line is printed:

```
✓ Memory Agent complete
✓ Planner Agent complete
✓ Research Agent complete
✓ Executor Agent complete
```

After the event stream is fully consumed, `session_service.get_session()` is
called to read the final session state.

---

## Agent Details

Each agent is defined in its own file under `src/agents/` and exposes a single
`build_agent()` factory function that returns an `LlmAgent`. The model is read
from `src/config.py` (`LLM_MODEL` environment variable) at call time.

| Agent | File | `LlmAgent` name | Input state keys | `output_key` | Tools |
|---|---|---|---|---|---|
| Memory Agent | `src/agents/memory_agent.py` | `memory_agent` | `project_path` | `memory_snapshot` | `read_project_context`, `get_git_log` |
| Planner Agent | `src/agents/planner_agent.py` | `planner_agent` | `memory_snapshot` | `plan` | `create_plan` |
| Research Agent | `src/agents/research_agent.py` | `research_agent` | `memory_snapshot`, `plan`, `project_path` | `research_notes` | `search_notes` |
| Executor Agent | `src/agents/executor_agent.py` | `executor_agent` | `plan`, `research_notes` | `next_actions` | `render_actions` |

---

## Local Tool Details

All five tools are pure Python with zero LLM calls and zero network I/O.
They are not yet exposed via an MCP server (pending Phase 3).

| Tool | Source file | Signature |
|---|---|---|
| `read_project_context` | `src/tools/context_reader.py` | `(path: str) -> str` |
| `get_git_log` | `src/tools/context_reader.py` | `(path: str, n: int = 10) -> str` |
| `search_notes` | `src/tools/note_searcher.py` | `(query: str, path: str) -> str` |
| `create_plan` | `src/tools/plan_tools.py` | `(context: str) -> str` |
| `render_actions` | `src/tools/plan_tools.py` | `(plan: str) -> str` |

**Note on tool file location:** The original plan (`docs/IMPLEMENTATION_PLAN.md`
Section 7) listed `src/tools/git_reader.py` as a separate file. The implementation
placed both `read_project_context` and `get_git_log` in `src/tools/context_reader.py`.
The file `src/tools/git_reader.py` does not exist. The architectural requirement
(pure-Python local tool, zero LLM/network calls) is satisfied by the actual location.
The `memory_agent.py` import confirms this:

```python
from src.tools.context_reader import get_git_log, read_project_context
```

---

## State Flow

```
Session initial state
  └── project_path: <cli argument>

After Memory Agent
  └── memory_snapshot: <structured Markdown from read_project_context + get_git_log>

After Planner Agent
  └── plan: <ordered task list from create_plan>

After Research Agent
  └── research_notes: <search results from search_notes>

After Executor Agent
  └── next_actions: <numbered action items from render_actions>
```

No state key is modified after it is written. Downstream agents reference keys
from upstream agents via instruction placeholder substitution by the ADK framework.

---

## Terminal Output Structure

```
─────────────── PAIOS-Lite ───────────────
Context: <path>

✓ Memory Agent complete
✓ Planner Agent complete
✓ Research Agent complete
✓ Executor Agent complete

╭─────────────────────────────────────────╮
│       PAIOS-Lite Continuity Brief       │
╰─────────────────────────────────────────╯

──────────── Current State ───────────────
<memory_snapshot rendered as Markdown>

──────────────── Plan ────────────────────
<plan rendered as Markdown>

──────────── Research Notes ──────────────
<research_notes rendered as Markdown>

──────────── Next Actions ────────────────
<next_actions rendered as Markdown>
──────────────────────────────────────────
```

Rich library components used: `Console`, `Rule`, `Markdown`, `Panel`, `Text`.

---

## MCP Server (Pending Phase 3)

`src/tools/mcp_server.py` does not yet exist. Phase 3 will implement a stdio
transport MCP server that exposes all five local tools so an external MCP client
(such as Claude Desktop) can call them directly. The local tool functions will
not change; only the server wrapper is new.

---

## Revision History

| Date | Change |
|---|---|
| 2026-06-22 | Initial content — documented Phase 2 implementation (HEAD `3f2314a`) |
