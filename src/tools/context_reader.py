"""Local file tools for the Memory Agent.

All functions are pure Python — no LLM calls, no network I/O.
Paths are resolved and validated before any filesystem access.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

_MAX_FILE_BYTES = 8_000  # truncate large files to keep prompts manageable

_PRIORITY_FILES = (
    "README.md",
    "README.rst",
    "README.txt",
    "CHANGELOG.md",
    "TODO.md",
    "NOTES.md",
    "pyproject.toml",
    "package.json",
    "Makefile",
)


def _resolve_safe(path: str) -> Path:
    """Return a resolved absolute Path after basic validation.

    Raises ValueError for empty strings, null bytes, or non-existent paths.
    """
    if not path or "\x00" in path:
        raise ValueError(f"Invalid path: {path!r}")
    resolved = Path(path).resolve()
    if not resolved.exists():
        raise ValueError(f"Path does not exist: {path!r}")
    return resolved


def read_project_context(path: str) -> str:
    """Return a structured text summary of the project at *path*.

    Accepts either a directory (scans top-level files) or a single file
    (returns its content directly). The path must exist locally.
    """
    root = _resolve_safe(path)

    # Single-file shortcut — useful for the sample_project_context.md fixture
    if root.is_file():
        text = root.read_text(encoding="utf-8", errors="replace")
        return f"## File: {root.name}\n\n{text}"

    sections: list[str] = [f"## Project root: {root}\n"]

    # Directory listing (dirs first, then files, alphabetical within each)
    entries = sorted(root.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
    listing = "\n".join(
        f"{'[dir]  ' if e.is_dir() else '[file] '}{e.name}" for e in entries
    )
    sections.append(f"### Top-level contents\n\n{listing}\n")

    # Read key files if present
    for name in _PRIORITY_FILES:
        candidate = root / name
        if candidate.is_file():
            raw = candidate.read_text(encoding="utf-8", errors="replace")
            body = raw[:_MAX_FILE_BYTES]
            if len(raw) > _MAX_FILE_BYTES:
                body += "\n\n[... truncated ...]"
            sections.append(f"### {name}\n\n{body}\n")

    # Collect TODO / FIXME markers (up to 20, skipping cache dirs)
    todos: list[str] = []
    _SKIP = {".git", ".venv", "venv", "__pycache__", "node_modules", ".pytest_cache"}
    for ext in ("*.py", "*.md", "*.txt"):
        for fpath in root.rglob(ext):
            if _SKIP.intersection(fpath.parts):
                continue
            try:
                for lineno, line in enumerate(
                    fpath.read_text(encoding="utf-8", errors="replace").splitlines(), 1
                ):
                    if "TODO" in line or "FIXME" in line:
                        rel = fpath.relative_to(root)
                        todos.append(f"  {rel}:{lineno}: {line.strip()}")
                        if len(todos) >= 20:
                            break
            except OSError:
                continue
            if len(todos) >= 20:
                break

    if todos:
        sections.append("### Open TODOs / FIXMEs\n\n" + "\n".join(todos) + "\n")

    return "\n".join(sections)


def get_git_log(path: str, n: int = 10) -> str:
    """Return the last *n* git commit one-liners from the repo at *path*.

    Falls back gracefully when git is unavailable or the directory is not a
    repo. The path must exist locally.
    """
    root = _resolve_safe(path)
    if root.is_file():
        root = root.parent

    try:
        result = subprocess.run(
            [
                "git", "-C", str(root),
                "log", f"-{n}",
                "--pretty=format:%h  %ad  %s",
                "--date=short",
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode != 0:
            return f"(git log unavailable: {result.stderr.strip() or 'not a git repo'})"
        return result.stdout.strip() or "(no commits found)"
    except FileNotFoundError:
        return "(git not found on PATH)"
    except subprocess.TimeoutExpired:
        return "(git log timed out)"
