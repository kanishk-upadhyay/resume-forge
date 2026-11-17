"""Base ATS Provider and shared filtering / text utilities."""

import html
import json
import re
import urllib.request
import urllib.error
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Set, TYPE_CHECKING

if TYPE_CHECKING:
    from ..core.hunter import JobPosting

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/html, */*"
}

ISO_COUNTRY_MAP = {
    "us": "USA", "usa": "USA", "united states": "USA",
    "uk": "GBR", "gbr": "GBR", "united kingdom": "GBR",
    "ca": "CAN", "can": "CAN", "canada": "CAN",
    "de": "DEU", "deu": "DEU", "germany": "DEU",
    "in": "IND", "ind": "IND", "india": "IND",
    "ch": "CHE", "che": "CHE", "switzerland": "CHE",
    "fr": "FRA", "fra": "FRA", "france": "FRA",
    "nl": "NLD", "nld": "NLD", "netherlands": "NLD",
    "au": "AUS", "aus": "AUS", "australia": "AUS",
    "ie": "IRL", "irl": "IRL", "ireland": "IRL",
    "sg": "SGP", "sgp": "SGP", "singapore": "SGP",
    "jp": "JPN", "jpn": "JPN", "japan": "JPN",
    "se": "SWE", "swe": "SWE", "sweden": "SWE",
    "es": "ESP", "esp": "ESP", "spain": "ESP",
    "it": "ITA", "ita": "ITA", "italy": "ITA",
    "pl": "POL", "pol": "POL", "poland": "POL",
    "br": "BRA", "bra": "BRA", "brazil": "BRA"
}

ISO_2_MAP = {
    "us": "us", "usa": "us", "united states": "us",
    "uk": "gb", "gbr": "gb", "united kingdom": "gb",
    "ca": "ca", "can": "ca", "canada": "ca",
    "de": "de", "deu": "de", "germany": "de",
    "in": "in", "ind": "in", "india": "in",
    "ch": "ch", "che": "ch", "switzerland": "ch",
    "fr": "fr", "fra": "fr", "france": "fr",
    "nl": "nl", "nld": "nl", "netherlands": "nl",
    "au": "au", "aus": "au", "australia": "au",
    "ie": "ie", "irl": "ie", "ireland": "ie",
    "sg": "sg", "sgp": "sg", "singapore": "sg",
    "jp": "jp", "jpn": "jp", "japan": "jp",
    "se": "se", "swe": "se", "sweden": "se",
    "es": "es", "esp": "es", "spain": "es",
    "it": "it", "ita": "it", "italy": "it",
    "pl": "pl", "pol": "pl", "poland": "pl",
    "br": "br", "bra": "br", "brazil": "br"
}

REMOTE_TERMS = {"remote", "anywhere", "worldwide", "distributed", "virtual", "telecommute", "wfh"}
EARLY_CAREER_SYNONYMS = ("intern", "internship", "student", "summer student", "co-op", "coop", "trainee", "fellow")


def clean_html(raw_html: str) -> str:
    """Strips HTML markup and decodes entities into clean plain text."""
    if not raw_html:
        return ""
    clean = re.sub(r'<[^<]+?>', ' ', raw_html)
    clean = html.unescape(clean)
    clean = re.sub(r'\s+', ' ', clean)
    return clean.strip()


def match_location(job_location_str: str, target_location: str = "") -> bool:
    """Matches job location against requested location query."""
    if not target_location or target_location.lower() in ("all", "*"):
        return True
    job_loc_lower = job_location_str.lower()
    target_tokens = [tok.strip().lower() for tok in target_location.split(",") if tok.strip()]

    for token in target_tokens:
        if token in job_loc_lower:
            return True
        if token in REMOTE_TERMS and any(r in job_loc_lower for r in REMOTE_TERMS):
            return True
        iso_code = ISO_COUNTRY_MAP.get(token)
        if iso_code and iso_code.lower() in job_loc_lower:
            return True
        iso2 = ISO_2_MAP.get(token)
        if iso2 and re.search(r'\b' + re.escape(iso2) + r'\b', job_loc_lower):
            return True
    return False


def match_seniority(title: str, target_seniority: str = "all", role_query: str = "") -> bool:
    """Matches role title against target seniority level, preventing false positives."""
    sen = (target_seniority or "all").lower().strip()
    title_lower = title.lower()
    query_lower = (role_query or "").lower()

    if sen == "all":
        is_early_career = any(k in query_lower for k in ("intern", "student", "graduate", "junior", "entry", "early career", "co-op", "trainee"))
        has_senior_in_query = any(k in query_lower for k in ("senior", "sr", "staff", "principal", "lead", "manager"))
        if is_early_career and not has_senior_in_query:
            if re.search(r'\b(senior|sr\b|sr\.|staff|principal|lead|director|manager|vp|head\s+of)\b', title_lower):
                return False
        return True

    if sen in ("intern", "internship", "co-op"):
        if re.search(r'\b(senior|sr\b|sr\.|staff|principal|lead|director|manager|vp|head\s+of)\b', title_lower):
            return False
        return True

    if sen in ("entry", "junior"):
        if re.search(r'\b(senior|sr\b|sr\.|staff|principal|lead|director|manager|vp|head\s+of)\b', title_lower):
            return False
        return True

    if sen in ("mid", "intermediate"):
        if re.search(r'\b(intern|internship|co-op|student|director|vp|chief)\b', title_lower):
            return False
        return True

    if sen in ("senior", "sr"):
        if re.search(r'\b(intern|internship|co-op|junior|jr\b|jr\.|entry|student|associate)\b', title_lower):
            return False
        return True

    if sen in ("staff", "principal"):
        if re.search(r'\b(intern|internship|co-op|junior|jr\b|jr\.|entry|student|associate)\b', title_lower):
            return False
        return True

    if sen in ("lead", "manager", "director"):
        if re.search(r'\b(intern|internship|co-op|junior|jr\b|jr\.|student)\b', title_lower):
            return False
        return True

    return True


def match_role(title: str,
               role_query: str = "",
               seniority: str = "all",
               exclude_titles: Optional[List[str]] = None) -> bool:
    """Matches role query tokens and seniority level against job title."""
    title_lower = title.lower()

    # User-defined title exclusions
    if exclude_titles:
        for excl in exclude_titles:
            excl_tok = excl.strip().lower()
            if excl_tok and excl_tok in title_lower:
                return False

    # Seniority guardrail
    if not match_seniority(title, seniority, role_query):
        return False

    if not role_query:
        return True

    # If role_query is an early career term, accept synonyms (e.g. "student", "summer student", "co-op", "trainee")
    if role_query.lower() in ("intern", "internship", "student", "co-op", "trainee"):
        if any(term in title_lower for term in EARLY_CAREER_SYNONYMS):
            return True

    tokens = [tok.strip().lower() for tok in role_query.split() if tok.strip()]
    for tok in tokens:
        if tok in ("intern", "internship", "student", "trainee", "co-op", "coop", "fellow"):
            if not any(syn in title_lower for syn in EARLY_CAREER_SYNONYMS):
                return False
        else:
            if tok not in title_lower:
                return False
    return True


def match_experience(description: str,
                     min_exp: Optional[int] = None,
                     max_exp: Optional[int] = None) -> bool:
    """Verifies that job description requirements align with user experience preferences."""
    if not description or (min_exp is None and max_exp is None):
        return True

    exp_matches = re.findall(
        r'\b(\d{1,2})\+?\s*(?:-\s*(\d{1,2})\s*)?years?(?:\s+of)?\s+experience\b',
        description,
        re.IGNORECASE
    )
    if not exp_matches:
        return True

    for low_str, high_str in exp_matches:
        low = int(low_str)
        high = int(high_str) if high_str else low
        if max_exp is not None and low > max_exp:
            return False
        if min_exp is not None and low < min_exp:
            return False
    return True


def match_grad_year(title: str, description: str, target_year: Optional[int]) -> bool:
    """Matches target graduation cohort year without restricting to arbitrary decades."""
    if not target_year:
        return True
    cohort_text = f"{title} {description[:1000]}"
    cohort_mentions = re.findall(
        r'\b(?:class of|graduating|cohort|batch|graduation(?:\s+date)?)\s*(?:in\s*|between\s*|:\s*)?(20\d{2})(?:\s*(?:-|–|to|and|or)\s*(20\d{2}))?\b',
        cohort_text,
        re.IGNORECASE
    )
    if not cohort_mentions:
        return True
    supported_years: Set[int] = set()
    for y1, y2 in cohort_mentions:
        if y1:
            supported_years.add(int(y1))
        if y2:
            supported_years.add(int(y2))
            if y1:
                for yr in range(int(y1), int(y2) + 1):
                    supported_years.add(yr)
    return target_year in supported_years


class BaseATSProvider(ABC):
    """Abstract base class for ATS API providers and scrapers.
    
    All standard ATS providers and third-party custom plugins inherit from this class.
    """
    name: str = "base"

    @abstractmethod
    def fetch_jobs(self, role: str = "", location: str = "", limit: int = 10) -> List["JobPosting"]:
        """Queries the ATS platform and returns verified, structured JobPosting objects."""
        raise NotImplementedError
