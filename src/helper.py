import fitz  # pymupdf
import os
from dotenv import load_dotenv
from groq import Groq
from apify_client import ApifyClient

load_dotenv()

# Load API keys
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
APIFY_API_TOKEN = os.getenv("APIFY_API_TOKEN")

if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY not found")

if not APIFY_API_TOKEN:
    raise ValueError("APIFY_API_TOKEN not found")

# Initialize clients
client = Groq(api_key=GROQ_API_KEY)
apify_client = ApifyClient(APIFY_API_TOKEN)


def extract_text_from_pdf(uploaded_file):
    """
    Extracts text from the PDF file
    """
    doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
    text = ""

    for page in doc:
        text += page.get_text()

    return text


def ask_groq(prompt, max_tokens=500):
    """
    Sends prompt to Groq and returns response
    """

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",

        messages=[
            {
                "role": "system",
                "content": prompt
            }
        ],

        temperature=0.5,
        max_tokens=max_tokens
    )

    return response.choices[0].message.content


def fetch_linkedin_jobs(search_query, location="india", rows=60):

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

    jobs = list(
        apify_client.dataset(run["defaultDatasetId"]).iterate_items()
    )

    return jobs


def fetch_naukri_jobs(search_query, location="india", rows=60):

    run_input = {
        "keyword": search_query,
        "maxJobs": rows,
        "freshness": "all",
        "sortBy": "relevance",
        "experience": "all"
    }

    run = apify_client.actor("wsrn5gy5C4EDeYCcD").call(run_input=run_input)

    jobs = list(
        apify_client.dataset(run["defaultDatasetId"]).iterate_items()
    )

    return jobs