"""Tests for src/tools/context_reader.py.

All tests are pure Python — no LLM calls, no network I/O, no API key needed.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from src.tools.context_reader import get_git_log, read_project_context

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
