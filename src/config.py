"""Environment configuration for PAIOS-Lite.

Reads LLM_MODEL and the matching provider API key from the environment.
Call validate_config() at startup; it raises EnvironmentError if the
required key is absent so the problem is surfaced before any LLM call.
"""

import os

from dotenv import load_dotenv

load_dotenv()

# Maps the provider prefix (first segment of a LiteLLM model string) to the
# environment variable that must be set. None means no key is required.
_PROVIDER_KEY_MAP: dict[str, str | None] = {
    "gemini": "GOOGLE_API_KEY",
    "google": "GOOGLE_API_KEY",
    "claude": "ANTHROPIC_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
    "ollama": None,
    "openai": "OPENAI_API_KEY",
}

# Bare model name prefixes (no provider/ prefix in the string)
_BARE_MODEL_PREFIXES: list[tuple[str, str]] = [
    ("claude-", "anthropic"),
    ("gemini-", "gemini"),
    ("gpt-", "openai"),
    ("o1-", "openai"),
    ("o3-", "openai"),
]


def _provider_from_model(model: str) -> str:
    """Extract provider from a LiteLLM model string.

    Handles both prefixed ('gemini/gemini-2.0-flash-exp') and bare
    ('claude-3-5-haiku-20241022') model name formats.
    """
    if "/" in model:
        return model.split("/")[0].lower()
    lower = model.lower()
    for prefix, provider in _BARE_MODEL_PREFIXES:
        if lower.startswith(prefix):
            return provider
    return lower  # fall through — unknown provider, no key required


def get_llm_model() -> str:
    """Return the configured LiteLLM model string, reading fresh from env."""
    return os.getenv("LLM_MODEL", "gemini/gemini-2.0-flash-exp")


def validate_config() -> None:
    """Raise EnvironmentError if the required provider API key is absent."""
    model = get_llm_model()
    provider = _provider_from_model(model)
    key_var = _PROVIDER_KEY_MAP.get(provider)
    if key_var is not None and not os.getenv(key_var):
        raise EnvironmentError(
            f"LLM_MODEL='{model}' requires {key_var} to be set.\n"
            "Copy .env.example → .env and add your API key."
        )


# Module-level alias for convenience in logging / display.
# Agent code should call get_llm_model() to pick up runtime env changes.
LLM_MODEL: str = get_llm_model()
