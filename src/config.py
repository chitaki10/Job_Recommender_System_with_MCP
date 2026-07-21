import os
from dataclasses import dataclass


class ConfigError(Exception):
    """Raised when required configuration (API keys) is missing."""


@dataclass(frozen=True)
class Config:
    groq_api_key: str
    apify_api_token: str
    log_level: str


def _load_secrets() -> dict:
    """Returns a secrets-like mapping: Streamlit secrets if available, else {}."""
    try:
        import streamlit as st
        return dict(st.secrets)
    except Exception:
        from dotenv import load_dotenv
        load_dotenv()
        return {}


def load_config() -> Config:
    """Loads and validates required configuration.

    Checks Streamlit secrets first (works on Streamlit Cloud), falls back to
    a .env file / process environment variables (works locally and for the
    standalone MCP server). Raises ConfigError if a required key is missing.
    """
    secrets = _load_secrets()

    def get(name: str) -> str | None:
        value = secrets.get(name) if secrets else None
        return value or os.getenv(name)

    groq_api_key = get("GROQ_API_KEY")
    apify_api_token = get("APIFY_API_TOKEN")
    log_level = os.getenv("LOG_LEVEL", "INFO")

    missing = [
        name
        for name, value in [("GROQ_API_KEY", groq_api_key), ("APIFY_API_TOKEN", apify_api_token)]
        if not value
    ]
    if missing:
        raise ConfigError(
            f"Missing required configuration: {', '.join(missing)}. "
            "Set them as environment variables, in a .env file, or in Streamlit secrets."
        )

    return Config(groq_api_key=groq_api_key, apify_api_token=apify_api_token, log_level=log_level)
