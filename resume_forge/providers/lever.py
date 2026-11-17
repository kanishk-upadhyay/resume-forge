"""Lever Public Postings API provider."""

import json
import urllib.request
from typing import List, Optional, Any
from .base import BaseATSProvider, DEFAULT_HEADERS, clean_html, match_location, match_role


class LeverProvider(BaseATSProvider):
    """Lever Public Postings API provider."""
    name = "lever"

    def __init__(self, company_id: str, company_name: Optional[str] = None):
        self.company_id = company_id
        self.company_name = company_name or company_id.capitalize()

    def fetch_jobs(self, role: str = "", location: str = "", limit: int = 10) -> List[Any]:
        from ..core.hunter import JobPosting
        postings = []
        url = f"https://api.lever.co/v0/postings/{self.company_id}?mode=json"
        req = urllib.request.Request(url, headers=DEFAULT_HEADERS)
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                jobs = json.loads(resp.read().decode("utf-8"))
                for job in jobs:
                    title = job.get("text", "")
                    job_id = str(job.get("id", ""))
                    cats = job.get("categories", {})
                    loc = cats.get("location", "") or "Unspecified"
                    desc_plain = job.get("descriptionPlain", "") or clean_html(job.get("description", ""))

                    # Match location
                    if not match_location(loc, location):
                        continue

                    # Match role
                    if not match_role(title, role):
                        continue

                    hosted_url = job.get("hostedUrl", f"https://jobs.lever.co/{self.company_id}/{job_id}")
                    apply_url = job.get("applyUrl", f"{hosted_url}/apply")

                    postings.append(JobPosting(
                        id=job_id,
                        title=title,
                        company=self.company_name,
                        ats_type="lever",
                        location=loc,
                        url=hosted_url,
                        apply_url=apply_url,
                        description=desc_plain
                    ))
                    if len(postings) >= limit:
                        break
        except Exception:
            pass
        return postings
