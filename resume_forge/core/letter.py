"""Cover Letter data models, serialization, and AI/rule-based synthesis."""

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Dict, Any, List, Optional
from .schema import ResumeData, Basics


@dataclass
class CoverLetterRecipient:
    """Recipient information for formal cover letters."""
    name: str = ""
    title: str = "Hiring Team"
    company: str = "Target Company"
    address: str = ""
    city: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "title": self.title,
            "company": self.company,
            "address": self.address,
            "city": self.city,
        }

    @classmethod
    def from_dict(cls, d: Optional[Dict[str, Any]]) -> "CoverLetterRecipient":
        if not d:
            return cls()
        return cls(
            name=d.get("name", ""),
            title=d.get("title", "Hiring Team"),
            company=d.get("company", "Target Company"),
            address=d.get("address", ""),
            city=d.get("city", "")
        )


@dataclass
class CoverLetterData:
    """Structured data representation of a tailored single-page cover letter."""
    sender: Basics = field(default_factory=Basics)
    recipient: CoverLetterRecipient = field(default_factory=CoverLetterRecipient)
    date: str = ""
    job_title: str = "Software Engineer"
    salutation: str = ""
    opening: str = ""
    body_paragraphs: List[str] = field(default_factory=list)
    closing: str = ""
    sign_off: str = "Sincerely,"

    def __post_init__(self):
        if not self.date:
            self.date = datetime.now().strftime("%B %d, %Y")
        if not self.salutation:
            comp = self.recipient.company if self.recipient.company else "the team"
            if self.recipient.name:
                self.salutation = f"Dear {self.recipient.name},"
            else:
                self.salutation = f"Dear Hiring Team at {comp},"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "CoverLetterData":
        from .schema import ResumeData
        dummy_resume = ResumeData.from_dict({"basics": d.get("sender", {})})
        sender = dummy_resume.basics
        recipient = CoverLetterRecipient.from_dict(d.get("recipient", {}))
        return cls(
            sender=sender,
            recipient=recipient,
            date=d.get("date", ""),
            job_title=d.get("job_title", "Software Engineer"),
            salutation=d.get("salutation", ""),
            opening=d.get("opening", ""),
            body_paragraphs=d.get("body_paragraphs", []),
            closing=d.get("closing", ""),
            sign_off=d.get("sign_off", "Sincerely,")
        )

    @classmethod
    def from_json(cls, json_str: str) -> "CoverLetterData":
        return cls.from_dict(json.loads(json_str))

    @classmethod
    def from_resume(
        cls,
        resume: ResumeData,
        company: str = "Target Company",
        role: str = "Software Engineer",
        recipient_name: str = "",
        recipient_title: str = "Hiring Team",
        city: str = ""
    ) -> "CoverLetterData":
        """Synthesizes a structured, high-impact cover letter tailored from candidate ResumeData."""
        recipient = CoverLetterRecipient(
            name=recipient_name,
            title=recipient_title,
            company=company,
            city=city
        )

        candidate_name = resume.basics.name or "Candidate"
        top_skills = []
        if resume.skills:
            for s in resume.skills[:2]:
                top_skills.extend(s.keywords[:3])
        skills_str = ", ".join(top_skills[:5]) if top_skills else "distributed systems and software development"

        # Extract top highlight from work
        work_story = ""
        if resume.work:
            w = resume.work[0]
            if w.highlights:
                work_story = f"Most recently at {w.name} as a {w.position or 'Engineer'}, I {w.highlights[0][0].lower() + w.highlights[0][1:]}"
            else:
                work_story = f"In my recent role at {w.name} as a {w.position or 'Engineer'}, I developed production-grade systems with high reliability."

        # Extract top project or open-source contribution
        project_story = ""
        if resume.projects:
            p = resume.projects[0]
            if p.highlights:
                project_story = f"Additionally, I architected {p.name}, where I {p.highlights[0][0].lower() + p.highlights[0][1:]}"
        elif resume.open_source:
            o = resume.open_source[0]
            if o.highlights:
                project_story = f"Furthermore, in my open-source work on {o.project}, I {o.highlights[0][0].lower() + o.highlights[0][1:]}"

        opening = (
            f"I am writing to express my enthusiastic interest in the {role} position at {company}. "
            f"With a strong foundation in {skills_str} and a proven track record of engineering robust, scalable solutions, "
            f"I am eager to contribute to {company}'s technical vision and ongoing innovations."
        )

        body_paragraphs = []
        if work_story:
            body_paragraphs.append(work_story)
        if project_story:
            body_paragraphs.append(project_story)

        if not body_paragraphs:
            body_paragraphs.append(
                f"Throughout my engineering experience, I have focused on building performant software architectures, "
                f"prioritizing code cleanliness, automated testing, and seamless user experiences."
            )

        closing = (
            f"I admire {company}'s engineering discipline and would welcome the opportunity to discuss how my "
            f"technical background and proactive problem-solving mindset can deliver measurable impact to your team. "
            f"Thank you for your time and consideration."
        )

        return cls(
            sender=resume.basics,
            recipient=recipient,
            job_title=role,
            opening=opening,
            body_paragraphs=body_paragraphs,
            closing=closing,
            sign_off="Sincerely,"
        )
