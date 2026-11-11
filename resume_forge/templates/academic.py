"""Academic & Research CV Template - IEEE, CERN Fellowship & Research Lab Standard."""

import re
from typing import List
from .base import BaseTemplate
from ..core.schema import ResumeData


class AcademicTemplate(BaseTemplate):
    """Academic & Research CV Template.
    
    Formal scientific curriculum vitae optimized for Research Residencies,
    PhD/Postdoc applications, CERN Fellowships, and Deep Tech R&D roles.
    Features numbered peer-reviewed publications, academic credentials,
    and formal Latin Modern typography.
    """

    name = "academic"
    display_name = "Academic & Research CV (IEEE / CERN)"
    description = "Formal academic CV with numbered publications, grant awards, and research appointments."
    category = "Academic & Research"
    target_roles = ["Research Scientist", "Machine Learning Researcher", "Postdoctoral Fellow", "CERN Fellow", "PhD Candidate"]
    default_font_size = 10.0
    default_line_height = 1.25
    default_margin = 0.45

    def render_latex(self, data: ResumeData) -> str:
        esc = self.escape_latex
        b = data.basics
        safe_name = self.clean_name(b.name)

        contact_items = []
        if b.location.city:
            contact_items.append(esc(b.location.city))
        if b.phone:
            contact_items.append(esc(b.phone))
        if b.email:
            contact_items.append(r'\href{mailto:' + b.email + '}{' + esc(b.email) + '}')
        if b.url:
            contact_items.append(r'\href{' + b.url + '}{' + esc(self.clean_url(b.url)) + '}')
        for p in b.profiles:
            p_url = p.url or (f"https://github.com/{p.username}" if "github" in (p.network or "").lower() else "")
            if p_url:
                contact_items.append(r'\href{' + p_url + '}{' + esc(self.clean_url(p_url)) + '}')

        contact_line = " $\\cdot$ ".join(contact_items)

        tex = [
            r"\documentclass[10pt,letterpaper]{article}",
            r"\usepackage[utf8]{inputenc}",
            r"\usepackage[T1]{fontenc}",
            r"\usepackage{lmodern}",
            r"\usepackage[margin=0.45in]{geometry}",
            r"\usepackage{titlesec}",
            r"\usepackage{enumitem}",
            r"\usepackage[hidelinks]{hyperref}",
            r"\usepackage{tabularx}",
            r"\usepackage{fancyhdr}",
            r"\pagestyle{empty}",
            r"\raggedbottom",
            r"\raggedright",
            r"\setlength{\tabcolsep}{0in}",
            "",
            r"% Academic Section Heading Style",
            r"\titleformat{\section}",
            r"  {\vspace{-3pt}\scshape\large\bfseries}",
            r"  {}{0em}{}[\vspace{1pt}\hrule height 0.5pt\vspace{3pt}]",
            r"\titlespacing*{\section}{0pt}{6pt}{3pt}",
            "",
            r"% Numbered publication list spacing",
            r"\setlist[enumerate]{leftmargin=1.8em, itemsep=1pt, topsep=1pt, parsep=0pt, partopsep=0pt}",
            r"\setlist[itemize]{leftmargin=1.2em, itemsep=-1pt, topsep=1pt, parsep=0pt, partopsep=0pt}",
            "",
            r"\begin{document}",
            "",
            r"%----------HEADER----------",
            r"\begin{center}",
            rf"  {{\LARGE \textbf{{{esc(safe_name)}}}}} \\[2pt]",
            rf"  {{\small {contact_line}}}",
            r"\end{center}",
            r"\vspace{-4pt}",
            ""
        ]

        if b.summary:
            tex.append(r"\section{Research Interests \& Focus}")
            tex.append(f"{esc(b.summary)}\n")

        # Academic CVs place Education first
        if data.education:
            tex.append(r"\section{Education}")
            for edu in data.education:
                dates = f"{edu.start_date} -- {edu.end_date}" if edu.end_date else edu.start_date
                tex.append(r"\noindent\begin{tabular*}{\textwidth}{@{\extracolsep{\fill}}lr}")
                tex.append(rf"  \textbf{{{esc(edu.institution)}}} & \textit{{{esc(dates)}}} \\")
                tex.append(rf"  \textit{{{esc(edu.study_type)}}} in {esc(edu.area or '')} & \textit{{{esc(edu.score or '')}}} \\")
                tex.append(r"\end{tabular*}\vspace{-2pt}")
                if edu.highlights:
                    tex.append(r"\begin{itemize}")
                    for h in edu.highlights:
                        tex.append(rf"  \item {esc(h)}")
                    tex.append(r"\end{itemize}\vspace{2pt}")
            tex.append("")

        if data.work:
            tex.append(r"\section{Research \& Professional Appointments}")
            for w in data.work:
                dates = f"{w.start_date} -- {w.end_date}" if w.end_date else w.start_date
                tex.append(r"\noindent\begin{tabular*}{\textwidth}{@{\extracolsep{\fill}}lr}")
                tex.append(rf"  \textbf{{{esc(w.position)}}}, \textit{{{esc(w.name)}}} & \textit{{{esc(dates)}}} \\")
                if w.location:
                    tex.append(rf"  \textit{{{esc(w.location)}}} & \\")
                tex.append(r"\end{tabular*}\vspace{-2pt}")
                if w.highlights:
                    tex.append(r"\begin{itemize}")
                    for h in w.highlights:
                        tex.append(rf"  \item {esc(h)}")
                    tex.append(r"\end{itemize}\vspace{2pt}")
            tex.append("")

        # Formal numbered publications section
        if data.publications:
            tex.append(r"\section{Publications \& Preprints}")
            tex.append(r"\begin{enumerate}")
            for pub in data.publications:
                tex.append(rf"  \item {esc(pub.name)}")
            tex.append(r"\end{enumerate}\vspace{2pt}")
            tex.append("")

        if data.projects:
            tex.append(r"\section{Selected Research Systems \& Artifacts}")
            for p in data.projects:
                dates = f"{p.start_date} -- {p.end_date}" if p.end_date else p.start_date
                tech = f" | \\textit{{{esc(', '.join(p.keywords))}}}" if p.keywords else ""
                url_s = f" [\\href{{{p.url}}}{{Artifact}}]" if p.url else ""
                tex.append(r"\noindent\begin{tabular*}{\textwidth}{@{\extracolsep{\fill}}lr}")
                tex.append(rf"  \textbf{{{esc(p.name)}}}{url_s}{tech} & \textit{{{esc(dates)}}} \\")
                tex.append(r"\end{tabular*}\vspace{-2pt}")
                if p.highlights:
                    tex.append(r"\begin{itemize}")
                    for h in p.highlights:
                        tex.append(rf"  \item {esc(h)}")
                    tex.append(r"\end{itemize}\vspace{2pt}")
            tex.append("")

        if data.open_source:
            tex.append(r"\section{Scientific Open-Source Contributions}")
            for os_item in data.open_source:
                tex.append(r"\noindent\begin{tabular*}{\textwidth}{@{\extracolsep{\fill}}lr}")
                tex.append(rf"  \textbf{{{esc(os_item.project)}}} $\cdot$ \textit{{{esc(os_item.role or '')}}} & \\")
                tex.append(r"\end{tabular*}\vspace{-2pt}")
                if os_item.highlights:
                    tex.append(r"\begin{itemize}")
                    for h in os_item.highlights:
                        tex.append(rf"  \item {esc(h)}")
                    tex.append(r"\end{itemize}\vspace{2pt}")
            tex.append("")

        if data.awards:
            tex.append(r"\section{Honors, Fellowships \& Grants}")
            tex.append(r"\begin{itemize}")
            for a in data.awards:
                date_s = f" ({esc(a.date)})" if a.date else ""
                awarder_s = f" -- {esc(a.awarder)}" if a.awarder else ""
                tex.append(rf"  \item \textbf{{{esc(a.title)}}}{awarder_s}{date_s}")
            tex.append(r"\end{itemize}\vspace{2pt}")
            tex.append("")

        if data.certificates:
            tex.append(r"\section{Certifications \& Credentials}")
            tex.append(r"\begin{itemize}")
            for c in data.certificates:
                date_s = f" ({esc(c.date)})" if c.date else ""
                issuer_s = f" -- {esc(c.issuer)}" if c.issuer else ""
                tex.append(rf"  \item \textbf{{{esc(c.name)}}}{issuer_s}{date_s}")
            tex.append(r"\end{itemize}\vspace{2pt}")
            tex.append("")

        if data.skills:
            tex.append(r"\section{Technical Methodologies \& Tooling}")
            tex.append(r"\begin{itemize}")
            for s in data.skills:
                tex.append(rf"  \item \textbf{{{esc(s.name)}}}: {esc(', '.join(s.keywords))}")
            tex.append(r"\end{itemize}\vspace{2pt}")
            tex.append("")

        if data.languages:
            tex.append(r"\section{Languages}")
            lang_strs = [f"{esc(l.language)} ({esc(l.fluency)})" if l.fluency else esc(l.language) for l in data.languages]
            tex.append(rf"\noindent\small{{{', '.join(lang_strs)}}}\vspace{{3pt}}")
            tex.append("")

        tex.append(r"\end{document}")
        return "\n".join(tex)

    def render_html(
        self,
        data: ResumeData,
        font_size_pt: float = 10.0,
        line_height: float = 1.25,
        margin_in: float = 0.45
    ) -> str:
        esc = self.escape_html
        b = data.basics
        safe_name = self.clean_name(b.name)

        contact_html = []
        if b.location.city:
            contact_html.append(f"<span>{esc(b.location.city)}</span>")
        if b.phone:
            contact_html.append(f"<span>{esc(b.phone)}</span>")
        if b.email:
            contact_html.append(f'<a href="mailto:{b.email}">{esc(b.email)}</a>')
        if b.url:
            contact_html.append(f'<a href="{b.url}" target="_blank">{esc(self.clean_url(b.url))}</a>')
        for p in b.profiles:
            clean_u = self.clean_url(p.url)
            contact_html.append(f'<a href="{p.url}" target="_blank">{esc(clean_u)}</a>')

        contact_line = " &middot; ".join(contact_html)

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>{esc(safe_name)} - Curriculum Vitae (Academic)</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Latin+Modern+Roman:ital,wght@0,400;0,700;1,400&display=swap" rel="stylesheet">
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
    background: #fff;
  }}
  header {{
    text-align: center;
    margin-bottom: 6px;
  }}
  h1 {{
    font-size: {font_size_pt * 1.8}pt;
    font-weight: 700;
    letter-spacing: 0.5px;
    margin-bottom: 2px;
  }}
  .contact-bar {{
    font-size: {font_size_pt * 0.9}pt;
    color: #222;
  }}
  .contact-bar a {{
    color: #0b57d0;
    text-decoration: none;
  }}
  section {{
    margin-top: 6px;
  }}
  .section-title {{
    font-size: {font_size_pt * 1.1}pt;
    font-weight: 700;
    letter-spacing: 0.5px;
    font-variant: small-caps;
    border-bottom: 1px solid #111;
    padding-bottom: 1px;
    margin-bottom: 3px;
  }}
  .item-row {{
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    font-weight: 700;
    margin-top: 3px;
  }}
  .item-subrow {{
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    font-style: italic;
    font-size: {font_size_pt * 0.95}pt;
    margin-bottom: 2px;
  }}
  ul.bullets {{
    margin-left: 16px;
    list-style-type: disc;
    margin-bottom: 2px;
  }}
  ul.bullets li {{
    margin-bottom: 1.5px;
    text-align: justify;
  }}
  ol.pub-list {{
    margin-left: 20px;
    margin-bottom: 3px;
  }}
  ol.pub-list li {{
    margin-bottom: 2.5px;
    text-align: justify;
    font-size: {font_size_pt * 0.95}pt;
  }}
  .skills-box p {{
    margin-bottom: 2px;
    font-size: {font_size_pt * 0.95}pt;
  }}
