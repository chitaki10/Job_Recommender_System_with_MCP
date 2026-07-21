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
