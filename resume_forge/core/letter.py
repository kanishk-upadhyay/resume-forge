"""Cover Letter data models, serialization, and AI/rule-based synthesis."""

import json
import re
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
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

        def _clean_highlight(text: str) -> str:
            if not text:
                return ""
            # Strip LaTeX commands like \textbf{...} -> ...
            clean = re.sub(r'\\(?:textbf|textit|emph|textsc|texttt|underline)\s*\{((?:[^{}]|\{[^{}]*\})*)\}', r'\1', text)
            clean = re.sub(r'\\[a-zA-Z]+(?:\*|\b)(?:\[[^\]]*\])?(?:\{[^{}]*\})?', '', clean)
            clean = clean.replace(r'\%', '%').replace(r'\&', '&').replace(r'\$', '$').replace(r'\_', '_')
            clean = re.sub(r'[{}]', '', clean).strip()
            return clean

        # Extract top highlight from work safely
        work_story = ""
        if resume.work:
            w = resume.work[0]
            valid_bullets = [b.strip() for b in w.highlights if b and b.strip()]
            if valid_bullets:
                clean_b = _clean_highlight(valid_bullets[0])
                if clean_b:
                    action_verb = clean_b[0].lower() + clean_b[1:]
                    work_story = f"Most recently at {w.name} as a {w.position or 'Engineer'}, I {action_verb}"
            if not work_story:
                work_story = f"In my recent role at {w.name} as a {w.position or 'Engineer'}, I developed production-grade systems with high reliability."

        # Extract top project or open-source contribution safely
        project_story = ""
        if resume.projects:
            p = resume.projects[0]
            valid_bullets = [b.strip() for b in p.highlights if b and b.strip()]
            if valid_bullets:
                clean_b = _clean_highlight(valid_bullets[0])
                if clean_b:
                    action_verb = clean_b[0].lower() + clean_b[1:]
                    project_story = f"Additionally, I architected {p.name}, where I {action_verb}"
        elif resume.open_source:
            o = resume.open_source[0]
            valid_bullets = [b.strip() for b in o.highlights if b and b.strip()]
            if valid_bullets:
                clean_b = _clean_highlight(valid_bullets[0])
                if clean_b:
                    action_verb = clean_b[0].lower() + clean_b[1:]
                    project_story = f"Furthermore, in my open-source work on {o.project}, I {action_verb}"

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

        import copy
        sender = copy.deepcopy(resume.basics) if resume.basics else Basics()
        if not sender.name:
            sender.name = "Candidate"

        return cls(
            sender=sender,
            recipient=recipient,
            job_title=role,
            opening=opening,
            body_paragraphs=body_paragraphs,
            closing=closing,
            sign_off="Sincerely,"
        )


class LatexCoverLetterParser:
    """Parses raw LaTeX cover letter documents into CoverLetterData."""

    def __init__(self, latex_content: Union[str, Path]):
        if hasattr(latex_content, "read_text"):
            latex_content = latex_content.read_text(encoding="utf-8")
        elif isinstance(latex_content, bytes):
            latex_content = latex_content.decode("utf-8")
        elif not isinstance(latex_content, str):
            latex_content = str(latex_content)
        self.raw = latex_content or ""

    def parse(self) -> CoverLetterData:
        # Strip comments
        cleaned = re.sub(r'(?<!\\)%.*$', '', self.raw, flags=re.MULTILINE)

        # 1. Name
        name_match = re.search(r'\{\s*\\(?:LARGE|Large|Huge|huge)\s*(?:\\textbf\{)?([^}]+)\}?', cleaned)
        if not name_match:
            name_match = re.search(r'\\textbf\{([A-Z][a-zA-Z\s]+)\}', cleaned)
        name = name_match.group(1).strip() if name_match else "Candidate"
        name = re.sub(r'[{}\\]', '', name).strip()

        # 2. Contact details
        email_match = re.search(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', cleaned)
        email = email_match.group(0) if email_match else ""

        phone_match = re.search(r'[\+]?[(]?[0-9]{1,4}[)]?[-\s./0-9]{6,15}', cleaned)
        phone = phone_match.group(0) if phone_match else ""

        # 3. Salutation
        sal_match = re.search(r'(?:\\textbf\{)?(Dear\s+[^,\n]+,)(?:\})?', cleaned)
        salutation = sal_match.group(1).strip() if sal_match else "Dear Hiring Team,"

        # 4. Sign-off
        sign_off_match = re.search(r'\b(Sincerely|Regards|Best regards|Respectfully|Warm regards),', cleaned, re.IGNORECASE)
        sign_off = sign_off_match.group(0).strip() if sign_off_match else "Sincerely,"

        # 5. Extract body content between salutation and sign-off
        body_paragraphs = []
        if sal_match:
            post_sal = cleaned[sal_match.end():]
            if sign_off_match:
                end_idx = post_sal.find(sign_off_match.group(0))
                body_raw = post_sal[:end_idx] if end_idx != -1 else post_sal
            else:
                body_raw = post_sal

            # Clean LaTeX spacing and commands from body
            body_clean = re.sub(r'\\vspace\{[^}]*\}', '\n', body_raw)
            body_clean = re.sub(r'\\(?:hrule|newpage|bigskip|medskip|smallskip)', '', body_clean)
            body_clean = re.sub(r'\\(?:textbf|textit|emph|textsc|texttt|underline)\s*\{((?:[^{}]|\{[^{}]*\})*)\}', r'\1', body_clean)
            body_clean = re.sub(r'\\[a-zA-Z]+(?:\*|\b)(?:\[[^\]]*\])?(?:\{[^{}]*\})?', '', body_clean)
            body_clean = re.sub(r'[{}]', '', body_clean)

            # Split paragraphs
            raw_paras = [p.strip() for p in re.split(r'\n\s*\n', body_clean) if p.strip()]
            for p in raw_paras:
                p_norm = re.sub(r'\s+', ' ', p).strip()
                if len(p_norm) > 15:
                    body_paragraphs.append(p_norm)

        opening = body_paragraphs[0] if body_paragraphs else "I am writing to express my interest in this position."
        closing = body_paragraphs[-1] if len(body_paragraphs) > 1 else "Thank you for your consideration."
        middle = body_paragraphs[1:-1] if len(body_paragraphs) > 2 else []

        sender = Basics(name=name, email=email, phone=phone)
        return CoverLetterData(
            sender=sender,
            salutation=salutation,
            opening=opening,
            body_paragraphs=middle,
            closing=closing,
            sign_off=sign_off
        )