</style>
</head>
<body>
<div class="resume-page">
  <header>
    <h1>{esc(safe_name)}</h1>
    <div class="contact-bar">{contact_line}</div>
  </header>
"""

        if b.summary:
            html += f"""
  <section>
    <div class="section-title">Research Interests & Focus</div>
    <p style="text-align: justify; margin-top: 2px;">{esc(b.summary)}</p>
  </section>
"""

        if data.education:
            html += """
  <section>
    <div class="section-title">Education</div>
"""
            for edu in data.education:
                dates = f"{esc(edu.start_date)} – {esc(edu.end_date)}" if edu.end_date else esc(edu.start_date)
                html += f"""
    <div class="item-row">
      <div>{esc(edu.institution)}</div>
      <div style="font-weight: normal; font-style: italic;">{dates}</div>
    </div>
    <div class="item-subrow">
      <div>{esc(edu.study_type)} in {esc(edu.area or '')}</div>
      <div>{esc(edu.score or '')}</div>
    </div>
"""
                if edu.highlights:
                    html += '    <ul class="bullets">\n'
                    for h in edu.highlights:
                        html += f"      <li>{esc(h)}</li>\n"
                    html += "    </ul>\n"
            html += "  </section>\n"

        if data.work:
            html += """
  <section>
    <div class="section-title">Research & Professional Appointments</div>
