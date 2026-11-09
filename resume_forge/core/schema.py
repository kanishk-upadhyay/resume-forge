"""JSON Resume standard schema dataclasses and serialization helpers."""

from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Any
import json


@dataclass
class Location:
    city: str = ""
    region: str = ""
    country_code: str = ""
    postal_code: str = ""
    address: str = ""


@dataclass
class Profile:
    network: str = ""
    username: str = ""
    url: str = ""


@dataclass
class Basics:
    name: str = ""
    label: str = ""
    email: str = ""
    phone: str = ""
    url: str = ""
    summary: str = ""
    location: Location = field(default_factory=Location)
    profiles: List[Profile] = field(default_factory=list)


@dataclass
class WorkItem:
    name: str = ""
    position: str = ""
    url: str = ""
    start_date: str = ""
    end_date: str = ""
    summary: str = ""
    highlights: List[str] = field(default_factory=list)
    location: str = ""


@dataclass
class EducationItem:
    institution: str = ""
    url: str = ""
    area: str = ""
    study_type: str = ""
    start_date: str = ""
    end_date: str = ""
    score: str = ""
    courses: List[str] = field(default_factory=list)
    highlights: List[str] = field(default_factory=list)


@dataclass
class ProjectItem:
    name: str = ""
    description: str = ""
    highlights: List[str] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)
    start_date: str = ""
    end_date: str = ""
    url: str = ""
    roles: List[str] = field(default_factory=list)


@dataclass
class SkillItem:
    name: str = ""
    level: str = ""
    keywords: List[str] = field(default_factory=list)


@dataclass
class OpenSourceItem:
    project: str = ""
    role: str = ""
    url: str = ""
    highlights: List[str] = field(default_factory=list)


@dataclass
class CertificateItem:
    name: str = ""
    date: str = ""
    issuer: str = ""
    url: str = ""


@dataclass
class AwardItem:
    title: str = ""
    date: str = ""
    awarder: str = ""
    summary: str = ""


@dataclass
class PublicationItem:
    name: str = ""
    publisher: str = ""
    release_date: str = ""
    url: str = ""
    summary: str = ""


@dataclass
class LanguageItem:
    language: str = ""
    fluency: str = ""


