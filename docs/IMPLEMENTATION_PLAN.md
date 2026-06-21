# Implementation Plan — PAIOS-Lite

> Kaggle Capstone · Concierge Agents track  
> Deadline: July 6, 2026 · 16 days from plan date (2026-06-20)

---

## 1. MVP Scope

A **CLI-first project continuity assistant** that accepts a local project directory,
runs a four-agent pipeline, and prints a structured "continuity brief" summarizing
current state, open questions, and prioritized next steps.

The user runs one command:

```bash
python -m paios_lite --context ./my_project
```

They receive a brief they can act on immediately. No web UI. No database. No login.

**In scope for MVP**

- Read project files, git log, and notes from a local directory
- Produce a Memory snapshot, a Plan, optional research context, and a list of
  actionable next steps
- Rich terminal output with section headers
- MCP-compatible tool functions exposed via stdio transport
- API key loaded from environment only (never from code)
- A working demo using the `examples/sample_project_context.md` fixture

**Out of scope for MVP** → see Section 2.

---

## 2. Non-Goals

The following are explicitly excluded from the initial build. They may be added
post-submission if time permits.

| Item | Reason excluded |
|---|---|
| Web UI / dashboard | Adds surface area, not required for judging |
| Persistent database / vector store | CLI file reads are sufficient for the demo scope |
| Real-time background monitoring | Complicates the demo and adds little judging value |
| Multi-user or team support | Out of scope for Concierge Agents track |
| Deployment to a live endpoint | Judges do not require a live URL; local CLI suffices |
| Fine-tuning or custom model training | Uses standard LLM API via ADK |
| Slack / email integration | Outside the project continuity demo scope |

---

## 3. Agent Responsibilities

All four agents are implemented with the Google Agent Development Kit (ADK).
The LLM backend is configurable via environment variable and defaults to Gemini
when `GOOGLE_API_KEY` is present; Claude or a local Ollama model are also
supported through ADK's LiteLLM integration. Agents run sequentially in the
default pipeline; the Planner and Executor may call each other in a light loop
if clarification is needed.

### Memory Agent
**Input:** raw project directory path  
**Output:** structured memory snapshot (Markdown)

- Scans `README`, top-level docs, recent git commits, and open TODO markers
- Summarizes what the project is, what was recently done, and what is left open
- Uses the `read_project_context` and `get_git_log` MCP tools
- Result is passed as context to all downstream agents

### Planner Agent
**Input:** memory snapshot + optional user query  
**Output:** ordered task list with priorities and estimated effort

- Identifies blockers, next milestones, and quick wins
- Labels tasks: `critical`, `high`, `low`, or `nice-to-have`
- Uses the `create_plan` MCP tool to structure output

### Research Agent
**Input:** task list  
**Output:** relevant context per high-priority task

- Searches local notes and the `examples/` directory for prior decisions
- Optionally calls a web search tool if a task requires external reference
- Uses `search_notes` MCP tool; web search is clearly labeled so judges see it

### Executor Agent
**Input:** plan + research context  
**Output:** concrete, copy-pasteable next steps or shell commands

- Translates each task into an action: a command to run, a file to edit, or a
  question to answer
- Does not execute commands autonomously — output is advisory
- Uses `render_actions` MCP tool for structured output formatting

---

## 4. CLI Demo Flow

```
$ python -m paios_lite --context ./examples/sample_project_context.md

[PAIOS-Lite] Reading project context...         ← Memory Agent
[PAIOS-Lite] Building continuity plan...        ← Planner Agent
[PAIOS-Lite] Researching relevant context...    ← Research Agent
[PAIOS-Lite] Generating action items...         ← Executor Agent

══════════════════════════════════════════════
  PROJECT CONTINUITY BRIEF
  2026-06-20 · paios-lite-capstone
══════════════════════════════════════════════

CURRENT STATE
  Last commit: "chore: initialize scaffold"
  Open TODOs: 3 (1 critical, 2 high)
  Key gap: agents are stubs; no LLM calls wired

PLAN (top 3)
  [1] CRITICAL  Wire Memory Agent to LLM via ADK (est. 2h)
  [2] HIGH      Implement Planner Agent tool calls (est. 3h)
  [3] HIGH      Draft README and setup instructions (est. 1h)

RESEARCH NOTES
  · ADK SequentialAgent pattern matches this pipeline (Day 3 slides)
  · MCP stdio transport: see docs/Agent Tools & Interoperability_Day_2.pdf

NEXT ACTIONS
  1. pip install google-adk python-dotenv rich
  2. Copy .env.example → .env and set LLM_MODEL + your provider API key
  3. Implement src/agents/memory_agent.py using ADK LlmAgent
  4. Run: python -m paios_lite --context examples/sample_project_context.md
══════════════════════════════════════════════
```

The entire run fits in a 90-second terminal recording suitable for the demo video.

---

## 5. MCP / Tool-Server Style Design

