"""Tests for src/tools/context_reader.py and src/tools/note_searcher.py.

All tests are pure Python — no LLM calls, no network I/O, no API key needed.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from src.tools.context_reader import get_git_log, read_project_context
from src.tools.note_searcher import search_notes

# Resolve project root relative to this test file
_PROJECT_ROOT = str(Path(__file__).parent.parent.resolve())
_SAMPLE_FILE = str(
    Path(__file__).parent.parent / "examples" / "sample_project_context.md"
)


# ── read_project_context ────────────────────────────────────────────────────


def test_read_sample_file_returns_string():
    result = read_project_context(_SAMPLE_FILE)
    assert isinstance(result, str)
    assert len(result) > 0


def test_read_sample_file_contains_filename():
    result = read_project_context(_SAMPLE_FILE)
    assert "sample_project_context" in result


def test_read_sample_file_contains_todo_markers():
    result = read_project_context(_SAMPLE_FILE)
    # The sample fixture includes TODO items
    assert "TODO" in result or "FIXME" in result


def test_read_directory_returns_top_level_listing():
    result = read_project_context(_PROJECT_ROOT)
    assert "Project root" in result
    assert "src" in result


def test_read_directory_finds_readme():
    result = read_project_context(_PROJECT_ROOT)
    assert "README" in result


def test_read_nonexistent_path_raises():
    with pytest.raises(ValueError, match="does not exist"):
        read_project_context("/tmp/paios_lite_nonexistent_xyz_12345")


def test_read_empty_path_raises():
    with pytest.raises(ValueError, match="Invalid path"):
        read_project_context("")


def test_read_null_byte_path_raises():
    with pytest.raises(ValueError, match="Invalid path"):
        read_project_context("some/path\x00evil")


# ── get_git_log ─────────────────────────────────────────────────────────────


def test_git_log_returns_string():
    result = get_git_log(_PROJECT_ROOT)
    assert isinstance(result, str)
    assert len(result) > 0


def test_git_log_contains_commit_hash():
    result = get_git_log(_PROJECT_ROOT, n=3)
    # Each line should start with a short hash (7 hex chars)
    first_line = result.strip().splitlines()[0]
    short_hash = first_line.split()[0]
    assert len(short_hash) == 7
    assert all(c in "0123456789abcdef" for c in short_hash)


def test_git_log_respects_n_limit():
    result = get_git_log(_PROJECT_ROOT, n=1)
    lines = [ln for ln in result.strip().splitlines() if ln.strip()]
    assert len(lines) == 1


def test_git_log_nonexistent_path_raises():
    with pytest.raises(ValueError, match="does not exist"):
        get_git_log("/tmp/paios_lite_nonexistent_xyz_12345")


def test_git_log_on_file_uses_parent_dir():
    # Should resolve to the project root and return valid log
    result = get_git_log(_SAMPLE_FILE, n=1)
    assert isinstance(result, str)
    assert len(result) > 0


# ── search_notes ─────────────────────────────────────────────────────────────

_EXAMPLES_DIR = str(Path(__file__).parent.parent / "examples")
_CONFIG_PY = str(Path(__file__).parent.parent / "src" / "config.py")


def test_search_notes_returns_string():
    result = search_notes("TODO", _SAMPLE_FILE)
    assert isinstance(result, str)
    assert len(result) > 0


def test_search_notes_file_finds_match():
    result = search_notes("TODO", _SAMPLE_FILE)
    # sample fixture contains TODO items; output must include them verbatim
    assert "TODO" in result


def test_search_notes_result_contains_line_numbers():
    import re
    result = search_notes("TODO", _SAMPLE_FILE)
    # line numbers appear as right-justified integers followed by a colon
    assert re.search(r"\s+\d+:", result)


def test_search_notes_single_file_shows_filename():
    result = search_notes("TODO", _SAMPLE_FILE)
    assert "sample_project_context" in result


def test_search_notes_case_insensitive():
    result_lower = search_notes("todo", _SAMPLE_FILE)
    result_upper = search_notes("TODO", _SAMPLE_FILE)
    # Both queries must agree on whether matches exist
    has_lower = "No matches" not in result_lower
    has_upper = "No matches" not in result_upper
    assert has_lower == has_upper


def test_search_notes_file_no_match():
    result = search_notes("xyzzy_paios_not_present_99999", _SAMPLE_FILE)
    assert "No matches" in result


def test_search_notes_empty_query_returns_message():
    result = search_notes("", _SAMPLE_FILE)
    assert "empty" in result.lower()
    # must not produce a results header
    assert "## Search results" not in result


def test_search_notes_whitespace_query_returns_message():
    result = search_notes("   ", _SAMPLE_FILE)
    assert "empty" in result.lower()


def test_search_notes_missing_path_raises():
    with pytest.raises(ValueError, match="does not exist"):
        search_notes("TODO", "/tmp/paios_lite_nonexistent_xyz_99999")


def test_search_notes_empty_path_raises():
    with pytest.raises(ValueError, match="Invalid path"):
        search_notes("TODO", "")


def test_search_notes_null_byte_path_raises():
    with pytest.raises(ValueError, match="Invalid path"):
        search_notes("TODO", "some/path\x00evil")


def test_search_notes_unsupported_file_returns_message():
    # A .py file is not a Markdown file — must return a descriptive message
    result = search_notes("TODO", _CONFIG_PY)
    assert "not a Markdown file" in result


def test_search_notes_directory_finds_match():
    result = search_notes("TODO", _EXAMPLES_DIR)
    assert "TODO" in result


def test_search_notes_directory_no_markdown_files(tmp_path):
    (tmp_path / "notes.py").write_text("# python file\n")
    (tmp_path / "data.txt").write_text("some text\n")
    result = search_notes("anything", str(tmp_path))
    assert "no Markdown files" in result


def test_search_notes_directory_no_matches(tmp_path):
    (tmp_path / "notes.md").write_text("Hello world, nothing special here.\n")
    result = search_notes("xyzzy_paios_not_present_99999", str(tmp_path))
    assert "No matches" in result


def test_search_notes_directory_sorted_order(tmp_path):
    # Create files in reverse alphabetical order to confirm sorting is applied
    (tmp_path / "zebra.md").write_text("target keyword\n")
    (tmp_path / "alpha.md").write_text("target keyword\n")
    (tmp_path / "middle.md").write_text("target keyword\n")
    result = search_notes("target", str(tmp_path))
    pos_alpha = result.find("alpha.md")
    pos_middle = result.find("middle.md")
    pos_zebra = result.find("zebra.md")
    assert 0 <= pos_alpha < pos_middle < pos_zebra


def test_search_notes_unreadable_file_is_skipped(tmp_path, monkeypatch):
    """An unreadable .md file is silently skipped; result reports no matches."""
    locked = tmp_path / "locked.md"
    locked.write_text("target keyword\n")

    original_read_text = Path.read_text
    locked_resolved = locked.resolve()

    def patched_read_text(self, *args, **kwargs):
        if self.resolve() == locked_resolved:
            raise PermissionError(f"Permission denied: {self}")
        return original_read_text(self, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", patched_read_text)

    result = search_notes("target", str(locked))

    assert isinstance(result, str)
    assert "No matches" in result
