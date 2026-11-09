"""Resume Exporter: Converts ResumeData into LaTeX (.tex), HTML (for PDF printing), and ATS Markdown."""

import re
from html import escape as html_escape
from typing import Dict, Any, Optional
from .schema import ResumeData


class ResumeExporter:
    """Exports structured ResumeData to multiple presentation formats."""

    def __init__(self, data: ResumeData):
        self.data = data

    def to_markdown(self) -> str:
        """Generates clean ATS-friendly Markdown."""
        lines = []
        b = self.data.basics
        lines.append(f"# {b.name}")
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
        """Generates industry-standard, ATS-optimized single-page LaTeX code."""
        b = self.data.basics
        
        # Escape helpers for LaTeX (prevents double-escaping)
        def esc(s: str) -> str:
            if not s:
                return ""
            s = re.sub(r'(?<!\\)&', r'\&', s)
            s = re.sub(r'(?<!\\)%', r'\%', s)
            s = re.sub(r'(?<!\\)\$', r'\$', s)
            s = re.sub(r'(?<!\\)#', r'\#', s)
            s = re.sub(r'(?<!\\)_', r'\_', s)
            s = s.replace('<', r'\textless{}').replace('>', r'\textgreater{}')
            return s

        contact_items = []
        if b.phone:
            contact_items.append(esc(b.phone))
        if b.email:
            contact_items.append(r'\href{mailto:' + b.email + '}{' + esc(b.email) + '}')
        if b.location.city:
            contact_items.append(esc(b.location.city))
        if b.url:
            clean_url = b.url.replace("https://", "").replace("http://", "")
            contact_items.append(r'\href{' + b.url + '}{' + esc(clean_url) + '}')
        for p in b.profiles:
            clean_u = p.url.replace("https://", "").replace("http://", "")
            contact_items.append(r'\href{' + p.url + '}{' + esc(clean_u) + '}')

        contact_line = " $|$ ".join(contact_items)

        tex = [
            r"\documentclass[letterpaper,10pt]{article}",
            r"\usepackage[T1]{fontenc}",
            r"\usepackage{latexsym}",
            r"\usepackage[empty]{fullpage}",
            r"\usepackage{titlesec}",
            r"\usepackage{marvosym}",
            r"\usepackage[usenames,dvipsnames]{color}",
            r"\usepackage{verbatim}",
            r"\usepackage{enumitem}",
            r"\usepackage[hidelinks]{hyperref}",
            r"\usepackage{fancyhdr}",
            r"\usepackage[english]{babel}",
            r"\usepackage{tabularx}",
            r"\pagestyle{fancy}",
            r"\fancyhf{}",
            r"\renewcommand{\headrulewidth}{0pt}",
            r"\renewcommand{\footrulewidth}{0pt}",
            r"\addtolength{\oddsidemargin}{-0.5in}",
            r"\addtolength{\evensidemargin}{-0.5in}",
            r"\addtolength{\textwidth}{1in}",
            r"\addtolength{\topmargin}{-.5in}",
            r"\addtolength{\textheight}{1.0in}",
            r"\urlstyle{same}",
            r"\raggedbottom",
            r"\raggedright",
            r"\setlength{\tabcolsep}{0in}",
            "",
            r"% Sections formatting",
            r"\titleformat{\section}{",
            r"  \vspace{-4pt}\scshape\raggedright\large",
            r"}{}{0em}{}[\color{black}\titlerule \vspace{-5pt}]",
            "",
            r"% Custom commands",
            r"\newcommand{\resumeItem}[1]{\item\small{{#1 \vspace{-2pt}}}}",
            r"\newcommand{\resumeSubheading}[4]{",
            r"  \vspace{-2pt}\item",
            r"    \begin{tabular*}{0.97\textwidth}[t]{l@{\extracolsep{\fill}}r}",
            r"      \textbf{#1} & #2 \\",
            r"      \textit{\small#3} & \textit{\small #4} \\",
            r"    \end{tabular*}\vspace{-7pt}",
            r"}",
            r"\newcommand{\resumeProjectHeading}[2]{",
            r"    \item",
            r"    \begin{tabular*}{0.97\textwidth}{l@{\extracolsep{\fill}}r}",
            r"      \small#1 & #2 \\",
            r"    \end{tabular*}\vspace{-7pt}",
            r"}",
            r"\newcommand{\resumeSubItem}[1]{\resumeItem{#1}\vspace{-4pt}}",
            r"\renewcommand\labelitemii{$\vcenter{\hbox{\tiny$\bullet$}}$}",
            r"\newcommand{\resumeSubHeadingListStart}{\begin{itemize}[leftmargin=0.15in, label={}]}",
            r"\newcommand{\resumeSubHeadingListEnd}{\end{itemize}}",
            r"\newcommand{\resumeItemListStart}{\begin{itemize}}",
            r"\newcommand{\resumeItemListEnd}{\end{itemize}\vspace{-5pt}}",
            "",
            r"\begin{document}",
            "",
            r"%----------HEADING----------",
            r"\begin{center}",
            rf"    \textbf{{\Huge \scshape {esc(b.name)}}} \\ \vspace{{1pt}}",
            rf"    \small {contact_line}",
            r"\end{center}",
            ""
        ]

        # Professional Summary
        if b.summary:
            tex.append(r"%-----------SUMMARY-----------")
            tex.append(r"\section{Professional Summary}")
            tex.append(rf"{esc(b.summary)}")
            tex.append(r"\vspace{-4pt}")
            tex.append("")

        # Education
        if self.data.education:
            tex.append(r"%-----------EDUCATION-----------")
            tex.append(r"\section{Education}")
            tex.append(r"\resumeSubHeadingListStart")
            for edu in self.data.education:
                dates = f"{edu.start_date} -- {edu.end_date}" if edu.end_date else edu.start_date
                tex.append(rf"  \resumeSubheading{{{esc(edu.institution)}}}{{{esc(dates)}}}{{{esc(edu.study_type)}}}{{{esc(edu.area)}}}")
                if edu.highlights:
                    tex.append(r"  \resumeItemListStart")
                    for h in edu.highlights:
                        tex.append(rf"    \resumeItem{{{esc(h)}}}")
                    tex.append(r"  \resumeItemListEnd")
            tex.append(r"\resumeSubHeadingListEnd")
            tex.append("")

        # Experience
        if self.data.work:
            tex.append(r"%-----------EXPERIENCE-----------")
            tex.append(r"\section{Experience}")
            tex.append(r"\resumeSubHeadingListStart")
            for w in self.data.work:
                dates = f"{w.start_date} -- {w.end_date}" if w.end_date else w.start_date
                tex.append(rf"  \resumeSubheading{{{esc(w.position)}}}{{{esc(dates)}}}{{{esc(w.name)}}}{{{esc(w.location)}}}")
                if w.highlights:
                    tex.append(r"  \resumeItemListStart")
                    for h in w.highlights:
                        tex.append(rf"    \resumeItem{{{esc(h)}}}")
                    tex.append(r"  \resumeItemListEnd")
            tex.append(r"\resumeSubHeadingListEnd")
            tex.append("")

        # Open Source
        if self.data.open_source:
            tex.append(r"%-----------OPEN-SOURCE CONTRIBUTIONS-----------")
            tex.append(r"\section{Open-Source Contributions}")
            tex.append(r"\resumeSubHeadingListStart")
            for os_item in self.data.open_source:
                tex.append(rf"  \resumeSubheading{{{esc(os_item.project)}}}{{}}{{{esc(os_item.role)}}}{{}}")
                if os_item.highlights:
                    tex.append(r"  \resumeItemListStart")
                    for h in os_item.highlights:
                        tex.append(rf"    \resumeItem{{{esc(h)}}}")
                    tex.append(r"  \resumeItemListEnd")
            tex.append(r"\resumeSubHeadingListEnd")
            tex.append("")

        # Projects
        if self.data.projects:
            tex.append(r"%-----------PROJECTS-----------")
            tex.append(r"\section{Projects}")
            tex.append(r"\resumeSubHeadingListStart")
            for p in self.data.projects:
                tech_str = rf"$|$ \emph{{{esc(', '.join(p.keywords))}}}" if p.keywords else ""
                url_str = rf" \href{{{p.url}}}{{[Link]}}" if p.url else ""
                header = rf"\textbf{{{esc(p.name)}}}{url_str} {tech_str}"
                dates = f"{p.start_date} -- {p.end_date}" if p.end_date else p.start_date
                tex.append(rf"  \resumeProjectHeading{{{header}}}{{{esc(dates)}}}")
                if p.highlights:
                    tex.append(r"  \resumeItemListStart")
                    for h in p.highlights:
                        tex.append(rf"    \resumeItem{{{esc(h)}}}")
                    tex.append(r"  \resumeItemListEnd")
            tex.append(r"\resumeSubHeadingListEnd")
            tex.append("")

        # Skills
        if self.data.skills:
            tex.append(r"%-----------TECHNICAL SKILLS-----------")
            tex.append(r"\section{Technical Skills}")
            tex.append(r"\begin{itemize}[leftmargin=0.15in, label={}]")
            tex.append(r"    \small{\item{")
            for s in self.data.skills:
                tex.append(rf"     \textbf{{{esc(s.name)}}}{{: {esc(', '.join(s.keywords))}}} \\")
            tex.append(r"    }}")
            tex.append(r"\end{itemize}")
            tex.append("")

        # Certifications
        if self.data.certificates:
            tex.append(r"%-----------CERTIFICATIONS-----------")
            tex.append(r"\section{Certifications}")
            tex.append(r"\begin{itemize}[leftmargin=0.15in, label={}]")
            for c in self.data.certificates:
                date_str = f" ({c.date})" if c.date else ""
                issuer_str = f" -- {c.issuer}" if c.issuer else ""
                tex.append(rf"    \item \small{{\textbf{{{esc(c.name)}}}{esc(issuer_str)}{esc(date_str)}}}")
            tex.append(r"\end{itemize}")
            tex.append("")

        # Honors & Awards
        if self.data.awards:
            tex.append(r"%-----------HONORS & AWARDS-----------")
            tex.append(r"\section{Honors \& Awards}")
            tex.append(r"\begin{itemize}[leftmargin=0.15in, label={}]")
            for a in self.data.awards:
                date_str = f" ({a.date})" if a.date else ""
                awarder_str = f" -- {a.awarder}" if a.awarder else ""
                tex.append(rf"    \item \small{{\textbf{{{esc(a.title)}}}{esc(awarder_str)}{esc(date_str)}}}")
            tex.append(r"\end{itemize}")
            tex.append("")

        # Publications
        if self.data.publications:
            tex.append(r"%-----------PUBLICATIONS-----------")
            tex.append(r"\section{Publications}")
            tex.append(r"\begin{itemize}[leftmargin=0.15in, label={}]")
            for pub in self.data.publications:
                tex.append(rf"    \item \small{{{esc(pub.name)}}}")
            tex.append(r"\end{itemize}")
            tex.append("")

        tex.append(r"\end{document}")
        return "\n".join(tex)

    def to_html(self, font_size_pt: float = 10.0, line_height: float = 1.25, margin_in: float = 0.4) -> str:
        """Generates pixel-perfect HTML styled for single-page print-to-PDF."""
        b = self.data.basics
        
        contact_html = []
        if b.phone:
            contact_html.append(f"<span>{b.phone}</span>")
        if b.email:
            contact_html.append(f'<a href="mailto:{b.email}">{b.email}</a>')
        if b.location.city:
            contact_html.append(f"<span>{b.location.city}</span>")
        if b.url:
            clean_url = b.url.replace("https://", "").replace("http://", "")
            contact_html.append(f'<a href="{b.url}" target="_blank">{clean_url}</a>')
        for p in b.profiles:
            clean_u = p.url.replace("https://", "").replace("http://", "")
            contact_html.append(f'<a href="{p.url}" target="_blank">{p.network}: {clean_u}</a>')

        contact_line = " | ".join(contact_html)

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>{b.name} - Resume</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Latin+Modern+Roman:ital,wght@0,400;0,700;1,400&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
<style>
  @page {{
    size: letter;
    margin: {margin_in}in;
  }}
  * {{
    box-sizing: border-box;
    margin: 0;
    padding: 0;
  }}
  body {{
    font-family: 'Latin Modern Roman', 'Computer Modern', 'Times New Roman', serif;
    font-size: {font_size_pt}pt;
    line-height: {line_height};
    color: #111;
    background: #fff;
    -webkit-print-color-adjust: exact;
  }}
  .resume-page {{
    width: 100%;
    margin: 0 auto;
    padding: 0;
    background: #fff;
  }}
  @media print {{
    body, .resume-page {{
      width: 100%;
      height: 100%;
      padding: 0;
      margin: 0;
    }}
  }}
  header {{
    text-align: center;
    margin-bottom: 5px;
  }}
  h1 {{
    font-size: {font_size_pt * 1.85}pt;
    font-weight: 700;
    letter-spacing: 0.5px;
    text-transform: uppercase;
    margin-bottom: 2px;
  }}
  .contact-bar {{
    font-size: {font_size_pt * 0.88}pt;
    color: #333;
  }}
  .contact-bar a {{
    color: #0d47a1;
    text-decoration: none;
  }}
  .contact-bar a:hover {{
    text-decoration: underline;
  }}
  section {{
    margin-top: 5px;
  }}
  .section-title {{
    font-size: {font_size_pt * 1.1}pt;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    border-bottom: 1px solid #111;
    padding-bottom: 1px;
    margin-bottom: 3px;
  }}
  .item-header {{
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    margin-top: 3px;
  }}
  .item-title {{
    font-weight: 700;
    font-size: {font_size_pt}pt;
  }}
  .item-subtitle {{
    font-style: italic;
    font-size: {font_size_pt * 0.95}pt;
  }}
  .item-date {{
    font-size: {font_size_pt * 0.88}pt;
    font-weight: 400;
    white-space: nowrap;
  }}
  .item-location {{
    font-style: italic;
    font-size: {font_size_pt * 0.88}pt;
    white-space: nowrap;
  }}
  ul.bullets {{
    margin-left: 16px;
    margin-top: 2px;
  }}
  ul.bullets li {{
    font-size: {font_size_pt * 0.92}pt;
    margin-bottom: 1.2px;
    line-height: {line_height * 0.95};
  }}
  .skill-line {{
    font-size: {font_size_pt * 0.92}pt;
    margin-bottom: 1.5px;
  }}
  .skill-name {{
    font-weight: 700;
  }}