"""
            for w in data.work:
                dates = f"{esc(w.start_date)} – {esc(w.end_date)}" if w.end_date else esc(w.start_date)
                html += f"""
    <div class="item-row">
      <div>{esc(w.position)}, <em>{esc(w.name)}</em></div>
      <div style="font-weight: normal; font-style: italic;">{dates}</div>
    </div>
"""
                if w.location:
                    html += f'    <div class="item-subrow"><div>{esc(w.location)}</div></div>\n'
                if w.highlights:
                    html += '    <ul class="bullets">\n'
                    for h in w.highlights:
                        html += f"      <li>{esc(h)}</li>\n"
                    html += "    </ul>\n"
            html += "  </section>\n"

        if data.publications:
            html += """
  <section>
    <div class="section-title">Publications & Preprints</div>
    <ol class="pub-list">
"""
            for pub in data.publications:
                html += f"      <li>{esc(pub.name)}</li>\n"
            html += "    </ol>\n  </section>\n"

        if data.projects:
            html += """
  <section>
    <div class="section-title">Selected Research Systems & Artifacts</div>
"""
            for p in data.projects:
                tech_str = f" | <em>{esc(', '.join(p.keywords))}</em>" if p.keywords else ""
                url_str = f' <a href="{p.url}" target="_blank" style="color: #0b57d0;">[Artifact]</a>' if p.url else ""
                dates = f"{esc(p.start_date)} – {esc(p.end_date)}" if p.end_date else esc(p.start_date)
                html += f"""
    <div class="item-row">
      <div>{esc(p.name)}{url_str}{tech_str}</div>
      <div style="font-weight: normal; font-style: italic;">{dates}</div>
    </div>
