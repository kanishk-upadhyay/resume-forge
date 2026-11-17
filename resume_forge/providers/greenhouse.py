"""Greenhouse Public Boards API provider."""

import json
import urllib.request
from typing import List, Optional, Any
from .base import BaseATSProvider, DEFAULT_HEADERS, clean_html, match_location, match_role


class GreenhouseProvider(BaseATSProvider):
    """Greenhouse Public Boards API provider."""
    name = "greenhouse"

    def __init__(self, board_token: str, company_name: Optional[str] = None):
        self.board_token = board_token
        self.company_name = company_name or board_token.capitalize()

    def fetch_jobs(self, role: str = "", location: str = "", limit: int = 10) -> List[Any]:
        from ..core.hunter import JobPosting
        postings = []
        url = f"https://boards-api.greenhouse.io/v1/boards/{self.board_token}/jobs?content=true"
        req = urllib.request.Request(url, headers=DEFAULT_HEADERS)
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                for job in data.get("jobs", []):
                    title = job.get("title", "")
                    job_id = str(job.get("id", ""))
                    loc_name = job.get("location", {}).get("name", "") or "Unspecified"
                    content_text = clean_html(job.get("content", ""))

                    # Match location
                    if not match_location(loc_name, location):
                        continue

                    # Match role
                    if not match_role(title, role):
                        continue

                    job_url = job.get("absolute_url", f"https://boards.greenhouse.io/{self.board_token}/jobs/{job_id}")
                    apply_url = f"{job_url}#app" if "#" not in job_url else job_url

                    postings.append(JobPosting(
                        id=job_id,
                        title=title,
                        company=self.company_name,
                        ats_type="greenhouse",
                        location=loc_name,
                        url=job_url,
                        apply_url=apply_url,
                        description=content_text
                    ))
                    if len(postings) >= limit:
                        break
        except Exception:
            pass
        return postings