Tools are defined as standard Python functions decorated with the ADK `@tool`
decorator and also registered with an MCP stdio server. This satisfies the
"MCP Server" course concept requirement while keeping the implementation simple.

| Tool name | Signature | Description |
|---|---|---|
| `read_project_context` | `(path: str) -> str` | Returns a structured summary of key files in the project directory |
| `get_git_log` | `(path: str, n: int = 10) -> str` | Returns the last N commit messages |
| `search_notes` | `(query: str, path: str) -> str` | Full-text search over Markdown files |
| `create_plan` | `(context: str) -> str` | Formats a task list from free-text context |
| `render_actions` | `(plan: str) -> str` | Renders the final action items block |

The MCP server (`src/tools/mcp_server.py`) wraps these tools in an stdio
transport so an external MCP client (e.g., Claude Desktop) could also call them.
This demonstrates the "MCP Server" course concept beyond basic tool-use.

---

## 6. Security and Privacy Features

This section maps directly to the "Security features" course concept and the
"safe handling of secrets" judging criterion.

| Control | Implementation |
|---|---|
| No hardcoded keys | All keys read from environment variables only |
| `.env.example` provided | Documents required vars without values |
| `.env` gitignored | Added to `.gitignore` before first commit |
| Local-only context | Project files are read locally; only the assembled prompt is sent to the LLM API |
| No disk logging of content | Debug output is opt-in via `--verbose` flag |
| Rate-limit retry | All LLM API calls wrapped with exponential backoff |
| Input sanitization | File paths validated before shell or `os.path` usage |
| Dependency pinning | `requirements.txt` with pinned versions for reproducibility |

The assistant never stores project content outside the current process. The user
retains full control over what is sent to the LLM (i.e., the assembled prompt).

---

## 7. File Structure

```
paios-lite-capstone/
├── src/
│   ├── __init__.py
│   ├── main.py                    # CLI entry point (argparse)
│   ├── config.py                  # Env-based config; loads .env
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── memory_agent.py        # ADK LlmAgent: context reader
│   │   ├── planner_agent.py       # ADK LlmAgent: task planner
│   │   ├── research_agent.py      # ADK LlmAgent: note searcher
│   │   └── executor_agent.py      # ADK LlmAgent: action generator
│   └── tools/
│       ├── __init__.py
│       ├── context_reader.py      # read_project_context tool
│       ├── git_reader.py          # get_git_log tool
│       ├── note_searcher.py       # search_notes tool
│       └── mcp_server.py          # MCP stdio server wrapping all tools
├── tests/
│   ├── test_scaffold.py
│   ├── test_tools.py              # Unit tests for MCP tool functions
│   └── test_agents.py             # Integration tests with mocked LLM
├── demo/
│   └── demo_script.md             # Step-by-step video recording guide
├── docs/
│   ├── REQUIREMENTS_ANALYSIS.md
│   ├── IMPLEMENTATION_PLAN.md     ← this file
│   ├── ARCHITECTURE.md            # Agent interaction diagram (to be filled)
│   ├── CAPSTONE_BRIEF.md          # Problem statement and value prop (to be filled)
│   └── SUBMISSION_NOTES.md
├── examples/
│   └── sample_project_context.md  # Demo fixture: a fake project for the CLI run
├── .env.example                   # LLM_MODEL + provider key (Gemini or Claude)
├── .gitignore                     # Includes .env, __pycache__, *.pyc
├── README.md                      # Setup, usage, architecture, video link
├── requirements.txt               # Pinned dependencies
└── pyproject.toml                 # Package metadata
```

---

## 8. Build Sequence

The deadline is **July 6, 2026**. The sequence is ordered to produce a
demoable artifact as early as possible, so the video can be recorded before
documentation is finalized.

### Phase 1 — Foundation (Days 1–3 · target: June 23)
- [ ] Add `requirements.txt`, `pyproject.toml`, `.env.example`, `.gitignore` updates
- [ ] Implement `src/config.py` (env loading, key validation)
- [ ] Implement `src/tools/context_reader.py` and `src/tools/git_reader.py`
- [ ] Wire `src/agents/memory_agent.py` to configured LLM via ADK `LlmAgent`
- [ ] `src/main.py`: accept `--context` arg, run Memory Agent, print raw output
- **Gate**: `python -m paios_lite --context examples/sample_project_context.md`
  prints a coherent memory summary

### Phase 2 — Multi-agent Pipeline (Days 4–6 · target: June 26)
- [ ] Implement `src/tools/note_searcher.py`
- [ ] Implement Planner Agent with `create_plan` tool
- [ ] Implement Research Agent with `search_notes` tool
- [ ] Implement Executor Agent with `render_actions` tool
- [ ] Wire agents into ADK `SequentialAgent` pipeline in `main.py`
- [ ] Polish terminal output (section headers, progress indicators)
- **Gate**: Full four-agent run produces the continuity brief shown in Section 4

