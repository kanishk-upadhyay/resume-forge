"""Live Job Description Ingestion and HTML/ATS Cleaning Utility."""

import json
import re
import urllib.request
import urllib.error
from pathlib import Path
from typing import Optional


DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml,application/json;q=0.9,*/*;q=0.8"
}


def clean_html_to_text(html: str) -> str:
    """Strips markup, scripts, and navigation boilerplate, returning clean readable text."""
    # 1. Remove comments
    text = re.sub(r'<!--.*?-->', '', html, flags=re.DOTALL)
    # 2. Remove script and style elements
    text = re.sub(r'<(?:script|style|head|nav|footer|header|noscript)[^>]*>.*?</(?:script|style|head|nav|footer|header|noscript)>', '', text, flags=re.DOTALL | re.IGNORECASE)
    # 3. Replace break and list elements with newlines
    text = re.sub(r'<(?:br|p|div|li|h[1-6]|tr)[^>]*>', '\n', text, flags=re.IGNORECASE)
    # 4. Strip remaining HTML tags
    text = re.sub(r'<[^>]+>', ' ', text)
    # 5. Decode common HTML entities
    text = text.replace('&nbsp;', ' ').replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>').replace('&quot;', '"').replace('&#39;', "'")
    # 6. Normalize whitespace
    lines = [line.strip() for line in text.splitlines()]
    non_empty = [l for l in lines if l]
    return "\n".join(non_empty)


def fetch_lever_job(url: str) -> Optional[str]:
    """Attempts to fetch structured job text from Lever public API."""
    m = re.search(r'jobs\.lever\.co/([^/]+)/([a-f0-9\-]+)', url)
    if not m:
        return None
    company, job_id = m.group(1), m.group(2)
    api_url = f"https://api.lever.co/v0/postings/{company}/{job_id}"
    req = urllib.request.Request(api_url, headers={"User-Agent": DEFAULT_HEADERS["User-Agent"]})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            title = data.get("text", "")
            desc = data.get("descriptionPlain", "") or data.get("description", "")
            lists = data.get("lists", [])
            reqs = []
            for lst in lists:
                reqs.append(lst.get("text", ""))
                reqs.append(lst.get("content", ""))
            return f"Role: {title}\nCompany: {company}\n\nDescription:\n{desc}\n\nRequirements:\n" + "\n".join(reqs)
    except Exception:
        return None


def fetch_greenhouse_job(url: str) -> Optional[str]:
    """Attempts to fetch structured job text from Greenhouse public API."""
    m = re.search(r'boards\.greenhouse\.io/([^/]+)/jobs/(\d+)', url) or re.search(r'job-boards\.greenhouse\.io/([^/]+)/jobs/(\d+)', url)
    if not m:
        return None
    board, job_id = m.group(1), m.group(2)
    api_url = f"https://boards-api.greenhouse.io/v1/boards/{board}/jobs/{job_id}"
    req = urllib.request.Request(api_url, headers={"User-Agent": DEFAULT_HEADERS["User-Agent"]})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            title = data.get("title", "")
            content = data.get("content", "")
            plain = clean_html_to_text(content)
            return f"Role: {title}\nCompany: {board}\n\nDescription:\n{plain}"
    except Exception:
        return None


def fetch_job_description(target: str) -> str:
    """Resolves a JD input: fetches from URL, reads from local file, or returns raw string."""
    trimmed = (target or "").strip()
    if not trimmed:
        return ""

    # Check if target is a web URL
    if trimmed.startswith("http://") or trimmed.startswith("https://"):
        # Try specific ATS endpoints first
        lever_text = fetch_lever_job(trimmed)
        if lever_text:
            return lever_text

        greenhouse_text = fetch_greenhouse_job(trimmed)
        if greenhouse_text:
            return greenhouse_text

        # Generic web page fetch
        req = urllib.request.Request(trimmed, headers=DEFAULT_HEADERS)
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                raw_html = resp.read().decode("utf-8", errors="ignore")
                return clean_html_to_text(raw_html)
        except Exception as e:
            raise RuntimeError(f"Failed to fetch job description from URL '{trimmed}': {e}")

    # Check if target is a local file
    p = Path(trimmed)
    if p.exists() and p.is_file():
        return p.read_text(encoding="utf-8")

    # Otherwise, treat as raw text content
    return trimmed