"""
                if p.highlights:
                    html += '    <ul class="bullets">\n'
                    for h in p.highlights:
                        html += f"      <li>{esc(h)}</li>\n"
                    html += "    </ul>\n"
            html += "  </section>\n"

        if data.open_source:
            html += """
  <section>
    <div class="section-title">Scientific Open-Source Contributions</div>
"""
            for os_item in data.open_source:
                html += f"""
    <div class="item-row">
      <div>{esc(os_item.project)} &middot; <em>{esc(os_item.role or '')}</em></div>
    </div>
"""
                if os_item.highlights:
                    html += '    <ul class="bullets">\n'
                    for h in os_item.highlights:
                        html += f"      <li>{esc(h)}</li>\n"
                    html += "    </ul>\n"
            html += "  </section>\n"

        if data.awards:
            html += """
  <section>
    <div class="section-title">Honors, Fellowships & Grants</div>
    <ul class="bullets">
"""
            for a in data.awards:
                date_s = f" ({esc(a.date)})" if a.date else ""
                awarder_s = f" — {esc(a.awarder)}" if a.awarder else ""
                html += f"      <li><strong>{esc(a.title)}</strong>{awarder_s}{date_s}</li>\n"
            html += "    </ul>\n  </section>\n"

        if data.certificates:
            html += """
  <section>
    <div class="section-title">Certifications & Credentials</div>
    <ul class="bullets">
"""
            for c in data.certificates:
                date_s = f" ({esc(c.date)})" if c.date else ""
                issuer_s = f" — {esc(c.issuer)}" if c.issuer else ""
                html += f"      <li><strong>{esc(c.name)}</strong>{issuer_s}{date_s}</li>\n"
            html += "    </ul>\n  </section>\n"

        if data.skills:
            html += """
  <section>
    <div class="section-title">Technical Methodologies & Tooling</div>
    <div class="skills-box" style="margin-top: 2px;">
"""
            for s in data.skills:
                html += f"      <p><strong>{esc(s.name)}:</strong> {esc(', '.join(s.keywords))}</p>\n"
            html += "    </div>\n  </section>\n"

        if data.languages:
            html += """
  <section>
    <div class="section-title">Languages</div>
    <p style="margin-top: 2px;">
"""
            lang_strs = [f"{esc(l.language)} ({esc(l.fluency)})" if l.fluency else esc(l.language) for l in data.languages]
            html += f"      {', '.join(lang_strs)}\n    </p>\n  </section>\n"

        html += """
</div>
</body>
</html>
"""
        return html