### Phase 3 — MCP Server + Security Hardening (Days 7–9 · target: June 29)
- [ ] Implement `src/tools/mcp_server.py` (stdio transport, exposes all 5 tools)
- [ ] Add exponential backoff wrapper for all LLM API calls
- [ ] Add input path validation and sanitization
- [ ] Write `tests/test_tools.py` (unit tests, no LLM calls)
- [ ] Write `tests/test_agents.py` (integration tests with mocked LLM responses)
- **Gate**: `python -m paios_lite.tools.mcp_server` starts without error; all
  tests pass

### Phase 4 — Demo, Docs, Submission (Days 10–14 · target: July 4)
- [ ] Record demo video (≤5 min, YouTube, unlisted until submission)
- [ ] Fill in `docs/ARCHITECTURE.md` with agent interaction diagram
- [ ] Fill in `docs/CAPSTONE_BRIEF.md` with problem statement and value prop
- [ ] Fill in `demo/demo_script.md` with the exact terminal commands shown
- [ ] Write `README.md`: problem, solution, architecture, setup, video link
- [ ] Draft Kaggle writeup (≤2,500 words)
- [ ] Final review: no API keys in any file, all tests pass, README is complete
- [ ] Submit on Kaggle before July 6

---

## 9. Success Criteria

A submission is ready when all of the following are true.

### Technical
- [ ] `python -m paios_lite --context <path>` runs end-to-end without errors
- [ ] All four agents produce distinct, non-placeholder output in the run
- [ ] At least five MCP tools are registered and callable via the MCP server
- [ ] No API keys, passwords, or `.env` files exist in the repo
- [ ] `requirements.txt` is present and all dependencies are pinned
- [ ] `tests/` includes at least one test per tool function

### Judging rubric coverage
- [ ] **Agent / multi-agent system**: four ADK agents in a SequentialAgent pipeline
- [ ] **MCP server**: `mcp_server.py` with stdio transport
- [ ] **Security features**: env-only keys, no logging of content, input validation
- [ ] **Agent skills / agents CLI**: ADK tool decorators and LlmAgent definitions
- [ ] **Antigravity**: demonstrated in the video walkthrough

### Submission completeness
- [ ] Kaggle writeup published (≤2,500 words)
- [ ] YouTube video attached (≤5 min)
- [ ] Public GitHub repo linked
- [ ] `README.md` has setup instructions reproducible by a judge

---

## 10. First Implementation Task

**Task**: Wire the Memory Agent to the configured LLM and print its output.

**Why this first**: It is the shortest path to a working LLM call in the project.
Every other agent depends on the same ADK + LLM setup, so unblocking this
unblocks everything else. It also validates the `.env` / key loading pattern
and confirms ADK's LiteLLM routing works before any other code is written.

**What to do**:

1. Create `requirements.txt` with:
   - `google-adk[litellm]`
   - `python-dotenv`
   - `rich` (terminal formatting)

2. Create `.env.example`:
   ```
   # Pick one provider and supply the matching key.
   LLM_MODEL=gemini/gemini-2.0-flash-exp

   # Gemini (default)
   GOOGLE_API_KEY=

   # Claude (alternative)
   # LLM_MODEL=claude-3-5-haiku-20241022
   # ANTHROPIC_API_KEY=
   ```

3. Implement `src/config.py` to load `.env`, read `LLM_MODEL`, and assert that
   at least one provider key is present.

4. Implement `src/tools/context_reader.py` with a `read_project_context(path)`
   function that reads the top-level README, lists files, and returns a string.

5. Implement `src/agents/memory_agent.py` as an ADK `LlmAgent` that receives
   `LLM_MODEL` from config and calls `read_project_context` as an ADK tool.

6. Update `src/main.py` to accept `--context <path>` and call the Memory Agent.

7. Run against `examples/sample_project_context.md` and verify the output is
   coherent.

**Definition of done**: The terminal prints a paragraph-length project summary
generated by the configured LLM, with no hardcoded model name or API key in any
source file.

---

## Architecture Recommendation

**CLI-first with MCP tool-server pattern.**

The project fits a CLI model naturally: the input is a local directory, the
output is structured text, and the demo is a terminal recording. A web UI would
add 30–40% more build time with no judging benefit — judges run local code,
they don't browse a deployed app.

The MCP tool-server pattern (exposing tools via stdio) satisfies the "MCP
Server" course concept requirement while keeping the code readable and testable
without a running server process during development.

The ADK `SequentialAgent` orchestrator connects the four agents with minimal
boilerplate, directly maps to the course material on Day 3, and produces an
architecture diagram that is easy to explain in the video and writeup.

**LLM provider**: Gemini is the expected demo provider because the course is
Google-hosted, but the code configures the model through a single `LLM_MODEL`
environment variable routed by ADK's LiteLLM integration. Claude or a local
Ollama model can be used as a drop-in substitute with no code changes. The
competition does not mandate Gemini specifically; it mandates ADK as the
framework.

---

*Plan written 2026-06-20. Update this document if scope, agent design, or build
sequence changes materially.*
