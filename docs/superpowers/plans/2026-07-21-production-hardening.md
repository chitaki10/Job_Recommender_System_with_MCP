# Production Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix the job-search query bug, replace crash-on-import/silent-failure error handling with typed exceptions + logging, remove dead code/deps, and add test coverage — per `docs/superpowers/specs/2026-07-21-production-hardening-design.md`.

**Architecture:** `src/config.py` centralizes secret loading and raises `ConfigError`. `src/helper.py` raises `LLMError`/`JobFetchError` on failure (logged via stdlib `logging` before raising) instead of returning fake-shaped data. `app.py` (Streamlit) catches these at UI boundaries and shows friendly messages; `mcp_server.py` lets them propagate so FastMCP reports proper tool errors.

**Tech Stack:** Python 3.12, Streamlit, `mcp[cli]` (FastMCP), Groq SDK, Apify client, pymupdf (`fitz`), `python-dotenv`, uv for packaging, pytest + pytest-mock for tests.

## Global Constraints

- Python `>=3.12` (from `pyproject.toml`).
- Dependency changes go through `uv` (`uv add`/`uv remove`) so `uv.lock` stays consistent — never hand-edit `uv.lock`.
- No new features beyond the spec (no PDF tool on MCP server, no CI/Docker) — YAGNI.
- Tests must not make real network calls (mock Groq/Apify clients).
- Preserve existing public behavior: `ask_groq`, `fetch_linkedin_jobs`, `fetch_naukri_jobs` keep their names/signatures; only their failure behavior changes (raise instead of return sentinel).

---

### Task 1: Dependency & dead-code cleanup

**Files:**
- Delete: `src/job_api.py`
- Delete: `requirements.txt`
- Modify: `pyproject.toml` (via `uv` commands, not hand-edited)
- Modify: `uv.lock` (auto-updated by `uv`)

**Interfaces:**
- Produces: `pytest` and `pytest-mock` available as dev dependencies for Tasks 2-4.

- [ ] **Step 1: Delete dead file and stale manifest**

```bash
git rm src/job_api.py requirements.txt
```

- [ ] **Step 2: Remove unused `pypdf2` dependency**

```bash
uv remove pypdf2
```

Expected: `pyproject.toml`'s `dependencies` list no longer contains `pypdf2`; `uv.lock` updates.

- [ ] **Step 3: Add pytest + pytest-mock as dev dependencies**

```bash
uv add --dev pytest pytest-mock
```

Expected: `pyproject.toml` gains a `[dependency-groups]` (or `[tool.uv]` dev-dependencies) section listing `pytest` and `pytest-mock`; `uv.lock` updates.

- [ ] **Step 4: Sanity check the environment still resolves**

```bash
uv run python -c "import fitz, groq, apify_client; print('ok')"
```

Expected: prints `ok`, no `ModuleNotFoundError`.

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "chore: remove dead job_api.py, stale requirements.txt, unused pypdf2 dep; add pytest"
```

---

### Task 2: Config module with typed `ConfigError`

**Files:**
- Create: `src/config.py`
- Create: `.env.example`
- Create: `tests/__init__.py` (empty, makes `tests` a package so `from src...` imports resolve the same way in every test file)
- Create: `tests/conftest.py`
- Create: `tests/test_config.py`

**Interfaces:**
- Produces: `src.config.ConfigError` (exception), `src.config.Config` (frozen dataclass with fields `groq_api_key: str`, `apify_api_token: str`, `log_level: str`), `src.config.load_config() -> Config`.
- Consumes: nothing from other tasks.

- [ ] **Step 1: Create `tests/__init__.py`**

Empty file.

- [ ] **Step 2: Create `tests/conftest.py` so importing `src.helper`/`mcp_server` later never crashes for lack of real API keys**

```python
import os

os.environ.setdefault("GROQ_API_KEY", "test-groq-key")
os.environ.setdefault("APIFY_API_TOKEN", "test-apify-token")
```

- [ ] **Step 3: Write the failing test**

```python
# tests/test_config.py
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

    with pytest.raises(ConfigError):
        load_config()
