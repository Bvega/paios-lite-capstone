"""Note-search tool for the Research Agent.

Pure local Python — no LLM calls, no network I/O.
Paths are resolved and validated before any filesystem access.
"""

from __future__ import annotations

from pathlib import Path

from src.tools.context_reader import _resolve_safe

_SKIP = {".git", ".venv", "venv", "__pycache__", "node_modules", ".pytest_cache"}
_MAX_LINES_PER_FILE = 20
_MAX_FILES = 200  # safety cap on very large directory trees


def search_notes(query: str, path: str) -> str:
    """Search Markdown files at *path* for lines matching *query*.

    Accepts a single .md file or a directory (searched recursively).
    Matching is case-insensitive. Files are processed in stable sorted order.
    Returns structured text suitable for LLM context.

    Raises ValueError for invalid or missing paths (via _resolve_safe).
    Unreadable files are silently skipped; all other edge cases return a
    descriptive message rather than raising.
    """
    if not query or not query.strip():
        return "(search_notes: query is empty — nothing to search)"

    root = _resolve_safe(path)
    query_lower = query.lower()

    # ── Collect candidate files ────────────────────────────────────────────
    if root.is_file():
        if root.suffix.lower() != ".md":
            return (
                f"(search_notes: {root.name!r} is not a Markdown file"
                " — only .md files are searched)"
            )
        files: list[Path] = [root]
    else:
        files = sorted(
            (
                f
                for f in root.rglob("*.md")
                if not _SKIP.intersection(f.parts)
            ),
            key=lambda p: str(p).lower(),
        )
        if not files:
            return f"(search_notes: no Markdown files found under {str(root)!r})"

    # ── Search ─────────────────────────────────────────────────────────────
    sections: list[str] = [f'## Search results: "{query}" in {str(root)}\n']
    files_searched = 0
    files_matched = 0

    for fpath in files[:_MAX_FILES]:
        files_searched += 1
        try:
            text_lines = fpath.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            continue

        match_lines: list[str] = []
        for lineno, line in enumerate(text_lines, 1):
            if query_lower in line.lower():
                match_lines.append(f"  {lineno:4d}: {line.rstrip()}")
                if len(match_lines) >= _MAX_LINES_PER_FILE:
                    break

        if not match_lines:
            continue

        rel = fpath.relative_to(root) if root.is_dir() else Path(fpath.name)
        block: list[str] = [f"### {rel}\n"]
        block.extend(match_lines)
        if len(match_lines) == _MAX_LINES_PER_FILE:
            block.append(f"  ... (first {_MAX_LINES_PER_FILE} matches shown)")
        sections.append("\n".join(block) + "\n")
        files_matched += 1

    # ── Summary ────────────────────────────────────────────────────────────
    if files_matched == 0:
        sections.append(
            f"No matches found for {query!r} in {files_searched} file(s) searched.\n"
        )
    else:
        sections.append(
            f"{files_searched} file(s) searched, {files_matched} matched.\n"
        )

    return "\n".join(sections)