</style>
</head>
<body>
<div class="resume-page">
  <header>
    <h1>{html_escape(b.name)}</h1>
    <div class="contact-bar">{contact_line}</div>
  </header>
"""

        # Professional Summary
        if b.summary:
            html += f"""
  <section>
    <div class="section-title">Professional Summary</div>
    <div style="font-size: {font_size_pt * 0.92}pt; line-height: {line_height * 0.95}; margin-top: 2px;">
      {html_escape(b.summary)}
    </div>
  </section>"""

        # Education
        if self.data.education:
            html += """
  <section>
    <div class="section-title">Education</div>"""
            for edu in self.data.education:
                dates = f"{edu.start_date} – {edu.end_date}" if edu.end_date else edu.start_date
                html += f"""
    <div class="item-header">
      <div class="item-title">{html_escape(edu.institution)}</div>
      <div class="item-date">{dates}</div>
    </div>
    <div class="item-header">
      <div class="item-subtitle">{html_escape(edu.study_type)}</div>
      <div class="item-location">{html_escape(edu.area)}</div>
    </div>"""
                if edu.highlights:
                    html += '<ul class="bullets">'
                    for h in edu.highlights:
                        html += f"<li>{html_escape(h)}</li>"
                    html += "</ul>"
            html += "\n  </section>"

        # Experience
        if self.data.work:
            html += """
  <section>
    <div class="section-title">Experience</div>"""
            for w in self.data.work:
                dates = f"{w.start_date} – {w.end_date}" if w.end_date else w.start_date
                html += f"""
    <div class="item-header">
      <div class="item-title">{html_escape(w.position)}</div>
      <div class="item-date">{dates}</div>
    </div>
    <div class="item-header">
      <div class="item-subtitle">{html_escape(w.name)}</div>
      <div class="item-location">{html_escape(w.location)}</div>
    </div>"""
                if w.highlights:
                    html += '<ul class="bullets">'
                    for h in w.highlights:
                        html += f"<li>{html_escape(h)}</li>"
                    html += "</ul>"
            html += "\n  </section>"

        # Open Source
        if self.data.open_source:
            html += """
  <section>
    <div class="section-title">Open-Source Contributions</div>"""
            for os_item in self.data.open_source:
                html += f"""
    <div class="item-header">
      <div class="item-title">{html_escape(os_item.project)}</div>
      <div class="item-subtitle">{html_escape(os_item.role)}</div>
    </div>"""
                if os_item.highlights:
                    html += '<ul class="bullets">'
                    for h in os_item.highlights:
                        html += f"<li>{html_escape(h)}</li>"
                    html += "</ul>"
            html += "\n  </section>"

        # Projects
        if self.data.projects:
            html += """
  <section>
    <div class="section-title">Projects</div>"""
            for p in self.data.projects:
                p_name = p.name.replace('$', '').strip().rstrip('|').strip()
                dates = f"{p.start_date} – {p.end_date}" if p.end_date else p.start_date
                tech_str = f" | <em>{html_escape(', '.join(p.keywords))}</em>" if p.keywords else ""
                url_str = f' <a href="{p.url}" target="_blank" style="font-size:0.85em; color:#0d47a1;">[Link]</a>' if p.url else ""
                html += f"""
    <div class="item-header">
      <div class="item-title">{html_escape(p_name)}{url_str}{tech_str}</div>
      <div class="item-date">{dates}</div>
    </div>"""
                if p.highlights:
                    html += '<ul class="bullets">'
                    for h in p.highlights:
                        html += f"<li>{html_escape(h)}</li>"
                    html += "</ul>"
            html += "\n  </section>"

        # Skills
        if self.data.skills:
            html += """
  <section>
    <div class="section-title">Technical Skills</div>"""
            for s in self.data.skills:
                html += f"""
    <div class="skill-line">
      <span class="skill-name">{html_escape(s.name)}:</span> {html_escape(', '.join(s.keywords))}
    </div>"""
            html += "\n  </section>"

        # Certifications
        if self.data.certificates:
            html += """
  <section>
    <div class="section-title">Certifications</div>"""
            for c in self.data.certificates:
                date_str = f" ({c.date})" if c.date else ""
                issuer_str = f" - {c.issuer}" if c.issuer else ""
                html += f"""
    <div class="skill-line">
      <span class="skill-name">{html_escape(c.name)}</span>{html_escape(issuer_str)}{date_str}
    </div>"""
            html += "\n  </section>"

        # Honors & Awards
        if self.data.awards:
            html += """
  <section>
    <div class="section-title">Honors & Awards</div>"""
            for a in self.data.awards:
                date_str = f" ({a.date})" if a.date else ""
                awarder_str = f" - {a.awarder}" if a.awarder else ""
                html += f"""
    <div class="skill-line">
      <span class="skill-name">{html_escape(a.title)}</span>{html_escape(awarder_str)}{date_str}
    </div>"""
            html += "\n  </section>"

        # Publications
        if self.data.publications:
            html += """
  <section>
    <div class="section-title">Publications</div>"""
            for pub in self.data.publications:
                html += f"""
    <div class="skill-line">
      {html_escape(pub.name)}
    </div>"""
            html += "\n  </section>"

        # Languages
        if self.data.languages:
            html += """
  <section>
    <div class="section-title">Languages</div>
    <div class="skill-line">"""
            lang_strs = [f"{html_escape(l.language)} ({html_escape(l.fluency)})" if l.fluency else html_escape(l.language) for l in self.data.languages]
            html += f"      {', '.join(lang_strs)}"
            html += """
    </div>
  </section>"""

        html += """
</div>
</body>
</html>"""
        return html
