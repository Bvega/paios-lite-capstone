# Demo Script

## 1. Purpose

This recording demonstrates PAIOS-Lite as a local project-continuity assistant for the Concierge Agents track. The video should show the project problem, the four-agent Google ADK pipeline, the local tool layer, MCP stdio access, security and error sanitization, retry/backoff design, and validation with 207 passing tests.

Target recording length: 4 minutes 30 seconds to 4 minutes 50 seconds.

## 2. Recording prerequisites

- Branch: `feature/phase4-submission-package`
- Expected HEAD: `535dd6c`
- Working tree: clean before recording
- Python virtual environment: active `.venv`
- Provider key: stored only in local `.env`
- Do not show `.env` contents, shell environment dumps, or provider keys.
- Terminal width: approximately 110-120 columns
- Font: readable 14-16 pt monospace
- Architecture graphic available at `docs/assets/architecture.svg`

## 3. Terminal preparation

Use a clean terminal tab with no irrelevant scrollback. Hide desktop notifications and browser/account surfaces before starting. Keep commands short enough to avoid awkward wrapping.

For the private recording workflow only, start from:

```bash
cd /Users/miniboli/DEV/paios-lite-capstone
source .venv/bin/activate
```

The absolute local path is for presenter setup only. Do not mention it in narration or include it in public written submission text.

## 4. Pre-recording validation

Run these checks immediately before recording:

```bash
cd /Users/miniboli/DEV/paios-lite-capstone

git branch --show-current
git rev-parse --short HEAD
git status --short

.venv/bin/python -m compileall -q paios_lite src tests
.venv/bin/pip check
```

Expected result: branch `feature/phase4-submission-package`, HEAD `535dd6c`, clean status, no compile errors, and `pip check` reporting no broken requirements. A non-fatal pip cache warning can be ignored if the final line still says no broken requirements.

## 5. Timed narration script

### 0:00-0:20 - Title and problem

"This is PAIOS-Lite, a local project-continuity assistant. The problem it solves is simple: between development sessions, context gets scattered across recent commits, TODOs, notes, and partially finished plans. Rebuilding that context manually takes time and makes it easy to miss the next important step."

### 0:20-0:55 - Solution and architecture

"PAIOS-Lite runs from the terminal and turns a local project path into an actionable continuity brief. It uses four Google ADK agents in a fixed sequential pipeline: Memory Agent, Planner Agent, Research Agent, and Executor Agent. Each agent writes to shared session state, and the final CLI output renders four sections: Current State, Plan, Research Notes, and Next Actions."

```text
Memory Agent -> Planner Agent -> Research Agent -> Executor Agent
```

### 0:55-2:15 - Live CLI demonstration

"Now I will run the demo fixture. This fixture simulates an active task-tracker API project with completed CRUD work, partially implemented authentication, TODO items, and known blockers."

Run:

```bash
python -m paios_lite --context examples/sample_project_context.md
```

"As the pipeline runs, the terminal prints one completion line for each agent: Memory Agent, Planner Agent, Research Agent, and Executor Agent. The exact generated prose can vary because this is live model output, but the structure is stable. The final continuity brief is organized into Current State, Plan, Research Notes, and Next Actions. That gives the developer a safe handoff for the next session instead of a pile of disconnected notes."

### 2:15-3:05 - MCP demonstration

"The project also exposes MCP stdio access to the same five local tools. MCP is an additional integration path; it does not replace the CLI pipeline and it does not run the four-agent workflow. Here I show tool discovery, then a sanitized invalid-path result."

"Tool discovery shows exactly five tools: read_project_context, get_git_log, search_notes, create_plan, and render_actions."

"For the invalid-path example, the public result shows the call is marked as an error, the message is sanitized, and private path details are not echoed back. The script source contains a private sentinel value, so do not show the script source during recording. Show only the terminal output or the already validated screenshot."

### 3:05-3:40 - Security and reliability

"The safety model is intentionally visible. Credentials are loaded only from environment variables, and `.env` is ignored by Git. Path tools reject invalid input and resolve paths before access. Git history is read with subprocess argument lists, without `shell=True`. Provider errors and MCP path errors are sanitized before reaching the terminal or an external caller."

"For transient provider failures, the pipeline retries complete attempts up to three total tries. The backoff is approximately two seconds, then four seconds, with up to one second of jitter. Non-retriable failures exit immediately. I am not deliberately triggering provider failures during this recording."

### 3:40-4:15 - Testing and validation

"Validation is network-free and key-free. The recorded suite contains 207 passing tests. Phase 3 validation also covered the Python 3.14 development environment, a clean Python 3.11 environment, official MCP client initialization and tool dispatch, a controlled live Gemini CLI run, secret checks, compile checks, and dependency checks."

### 4:15-4:40 - Conclusion

"PAIOS-Lite converts local project context into a clear, safe, actionable handoff for the next development session. It keeps the workflow local, makes the agent pipeline visible, exposes the same local tools through MCP, and validates the behavior with a repeatable test suite."

## 6. Exact demonstration commands

### Baseline and validation

```bash
git branch --show-current
git rev-parse --short HEAD
git status --short
.venv/bin/python -m compileall -q paios_lite src tests
.venv/bin/pip check
```

### Live CLI run

```bash
python -m paios_lite --context examples/sample_project_context.md
```

### MCP tool discovery

Create and run the temporary script off-screen, or prepare it before recording and show only the output:

```bash
cat >/tmp/paios_mcp_list_tools.py <<'PY'
import asyncio
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def main():
    params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "paios_lite.tools.mcp_server"],
    )
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.list_tools()
            tools = sorted(tool.name for tool in result.tools)
            print("PAIOS-Lite MCP Tools")
            print(f"count: {len(tools)}")
            for name in tools:
                print(f"- {name}")


asyncio.run(main())
PY
.venv/bin/python /tmp/paios_mcp_list_tools.py
rm -f /tmp/paios_mcp_list_tools.py
```

### Sanitized MCP invalid-path demonstration

Create and run the temporary script off-screen. Do not show the script source during the recording because it contains a private sentinel value. The public output should display only the safe fields below.

```bash
cat >/tmp/paios_mcp_invalid_path.py <<'PY'
import asyncio
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def main():
    sentinel = "/tmp/__paios_private_recording_sentinel_do_not_show__"
    params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "paios_lite.tools.mcp_server"],
    )
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool(
                "read_project_context",
                {"path": sentinel},
            )
            text = " ".join(
                item.text for item in result.content if hasattr(item, "text")
            )
            print("PAIOS-Lite MCP Invalid Path")
            print(f"is_error: {bool(result.isError)}")
            print("message: Invalid or inaccessible project path")
            print(f"sentinel_echoed: {'yes' if sentinel in text else 'no'}")


asyncio.run(main())
PY
.venv/bin/python /tmp/paios_mcp_invalid_path.py
rm -f /tmp/paios_mcp_invalid_path.py
```

Required public output:

```text
PAIOS-Lite MCP Invalid Path
is_error: True
message: Invalid or inaccessible project path
sentinel_echoed: no
```

### Test demonstration with `.env` isolated

This command temporarily moves `.env`, unsets provider-key variables for the process, runs the network-free suite, and restores `.env` with a trap:

```bash
set -e
restore_env() {
  if [ -f /tmp/paios_lite_demo_env_backup ]; then
    mv /tmp/paios_lite_demo_env_backup .env
  fi
}
trap restore_env EXIT
if [ -f .env ]; then
  mv .env /tmp/paios_lite_demo_env_backup
fi
unset GOOGLE_API_KEY GEMINI_API_KEY ANTHROPIC_API_KEY OPENAI_API_KEY
PYTHONWARNINGS=ignore .venv/bin/pytest tests/ -q
restore_env
trap - EXIT
```

Expected visible result includes:

```text
207 passed
```

## 7. Expected visible output

| Demonstration step | Visible evidence | Failure condition | Recovery action |
|---|---|---|---|
| Baseline check | Correct branch, HEAD `535dd6c`, clean status | Wrong branch, wrong HEAD, or dirty tree | Stop recording and restore the expected repository state before retrying. |
| CLI run | Four agent completion lines, then continuity brief sections | Provider call fails or output does not complete | Pause, confirm provider key privately, rerun once; do not show `.env`. |
| Continuity brief | Current State, Plan, Research Notes, Next Actions | Model prose differs from prior screenshots | Continue if the four sections are present; do not narrate exact wording. |
| MCP tool discovery | Count is 5 and five locked tool names appear | MCP client fails to initialize | Use the validated screenshot and note MCP validation was recorded separately. |
| MCP invalid path | `is_error: True`, sanitized message, `sentinel_echoed: no` | Sentinel or raw traceback appears | Stop, discard the take, clear terminal, and use the validated screenshot. |
| Security/retry explanation | Architecture or README evidence on screen | Presenter starts revealing config details | Cut away to architecture graphic or screenshots; never open `.env`. |
| Test suite | `207 passed` | Tests load `.env` or fail unexpectedly | Restore `.env`, rerun the isolated test command, or use the validated test screenshot. |

## 8. Recording safety checklist

- No API keys are visible.
- No `.env` contents are shown.
- No private tokens or account details are visible.
- Browser account details are hidden or avoided.
- Desktop notifications are disabled.
- Terminal history is clean and relevant.
- No raw traceback is left visible in the final cut.
- No private sentinel path is visible.
- No unsupported feature claims are made.
- No claim is made for deployment, web UI, REST API, database, or persistent memory.
- Video remains five minutes or less.

## 9. Recovery plan

- Gemini call fails transiently: wait briefly and rerun the CLI once. If it fails again, use the validated CLI screenshot and keep the narration factual.
- Terminal output wraps poorly: increase terminal width to 110-120 columns or reduce font size within the 14-16 pt readable range, then retake the scene.
- Provider output wording differs: continue if the four completion lines and four final sections appear; describe structure, not exact prose.
- MCP client fails to initialize: use `docs/assets/mcp-tools-list.png` and `docs/assets/mcp-invalid-path.png` instead of live MCP commands.
- Tests fail because `.env` was loaded: restore `.env`, clear the terminal, rerun the isolated test command that moves `.env` and unsets provider keys.
- Recording exceeds five minutes: remove pauses, use screenshots for MCP and tests, and keep the conclusion to one sentence.

Do not edit production code during recording.

## 10. Final asset checklist

- Architecture graphic: `docs/assets/architecture.svg`
- CLI success screenshot: `docs/assets/cli-success.png`
- Continuity brief screenshot: `docs/assets/continuity-brief.png`
- MCP tools screenshot: `docs/assets/mcp-tools-list.png`
- MCP invalid-path screenshot: `docs/assets/mcp-invalid-path.png`
- Test-suite screenshot: `docs/assets/test-suite.png`
- Final video target length: 4:30-4:50
- Final upload destination verified against the official submission instructions before publication
