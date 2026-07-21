import pytest

from mcp_server import get_linkedin_jobs, get_naukri_jobs


def test_get_linkedin_jobs_rejects_blank_job_title():
    with pytest.raises(ValueError):
        get_linkedin_jobs("   ")


def test_get_naukri_jobs_rejects_blank_job_title():
    with pytest.raises(ValueError):
        get_naukri_jobs("")
