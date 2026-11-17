"""Amazon Jobs JSON API provider."""

import json
import urllib.request
from typing import List, Any
from .base import BaseATSProvider, DEFAULT_HEADERS, ISO_COUNTRY_MAP, clean_html, match_location, match_role


class AmazonProvider(BaseATSProvider):
    """Direct Amazon Jobs JSON API provider."""
    name = "amazon"

    def fetch_jobs(self, role: str = "", location: str = "", limit: int = 10) -> List[Any]:
        from ..core.hunter import JobPosting
        postings = []
        base_url = "https://www.amazon.jobs/en/search.json"
        params = [
            f"result_limit={limit * 4}",
            "sort=recent"
        ]
        if role:
            params.append(f"base_query={urllib.request.quote(role)}")

        # Location parameter if provided
        if location and location.lower() not in ("all", "*", "remote"):
            for loc_part in location.split(","):
                clean = loc_part.strip().lower()
                iso = ISO_COUNTRY_MAP.get(clean)
                if iso:
                    params.append(f"country={iso}")
                    break

        url = f"{base_url}?{'&'.join(params)}"
        req = urllib.request.Request(url, headers=DEFAULT_HEADERS)
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                for job in data.get("jobs", []):
                    title = job.get("title", "")
                    job_path = job.get("job_path", "")
                    job_id = str(job.get("id_icims") or job.get("id", ""))
                    loc_desc = job.get("location", "") or job.get("city", "") or "Unspecified"
                    desc = clean_html(job.get("description", "") + " " + job.get("basic_qualifications", ""))

                    direct_url = f"https://www.amazon.jobs{job_path}" if job_path.startswith("/") else job_path
                    apply_url = f"https://www.amazon.jobs/applicant/jobs/{job_id}/apply" if job_id else direct_url

                    # Check location filter
                    loc_full = f"{loc_desc} {job.get('country_code', '')}"
                    if not match_location(loc_full, location):
                        continue

                    # Check role match
                    if not match_role(title, role):
                        continue

                    postings.append(JobPosting(
                        id=job_id,
                        title=title,
                        company="Amazon",
                        ats_type="amazon",
                        location=loc_desc,
                        url=direct_url,
                        apply_url=apply_url,
                        description=desc
                    ))
                    if len(postings) >= limit:
                        break
        except Exception:
            pass
        return postings
