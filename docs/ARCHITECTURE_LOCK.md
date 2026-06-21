# Architecture Lock — PAIOS-Lite MVP

> Status: **LOCKED**  
> Locked on: 2026-06-20  
> Do not modify this document during implementation. Any structural change
> requires an explicit decision and a new revision with a date stamp.

---

## What this document is for

This file defines the MVP architecture in terms that are binding for the build.
Implementation details (retry logic, formatting, test coverage) are free to
vary. The items marked **LOCKED** below are not.

---

## System overview

PAIOS-Lite is a **local CLI tool**. It accepts a project directory, runs four
agents in sequence, and prints a structured continuity brief. Nothing is
deployed. Nothing is stored on disk between runs. No web server is started.

```
User
 │
 ▼
CLI  (python -m paios_lite --context <path>)
 │
 ▼
SequentialAgent  [ADK orchestrator]
 ├── Memory Agent   ──► read_project_context, get_git_log   ◄── MCP tools
 ├── Planner Agent  ──► create_plan                         ◄── MCP tools
 ├── Research Agent ──► search_notes                        ◄── MCP tools
 └── Executor Agent ──► render_actions                      ◄── MCP tools
                                                                    │
                                                              MCP stdio server
                                                          (also callable externally)
 │
 ▼
Continuity Brief  (printed to stdout)
```

---

## LOCKED: Four agents

Each agent is an ADK `LlmAgent`. Names, inputs, outputs, and tool assignments
are fixed.

| Agent | Input | Output | MCP tools used |
|---|---|---|---|
| **Memory Agent** | project path | memory snapshot (Markdown) | `read_project_context`, `get_git_log` |
| **Planner Agent** | memory snapshot | ordered task list | `create_plan` |
| **Research Agent** | task list | annotated context per task | `search_notes` |
| **Executor Agent** | plan + research | action items (copy-pasteable) | `render_actions` |

Orchestration: ADK `SequentialAgent` runs them in the order above. Output of
each agent is passed as context to the next.

---

## LOCKED: Five MCP tools

Exposed via an MCP stdio server (`src/tools/mcp_server.py`). Also registered
directly as ADK tools on each agent. Names and signatures are fixed.

| Tool | Signature | Pure local? |
|---|---|---|
| `read_project_context` | `(path: str) -> str` | Yes |
| `get_git_log` | `(path: str, n: int = 10) -> str` | Yes |
| `search_notes` | `(query: str, path: str) -> str` | Yes |
| `create_plan` | `(context: str) -> str` | Yes — formats text, no LLM call |
| `render_actions` | `(plan: str) -> str` | Yes — formats text, no LLM call |

All five tools operate on local files only. No network calls inside any tool
function. Network calls happen only in the ADK agent layer (LLM inference).

---

## LOCKED: MCP transport

The MCP server uses **stdio transport**. This is the simplest MCP transport and
requires no open ports, no authentication, and no deployment. An external MCP
client (e.g., Claude Desktop, VS Code extension) can point to the server binary
and call the five tools without modification.

Start command (to be documented in README):

```bash
python -m paios_lite.tools.mcp_server
```

---

## LOCKED: Interface

**CLI only.** No web UI, no REST API, no GUI. The entry point is:

```bash
python -m paios_lite --context <path>
```

Optional flags (not locked in this document, but expected):
- `--verbose` — show agent reasoning steps
- `--output <file>` — write brief to a file instead of stdout

---

## LOCKED: LLM backend contract

The LLM provider is **not locked** to Gemini. The implementation must satisfy
all three of the following rules:

1. The model name is read from the `LLM_MODEL` environment variable.
2. ADK's LiteLLM integration routes the call — no provider SDK is imported
   directly in agent code.
3. The tool functions (`src/tools/`) contain **zero** LLM calls. They are
   pure Python operating on local files.

Expected values for `LLM_MODEL`:

| Value | Provider | Key var required |
|---|---|---|
| `gemini/gemini-2.0-flash-exp` | Google Gemini | `GOOGLE_API_KEY` |
| `claude-3-5-haiku-20241022` | Anthropic Claude | `ANTHROPIC_API_KEY` |
| `ollama/llama3.2` | Ollama (local) | none |

`src/config.py` validates that the key required by the chosen provider is
present before any agent runs.

---

## LOCKED: Security controls

These controls are non-negotiable for the competition submission.

| Control | Rule |
|---|---|
| No hardcoded secrets | No API key, token, or password appears anywhere in source files |
| `.env` excluded from git | `.gitignore` must list `.env` before the first commit |
| `.env.example` provided | Documents all required vars without values |
| Path validation | `read_project_context` and `get_git_log` must reject paths outside the given root |
| No content logging | Tool outputs must not be written to disk; `--verbose` may print to stdout only |
| Backoff on API errors | All LLM calls must retry with exponential backoff on rate-limit errors |

---

## LOCKED: Course concept coverage

The following table is the acceptance checklist against the Kaggle rubric.
All five items must be satisfiable from the code before submission.

| Course concept | Where it appears | Satisfies rule? |
|---|---|---|
| **Agent / multi-agent system (ADK)** | `SequentialAgent` wrapping four `LlmAgent` instances in `src/agents/` | Code |
| **MCP server** | `src/tools/mcp_server.py`, stdio transport, five registered tools | Code |
| **Security features** | Env-only keys, path validation, no content logging, backoff | Code |
| **Agent skills / agents CLI** | ADK `@tool` decorators on all tool functions; `LlmAgent` definitions | Code |
| **Antigravity** | Demonstrated in the 5-minute video walkthrough | Video |

Three are required; this architecture demonstrates five.

---

## NOT locked (implementation is free to vary)

- Output formatting and color scheme
- Retry/backoff implementation details (tenacity, custom loop, etc.)
- Test framework (pytest is expected but not locked)
- Exact Markdown format of the memory snapshot and plan
- Whether `create_plan` and `render_actions` use templating or string formatting
- Number of files read by `read_project_context` (depth/breadth heuristic)
- Whether `search_notes` uses regex, ripgrep, or another method

---

## File locations (locked paths)

These paths must not be moved or renamed without updating this document.

| Path | Role |
|---|---|
| `src/main.py` | CLI entry point |
| `src/config.py` | Env loading and validation |
| `src/agents/memory_agent.py` | Memory Agent |
| `src/agents/planner_agent.py` | Planner Agent |
| `src/agents/research_agent.py` | Research Agent |
| `src/agents/executor_agent.py` | Executor Agent |
| `src/tools/context_reader.py` | `read_project_context` + `get_git_log` tools |
| `src/tools/note_searcher.py` | `search_notes` tool |
| `src/tools/mcp_server.py` | MCP stdio server |
| `.env.example` | Env variable template (committed) |
| `examples/sample_project_context.md` | Demo fixture for CLI run |

---

## Revision history

| Date | Change | Author |
|---|---|---|
| 2026-06-20 | Initial lock — LLM-agnostic, CLI-first, four agents, five MCP tools | PAIOS-Lite team |
