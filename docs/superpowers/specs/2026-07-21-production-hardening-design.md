# Production Hardening — Design

Date: 2026-07-21

## Problem

Repo review found: a real bug (job search sends whole resume text as query), a
hard crash on missing API keys (raised at import time), a dead file
(`src/job_api.py`), an unused dependency (`pypdf2`), a stale duplicate
dependency manifest (`requirements.txt` vs `pyproject.toml`/`uv.lock`), an
unused import in `mcp_server.py`, and error paths that swallow exceptions and
return fake-shaped data (a job dict with `title: "⚠️ ... failed"`) instead of
signaling failure.

## Scope (user-approved)

Fix all of the above, plus: config/secrets hardening, proper error handling
and logging, and unit tests. Drop `requirements.txt` in favor of uv +
`pyproject.toml`. Delete `src/job_api.py`.

## Design

**Error architecture (`src/helper.py`)** — typed exceptions instead of
swallow-and-return-fake-data:
- `ConfigError` — missing API key.
- `LLMError` — Groq call fails.
- `JobFetchError` — Apify call fails.

Each raise site logs via stdlib `logging` (`log.exception(...)`) before
raising.

**Config (`src/config.py`, new)** — centralizes env/secrets loading
(Streamlit secrets first, falls back to `.env`/env vars, same precedence as
today). Validates once; raises `ConfigError` with a clear message instead of
a bare `ValueError` at import time. `.env.example` added with
`GROQ_API_KEY=`, `APIFY_API_TOKEN=`, `LOG_LEVEL=INFO`.

**Callers handle errors at their boundary:**
- `app.py` (Streamlit): catches `ConfigError` at startup → `st.error` +
  `st.stop()`, no raw traceback. Catches `LLMError`/`JobFetchError`
  per-section → friendly `st.error`/`st.warning`; rest of the page keeps
  working.
- `mcp_server.py`: lets exceptions propagate. FastMCP turns a raised
  exception into a proper tool-call error for the MCP client — the
  idiomatic behavior, versus today's fake "successful" result embedding an
  error string.

**Bug fix (`app.py` + `src/helper.py`)** — new `extract_job_title(resume_text)`
helper makes one small Groq call (`max_tokens=20`) to pull a real job
title/role out of the resume. `app.py` uses that (not the raw resume dump)
as the query for both `fetch_linkedin_jobs`/`fetch_naukri_jobs`.

**Cleanup:**
- Delete `src/job_api.py` (empty, unreferenced).
- Delete `requirements.txt` (uv + `pyproject.toml` is the single source of
  dependency truth).
- Drop unused `pypdf2` dependency from `pyproject.toml`.
- Remove unused `extract_text_from_pdf` import in `mcp_server.py`.
- Basic input validation in MCP tools: reject blank `job_title`.

**Tests (`tests/test_helper.py`, pytest + `unittest.mock`)** — no network
calls. Covers:
- Missing config key → `ConfigError`.
- `ask_groq` success path and `LLMError` on client failure.
- `fetch_linkedin_jobs`/`fetch_naukri_jobs` success path and `JobFetchError`
  on client failure.
- `extract_job_title` happy path.

## Out of scope

CI pipeline, Docker, deployment changes, new features (e.g. exposing a PDF
tool via MCP) — not requested, not added.
