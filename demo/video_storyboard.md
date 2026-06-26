# Video Storyboard

Planned runtime: 4:40, leaving a 20-second buffer below the five-minute limit and staying within the 4:30-4:50 target.

| Time | Duration | Visual | Presenter action | Narration goal | Asset/command | Editing note |
|---|---:|---|---|---|---|---|
| 0:00 | 0:10 | Static title card | Start on concise title text: "PAIOS-Lite: Local Project Continuity Assistant" | Establish project name and local continuity purpose. | narration only | Simple static card, no vendor logos. |
| 0:10 | 0:35 | Architecture SVG | Show the pipeline and state flow. | Explain four Google ADK agents, sequential orchestration, shared state, and final brief. | `docs/assets/architecture.svg` | Pan or zoom only if labels remain crisp. |
| 0:45 | 0:10 | Repository overview in VS Code | Show README top section and project tree briefly. | Connect the architecture to the repository evidence. | `README.md` | Keep zoom readable; avoid showing hidden files. |
| 0:55 | 0:15 | Live terminal | Type or reveal the CLI command. | Introduce the demo fixture as a stable sample project context. | `python -m paios_lite --context examples/sample_project_context.md` | Cut dead time before model output if needed. |
| 1:10 | 0:25 | Live terminal or static screenshot | Show the four completion lines. | Point out Memory Agent, Planner Agent, Research Agent, and Executor Agent completion. | `docs/assets/cli-success.png` | Use screenshot if live output timing is slow. |
| 1:35 | 0:40 | Live terminal or static screenshot | Scroll through final brief sections. | Highlight Current State, Plan, Research Notes, and Next Actions without relying on exact generated prose. | `docs/assets/continuity-brief.png` | Crop only enough to keep section headings legible. |
| 2:15 | 0:25 | Static screenshot or live terminal | Show MCP tool discovery. | Explain MCP as a stdio access path to the same five local tools. | `docs/assets/mcp-tools-list.png`; `/tmp/paios_mcp_list_tools.py` | Show count of 5 and tool names clearly. |
| 2:40 | 0:25 | Static screenshot or live terminal | Show sanitized invalid-path result. | Demonstrate marked error, sanitized public message, and no private path echo. | `docs/assets/mcp-invalid-path.png`; `/tmp/paios_mcp_invalid_path.py` | Do not show the temporary script source. |
| 3:05 | 0:35 | Architecture SVG or README security section | Point to security and retry bullets. | Explain environment-only credentials, `.env` ignored by Git, path validation, no `shell=True`, sanitized errors, and 3-attempt backoff. | `docs/assets/architecture.svg`; `README.md` | Do not trigger a provider failure live. |
| 3:40 | 0:35 | Static screenshot or live terminal | Show test evidence. | State that validation includes 207 passing tests, Python 3.14 and clean Python 3.11 runs, MCP client checks, live Gemini CLI validation, secret checks, and dependency checks. | `docs/assets/test-suite.png`; `PYTHONWARNINGS=ignore .venv/bin/pytest tests/ -q` | If running tests live, use the `.env` isolation command from the script. |
| 4:15 | 0:25 | Static closing card | End with one concise value statement. | Close on safe, local, actionable handoff for the next development session. | narration only | End at 4:40; hard cap for edit is 04:50. |

## Screen-recording settings

- Resolution: 1920 × 1080
- Frame rate: 30 fps
- Terminal font: 14-16 pt monospace
- Terminal width: approximately 110-120 columns
- Capture area: one focused window or clean full screen
- Notifications: disabled
- Browser/account surfaces: hidden unless absolutely needed

## Audio guidance

- Record in a quiet room with a consistent microphone position.
- Keep narration close to the timed script.
- Leave short pauses after major scene changes for easier editing.
- Re-record any section that includes hesitation around credentials, private paths, or unsupported claims.

## Editing guidance

- Planned total runtime is 4:40; final edit must be no more than 4:50.
- Cut waiting time from live model and test runs.
- Use existing screenshots when live terminal output is slow or visually noisy.
- Do not add vendor logos or unsupported product claims.
- Do not include raw traceback output, `.env` contents, private sentinel paths, or terminal history unrelated to the demo.

## Caption guidance

- Caption the four agent names exactly as shown in the project: Memory Agent, Planner Agent, Research Agent, Executor Agent.
- Caption the four final brief sections: Current State, Plan, Research Notes, Next Actions.
- Caption the MCP tool count as five local tools.
- Caption validation as "207 passing tests" or "`207 passed`".
- Keep captions short enough to read without covering terminal output.

## Export guidance

Recommended export:

```text
1920 × 1080
30 fps
H.264 MP4
```

Verify the final platform upload against the official submission instructions before publication.

## Final quality-control checklist

- Runtime is 4:50 or less.
- Audio is clear and synchronized.
- Text is readable at 1080p.
- No credentials, `.env` contents, tokens, private paths, or account details appear.
- No unsupported claims about deployment, web UI, REST API, database, or persistent memory appear.
- Existing assets are used accurately: `docs/assets/architecture.svg`, `docs/assets/cli-success.png`, `docs/assets/continuity-brief.png`, `docs/assets/mcp-tools-list.png`, `docs/assets/mcp-invalid-path.png`, and `docs/assets/test-suite.png`.
- Final upload target is checked against the official submission instructions.
