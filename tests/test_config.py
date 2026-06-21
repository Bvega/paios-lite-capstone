"""Tests for src/config.py — env loading and validation.

All tests patch os.environ via monkeypatch so no real API key is needed.
"""

import pytest


def test_get_llm_model_default(monkeypatch):
    monkeypatch.delenv("LLM_MODEL", raising=False)
    from src import config
    assert "gemini" in config.get_llm_model()


def test_get_llm_model_custom(monkeypatch):
    monkeypatch.setenv("LLM_MODEL", "ollama/llama3.2")
    from src import config
    assert config.get_llm_model() == "ollama/llama3.2"


def test_validate_config_raises_when_gemini_key_missing(monkeypatch):
    monkeypatch.setenv("LLM_MODEL", "gemini/gemini-2.0-flash-exp")
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    from src import config
    with pytest.raises(EnvironmentError, match="GOOGLE_API_KEY"):
        config.validate_config()


def test_validate_config_passes_when_gemini_key_present(monkeypatch):
    monkeypatch.setenv("LLM_MODEL", "gemini/gemini-2.0-flash-exp")
    monkeypatch.setenv("GOOGLE_API_KEY", "fake-key-for-test")
    from src import config
    config.validate_config()  # must not raise


def test_validate_config_raises_when_claude_key_missing(monkeypatch):
    monkeypatch.setenv("LLM_MODEL", "claude-3-5-haiku-20241022")
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    from src import config
    with pytest.raises(EnvironmentError, match="ANTHROPIC_API_KEY"):
        config.validate_config()


def test_validate_config_ollama_needs_no_key(monkeypatch):
    monkeypatch.setenv("LLM_MODEL", "ollama/llama3.2")
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    from src import config
    config.validate_config()  # must not raise


def test_validate_config_unknown_provider_passes(monkeypatch):
    # Unknown providers are not blocked — warn but don't raise
    monkeypatch.setenv("LLM_MODEL", "unknown_provider/some-model")
    from src import config
    config.validate_config()  # must not raise