```

- [ ] **Step 4: Run test to verify it fails**

Run: `uv run pytest tests/test_config.py -v`
Expected: FAIL/ERROR — `ModuleNotFoundError: No module named 'src.config'`

- [ ] **Step 5: Implement `src/config.py`**

```python
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
        return st.secrets
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
```

- [ ] **Step 6: Run test to verify it passes**

Run: `uv run pytest tests/test_config.py -v`
Expected: 2 passed

- [ ] **Step 7: Create `.env.example`**

```
GROQ_API_KEY=
APIFY_API_TOKEN=
LOG_LEVEL=INFO
```

- [ ] **Step 8: Commit**

```bash
git add src/config.py .env.example tests/__init__.py tests/conftest.py tests/test_config.py
git commit -m "feat: add src/config.py with typed ConfigError, .env.example"
```

---

### Task 3: `src/helper.py` — typed exceptions, logging, job-title extraction

**Files:**
- Modify: `src/helper.py` (entire file)
- Create: `tests/test_helper.py`

**Interfaces:**
- Consumes: `src.config.load_config() -> Config`, `src.config.ConfigError` (Task 2).
- Produces: `src.helper.LLMError` (exception), `src.helper.JobFetchError` (exception), `src.helper.extract_job_title(resume_text: str) -> str`. Keeps existing `extract_text_from_pdf(uploaded_file)`, `ask_groq(prompt, max_tokens=500) -> str`, `fetch_linkedin_jobs(search_query, location="india", rows=60) -> list`, `fetch_naukri_jobs(search_query, location="india", rows=60) -> list` names/signatures — only their failure path changes from "return sentinel" to "raise".

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_helper.py
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_helper.py -v`
Expected: FAIL — `ImportError: cannot import name 'LLMError' from 'src.helper'` (current `helper.py` has no such name yet)

- [ ] **Step 3: Rewrite `src/helper.py`**

```python
import logging

import fitz  # pymupdf
from apify_client import ApifyClient
from groq import Groq

from src.config import load_config

log = logging.getLogger(__name__)


class LLMError(Exception):
    """Raised when the Groq LLM call fails."""


class JobFetchError(Exception):
    """Raised when a job-listing fetch via Apify fails."""


_config = load_config()
client = Groq(api_key=_config.groq_api_key)
apify_client = ApifyClient(_config.apify_api_token)


def extract_text_from_pdf(uploaded_file):
    """Extracts text from an uploaded PDF file."""
    doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()
    return text


def ask_groq(prompt, max_tokens=500):
    """Sends a prompt to Groq LLM and returns the response text."""
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content
    except Exception as e:
        log.exception("Groq LLM call failed")
        raise LLMError(str(e)) from e


def extract_job_title(resume_text: str) -> str:
    """Extracts a single job title/role from resume text, for use as a job-search query."""
    title = ask_groq(
        "Extract ONLY the single most relevant job title for this person's next role, "
        "based on their resume below. Respond with just the job title, nothing else, "
        "no punctuation, no explanation.\n\n" + resume_text,
        max_tokens=20,
    )
    return title.strip()


def fetch_linkedin_jobs(search_query, location="india", rows=60):
    """Fetches LinkedIn jobs via Apify actor."""
    try:
        run_input = {
            "title": search_query,
            "location": location,
            "rows": rows,
            "proxy": {
                "useApifyProxy": True,
                "apifyProxyGroups": ["RESIDENTIAL"],
            },
        }
        run = apify_client.actor("BHzefUZlZRKWxkTck").call(run_input=run_input)
        return list(apify_client.dataset(run["defaultDatasetId"]).iterate_items())
    except Exception as e:
        log.exception("LinkedIn job fetch failed")
        raise JobFetchError(str(e)) from e


def fetch_naukri_jobs(search_query, location="india", rows=60):
    """Fetches Naukri jobs via Apify actor."""
    try:
        run_input = {
            "keyword": search_query,
            "maxJobs": rows,
            "freshness": "all",
            "sortBy": "relevance",
            "experience": "all",
        }
        run = apify_client.actor("wsrn5gy5C4EDeYCcD").call(run_input=run_input)
        return list(apify_client.dataset(run["defaultDatasetId"]).iterate_items())
    except Exception as e:
        log.exception("Naukri job fetch failed")
        raise JobFetchError(str(e)) from e
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_helper.py -v`
Expected: 6 passed

