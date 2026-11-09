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
        basics_data = data.get("basics", {})
        location_data = basics_data.get("location", {})
        location = Location(**{k: v for k, v in location_data.items() if k in Location.__annotations__})
        
        profiles = [
            Profile(**{k: v for k, v in p.items() if k in Profile.__annotations__})
            for p in basics_data.get("profiles", [])
        ]
        
        basics_kwargs = {k: v for k, v in basics_data.items() if k in Basics.__annotations__ and k not in ("location", "profiles")}
        basics = Basics(location=location, profiles=profiles, **basics_kwargs)
        
        work = [
            WorkItem(**{k: v for k, v in item.items() if k in WorkItem.__annotations__})
            for item in data.get("work", [])
        ]
        
        education = [
            EducationItem(**{k: v for k, v in item.items() if k in EducationItem.__annotations__})
            for item in data.get("education", [])
        ]
        
        projects = [
            ProjectItem(**{k: v for k, v in item.items() if k in ProjectItem.__annotations__})
            for item in data.get("projects", [])
        ]
        
        skills = [
            SkillItem(**{k: v for k, v in item.items() if k in SkillItem.__annotations__})
            for item in data.get("skills", [])
        ]

        open_source = [
            OpenSourceItem(**{k: v for k, v in item.items() if k in OpenSourceItem.__annotations__})
            for item in data.get("open_source", [])
        ]

        certificates = [
            CertificateItem(**{k: v for k, v in item.items() if k in CertificateItem.__annotations__})
            for item in data.get("certificates", [])
        ]

        awards = [
            AwardItem(**{k: v for k, v in item.items() if k in AwardItem.__annotations__})
            for item in data.get("awards", [])
        ]

        raw_pubs = data.get("publications", [])
        publications = []
        for pub in raw_pubs:
            p_dict = dict(pub)
            if "releaseDate" in p_dict and "release_date" not in p_dict:
                p_dict["release_date"] = p_dict["releaseDate"]
            publications.append(PublicationItem(**{k: v for k, v in p_dict.items() if k in PublicationItem.__annotations__}))

        languages = [
            LanguageItem(**{k: v for k, v in item.items() if k in LanguageItem.__annotations__})
            for item in data.get("languages", [])
        ]
        
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
            meta=data.get("meta", {})
        )

    @classmethod
    def from_json(cls, json_str: str) -> "ResumeData":
        return cls.from_dict(json.loads(json_str))
