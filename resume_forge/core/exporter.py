"""Resume Exporter: Converts ResumeData into LaTeX (.tex), HTML (for PDF printing), and ATS Markdown."""

import re
from typing import Dict, Any, Optional
from .schema import ResumeData
from ..templates import TemplateRegistry


class ResumeExporter:
    """Exports structured ResumeData to multiple presentation formats."""

    def __init__(self, data: ResumeData):
        self.data = data

    def to_markdown(self) -> str:
        """Generates clean ATS-friendly Markdown."""
        lines = []
        b = self.data.basics
        safe_name = re.sub(r'[{}]', '', b.name).strip() if b.name else ""
        lines.append(f"# {safe_name}")
        contact_parts = []
        if b.email:
            contact_parts.append(b.email)
        if b.phone:
            contact_parts.append(b.phone)
        if b.location.city:
            contact_parts.append(b.location.city)
        if b.url:
            contact_parts.append(b.url)
        for p in b.profiles:
            contact_parts.append(f"{p.network}: {p.url}")
        lines.append(" | ".join(contact_parts))
        lines.append("\n---\n")

        if b.summary:
            lines.append("## Professional Summary")
            lines.append(b.summary)
            lines.append("")

        if self.data.education:
            lines.append("## Education")
            for edu in self.data.education:
                dates = f"{edu.start_date} – {edu.end_date}" if edu.end_date else edu.start_date
                lines.append(f"### {edu.institution} ({dates})")
                if edu.study_type:
                    lines.append(f"**Degree:** {edu.study_type}")
                for h in edu.highlights:
                    lines.append(f"- {h}")
                lines.append("")

        if self.data.work:
            lines.append("## Work Experience")
            for w in self.data.work:
                dates = f"{w.start_date} – {w.end_date}" if w.end_date else w.start_date
                loc = f" | {w.location}" if w.location else ""
                lines.append(f"### {w.position} at {w.name} ({dates}){loc}")
                for h in w.highlights:
                    lines.append(f"- {h}")
                lines.append("")

        if self.data.open_source:
            lines.append("## Open-Source Contributions")
            for os_item in self.data.open_source:
                role = f" ({os_item.role})" if os_item.role else ""
                lines.append(f"### {os_item.project}{role}")
                for h in os_item.highlights:
                    lines.append(f"- {h}")
                lines.append("")

        if self.data.projects:
            lines.append("## Key Projects")
            for p in self.data.projects:
                tech = f" [{', '.join(p.keywords)}]" if p.keywords else ""
                lines.append(f"### {p.name}{tech}")
                if p.description:
                    lines.append(f"*{p.description}*")
                for h in p.highlights:
                    lines.append(f"- {h}")
                lines.append("")

        if self.data.skills:
            lines.append("## Technical Skills")
            for s in self.data.skills:
                lines.append(f"- **{s.name}:** {', '.join(s.keywords)}")
            lines.append("")

        if self.data.certificates:
            lines.append("## Certifications")
            for c in self.data.certificates:
                date_str = f" ({c.date})" if c.date else ""
                issuer_str = f" - {c.issuer}" if c.issuer else ""
                lines.append(f"- **{c.name}**{issuer_str}{date_str}")
            lines.append("")

        if self.data.awards:
            lines.append("## Honors & Awards")
            for a in self.data.awards:
                date_str = f" ({a.date})" if a.date else ""
                awarder_str = f" - {a.awarder}" if a.awarder else ""
                lines.append(f"- **{a.title}**{awarder_str}{date_str}")
            lines.append("")

        if self.data.publications:
            lines.append("## Publications")
            for pub in self.data.publications:
                lines.append(f"- {pub.name}")
            lines.append("")

        if self.data.languages:
            lines.append("## Languages")
            lang_strs = [f"{l.language} ({l.fluency})" if l.fluency else l.language for l in self.data.languages]
            lines.append(", ".join(lang_strs))
            lines.append("")

        return "\n".join(lines)

    def to_latex(self, template: str = "cern") -> str:
        """Generates industry-standard, ATS-optimized single-page LaTeX code using the specified template."""
        tmpl = TemplateRegistry.get(template)
        return tmpl.render_latex(self.data)

    def to_html(
        self,
        template: str = "cern",
        font_size_pt: Optional[float] = None,
        line_height: Optional[float] = None,
        margin_in: Optional[float] = None
    ) -> str:
        """Generates pixel-perfect HTML styled for single-page print-to-PDF."""
        # Handle backward compatibility where someone called to_html(10.0, 1.25, 0.4)
        if isinstance(template, (int, float)):
            f_size = float(template)
            l_height = line_height if line_height is not None else 1.25
            m_in = margin_in if margin_in is not None else 0.4
            tmpl = TemplateRegistry.get("cern")
            return tmpl.render_html(self.data, font_size_pt=f_size, line_height=l_height, margin_in=m_in)

        tmpl = TemplateRegistry.get(template)
        f_size = font_size_pt if font_size_pt is not None else tmpl.default_font_size
        l_height = line_height if line_height is not None else tmpl.default_line_height
        m_in = margin_in if margin_in is not None else tmpl.default_margin
        return tmpl.render_html(self.data, font_size_pt=f_size, line_height=l_height, margin_in=m_in)