- [ ] **Step 5: Commit**

```bash
git add src/helper.py tests/test_helper.py
git commit -m "refactor: helper.py raises LLMError/JobFetchError instead of returning fake data"
```

---

### Task 4: `mcp_server.py` — drop unused import, validate input, propagate errors

**Files:**
- Modify: `mcp_server.py` (entire file)
- Create: `tests/test_mcp_server.py`

**Interfaces:**
- Consumes: `src.helper.ask_groq`, `src.helper.fetch_linkedin_jobs`, `src.helper.fetch_naukri_jobs` (Task 3). Does NOT import `extract_text_from_pdf` (unused, removed).
- Produces: `mcp_server.get_linkedin_jobs(job_title, location="india") -> list`, `mcp_server.get_naukri_jobs(job_title, location="india") -> list` now raise `ValueError` for blank `job_title` (checked before Task 5's `app.py` needs anything from this file — no dependency).

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_mcp_server.py
import pytest

from mcp_server import get_linkedin_jobs, get_naukri_jobs


def test_get_linkedin_jobs_rejects_blank_job_title():
    with pytest.raises(ValueError):
        get_linkedin_jobs("   ")


def test_get_naukri_jobs_rejects_blank_job_title():
    with pytest.raises(ValueError):
        get_naukri_jobs("")
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_mcp_server.py -v`
Expected: FAIL — no `ValueError` raised (current code calls the fetch function with the blank string)

- [ ] **Step 3: Rewrite `mcp_server.py`**

```python
import logging
import os

from mcp.server.fastmcp import FastMCP

from src.helper import ask_groq, fetch_linkedin_jobs, fetch_naukri_jobs

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))

mcp = FastMCP("Job Recommender")


@mcp.tool()
def get_linkedin_jobs(job_title: str, location: str = "india") -> list:
    """Fetch live LinkedIn job listings by job title."""
    if not job_title or not job_title.strip():
        raise ValueError("job_title must not be empty")
    return fetch_linkedin_jobs(job_title, location)


@mcp.tool()
def get_naukri_jobs(job_title: str, location: str = "india") -> list:
    """Fetch live Naukri job listings by job title."""
    if not job_title or not job_title.strip():
        raise ValueError("job_title must not be empty")
    return fetch_naukri_jobs(job_title, location)


@mcp.tool()
def analyze_resume(resume_summary: str) -> str:
    """Analyze skill gaps from a compressed resume summary."""
    return ask_groq(f"Identify skill gaps for this profile:\n{resume_summary}", max_tokens=500)


@mcp.tool()
def get_career_roadmap(resume_summary: str) -> str:
    """Generate a 6-month career roadmap from a resume summary."""
    return ask_groq(f"Create a career roadmap for:\n{resume_summary}", max_tokens=500)


if __name__ == "__main__":
    mcp.run()
```

Note: exceptions raised by `fetch_linkedin_jobs`/`fetch_naukri_jobs`/`ask_groq` (`JobFetchError`, `LLMError`) are intentionally NOT caught here — FastMCP converts an uncaught exception raised inside a `@mcp.tool()` function into a proper tool-call error returned to the MCP client, which is the correct behavior (versus the old code path returning a fake successful list).

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_mcp_server.py -v`
Expected: 2 passed

- [ ] **Step 5: Commit**

```bash
git add mcp_server.py tests/test_mcp_server.py
git commit -m "fix: mcp_server drops unused import, validates job_title, lets tool errors propagate"
```

---

### Task 5: `app.py` — fix job-search query bug, per-section error handling

**Files:**
- Modify: `app.py` (entire file)

