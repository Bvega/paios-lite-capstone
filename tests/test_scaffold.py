"""Basic scaffold sanity tests."""

from pathlib import Path


def test_readme_exists() -> None:
    assert Path("README.md").exists()


def test_docs_directory_exists() -> None:
    assert Path("docs").is_dir()


def test_src_directory_exists() -> None:
    assert Path("src").is_dir()
