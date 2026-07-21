import pytest

from src.config import Config, ConfigError, load_config


def test_load_config_returns_values_when_present(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "abc")
    monkeypatch.setenv("APIFY_API_TOKEN", "xyz")
    monkeypatch.delenv("LOG_LEVEL", raising=False)

    config = load_config()

    assert config == Config(groq_api_key="abc", apify_api_token="xyz", log_level="INFO")


def test_load_config_raises_config_error_when_missing(monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    monkeypatch.delenv("APIFY_API_TOKEN", raising=False)
    # Block a real local .env from refilling the deleted vars, so this test
    # is deterministic regardless of the machine it runs on.
    monkeypatch.setattr("dotenv.load_dotenv", lambda *args, **kwargs: None)

    with pytest.raises(ConfigError):
        load_config()
