"""SmartRecruiters REST API provider."""

import json
import urllib.request
from typing import List, Optional, Any
from .base import BaseATSProvider, DEFAULT_HEADERS, ISO_2_MAP, match_location, match_role


class SmartRecruitersProvider(BaseATSProvider):
    """SmartRecruiters REST API provider."""
    name = "smartrecruiters"

    COMMUNITY_PRESETS = {
        "bosch": {"id": "BoschGroup", "name": "Bosch Group"},
        "boschgroup": {"id": "BoschGroup", "name": "Bosch Group"},
        "cern": {"id": "CERN", "name": "CERN"},
        "square": {"id": "Block", "name": "Block / Square"},
        "block": {"id": "Block", "name": "Block / Square"},
    }

    def __init__(self, company_id: str, company_name: Optional[str] = None):
        preset = self.COMMUNITY_PRESETS.get(company_id.lower().strip(), {})
        self.company_id = preset.get("id") or company_id
        self.company_name = company_name or preset.get("name") or self.company_id.upper()

    def fetch_jobs(self, role: str = "", location: str = "", limit: int = 10) -> List[Any]:
        from ..core.hunter import JobPosting
        postings = []
        is_cern = self.company_id.upper() == "CERN" or "CERN" in self.company_name.upper()

        # Limit 100 prevents early pagination truncation across large requisitions
        params = ["limit=100"]

        # Only pass q parameter if not CERN (CERN roles use specialized titles like CERN Summer Student Programme)
        if role and not is_cern:
            params.append(f"q={urllib.request.quote(role)}")

        # When querying SmartRecruiters for multi-location or global roles, NEVER pass server-side country=in for CERN
        # (or it queries CERN for positions physically hosted in India, returning 0). Only pass country= for non-CERN single-country requests.
        if not is_cern and location and location.lower() not in ("all", "*", "remote", "worldwide") and "," not in location:
            iso2 = ISO_2_MAP.get(location.strip().lower())
            if iso2:
                params.append(f"country={iso2}")

        query_str = f"?{'&'.join(params)}" if params else ""
        url = f"https://api.smartrecruiters.com/v1/companies/{self.company_id}/postings{query_str}"
        req = urllib.request.Request(url, headers=DEFAULT_HEADERS)
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                content = data.get("content", [])
                for item in content:
                    title = item.get("name", "")
                    job_id = str(item.get("id", ""))
                    loc_city = item.get("location", {}).get("city", "")
                    loc_country = item.get("location", {}).get("country", "")
                    loc = loc_city or loc_country or "Unspecified"
                    dept = item.get("department", {}).get("label", "")

                    # Check location filter
                    loc_full = f"{loc} {loc_country}"
                    if not match_location(loc_full, location):
                        continue

                    # Check role match against title or department
                    if role and not (match_role(title, role) or match_role(dept, role)):
                        continue

                    direct_url = f"https://jobs.smartrecruiters.com/{self.company_id}/{job_id}"
                    apply_url = f"https://jobs.smartrecruiters.com/{self.company_id}/{job_id}"

                    postings.append(JobPosting(
                        id=job_id,
                        title=title,
                        company=self.company_name,
                        ats_type="smartrecruiters",
                        location=loc,
                        url=direct_url,
                        apply_url=apply_url,
                        description=f"{title} in department {dept}"
                    ))
                    if len(postings) >= limit:
                        break
        except Exception:
            pass
        return postings
