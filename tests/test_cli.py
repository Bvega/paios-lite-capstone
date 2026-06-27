"""CLI smoke tests for PAIOS-Lite.

All tests invoke `python -m paios_lite` as a subprocess. No API key is
required because each test exercises a failure mode that exits before any
LLM call:
  - missing --context flag  → argparse exits 2
  - non-existent path       → path guard exits 1
  - valid path, no API key  → config guard exits 1
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

_PYTHON = sys.executable
_REPO_ROOT = Path(__file__).parent.parent.resolve()
_SAMPLE_FILE = str(_REPO_ROOT / "examples" / "sample_project_context.md")


def _run(*args: str, extra_env: dict[str, str] | None = None) -> subprocess.CompletedProcess:
    """Run paios_lite as a subprocess with a sanitized environment."""
    env = dict(os.environ)
    # Keep provider keys explicitly empty so load_dotenv() cannot refill them.
    env["GOOGLE_API_KEY"] = ""
    env["ANTHROPIC_API_KEY"] = ""
    env["OPENAI_API_KEY"] = ""
    if extra_env:
        env.update(extra_env)
    return subprocess.run(
        [_PYTHON, "-m", "paios_lite", *args],
        capture_output=True,
        text=True,
        env=env,
        cwd=str(_REPO_ROOT),
        timeout=30,
    )


# ---------------------------------------------------------------------------
# Argument-parsing errors
# ---------------------------------------------------------------------------


def test_cli_no_context_flag_exits_2():
    """Omitting --context causes argparse to exit with code 2."""
    result = _run()
    assert result.returncode == 2
    assert "--context" in result.stderr or "usage" in result.stderr.lower()


# ---------------------------------------------------------------------------
# Path-guard errors (exit 1 before any LLM call)
# ---------------------------------------------------------------------------


def test_cli_nonexistent_path_exits_1():
    """A path that does not exist on disk exits 1 with a clear message."""
    result = _run("--context", "/tmp/paios_lite_nonexistent_smoke_xyz_99999")
    assert result.returncode == 1
    combined = result.stdout + result.stderr
    assert "does not exist" in combined.lower() or "error" in combined.lower()


# ---------------------------------------------------------------------------
# Config-guard errors (exit 1 before any LLM call)
# ---------------------------------------------------------------------------


def test_cli_no_api_key_exits_1():
    """Valid path but no provider API key exits 1 at the config guard."""
    result = _run("--context", _SAMPLE_FILE, extra_env={"LLM_MODEL": "gemini/gemini-2.0-flash-exp"})
    assert result.returncode == 1
    combined = result.stdout + result.stderr
    assert (
        "GOOGLE_API_KEY" in combined
        or "configuration" in combined.lower()
        or "api key" in combined.lower()
    )


def test_cli_prints_header_before_error():
    """The PAIOS-Lite banner is printed before the config guard fires."""
    result = _run("--context", _SAMPLE_FILE, extra_env={"LLM_MODEL": "gemini/gemini-2.0-flash-exp"})
    assert "PAIOS-Lite" in result.stdout or "Memory Agent" in result.stdout


def test_cli_sample_file_path_exists():
    """The demo fixture used in CLI tests is present in the repository."""
    assert Path(_SAMPLE_FILE).is_file()
