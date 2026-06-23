# PAIOS-Lite Capstone Brief

## 1. Project Title

**PAIOS-Lite**

## 2. Track

**Concierge Agents**

## 3. Elevator Pitch

PAIOS-Lite is a local project-continuity assistant that turns a project path into a concise continuity brief: what changed, what matters now, what context supports the work, and what to do next.

## 4. Problem Statement

Developers often return to a project after hours or days away and need to rebuild context from README files, notes, TODO markers, recent commits, and partially completed plans. That context reconstruction takes time and can cause important details to be missed.

PAIOS-Lite addresses that gap with a local CLI workflow that summarizes the current state and produces next-session actions without adding a web service, database, or hosted backend.

## 5. Target Users

- Individual developers returning to an active project
- Students preparing a project handoff or demo
- Builders who want a local assistant that respects project privacy
- Reviewers who need a quick continuity snapshot before inspecting code

## 6. Solution

The user runs:

```bash
python -m paios_lite --context examples/sample_project_context.md
```

PAIOS-Lite validates configuration, runs a four-agent Google ADK pipeline, and prints a Rich terminal continuity brief with:

1. Current State
2. Plan
3. Research Notes
4. Next Actions

## 7. Why a Multi-Agent Approach

Project continuity is naturally staged. One agent should inspect and summarize context, another should plan, another should search for supporting notes, and a final agent should translate the plan into actions. Splitting those responsibilities makes each prompt smaller, gives each agent a clear output contract, and allows session state to flow through the pipeline in a predictable order.

## 8. Agent Responsibilities

| Agent | Responsibility | Output key |
|---|---|---|
| Memory Agent | Reads project context and recent git history; produces a structured memory snapshot. | `memory_snapshot` |
| Planner Agent | Converts the memory snapshot into an ordered task plan. | `plan` |
| Research Agent | Searches local Markdown notes for context relevant to high-priority tasks. | `research_notes` |
| Executor Agent | Converts plan and research context into concrete next actions. | `next_actions` |

Pipeline order:

```text
Memory Agent → Planner Agent → Research Agent → Executor Agent
```

## 9. Tools and MCP

Five local tools support both the agent pipeline and the MCP stdio server:

- `read_project_context`
- `get_git_log`
- `search_notes`
- `create_plan`
- `render_actions`

The MCP server runs with:

```bash
python -m paios_lite.tools.mcp_server
```

It uses FastMCP stdio transport and wraps the existing local tool functions instead of duplicating tool logic.

## 10. Security and Reliability

Security and reliability features demonstrated in the repository:

- API keys are read from environment variables.
- `.env` is ignored by Git.
- `.env.example` contains placeholders only.
- Local tools reject null bytes and resolve paths before access.
- Git history is read with subprocess argument lists and no `shell=True`.
- MCP path errors are sanitized.
- Provider terminal errors are sanitized.
- Transient provider failures retry with exponential backoff.
- Non-retriable failures fail immediately.
- Direct dependencies are pinned exactly in `requirements.txt`.

## 11. Course Concepts Demonstrated

PAIOS-Lite demonstrates these course concepts:

- Google ADK
- Multi-agent system
- Sequential orchestration
- Tool-enabled agents
- MCP stdio server
- Security and error sanitization
- Retry and exponential backoff
- Reproducible dependency management

The project does not claim Agents CLI skills, Antigravity implementation, cloud deployment, production hosting, or a persistent database.

## 12. Validation Results

Final Phase 3 validation recorded:

- Python 3.14 development validation passed.
- Clean Python 3.11 validation passed.
- `207 passed`.
- Official MCP client validation passed.
- Controlled live Gemini CLI run passed.
- No tracked secrets detected.
- Only upstream dependency deprecation warnings remained.

## 13. Limitations

- PAIOS-Lite is a local CLI tool, not a hosted product.
- It does not include a web UI, REST API, cloud deployment, database, or persistent memory service.
- The MCP server exposes the five local tools; it does not run the four-agent CLI pipeline.
- Live model execution requires a configured provider key unless a local no-key model is used.
- Gemini was the demonstrated live runtime; other documented provider options have not all been live-tested.

## 14. Submission Assets Status

| Asset | Status |
|---|---|
| Public repository | Available |
| Final README | Drafted in Phase 4A |
| Architecture guide | Drafted in Phase 4A |
| Capstone brief | Drafted in Phase 4A |
| Demo script | Placeholder; planned for Phase 4C |
| Screenshots | Coming before submission |
| Demo video | Coming before submission |
| Kaggle write-up | Coming before submission |
| Submission checklist | Coming before submission |
