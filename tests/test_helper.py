from unittest.mock import MagicMock

import pytest

import src.helper as helper
from src.helper import JobFetchError, LLMError, ask_groq, extract_job_title, fetch_linkedin_jobs, fetch_naukri_jobs


def test_ask_groq_returns_content_on_success(monkeypatch):
    mock_message = MagicMock(content="hello")
    mock_choice = MagicMock(message=mock_message)
    mock_response = MagicMock(choices=[mock_choice])
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = mock_response
    monkeypatch.setattr(helper, "client", mock_client)

    assert ask_groq("prompt") == "hello"


def test_ask_groq_raises_llm_error_on_failure(monkeypatch):
    mock_client = MagicMock()
    mock_client.chat.completions.create.side_effect = RuntimeError("boom")
    monkeypatch.setattr(helper, "client", mock_client)

    with pytest.raises(LLMError):
        ask_groq("prompt")


def test_extract_job_title_strips_whitespace(monkeypatch):
    monkeypatch.setattr(helper, "ask_groq", lambda prompt, max_tokens=20: "  Senior Backend Engineer  \n")

    assert extract_job_title("some resume text") == "Senior Backend Engineer"


def test_fetch_linkedin_jobs_returns_items_on_success(monkeypatch):
    mock_dataset = MagicMock()
    mock_dataset.iterate_items.return_value = iter([{"title": "Engineer"}])
    mock_apify = MagicMock()
    mock_apify.actor.return_value.call.return_value = {"defaultDatasetId": "abc"}
    mock_apify.dataset.return_value = mock_dataset
    monkeypatch.setattr(helper, "apify_client", mock_apify)

    assert fetch_linkedin_jobs("python developer") == [{"title": "Engineer"}]


def test_fetch_linkedin_jobs_raises_job_fetch_error_on_failure(monkeypatch):
    mock_apify = MagicMock()
    mock_apify.actor.return_value.call.side_effect = RuntimeError("apify down")
    monkeypatch.setattr(helper, "apify_client", mock_apify)

    with pytest.raises(JobFetchError):
        fetch_linkedin_jobs("python developer")


def test_fetch_naukri_jobs_raises_job_fetch_error_on_failure(monkeypatch):
    mock_apify = MagicMock()
    mock_apify.actor.return_value.call.side_effect = RuntimeError("apify down")
    monkeypatch.setattr(helper, "apify_client", mock_apify)

    with pytest.raises(JobFetchError):
        fetch_naukri_jobs("python developer")