@dataclass
class ResumeData:
    basics: Basics = field(default_factory=Basics)
    work: List[WorkItem] = field(default_factory=list)
    education: List[EducationItem] = field(default_factory=list)
    projects: List[ProjectItem] = field(default_factory=list)
    skills: List[SkillItem] = field(default_factory=list)
    open_source: List[OpenSourceItem] = field(default_factory=list)
    certificates: List[CertificateItem] = field(default_factory=list)
    awards: List[AwardItem] = field(default_factory=list)
    publications: List[PublicationItem] = field(default_factory=list)
    languages: List[LanguageItem] = field(default_factory=list)
    meta: Dict[str, Any] = field(default_factory=lambda: {
        "version": "1.0.0",
        "canonical": "https://jsonresume.org/schema/",
        "generator": "resume-forge"
    })

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ResumeData":
        if not data or not isinstance(data, dict):
            return cls()

        def _str(val: Any) -> str:
            return "" if val is None else str(val)

        def _str_list(val: Any) -> List[str]:
            if not val:
                return []
            if isinstance(val, list):
                return [_str(x) for x in val if x is not None]
            if isinstance(val, str):
                return [s.strip() for s in val.split(",") if s.strip()]
            return [_str(val)]

        basics_data = data.get("basics") or {}
        location_data = basics_data.get("location") or {}
        location_dict = {
            "city": _str(location_data.get("city", "")),
            "region": _str(location_data.get("region", "")),
            "country_code": _str(location_data.get("country_code") or location_data.get("countryCode", "")),
            "postal_code": _str(location_data.get("postal_code") or location_data.get("postalCode", "")),
            "address": _str(location_data.get("address", ""))
        }
        location = Location(**location_dict)

        raw_profiles = basics_data.get("profiles") or []
        profiles = []
        for p in raw_profiles:
            if isinstance(p, dict):
                profiles.append(Profile(
                    network=_str(p.get("network", "")),
                    username=_str(p.get("username", "")),
                    url=_str(p.get("url", ""))
                ))

        basics = Basics(
            name=_str(basics_data.get("name", "")),
            label=_str(basics_data.get("label", "")),
            email=_str(basics_data.get("email", "")),
            phone=_str(basics_data.get("phone", "")),
            url=_str(basics_data.get("url", "")),
            summary=_str(basics_data.get("summary", "")),
            location=location,
            profiles=profiles
        )

        work = []
        for item in (data.get("work") or []):
            if isinstance(item, dict):
                work.append(WorkItem(
                    name=_str(item.get("name", "")),
                    position=_str(item.get("position", "")),
                    url=_str(item.get("url", "")),
                    start_date=_str(item.get("start_date") or item.get("startDate", "")),
                    end_date=_str(item.get("end_date") or item.get("endDate", "")),
                    summary=_str(item.get("summary", "")),
                    highlights=_str_list(item.get("highlights", [])),
                    location=_str(item.get("location", ""))
                ))

        education = []
        for item in (data.get("education") or []):
            if isinstance(item, dict):
                education.append(EducationItem(
                    institution=_str(item.get("institution", "")),
                    url=_str(item.get("url", "")),
                    area=_str(item.get("area", "")),
                    study_type=_str(item.get("study_type") or item.get("studyType", "")),
                    start_date=_str(item.get("start_date") or item.get("startDate", "")),
                    end_date=_str(item.get("end_date") or item.get("endDate", "")),
                    score=_str(item.get("score", "")),
                    courses=_str_list(item.get("courses", [])),
                    highlights=_str_list(item.get("highlights", []))
                ))

        projects = []
        for item in (data.get("projects") or []):
            if isinstance(item, dict):
                projects.append(ProjectItem(
                    name=_str(item.get("name", "")),
                    description=_str(item.get("description", "")),
                    highlights=_str_list(item.get("highlights", [])),
                    keywords=_str_list(item.get("keywords", [])),
                    start_date=_str(item.get("start_date") or item.get("startDate", "")),
                    end_date=_str(item.get("end_date") or item.get("endDate", "")),
                    url=_str(item.get("url", "")),
                    roles=_str_list(item.get("roles", []))
                ))

        skills = []
        for item in (data.get("skills") or []):
            if isinstance(item, dict):
                skills.append(SkillItem(
                    name=_str(item.get("name", "")),
                    level=_str(item.get("level", "")),
                    keywords=_str_list(item.get("keywords", []))
                ))

        open_source = []
        for item in (data.get("open_source") or []):
            if isinstance(item, dict):
                open_source.append(OpenSourceItem(
                    project=_str(item.get("project", "")),
                    role=_str(item.get("role", "")),
                    url=_str(item.get("url", "")),
                    highlights=_str_list(item.get("highlights", []))
                ))
        if not open_source and data.get("volunteer"):
            for item in data.get("volunteer", []):
                if isinstance(item, dict):
                    open_source.append(OpenSourceItem(
                        project=_str(item.get("organization", "")),
                        role=_str(item.get("position", "")),
                        url=_str(item.get("url", "")),
                        highlights=_str_list(item.get("highlights", []))
                    ))

        certificates = []
        for item in (data.get("certificates") or []):
            if isinstance(item, dict):
                certificates.append(CertificateItem(
                    name=_str(item.get("name", "")),
                    date=_str(item.get("date") or item.get("issueDate") or item.get("releaseDate", "")),
                    issuer=_str(item.get("issuer", "")),
                    url=_str(item.get("url", ""))
                ))

        awards = []
        for item in (data.get("awards") or []):
            if isinstance(item, dict):
                awards.append(AwardItem(
                    title=_str(item.get("title", "")),
                    date=_str(item.get("date", "")),
                    awarder=_str(item.get("awarder") or item.get("organization", "")),
                    summary=_str(item.get("summary", ""))
                ))

        publications = []
        for item in (data.get("publications") or []):
            if isinstance(item, dict):
                publications.append(PublicationItem(
                    name=_str(item.get("name", "")),
                    publisher=_str(item.get("publisher", "")),
                    release_date=_str(item.get("release_date") or item.get("releaseDate", "")),
                    url=_str(item.get("url", "")),
                    summary=_str(item.get("summary", ""))
                ))

        languages = []
        for item in (data.get("languages") or []):
            if isinstance(item, dict):
                languages.append(LanguageItem(
                    language=_str(item.get("language", "")),
                    fluency=_str(item.get("fluency", ""))
                ))

        return cls(
            basics=basics,
            work=work,
            education=education,
            projects=projects,
            skills=skills,
            open_source=open_source,
            certificates=certificates,
            awards=awards,
            publications=publications,
            languages=languages,
            meta=data.get("meta") or {}
        )

    @classmethod
    def from_json(cls, json_str: str) -> "ResumeData":
        return cls.from_dict(json.loads(json_str))
