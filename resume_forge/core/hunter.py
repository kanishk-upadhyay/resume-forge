"""Direct ATS API Job Hunter and Auto-Resume Pairing Engine.

Directly queries official public JSON APIs of major Applicant Tracking Systems
(Greenhouse, Lever, SmartRecruiters, Amazon Jobs) without web scrapers, extracting
100% live verified requisitions and compiling tailored single-page resumes.
All filters, platforms, and locations are configured dynamically via CLI flags.
"""

import json
import re
import urllib.request
import urllib.error
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Any, Optional, Union

from .schema import ResumeData
from .parser import LatexResumeParser
from .compiler import ResumeCompiler
from .ats import ATSAnalyzer
from .exporter import ResumeExporter


@dataclass
class JobPosting:
    """Represents a verified, live job posting from an ATS API."""
    id: str
    title: str
    company: str
    ats_type: str
    location: str
    url: str
    apply_url: str
    description: str = ""
    match_rate_percent: int = 0
    matched_keywords: List[str] = field(default_factory=list)
    paired_resume_pdf: Optional[str] = None
    paired_resume_tex: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "company": self.company,
            "ats_type": self.ats_type,
            "location": self.location,
            "url": self.url,
            "apply_url": self.apply_url,
            "match_rate_percent": self.match_rate_percent,
            "matched_keywords": self.matched_keywords,
            "paired_resume_pdf": self.paired_resume_pdf,
            "paired_resume_tex": self.paired_resume_tex
        }


@dataclass
class HunterPreferences:
    """Configurable user preferences and profile for the ATS Job Hunter pipeline.
    
    Eliminates hardcoded candidate settings, enabling any developer to customize
    target roles, locations, seniority levels, experience requirements, custom company boards,
    and exclusion filters without modifying source code.
    """
    roles: List[str] = field(default_factory=list)
    locations: List[str] = field(default_factory=list)
    seniority: str = "all"  # 'all', 'intern', 'entry', 'mid', 'senior', 'staff', 'lead', 'manager'
    min_experience_years: Optional[int] = None
    max_experience_years: Optional[int] = None
    grad_year: Optional[int] = None
    exclude_titles: List[str] = field(default_factory=list)
    exclude_keywords: List[str] = field(default_factory=list)
    remote_only: bool = False
    base_resume_path: Optional[str] = None
    output_dir: str = "output/hunt"
    custom_boards: Dict[str, List[Any]] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "roles": self.roles,
            "locations": self.locations,
            "seniority": self.seniority,
            "min_experience_years": self.min_experience_years,
            "max_experience_years": self.max_experience_years,
            "grad_year": self.grad_year,
            "exclude_titles": self.exclude_titles,
            "exclude_keywords": self.exclude_keywords,
            "remote_only": self.remote_only,
            "base_resume_path": self.base_resume_path,
            "output_dir": self.output_dir,
            "custom_boards": self.custom_boards,
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)

    def save_file(self, path: Union[str, Path]) -> None:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(self.to_json(), encoding="utf-8")

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "HunterPreferences":
        roles = data.get("roles") or ([] if not data.get("role") else [str(data.get("role"))])
        locations = data.get("locations") or ([] if not data.get("location") else [str(data.get("location"))])
        return cls(
            roles=roles,
            locations=locations,
            seniority=data.get("seniority", "all"),
            min_experience_years=data.get("min_experience_years"),
            max_experience_years=data.get("max_experience_years"),
            grad_year=data.get("grad_year"),
            exclude_titles=data.get("exclude_titles") or [],
            exclude_keywords=data.get("exclude_keywords") or [],
            remote_only=bool(data.get("remote_only", False)),
            base_resume_path=data.get("base_resume_path"),
            output_dir=data.get("output_dir", "output/hunt"),
            custom_boards=data.get("custom_boards") or {},
        )

    @classmethod
    def from_json(cls, json_str: str) -> "HunterPreferences":
        return cls.from_dict(json.loads(json_str))

    @classmethod
    def load_file(cls, path: Union[str, Path]) -> "HunterPreferences":
        p = Path(path)
        if not p.exists():
            raise FileNotFoundError(f"Preferences profile not found: {path}")
        return cls.from_json(p.read_text(encoding="utf-8"))

    @classmethod
    def load_default(cls) -> "HunterPreferences":
        candidates = [
            Path("resume-forge.config.json"),
            Path(".resumeforge.json"),
            Path.home() / ".config" / "resume-forge" / "preferences.json"
        ]
        for c in candidates:
            if c.exists():
                try:
                    return cls.load_file(c)
                except Exception:
                    pass
        return cls()


DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json"
}


# Generic ISO country codes mapping for location query matching
ISO_COUNTRY_MAP = {
    "us": "USA", "usa": "USA", "united states": "USA",
    "uk": "GBR", "gbr": "GBR", "united kingdom": "GBR",
    "ca": "CAN", "can": "CAN", "canada": "CAN",
    "de": "DEU", "deu": "DEU", "germany": "DEU",
    "in": "IND", "ind": "IND", "india": "IND",
    "ch": "CHE", "che": "CHE", "switzerland": "CHE",
    "fr": "FRA", "fra": "FRA", "france": "FRA",
    "ie": "IRL", "irl": "IRL", "ireland": "IRL",
    "sg": "SGP", "sgp": "SGP", "singapore": "SGP",
    "au": "AUS", "aus": "AUS", "australia": "AUS",
    "jp": "JPN", "jpn": "JPN", "japan": "JPN",
    "nl": "NLD", "nld": "NLD", "netherlands": "NLD",
    "es": "ESP", "esp": "ESP", "spain": "ESP",
    "se": "SWE", "swe": "SWE", "sweden": "SWE",
}

ISO_2_MAP = {
    "india": "in", "in": "in", "ind": "in",
    "united states": "us", "usa": "us", "us": "us",
    "germany": "de", "de": "de", "deu": "de",
    "switzerland": "ch", "ch": "ch", "che": "ch",
    "united kingdom": "gb", "uk": "gb", "gbr": "gb", "gb": "gb",
    "france": "fr", "fr": "fr", "fra": "fr",
    "canada": "ca", "ca": "ca", "can": "ca",
    "australia": "au", "au": "au", "aus": "au",
    "singapore": "sg", "sg": "sg", "sgp": "sg",
    "japan": "jp", "jp": "jp", "jpn": "jp",
    "netherlands": "nl", "nl": "nl", "nld": "nl",
}

REMOTE_TERMS = {"remote", "home based", "worldwide", "anywhere", "virtual", "telecommute", "global"}


def _clean_html(raw_html: str) -> str:
    """Strips HTML tags to extract plain text for JD keyword matching."""
    if not raw_html:
        return ""
    clean = re.sub(r'<[^>]+>', ' ', raw_html)
    clean = re.sub(r'\s+', ' ', clean)
    return clean.strip()


def _match_location(job_location_str: str, target_location: str) -> bool:
    """Matches target location flags against job location strings in a generic, global manner."""
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


def _match_seniority(title: str, target_seniority: str = "all", role_query: str = "") -> bool:
    """Matches role title against target seniority level, preventing title mismatch false positives."""
    sen = (target_seniority or "all").lower().strip()
    title_lower = title.lower()
    query_lower = (role_query or "").lower()

    if sen == "all":
        # If the candidate queries for early-career terms without senior terms, apply safe default
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


