"""Ashby Public Postings API provider."""

import json
import urllib.request
from typing import List, Optional, Any
from .base import BaseATSProvider, DEFAULT_HEADERS, clean_html, match_location, match_role


class AshbyProvider(BaseATSProvider):
    """Ashby Public Postings API provider (used by Linear, Ramp, Cursor, etc.)."""
    name = "ashby"

    def __init__(self, organization_token: str, company_name: Optional[str] = None):
        self.organization_token = organization_token
        self.company_name = company_name or organization_token.capitalize()

    def fetch_jobs(self, role: str = "", location: str = "", limit: int = 10) -> List[Any]:
        from ..core.hunter import JobPosting
        postings = []
        url = f"https://api.ashbyhq.com/posting-api/job-board/{self.organization_token}"
        req = urllib.request.Request(url, headers=DEFAULT_HEADERS)
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                jobs = data.get("jobs", [])
                for job in jobs:
                    title = job.get("title", "")
                    job_id = str(job.get("id", ""))
                    loc_name = job.get("location", "") or ("Remote" if job.get("isRemote") else "Unspecified")
                    desc = job.get("descriptionPlain", "") or clean_html(job.get("descriptionHtml", ""))
                    job_url = job.get("jobUrl", f"https://jobs.ashbyhq.com/{self.organization_token}/{job_id}")
                    apply_url = job.get("applyUrl", f"{job_url}/application")

                    # Location match
                    if not match_location(loc_name, location):
                        continue

                    # Role match
                    if not match_role(title, role):
                        continue

                    postings.append(JobPosting(
                        id=job_id,
                        title=title,
                        company=self.company_name,
                        ats_type="ashby",
                        location=loc_name,
                        url=job_url,
                        apply_url=apply_url,
                        description=desc
                    ))
                    if len(postings) >= limit:
                        break
        except Exception:
            pass
        return postings
