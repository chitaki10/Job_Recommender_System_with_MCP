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
