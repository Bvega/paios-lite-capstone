# PAIOS-Lite: A Multi-Agent Project Continuity Assistant

## Track

Concierge Agents

## Project summary

PAIOS-Lite is a local project-continuity assistant that analyzes repository context and produces an actionable continuity brief for the next development session. It is designed for the common moment when a developer returns to a project after time away and needs to quickly answer: what changed, what matters now, what context supports the work, and what should I do next?

The system runs from the terminal, accepts a local project path or supported context file, executes a four-agent Google ADK pipeline, and prints a structured Rich terminal brief with four sections:

1. Current State
2. Plan
3. Research Notes
4. Next Actions

## Problem statement

Software projects lose continuity easily. Recent commits, TODO markers, notes, partially finished decisions, and known blockers often live in separate places. Rebuilding that context manually is slow, especially for individual builders, students, and reviewers who need a focused handoff before making the next change.

PAIOS-Lite addresses that gap with a local workflow. Instead of creating a hosted service or storing project data, it reads the supplied project context at run time and turns it into a concise next-session brief.

## Target users

The primary users are individual developers returning to an active repository, students preparing a project handoff or demo, builders who want local-first assistance, and reviewers who need a quick continuity snapshot before inspecting code.

## Solution overview

The core CLI command is:

```bash
python -m paios_lite --context examples/sample_project_context.md
```

The demo fixture represents an active task-tracker API project with completed CRUD work, partially implemented authentication, TODO items, and known blockers. PAIOS-Lite reads that context, runs the agent pipeline, and renders a brief that helps the next session start with a concrete direction rather than a search through scattered notes.

## Why an agent-based approach

Project continuity is naturally staged. First, the current state must be summarized. Next, the work must be organized into a plan. Then supporting notes and risks need to be identified. Finally, the plan and research need to become clear next actions. Splitting those responsibilities across agents keeps each prompt focused, makes the output contract explicit, and lets state flow through the system in a predictable order.

## System architecture

The pipeline is:

```text
Memory Agent -> Planner Agent -> Research Agent -> Executor Agent
```

PAIOS-Lite uses Google ADK with four `LlmAgent` agents coordinated by one `SequentialAgent`. For each pipeline attempt, the CLI creates one Runner, one in-memory session service, and one session. The CLI entry point owns the single event loop, so retry attempts remain inside the same top-level `asyncio.run()` boundary while each attempt receives fresh ADK runtime objects.

The architecture is intentionally local-first. There is no web interface, HTTP API, hosted service, or database-backed memory store.

## Agent responsibilities

The Memory Agent extracts current project state and relevant history from local context. It uses the project reader and git-log tools to build a concise memory snapshot.

The Planner Agent converts that state into an ordered development plan.

The Research Agent identifies supporting context, notes, risks, and dependencies that matter for the plan.

The Executor Agent produces the final actionable next-step brief. It does not edit files or execute shell commands; its role is to turn accumulated context into clear guidance.

## Shared state and execution flow

The initial session state contains the supplied `project_path`. Each agent writes one downstream key:

- `memory_snapshot`
- `plan`
- `research_notes`
- `next_actions`

The CLI reads the final session state after the ADK event stream completes and renders those values as Current State, Plan, Research Notes, and Next Actions. In the controlled live validation, all four agent completion messages appeared exactly once, and the final continuity-brief sections appeared in the required order.

## Local tools

PAIOS-Lite includes exactly five local tools:

- `read_project_context`
- `get_git_log`
- `search_notes`
- `create_plan`
- `render_actions`

The tools are local and read-focused, with deterministic plan and action rendering helpers. File access is limited to the supplied path or context derived from it; the project does not claim unrestricted filesystem access. Tool functions do not perform LLM calls or network I/O.

## MCP integration

PAIOS-Lite also includes a FastMCP stdio server:

```bash
python -m paios_lite.tools.mcp_server
```

MCP provides an additional access path to the same local tool implementations used by the agents. It does not replace the CLI multi-agent pipeline and does not run the four-agent workflow by itself.

The official MCP client was used to validate initialization, tool discovery, tool dispatch, sanitized invalid-path errors, and clean shutdown. Tool discovery shows the five expected tool names, and the sanitized error evidence confirms that invalid-path calls are marked as errors without echoing private path details.

## Security and privacy

The project keeps security controls simple and visible. Credentials are loaded from environment variables, `.env` is ignored by Git, and no credentials are embedded in code. Path handling rejects null bytes and resolves paths before access. Git history is read through subprocess argument lists without `shell=True`.

MCP path errors are sanitized as a generic invalid-path message, and terminal provider errors are summarized by HTTP code or exception class instead of raw provider text. Secret scans were run before release checkpoints, and no tracked secrets were detected. PAIOS-Lite is local-first, but it is not presented as a complete security sandbox.

## Reliability and retry behavior

Transient provider failures are classified explicitly. Retriable HTTP status codes are 408, 429, 500, 502, 503, and 504, and retryable network exceptions include timeout and connection errors. The pipeline makes at most three total attempts, with approximately two-second and four-second exponential delays plus bounded jitter. Non-retriable errors fail immediately.

Each retry attempt creates a fresh pipeline, Runner, session service, and session, while remaining inside one event loop owned by the CLI entry point. Provider failures are not intentionally triggered in the demo video; the behavior is covered by automated tests and documentation.

## Evaluation and testing

The validated suite contains 207 automated tests. Validation also recorded:

- Python 3.14 development validation passed.
- Clean Python 3.11 validation passed.
- `compileall` passed.
- `pip check` passed.
- Official MCP client validation passed.
- Controlled live Gemini CLI execution passed.
- All four agent completion messages appeared exactly once.
- Continuity-brief sections appeared in the required order.
- No tracked secrets were detected.

The automated tests are network-free and key-free. They mock provider-backed infrastructure where needed and focus on configuration, tools, CLI structure, ADK orchestration boundaries, retry behavior, MCP registration, MCP dispatch, and sanitized error handling.

## Results

PAIOS-Lite demonstrates that a small, local multi-agent workflow can turn scattered project context into a useful next-session handoff. The output is practical rather than decorative: it tells the developer the current state, proposes an ordered plan, surfaces supporting notes, and converts that into next actions.

The implementation also demonstrates that the same local tool layer can support both the agent pipeline and MCP stdio access without duplicating tool logic.

## Course concepts demonstrated

This project demonstrates:

- Google ADK
- multi-agent system
- sequential orchestration
- tool-enabled agents
- shared session state
- MCP stdio server
- security and error sanitization
- retry and exponential backoff
- reproducible dependency management

## Limitations

PAIOS-Lite requires a configured model provider and API credentials unless a supported local no-key model path is used. Generated prose may vary between runs. Project context must be supplied through the CLI. Session state is in memory for each attempt and is not saved as durable memory. The project has no graphical interface and no hosted service. Retry handles selected transient failures, not every possible provider condition.

## Future improvements

Future work could add optional persistent local memory, richer repository indexing, broader MCP client integration, configurable agent pipelines, additional deterministic evaluation fixtures, optional local-model support, and packaging improvements. These are future directions, not current submission claims.

## Repository and demo links

Repository: https://github.com/Bvega/paios-lite-capstone

Video: Coming before submission

Kaggle project: Added during final submission

Submission media includes an architecture diagram, CLI success screenshot, continuity-brief screenshot, MCP tool-discovery screenshot, sanitized-error screenshot, test-suite screenshot, and demonstration video storyboard.
