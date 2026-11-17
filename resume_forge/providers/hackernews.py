"""Hacker News / Y Combinator 'Who is hiring?' Algolia API provider."""

import html
import json
import re
import urllib.request
from typing import List, Any
from .base import BaseATSProvider, DEFAULT_HEADERS, clean_html, match_location, match_role


class HNHiringProvider(BaseATSProvider):
    """Hacker News / Y Combinator 'Who is hiring?' public Algolia API provider."""
    name = "hn"

    def fetch_jobs(self, role: str = "", location: str = "", limit: int = 10) -> List[Any]:
        from ..core.hunter import JobPosting
        postings = []
        story_url = "https://hn.algolia.com/api/v1/search_by_date?tags=story,author_whoishiring&query=Who%20is%20hiring&hitsPerPage=1"
        try:
            req = urllib.request.Request(story_url, headers=DEFAULT_HEADERS)
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                hits = data.get("hits", [])
                if not hits:
                    return postings
                story_id = hits[0].get("objectID")

            if not story_id:
                return postings

            comments_url = f"https://hn.algolia.com/api/v1/search_by_date?tags=comment,story_{story_id}&hitsPerPage=200"
            req2 = urllib.request.Request(comments_url, headers=DEFAULT_HEADERS)
            with urllib.request.urlopen(req2, timeout=10) as resp2:
                cdata = json.loads(resp2.read().decode("utf-8"))
                comments = cdata.get("hits", [])

            for comm in comments:
                text_raw = comm.get("comment_text") or ""
                if not text_raw:
                    continue
                clean_text = clean_html(text_raw)
                lines = [l.strip() for l in clean_text.splitlines() if l.strip()]
                if not lines:
                    continue

                first_line = lines[0]
                parts = [p.strip() for p in first_line.split("|")]
                if len(parts) >= 2:
                    company = parts[0]
                    title_candidate = parts[1]
                    loc_candidate = parts[2] if len(parts) > 2 else "Remote / Flexible"
                else:
                    company = "YC / HN Startup"
                    title_candidate = first_line
                    loc_candidate = "Remote / Flexible"

                if not match_role(title_candidate, role):
                    continue
                if not match_location(loc_candidate, location):
                    continue

                comm_id = comm.get("objectID", "")
                hn_url = f"https://news.ycombinator.com/item?id={comm_id}"

                urls = re.findall(r'https?://[^\s<>"]+|www\.[^\s<>"]+', text_raw)
                apply_url = urls[0] if urls else hn_url

                postings.append(JobPosting(
                    id=f"hn_{comm_id}",
                    title=title_candidate,
                    company=company,
                    ats_type="hn",
                    location=loc_candidate,
                    url=hn_url,
                    apply_url=apply_url,
                    description=clean_text[:1200]
                ))
                if len(postings) >= limit:
                    break
        except Exception:
            pass
        return postings
