"""Workday CXS REST API provider."""

import json
import urllib.request
from typing import List, Optional, Any
from .base import BaseATSProvider, DEFAULT_HEADERS, match_location, match_role


class WorkdayProvider(BaseATSProvider):
    """Workday modern CXS REST API provider (e.g. Red Hat, Samsung, Nvidia, etc.)."""
    name = "workday"

    COMMUNITY_PRESETS = {
        "redhat": {
            "name": "Red Hat",
            "host": "redhat.wd5.myworkdayjobs.com",
            "site": "Jobs"
        },
        "samsung": {
            "name": "Samsung Electronics",
            "host": "sec.wd3.myworkdayjobs.com",
            "site": "Samsung_Careers"
        }
    }

    def __init__(self,
                 company_identifier: str,
                 host: Optional[str] = None,
                 site: Optional[str] = None,
                 company_name: Optional[str] = None):
        preset = self.COMMUNITY_PRESETS.get(company_identifier.lower().strip(), {})
        self.company_id = company_identifier
        self.host = host or preset.get("host")
        self.site = site or preset.get("site")
        self.company_name = company_name or preset.get("name") or company_identifier.capitalize()

    def fetch_jobs(self, role: str = "", location: str = "", limit: int = 10) -> List[Any]:
        from ..core.hunter import JobPosting
        postings = []
        if not self.host or not self.site:
            return postings

        url = f"https://{self.host}/wday/cxs/{self.host.split('.')[0]}/{self.site}/jobs"
        payload = {
            "appliedFacets": {},
            "limit": limit * 2,
            "offset": 0,
            "searchText": role or ""
        }
        body_bytes = json.dumps(payload).encode("utf-8")
        headers = dict(DEFAULT_HEADERS)
        headers["Content-Type"] = "application/json"

        req = urllib.request.Request(url, data=body_bytes, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                job_postings = data.get("jobPostings", [])
                for job in job_postings:
                    title = job.get("title", "")
                    job_path = job.get("externalPath", "")
                    job_id = job.get("bulletFields", [None])[0] if job.get("bulletFields") else ""
                    if not job_id and job_path:
                        job_id = job_path.split("/")[-1].split("?")[0]
                    loc = job.get("locationsText", "") or "Unspecified"

                    # Match location
                    if not match_location(loc, location):
                        continue

                    # Match role
                    if not match_role(title, role):
                        continue

                    clean_path = job_path.lstrip("/")
                    full_url = f"https://{self.host}/en-US/{self.site}/{clean_path}" if not clean_path.startswith("http") else clean_path
                    apply_url = f"{full_url}/apply"

                    postings.append(JobPosting(
                        id=str(job_id or job_path),
                        title=title,
                        company=self.company_name,
                        ats_type="workday",
                        location=loc,
                        url=full_url,
                        apply_url=apply_url,
                        description=f"{title} at {self.company_name} ({loc}). Posted on Workday."
                    ))
                    if len(postings) >= limit:
                        break
        except Exception:
            pass
        return postings