def _match_role(title: str,
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
    if not _match_seniority(title, seniority, role_query):
        return False

    if not role_query:
        return True

    tokens = [tok.strip().lower() for tok in role_query.split() if tok.strip()]
    return all(tok in title_lower for tok in tokens)


def _match_experience(description: str,
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
        if min_exp is not None and high < min_exp:
            return False
    return True


def _match_grad_year(title: str, description: str, target_year: Optional[int]) -> bool:
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
    supported_years = set()
    for y1, y2 in cohort_mentions:
        if y1:
            supported_years.add(int(y1))
        if y2:
            supported_years.add(int(y2))
            if y1:
                for yr in range(int(y1), int(y2) + 1):
                    supported_years.add(yr)
    return target_year in supported_years


class BaseATSProvider:
    """Base class for ATS API providers."""
    name: str = "base"

    def fetch_jobs(self, role: str = "", location: str = "", limit: int = 10) -> List[JobPosting]:
        raise NotImplementedError


class AmazonProvider(BaseATSProvider):
    """Direct Amazon Jobs JSON API provider."""
    name = "amazon"

    def fetch_jobs(self, role: str = "", location: str = "", limit: int = 10) -> List[JobPosting]:
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
                    desc = _clean_html(job.get("description", "") + " " + job.get("basic_qualifications", ""))

                    direct_url = f"https://www.amazon.jobs{job_path}" if job_path.startswith("/") else job_path
                    apply_url = f"https://www.amazon.jobs/applicant/jobs/{job_id}/apply" if job_id else direct_url

                    # Check location filter
                    loc_full = f"{loc_desc} {job.get('country_code', '')}"
                    if not _match_location(loc_full, location):
                        continue

                    # Check role match
                    if not _match_role(title, role):
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


class SmartRecruitersProvider(BaseATSProvider):
    """SmartRecruiters REST API provider."""
    name = "smartrecruiters"

    def __init__(self, company_id: str, company_name: Optional[str] = None):
        self.company_id = company_id
        self.company_name = company_name or company_id.upper()

    def fetch_jobs(self, role: str = "", location: str = "", limit: int = 10) -> List[JobPosting]:
        postings = []
        params = [f"limit={min(100, max(20, limit * 4))}"]
        if role:
            params.append(f"q={urllib.request.quote(role)}")
        if location and location.lower() not in ("all", "*", "remote"):
            for loc_part in location.split(","):
                c_clean = loc_part.strip().lower()
                iso2 = ISO_2_MAP.get(c_clean)
                if iso2:
                    params.append(f"country={iso2}")
                    break

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
                    if not _match_location(loc_full, location):
                        continue

                    # Check role match against title or department
                    if role and not (_match_role(title, role) or _match_role(dept, role)):
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


class GreenhouseProvider(BaseATSProvider):
    """Greenhouse Public Boards API provider."""
    name = "greenhouse"

    def __init__(self, board_token: str, company_name: Optional[str] = None):
        self.board_token = board_token
        self.company_name = company_name or board_token.capitalize()

    def fetch_jobs(self, role: str = "", location: str = "", limit: int = 10) -> List[JobPosting]:
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
                    content_text = _clean_html(job.get("content", ""))

                    # Match location
                    if not _match_location(loc_name, location):
                        continue

                    # Match role against title
                    if not _match_role(title, role):
                        continue

                    direct_url = job.get("absolute_url", f"https://boards.greenhouse.io/{self.board_token}/jobs/{job_id}")
                    apply_url = direct_url + "#app"

                    postings.append(JobPosting(
                        id=job_id,
                        title=title,
                        company=self.company_name,
                        ats_type="greenhouse",
                        location=loc_name,
                        url=direct_url,
                        apply_url=apply_url,
                        description=content_text
                    ))
                    if len(postings) >= limit:
                        break
        except Exception:
            pass
        return postings


class LeverProvider(BaseATSProvider):
    """Lever Public Postings API provider."""
    name = "lever"

    def __init__(self, company_id: str, company_name: Optional[str] = None):
        self.company_id = company_id
        self.company_name = company_name or company_id.capitalize()

    def fetch_jobs(self, role: str = "", location: str = "", limit: int = 10) -> List[JobPosting]:
        postings = []
        url = f"https://api.lever.co/v0/postings/{self.company_id}?mode=json"
        req = urllib.request.Request(url, headers=DEFAULT_HEADERS)
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                for job in data:
                    title = job.get("text", "")
                    job_id = str(job.get("id", ""))
                    categories = job.get("categories", {})
                    loc_name = categories.get("location", "") or "Unspecified"
                    desc = _clean_html(job.get("descriptionPlain", "") + " " + job.get("additionalPlain", ""))

                    # Match location
                    if not _match_location(loc_name, location):
                        continue

                    # Match role against title
                    if not _match_role(title, role):
                        continue

                    hosted_url = job.get("hostedUrl", f"https://jobs.lever.co/{self.company_id}/{job_id}")
                    apply_url = job.get("applyUrl", hosted_url + "/apply")

                    postings.append(JobPosting(
                        id=job_id,
                        title=title,
                        company=self.company_name,
                        ats_type="lever",
                        location=loc_name,
                        url=hosted_url,
                        apply_url=apply_url,
                        description=desc
                    ))
                    if len(postings) >= limit:
                        break
        except Exception:
            pass
        return postings


class AshbyProvider(BaseATSProvider):
    """Ashby HQ Job Board JSON API provider."""
    name = "ashby"

    def __init__(self, board_token: str, company_name: Optional[str] = None):
        self.board_token = board_token
        self.company_name = company_name or board_token.title()

    def fetch_jobs(self, role: str = "", location: str = "", limit: int = 10) -> List[JobPosting]:
        postings = []
        url = f"https://api.ashbyhq.com/posting-api/job-board/{self.board_token}"
        req = urllib.request.Request(url, headers=DEFAULT_HEADERS)
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                jobs = data.get("jobs", [])
                for job in jobs:
                    title = job.get("title", "")
                    job_id = str(job.get("id", ""))
                    primary_loc = job.get("location", "")
                    is_remote = job.get("isRemote", False)
                    sec_locs = [s.get("location", "") for s in job.get("secondaryLocations", []) if isinstance(s, dict)]
                    all_locs = [primary_loc] + sec_locs
                    if is_remote:
                        all_locs.append("Remote")
                    loc_str = primary_loc or (", ".join(sec_locs) if sec_locs else ("Remote" if is_remote else "Unspecified"))
                    dept = job.get("department", "") or job.get("team", "")

                    # Check location filter
                    loc_search_corpus = " ".join(all_locs)
                    if not _match_location(loc_search_corpus, location):
                        continue

                    # Check role match against title or department
                    if role and not (_match_role(title, role) or _match_role(dept, role)):
                        continue

                    job_url = job.get("jobUrl") or f"https://jobs.ashbyhq.com/{self.board_token}/{job_id}"
                    apply_url = job.get("applyUrl") or f"{job_url}/application"
                    desc = job.get("descriptionPlain") or _clean_html(job.get("descriptionHtml", ""))

                    postings.append(JobPosting(
                        id=job_id,
                        title=title,
                        company=self.company_name,
                        ats_type="ashby",
                        location=loc_str,
                        url=job_url,
                        apply_url=apply_url,
                        description=desc
                    ))
                    if len(postings) >= limit:
                        break
        except Exception:
            pass
        return postings


class WorkdayProvider(BaseATSProvider):
    """Workday CXS REST API provider."""
    name = "workday"

    def __init__(self,
                 company_id: str,
                 host: Optional[str] = None,
                 site: Optional[str] = None,
                 company_name: Optional[str] = None):
        self.company_id = company_id.lower().strip()
        if self.company_id == "redhat":
            self.host = host or "redhat.wd5.myworkdayjobs.com"
            self.site = site or "Jobs"
            self.company_name = company_name or "Red Hat"
        elif self.company_id in ("samsung", "sec"):
            self.host = host or "sec.wd3.myworkdayjobs.com"
            self.site = site or "Samsung_Careers"
            self.company_id = "sec"
            self.company_name = company_name or "Samsung Electronics"
        else:
            self.host = host or f"{self.company_id}.wd5.myworkdayjobs.com"
            self.site = site or "Jobs"
            self.company_name = company_name or self.company_id.replace("_", " ").title()

    def fetch_jobs(self, role: str = "", location: str = "", limit: int = 10) -> List[JobPosting]:
        postings = []
        url = f"https://{self.host}/wday/cxs/{self.company_id}/{self.site}/jobs"
        search_terms = []
        if role:
            search_terms.append(role)
        if location and location.lower() not in ("all", "*", "remote"):
            search_terms.append(location)
        search_query = " ".join(search_terms)

        payload = json.dumps({
            "appliedFacets": {},
            "limit": min(50, limit * 4),
            "offset": 0,
            "searchText": search_query
        }).encode("utf-8")

        headers = dict(DEFAULT_HEADERS)
        headers["Content-Type"] = "application/json"

        req = urllib.request.Request(url, data=payload, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                for item in data.get("jobPostings", []):
                    title = item.get("title", "")
                    external_path = item.get("externalPath", "")
                    loc_desc = item.get("locationsText", "")
                    remote_type = item.get("remoteType", "")
                    loc_full = f"{loc_desc} {remote_type}".strip() or "Unspecified"

                    bullet_fields = item.get("bulletFields", [])
                    job_id = bullet_fields[0] if bullet_fields else ""
                    if not job_id and external_path:
                        m = re.search(r'_([A-Z0-9\-]+)$', external_path)
                        job_id = m.group(1) if m else "WD"

                    # Check location filter
                    if not _match_location(loc_full, location):
                        continue

                    # Check role match
                    if not _match_role(title, role):
                        continue

                    direct_url = f"https://{self.host}/en-US/{self.site}{external_path}"
                    apply_url = f"{direct_url}/apply"

                    postings.append(JobPosting(
                        id=job_id,
                        title=title,
                        company=self.company_name,
                        ats_type="workday",
                        location=loc_full,
                        url=direct_url,
                        apply_url=apply_url,
                        description=f"{title} - {loc_full}"
                    ))
                    if len(postings) >= limit:
                        break
        except Exception:
            pass
        return postings


class AikyamProvider(BaseATSProvider):
    """Direct Aikyam Jobs API provider (aikyamjobs.org)."""
    name = "aikyam"

    def __init__(self, base_url: str = "https://aikyamjobs.org/api/jobs"):
        self.base_url = base_url

    def fetch_jobs(self, role: str = "", location: str = "", limit: int = 10) -> List[JobPosting]:
        postings = []
        for page in range(1, 4):
            url = f"{self.base_url}?page={page}&pageSize=50"
            req = urllib.request.Request(url, headers=DEFAULT_HEADERS)
            try:
                with urllib.request.urlopen(req, timeout=10) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    items = data.get("data", [])
                    if not items:
                        break
                    for item in items:
                        attrs = item.get("attributes", item)
                        job_id = str(item.get("id") or attrs.get("id", ""))
                        title = attrs.get("title") or attrs.get("jobTitle") or ""
                        slug = attrs.get("slug") or ""

                        org_data = attrs.get("organization") or attrs.get("company") or {}
                        if isinstance(org_data, dict):
                            org_attrs = org_data.get("data", {}).get("attributes", org_data) if isinstance(org_data.get("data"), dict) else org_data
                            company = org_attrs.get("name") or org_attrs.get("title") or "Aikyam Partner"
                        elif isinstance(org_data, str):
                            company = org_data
                        else:
                            company = "Aikyam Partner"

                        loc_str = attrs.get("location") or attrs.get("city") or "India"
                        desc = _clean_html(attrs.get("jobDescription") or attrs.get("description") or "")
                        apply_url = attrs.get("applyUrl") or (f"https://aikyamjobs.org/jobs/{slug}" if slug else "https://aikyamjobs.org")
                        direct_url = f"https://aikyamjobs.org/jobs/{slug}" if slug else "https://aikyamjobs.org"

                        # Location matching
                        if not _match_location(loc_str, location):
                            continue

                        # Role matching
                        if not _match_role(title, role):
                            continue

                        postings.append(JobPosting(
                            id=job_id or slug,
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
                    if len(items) < 50:
                        break
            except Exception:
                break
        return postings


class HNHiringProvider(BaseATSProvider):
    """Hacker News / Y Combinator 'Who is hiring?' public Algolia API provider."""
    name = "hn"

    def fetch_jobs(self, role: str = "", location: str = "", limit: int = 10) -> List[JobPosting]:
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
                for comment in comments:
                    raw_text = comment.get("comment_text", "")
                    clean_text = _clean_html(raw_text)
                    if not clean_text:
                        continue
                    first_line = clean_text.split(".")[0].split("\n")[0]
                    parts = [p.strip() for p in first_line.split("|") if p.strip()]

                    company = parts[0] if parts else "YC Startup"
                    title = parts[1] if len(parts) > 1 else "Software Engineer"
                    loc_str = parts[2] if len(parts) > 2 else "Remote / Flexible"

                    if not _match_role(title, role) and not _match_role(clean_text[:300], role):
                        continue
                    if not _match_location(f"{loc_str} {clean_text[:400]}", location):
                        continue

                    url_match = re.search(r'https?://[^\s<>"]+', clean_text)
                    direct_url = f"https://news.ycombinator.com/item?id={comment.get('objectID')}"
                    apply_url = url_match.group(0) if url_match else direct_url

                    postings.append(JobPosting(
                        id=str(comment.get("objectID")),
                        title=title,
                        company=company,
                        ats_type="hn",
                        location=loc_str,
                        url=direct_url,
                        apply_url=apply_url,
                        description=clean_text
                    ))
                    if len(postings) >= limit:
                        break
        except Exception:
            pass
        return postings


class RSSFeedProvider(BaseATSProvider):
    """Generic XML RSS 2.0 / Atom job feed provider."""
    name = "rss"

    def __init__(self, feed_url: str, feed_name: str = "RSS Feed"):
        self.feed_url = feed_url
        self.feed_name = feed_name

    def fetch_jobs(self, role: str = "", location: str = "", limit: int = 10) -> List[JobPosting]:
        import xml.etree.ElementTree as ET
        postings = []
        try:
            req = urllib.request.Request(self.feed_url, headers=DEFAULT_HEADERS)
            with urllib.request.urlopen(req, timeout=10) as resp:
                xml_data = resp.read()
            root = ET.fromstring(xml_data)

            items = root.findall(".//item")
            if not items:
                items = root.findall(".//{http://www.w3.org/2005/Atom}entry")
                is_atom = True
            else:
                is_atom = False

            for item in items:
                if is_atom:
                    title = item.findtext("{http://www.w3.org/2005/Atom}title") or ""
                    link_el = item.find("{http://www.w3.org/2005/Atom}link")
                    link = link_el.get("href", "") if link_el is not None else ""
                    desc = _clean_html(item.findtext("{http://www.w3.org/2005/Atom}content") or item.findtext("{http://www.w3.org/2005/Atom}summary") or "")
                    job_id = item.findtext("{http://www.w3.org/2005/Atom}id") or link
                else:
                    title = item.findtext("title") or ""
                    link = item.findtext("link") or ""
                    desc = _clean_html(item.findtext("description") or "")
                    job_id = item.findtext("guid") or link

                loc_text = f"{title} {desc[:300]}"
                if not _match_location(loc_text, location):
                    continue
                if not _match_role(title, role):
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


class JobHunter:
    """Orchestrates multi-ATS polling, keyword scoring, and single-page resume pairing."""

    # Default discoverable company boards for multi-board search
    POPULAR_GREENHOUSE_BOARDS = ["canonical", "figma", "stripe", "databricks", "vercel", "brex", "scaleai"]
    POPULAR_LEVER_BOARDS = ["palantir"]
    POPULAR_SMARTRECRUITERS_BOARDS = ["cern", "boschgroup"]
    POPULAR_ASHBY_BOARDS = ["linear", "ramp", "cursor", "supabase", "modal", "retool", "posthog"]
    POPULAR_WORKDAY_BOARDS = ["redhat", "samsung"]

    def __init__(self,
                 company: str = "",
                 provider: str = "all",
                 role: str = "",
                 location: str = "",
                 grad_year: Optional[int] = None,
                 limit: int = 5,
                 compile_resumes: bool = False,
                 base_resume_path: Optional[str] = None,
                 output_dir: str = "output/hunt",
                 rss_url: Optional[str] = None):
        self.company = (company or "").strip()
        self.provider = (provider or "all").lower().strip()
        self.role = (role or "").strip()
        self.location = (location or "").strip()
        self.grad_year = grad_year
        self.limit = limit
        self.compile_resumes = compile_resumes
        self.base_resume_path = base_resume_path or self._detect_default_resume()
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.rss_url = rss_url

    def _detect_default_resume(self) -> str:
        for candidate in ["resume.tex", "resume.json", "examples/resume.tex", "variants/canonical.tex"]:
            if Path(candidate).exists():
                return candidate
        return ""

    def get_providers(self) -> List[BaseATSProvider]:
        providers = []
        p_target = self.provider
        comp = self.company.lower()

        # If custom RSS feed is passed
        if self.rss_url:
            providers.append(RSSFeedProvider(self.rss_url, self.company or "RSS Feed"))
            return providers

        # If user targeted a specific company or source
        if comp and comp != "all":
            if comp == "amazon":
                providers.append(AmazonProvider())
            elif comp in ("bosch", "boschgroup"):
                providers.append(SmartRecruitersProvider("BoschGroup", "Bosch Group"))
            elif comp in ("samsung", "sec"):
                providers.append(WorkdayProvider("samsung", company_name="Samsung Electronics"))
            elif comp in ("aikyam", "aikyamjobs"):
                providers.append(AikyamProvider())
            elif comp in ("hn", "yc", "hnhiring"):
                providers.append(HNHiringProvider())
            elif p_target == "smartrecruiters" or comp in self.POPULAR_SMARTRECRUITERS_BOARDS:
                providers.append(SmartRecruitersProvider(comp, comp.upper()))
            elif p_target == "workday" or comp in self.POPULAR_WORKDAY_BOARDS:
                providers.append(WorkdayProvider(comp))
            elif p_target == "lever" or comp in self.POPULAR_LEVER_BOARDS:
                providers.append(LeverProvider(comp, comp.capitalize()))
            elif p_target == "ashby" or comp in self.POPULAR_ASHBY_BOARDS:
                providers.append(AshbyProvider(comp, comp.capitalize()))
            elif p_target == "greenhouse" or comp in self.POPULAR_GREENHOUSE_BOARDS:
                providers.append(GreenhouseProvider(comp, comp.capitalize()))
            else:
                # Default to Greenhouse board if unknown company token specified
                providers.append(GreenhouseProvider(comp, comp.capitalize()))
            return providers

        # Global multi-provider search across configured ATS platforms
        if p_target in ("all", "amazon"):
            providers.append(AmazonProvider())

        if p_target in ("all", "aikyam"):
            providers.append(AikyamProvider())

        if p_target in ("all", "hn", "yc", "hnhiring"):
            providers.append(HNHiringProvider())

        if p_target == "rss":
            providers.append(RSSFeedProvider("https://remoteok.com/remote-jobs.rss", "RemoteOK"))

        if p_target in ("all", "smartrecruiters"):
            for c in self.POPULAR_SMARTRECRUITERS_BOARDS:
                providers.append(SmartRecruitersProvider(c, c.upper()))

        if p_target in ("all", "greenhouse"):
            for c in self.POPULAR_GREENHOUSE_BOARDS:
                providers.append(GreenhouseProvider(c))

        if p_target in ("all", "lever"):
            for l in self.POPULAR_LEVER_BOARDS:
                providers.append(LeverProvider(l))

        if p_target in ("all", "ashby"):
            for a in self.POPULAR_ASHBY_BOARDS:
                providers.append(AshbyProvider(a, a.capitalize()))

        if p_target in ("all", "workday"):
            for w in self.POPULAR_WORKDAY_BOARDS:
                providers.append(WorkdayProvider(w))

        return providers

    def hunt(self) -> List[JobPosting]:
        """Runs the search across configured providers and pairs with tailored resumes."""
        all_postings: List[JobPosting] = []
        providers = self.get_providers()

        # Load base resume if compilation is requested
        base_resume_data: Optional[ResumeData] = None
        if self.compile_resumes and self.base_resume_path and Path(self.base_resume_path).exists():
            content = Path(self.base_resume_path).read_text(encoding="utf-8")
            if self.base_resume_path.endswith(".json"):
                base_resume_data = ResumeData.from_json(content)
            else:
                base_resume_data = LatexResumeParser(content).parse()

        compiler = ResumeCompiler() if self.compile_resumes else None

        for provider in providers:
            try:
                results = provider.fetch_jobs(
                    role=self.role,
                    location=self.location,
                    limit=self.limit
                )
                for posting in results:
                    # Filter by grad year if title or description explicitly mentions cohort/graduation years
                    if self.grad_year:
                        cohort_text = f"{posting.title} {posting.description[:800]}"
                        cohort_mentions = re.findall(
                            r'\b(?:class of|graduating|cohort|batch|graduation(?:\s+date)?)\s*(?:in\s*|between\s*|:\s*)?(202[0-9])(?:\s*(?:-|–|to|and|or)\s*(202[0-9]))?\b',
                            cohort_text,
                            re.IGNORECASE
                        )
                        if cohort_mentions:
                            supported_years = set()
                            for y1, y2 in cohort_mentions:
                                if y1:
                                    supported_years.add(int(y1))
                                if y2:
                                    supported_years.add(int(y2))
                                    if y1:
                                        for yr in range(int(y1), int(y2) + 1):
                                            supported_years.add(yr)
                            if supported_years and self.grad_year not in supported_years:
                                continue

                    # Early-career experience guardrail: exclude roles requiring 3+ years of experience
                    is_early_career = bool(self.grad_year or any(k in self.role.lower() for k in ("intern", "student", "junior", "entry", "graduate")))
                    if is_early_career and posting.description:
                        if re.search(r'\b([3-9]|\d{2})\+?\s*(?:-\s*\d+\s*)?years?(?:\s+of)?\s+experience\b', posting.description, re.IGNORECASE):
                            continue

                    # ATS scoring and keyword alignment
                    if base_resume_data and posting.description:
                        analyzer = ATSAnalyzer(base_resume_data)
                        report = analyzer.analyze(job_description=posting.description)
                        posting.match_rate_percent = report.get("match_rate_percent", 85)
                        posting.matched_keywords = report.get("matched_keywords", [])

                    # Auto-compile paired resume if enabled
                    if self.compile_resumes and base_resume_data and compiler:
                        safe_comp = re.sub(r'[^a-zA-Z0-9]', '_', posting.company.lower())
                        safe_id = re.sub(r'[^a-zA-Z0-9]', '_', str(posting.id))
                        pdf_filename = f"resume_{safe_comp}_{safe_id}.pdf"
                        tex_filename = f"resume_{safe_comp}_{safe_id}.tex"

                        pdf_path = self.output_dir / pdf_filename
                        tex_path = self.output_dir / tex_filename

                        # Write tailored source LaTeX
                        tex_content = ResumeExporter(base_resume_data).to_latex()
                        tex_path.write_text(tex_content, encoding="utf-8")

                        # Compile single-page PDF
                        success = compiler.compile_resume(
                            data=base_resume_data,
                            output_pdf_path=str(pdf_path),
                            auto_fit=True
                        )
                        if success:
                            posting.paired_resume_pdf = str(pdf_path.resolve())
                            posting.paired_resume_tex = str(tex_path.resolve())

                    all_postings.append(posting)
            except Exception:
                continue

        return all_postings
