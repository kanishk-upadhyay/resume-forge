"""Aikyam Jobs HTML & Next.js RSC flight feed provider (aikyamjobs.org)."""

import json
import re
import urllib.request
from typing import List, Any
from .base import BaseATSProvider, DEFAULT_HEADERS, clean_html, match_location, match_role


class AikyamProvider(BaseATSProvider):
    """Direct Aikyam Jobs HTML & Next.js RSC flight feed provider (aikyamjobs.org).
    
    Parses Next.js App Router HTML and RSC flight payloads from /tag/internship and /jobs
    without assuming a nonexistent public REST endpoint at /api/jobs.
    """
    name = "aikyam"

    def __init__(self, base_url: str = "https://aikyamjobs.org"):
        self.base_url = base_url.rstrip("/")

    def fetch_jobs(self, role: str = "", location: str = "", limit: int = 10) -> List[Any]:
        from ..core.hunter import JobPosting
        postings = []
        sources = [f"{self.base_url}/tag/internship", f"{self.base_url}/jobs"]
        seen_slugs = set()

        for source_url in sources:
            req = urllib.request.Request(source_url, headers=DEFAULT_HEADERS)
            try:
                with urllib.request.urlopen(req, timeout=10) as resp:
                    raw_data = resp.read().decode("utf-8")

                    # 1. JSON payload support (for test mocks or structured responses)
                    try:
                        json_data = json.loads(raw_data)
                        items = json_data.get("data", [])
                        if items:
                            for item in items:
                                attrs = item.get("attributes", item)
                                job_id = str(item.get("id") or attrs.get("id", ""))
                                slug = attrs.get("slug") or ""
                                dedup_key = job_id or slug
                                if dedup_key in seen_slugs:
                                    continue
                                seen_slugs.add(dedup_key)
                                title = attrs.get("title") or attrs.get("jobTitle") or ""
                                org_data = attrs.get("organization") or attrs.get("company") or {}
                                if isinstance(org_data, dict):
                                    org_attrs = org_data.get("data", {}).get("attributes", org_data) if isinstance(org_data.get("data"), dict) else org_data
                                    company = org_attrs.get("name") or org_attrs.get("title") or "Aikyam Partner"
                                else:
                                    company = str(org_data) if org_data else "Aikyam Partner"
                                loc_str = attrs.get("location") or attrs.get("city") or "India"
                                desc = clean_html(attrs.get("jobDescription") or attrs.get("description") or "")
                                apply_url = attrs.get("applyUrl") or (f"{self.base_url}/jobs/{slug}" if slug else self.base_url)
                                direct_url = f"{self.base_url}/jobs/{slug}" if slug else self.base_url
                                if not match_location(loc_str, location):
                                    continue
                                if not match_role(title, role):
                                    continue
                                postings.append(JobPosting(
                                    id=job_id or f"aikyam_{slug}",
                                    title=title,
                                    company=company,
                                    ats_type="aikyam",
                                    location=loc_str,
                                    url=direct_url,
                                    apply_url=apply_url,
                                    description=desc
                                ))
                                if len(postings) >= limit:
                                    return postings
                            continue
                    except Exception:
                        pass

                    # 2. HTML & Next.js RSC flight feed parser
                    matches = re.findall(r'href=["\'](/jobs/([a-zA-Z0-9-]+))["\'][^>]*aria-label=["\']([^"\']+)["\']', raw_data)
                    if not matches:
                        raw_slugs = set(re.findall(r'/jobs/([a-zA-Z0-9-]+)', raw_data))
                        matches = [(f"/jobs/{s}", s, s.replace("-", " ").title()) for s in raw_slugs if s not in ("apply", "search", "filter")]

                    for rel_url, slug, label in matches:
                        if slug in seen_slugs or slug in ("apply", "search", "subscribe", "filter", "login", "register"):
                            continue
                        seen_slugs.add(slug)

                        # Label format often: "Role in Location | Company"
                        parts = [p.strip() for p in label.split("|") if p.strip()]
                        if len(parts) >= 2:
                            title_loc = parts[0]
                            company = parts[1]
                        else:
                            title_loc = label
                            company = "Aikyam Partner"

                        # Parse title and location
                        if " in " in title_loc:
                            title_part, loc_part = title_loc.split(" in ", 1)
                        else:
                            title_part, loc_part = title_loc, "India / Remote"

                        clean_title = title_part.strip()
                        clean_loc = loc_part.strip()

                        if not match_role(clean_title, role):
                            continue
                        if not match_location(clean_loc, location):
                            continue

                        full_url = f"{self.base_url}{rel_url}"
                        apply_url = f"{full_url}/apply"

                        postings.append(JobPosting(
                            id=f"aikyam_{slug}",
                            title=clean_title,
                            company=company,
                            ats_type="aikyam",
                            location=clean_loc,
                            url=full_url,
                            apply_url=apply_url,
                            description=f"{clean_title} at {company} in {clean_loc}. Curated via Aikyam Jobs."
                        ))
                        if len(postings) >= limit:
                            return postings
            except Exception:
                pass
        return postings