**Interfaces:**
- Consumes: `src.config.ConfigError` (Task 2), `src.helper.extract_text_from_pdf`, `src.helper.ask_groq`, `src.helper.extract_job_title`, `src.helper.fetch_linkedin_jobs`, `src.helper.fetch_naukri_jobs`, `src.helper.LLMError`, `src.helper.JobFetchError` (Task 3).
- Produces: nothing consumed by later tasks (this is the UI entrypoint).

- [ ] **Step 1: Rewrite `app.py`**

```python
import logging
import os

import streamlit as st

# ─── Page Config (must be the first Streamlit call) ────────────────────────────
st.set_page_config(
    page_title="AI Job Recommender",
    page_icon="💼",
    layout="wide"
)

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))

try:
    from src.config import ConfigError
    from src.helper import (
        JobFetchError,
        LLMError,
        ask_groq,
        extract_job_title,
        extract_text_from_pdf,
        fetch_linkedin_jobs,
        fetch_naukri_jobs,
    )
except ConfigError as e:
    st.error(f"⚠️ Configuration error: {e}")
    st.stop()

# ─── Header ────────────────────────────────────────────────────────────────────
st.title("💼 AI Job Recommender")
st.markdown(
    "> Upload your resume and get **AI-powered** job recommendations, "
    "skill gap analysis, and a personalized career roadmap."
)
st.divider()


def display_section(icon: str, title: str, content: str):
    """Renders a styled markdown card for each analysis section."""
    with st.container(border=True):
        st.markdown(f"### {icon} {title}")
        st.markdown(content)


def main():
    uploaded_file = st.file_uploader(
        "📄 Upload your Resume (PDF only)",
        type=["pdf"],
        help="Supported format: PDF. Max size: 10MB."
    )

    if not uploaded_file:
        return

    # ── Step 1: Extract ──────────────────────────────────────────────────
    with st.spinner("📖 Extracting text from your resume..."):
        resume_text = extract_text_from_pdf(uploaded_file)

    if not resume_text or len(resume_text.strip()) < 50:
        st.error("⚠️ Could not extract enough text. Is your PDF scanned? Try a text-based PDF.")
        st.stop()

    st.success("✅ Resume parsed successfully!")
    st.divider()

    # ── Step 2: Resume Summary ───────────────────────────────────────────
    try:
        with st.spinner("🧠 Summarizing your resume..."):
            summary = ask_groq(
                f"Summarize this resume. Highlight key skills, years of experience, "
                f"tech stack, and notable achievements. Be concise.\n\n{resume_text}",
                max_tokens=500
            )
        display_section("🧠", "Resume Summary", summary)
    except LLMError as e:
        st.error(f"⚠️ Could not generate resume summary: {e}")

    # ── Step 3: Skill Gap Analysis ───────────────────────────────────────
    try:
        with st.spinner("🔍 Analyzing skill gaps..."):
            skill_gap = ask_groq(
                f"Analyze this resume and identify:\n"
                f"1. Missing technical skills for current job market\n"
                f"2. Gaps in certifications or education\n"
                f"3. Weak areas compared to industry standards\n"
                f"4. Specific suggestions to close each gap\n\n"
                f"Format your response using bullet points.\n\n{resume_text}",
                max_tokens=500
            )
        display_section("🔍", "Skill Gap Analysis", skill_gap)
    except LLMError as e:
        st.error(f"⚠️ Could not analyze skill gaps: {e}")

    # ── Step 4: Career Roadmap ────────────────────────────────────────────
    try:
        with st.spinner("🗺️ Building your career roadmap..."):
            roadmap = ask_groq(
                f"Based on this resume, create a 6–12 month career improvement roadmap:\n"
                f"1. Top 3 skills to learn immediately\n"
                f"2. Certifications to pursue (with priority order)\n"
                f"3. Projects to build for portfolio\n"
                f"4. Industry exposure and networking steps\n\n"
                f"Format as a numbered, structured plan.\n\n{resume_text}",
                max_tokens=500
            )
        display_section("🗺️", "Career Roadmap", roadmap)
    except LLMError as e:
        st.error(f"⚠️ Could not build career roadmap: {e}")

    # ── Step 5: Job Recommendations ──────────────────────────────────────
    st.divider()
    st.markdown("### 💼 Job Recommendations")

    try:
        with st.spinner("🎯 Identifying your target job title..."):
            job_title = extract_job_title(resume_text)
        st.caption(f"Searching jobs for: **{job_title}**")
    except LLMError as e:
        job_title = None
        st.warning(f"⚠️ Could not determine a target job title, skipping live job search: {e}")

    if job_title:
        col1, col2 = st.columns(2)

        with col1:
            with st.container(border=True):
                st.markdown("#### 🔗 LinkedIn Matches")
                try:
                    with st.spinner("🔗 Fetching LinkedIn jobs..."):
                        linkedin_jobs = fetch_linkedin_jobs(job_title)
                    if linkedin_jobs:
                        for job in linkedin_jobs:
                            st.markdown(
                                f"- **{job.get('title', 'N/A')}** at {job.get('company', 'N/A')} "
                                f"— [Apply]({job.get('url', '#')})"
                            )
                    else:
                        st.info("No LinkedIn jobs found for this title.")
                except JobFetchError as e:
                    st.error(f"⚠️ LinkedIn fetch failed: {e}")

        with col2:
            with st.container(border=True):
                st.markdown("#### 🏢 Naukri Matches")
                try:
                    with st.spinner("🏢 Fetching Naukri jobs..."):
                        naukri_jobs = fetch_naukri_jobs(job_title)
                    if naukri_jobs:
                        for job in naukri_jobs:
                            st.markdown(
                                f"- **{job.get('title', 'N/A')}** at {job.get('company', 'N/A')} "
                                f"— [Apply]({job.get('url', '#')})"
                            )
                    else:
                        st.info("No Naukri jobs found for this title.")
                except JobFetchError as e:
                    st.error(f"⚠️ Naukri fetch failed: {e}")

    # ── Footer ────────────────────────────────────────────────────────────
    st.divider()
    st.caption("⚡ Powered by Groq LLM · Built with Streamlit · AI Job Recommender v1.0")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Compile-check the file**

Run: `uv run python -m py_compile app.py`
Expected: no output, exit code 0

- [ ] **Step 3: Manual smoke test**

Run: `uv run streamlit run app.py` (requires real `GROQ_API_KEY`/`APIFY_API_TOKEN` in `.env` or env vars — Streamlit UI is not covered by the pytest suite). Upload a real text-based PDF resume and confirm:
- Resume summary/skill-gap/roadmap sections render.
- The "Searching jobs for: **`<title>`**" caption shows a short job title/role, NOT the full resume text.
- LinkedIn/Naukri columns render job cards or a clean "No jobs found"/error message — never a fake job card with a `⚠️` title.

Stop the server (Ctrl+C) once confirmed.

- [ ] **Step 4: Commit**

```bash
git add app.py
git commit -m "fix: app.py searches jobs by extracted title instead of full resume text; per-section error handling"
```

---

### Task 6: Full verification

**Files:** none (verification only)

- [ ] **Step 1: Run the full test suite**

Run: `uv run pytest -v`
Expected: all tests pass (2 config + 6 helper + 2 mcp_server = 10 passed), 0 failed

- [ ] **Step 2: Confirm no stray dead references**

Run: `grep -rn "job_api\|PyPDF2\|pypdf2" --include=*.py .`
Expected: no matches outside `.venv/`

- [ ] **Step 3: Review full diff against `origin/main`**

Run: `git diff origin/main --stat`
Expected: shows exactly the files touched in Tasks 1-5 (`src/config.py`, `src/helper.py`, `mcp_server.py`, `app.py`, `.env.example`, `tests/*`, `pyproject.toml`, `uv.lock`, deletions of `src/job_api.py`/`requirements.txt`, plus the two docs files from brainstorming/planning)

- [ ] **Step 4: Push the branch (no PR — user opens it from the GitHub UI)**

```bash
git push -u origin fix/production-hardening
```
