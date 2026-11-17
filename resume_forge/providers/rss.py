"""RSS / Atom XML job feed provider."""

import urllib.request
import xml.etree.ElementTree as ET
from typing import List, Any
from .base import BaseATSProvider, DEFAULT_HEADERS, clean_html, match_location, match_role


class RSSFeedProvider(BaseATSProvider):
    """Parses standard RSS 2.0 or Atom XML feeds."""
    name = "rss"

    def __init__(self, feed_url: str, feed_name: str = "RSS Feed"):
        self.feed_url = feed_url
        self.feed_name = feed_name

    def fetch_jobs(self, role: str = "", location: str = "", limit: int = 10) -> List[Any]:
        from ..core.hunter import JobPosting
        postings = []
        req = urllib.request.Request(self.feed_url, headers=DEFAULT_HEADERS)
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                xml_content = resp.read()
                root = ET.fromstring(xml_content)

            # Handle RSS 2.0 (<channel><item>) and Atom (<feed><entry>)
            items = root.findall(".//item") or root.findall(".//{http://www.w3.org/2005/Atom}entry")
            for item in items:
                title = (item.findtext("title") or item.findtext("{http://www.w3.org/2005/Atom}title") or "").strip()
                link = (item.findtext("link") or "").strip()
                if not link:
                    link_elem = item.find("{http://www.w3.org/2005/Atom}link")
                    if link_elem is not None:
                        link = link_elem.attrib.get("href", "")

                desc = clean_html(
                    item.findtext("description") or
                    item.findtext("{http://www.w3.org/2005/Atom}summary") or
                    item.findtext("{http://www.w3.org/2005/Atom}content") or ""
                )

                job_id = (item.findtext("guid") or item.findtext("{http://www.w3.org/2005/Atom}id") or link).strip()

                if not match_location(desc + " " + title, location):
                    continue

                if not match_role(title, role):
                    continue

                postings.append(JobPosting(
                    id=job_id,
                    title=title,
                    company=self.feed_name,
                    ats_type="rss",
                    location=location or "Remote / Unspecified",
                    url=link,
                    apply_url=link,
                    description=desc
                ))
                if len(postings) >= limit:
                    break
        except Exception:
            pass
        return postings
