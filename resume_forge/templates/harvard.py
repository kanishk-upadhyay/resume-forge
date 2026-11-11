"""Harvard University FAS (Faculty of Arts & Sciences) Standard Resume Template."""

import re
from typing import List
from .base import BaseTemplate
from ..core.schema import ResumeData


class HarvardTemplate(BaseTemplate):
    """Harvard University FAS Standard Resume Template.
    
    The authoritative Ivy League standard: classic Times serif, centered header
    with middot separators, all-caps bold section headers with solid rules,
    institution/company bold on left with location on right, and degree/role
    italicized below.
    """

    name = "harvard"
    display_name = "Harvard Classic (Ivy League)"
    description = "Official Harvard FAS career service standard: authoritative serif, monochrome, high-prestige."
    category = "Ivy League & Professional"
    target_roles = ["Software Engineer", "Management Consultant", "Finance Analyst", "Research Fellow", "General Tech"]
    default_font_size = 10.5
    default_line_height = 1.25
    default_margin = 0.45

    def render_latex(self, data: ResumeData) -> str:
        esc = self.escape_latex
        b = data.basics
        safe_name = self.clean_name(b.name).upper()

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
            r"\usepackage{newtxtext,newtxmath}",  # Times New Roman
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
            r"% Harvard Section Style: Bold Uppercase with Solid Line",
            r"\titleformat{\section}",
            r"  {\vspace{-3pt}\bfseries\uppercase}",
            r"  {}{0em}{}[\titlerule\vspace{2pt}]",
            r"\titlespacing*{\section}{0pt}{5pt}{4pt}",
            "",
            r"% List item spacing",
            r"\setlist[itemize]{leftmargin=1.2em, itemsep=-1.5pt, topsep=1pt, parsep=0pt, partopsep=0pt}",
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
            tex.append(r"\section{Professional Summary}")
            tex.append(f"{esc(b.summary)}\n")

        # In Harvard resumes, Education typically precedes or follows Experience based on graduation status
        if data.education:
            tex.append(r"\section{Education}")
            for edu in data.education:
                dates = f"{edu.start_date} -- {edu.end_date}" if edu.end_date else edu.start_date
                tex.append(r"\noindent\begin{tabular*}{\textwidth}{@{\extracolsep{\fill}}lr}")
                tex.append(rf"  \textbf{{{esc(edu.institution)}}} & \textit{{{esc(edu.area or '')}}} \\")
                tex.append(rf"  \textit{{{esc(edu.study_type)}}} & \textit{{{esc(dates)}}} \\")
                tex.append(r"\end{tabular*}\vspace{-2pt}")
                if edu.highlights:
                    tex.append(r"\begin{itemize}")
                    for h in edu.highlights:
                        tex.append(rf"  \item {esc(h)}")
                    tex.append(r"\end{itemize}\vspace{2pt}")
            tex.append("")

        if data.work:
            tex.append(r"\section{Experience}")
            for w in data.work:
                dates = f"{w.start_date} -- {w.end_date}" if w.end_date else w.start_date
                tex.append(r"\noindent\begin{tabular*}{\textwidth}{@{\extracolsep{\fill}}lr}")
                tex.append(rf"  \textbf{{{esc(w.name)}}} & \textit{{{esc(w.location or '')}}} \\")
                tex.append(rf"  \textit{{{esc(w.position)}}} & \textit{{{esc(dates)}}} \\")
                tex.append(r"\end{tabular*}\vspace{-2pt}")
                if w.highlights:
                    tex.append(r"\begin{itemize}")
                    for h in w.highlights:
                        tex.append(rf"  \item {esc(h)}")
                    tex.append(r"\end{itemize}\vspace{2pt}")
            tex.append("")

        if data.open_source:
            tex.append(r"\section{Open-Source & Leadership}")
            for os_item in data.open_source:
                tex.append(r"\noindent\begin{tabular*}{\textwidth}{@{\extracolsep{\fill}}lr}")
                tex.append(rf"  \textbf{{{esc(os_item.project)}}} & \textit{{{esc(os_item.role or '')}}} \\")
                tex.append(r"\end{tabular*}\vspace{-2pt}")
                if os_item.highlights:
                    tex.append(r"\begin{itemize}")
                    for h in os_item.highlights:
                        tex.append(rf"  \item {esc(h)}")
                    tex.append(r"\end{itemize}\vspace{2pt}")
            tex.append("")

        if data.projects:
            tex.append(r"\section{Projects}")
            for p in data.projects:
                dates = f"{p.start_date} -- {p.end_date}" if p.end_date else p.start_date
                tech = f" | \\textit{{{esc(', '.join(p.keywords))}}}" if p.keywords else ""
                url_s = f" [\\href{{{p.url}}}{{Link}}]" if p.url else ""
                tex.append(r"\noindent\begin{tabular*}{\textwidth}{@{\extracolsep{\fill}}lr}")
                tex.append(rf"  \textbf{{{esc(p.name)}}}{url_s}{tech} & \textit{{{esc(dates)}}} \\")
                tex.append(r"\end{tabular*}\vspace{-2pt}")
                if p.highlights:
                    tex.append(r"\begin{itemize}")
                    for h in p.highlights:
                        tex.append(rf"  \item {esc(h)}")
                    tex.append(r"\end{itemize}\vspace{2pt}")
            tex.append("")

        if data.skills:
            tex.append(r"\section{Technical Skills \& Interests}")
            tex.append(r"\begin{itemize}")
            for s in data.skills:
                tex.append(rf"  \item \textbf{{{esc(s.name)}}}: {esc(', '.join(s.keywords))}")
            tex.append(r"\end{itemize}\vspace{2pt}")
            tex.append("")

        if data.certificates:
            tex.append(r"\section{Certifications}")
            tex.append(r"\begin{itemize}")
            for c in data.certificates:
                date_s = f" ({esc(c.date)})" if c.date else ""
                issuer_s = f" -- {esc(c.issuer)}" if c.issuer else ""
                tex.append(rf"  \item \textbf{{{esc(c.name)}}}{issuer_s}{date_s}")
            tex.append(r"\end{itemize}\vspace{2pt}")
            tex.append("")

        if data.awards:
            tex.append(r"\section{Honors \& Awards}")
            tex.append(r"\begin{itemize}")
            for a in data.awards:
                date_s = f" ({esc(a.date)})" if a.date else ""
                awarder_s = f" -- {esc(a.awarder)}" if a.awarder else ""
                tex.append(rf"  \item \textbf{{{esc(a.title)}}}{awarder_s}{date_s}")
            tex.append(r"\end{itemize}\vspace{2pt}")
            tex.append("")

        if data.publications:
            tex.append(r"\section{Publications}")
            tex.append(r"\begin{itemize}")
            for pub in data.publications:
                tex.append(rf"  \item {esc(pub.name)}")
            tex.append(r"\end{itemize}\vspace{2pt}")
            tex.append("")

        if data.languages:
            tex.append(r"\section{Languages}")
            lang_strs = [f"{esc(l.language)} ({esc(l.fluency)})" if l.fluency else esc(l.language) for l in data.languages]
            tex.append(rf"\noindent\small{{{', '.join(lang_strs)}}}\vspace{{4pt}}")
            tex.append("")

        tex.append(r"\end{document}")
        return "\n".join(tex)

    def render_html(
        self,
        data: ResumeData,
        font_size_pt: float = 10.5,
        line_height: float = 1.25,
        margin_in: float = 0.45
    ) -> str:
        esc = self.escape_html
        b = data.basics
        safe_name = self.clean_name(b.name).upper()

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
<title>{esc(safe_name)} - Resume (Harvard Standard)</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Cinzel:wght@700&family=Lora:ital,wght@0,400;0,600;0,700;1,400&display=swap" rel="stylesheet">
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
    font-family: 'Times New Roman', 'Times', 'Lora', Georgia, serif;
    font-size: {font_size_pt}pt;
    line-height: {line_height};
    color: #000;
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
    font-size: {font_size_pt * 1.75}pt;
    font-weight: 700;
    letter-spacing: 0.8px;
    text-transform: uppercase;
    margin-bottom: 3px;
  }}
  .contact-bar {{
    font-size: {font_size_pt * 0.9}pt;
    color: #111;
  }}
  .contact-bar a {{
    color: #000;
    text-decoration: underline;
  }}
  section {{
    margin-top: 6px;
  }}
  .section-title {{
    font-size: {font_size_pt * 1.05}pt;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    border-bottom: 1.5px solid #000;
    padding-bottom: 1px;
    margin-bottom: 4px;
  }}
  .item-row-1 {{
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    font-weight: 700;
    margin-top: 3px;
  }}
  .item-row-2 {{
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    font-style: italic;
    font-size: {font_size_pt * 0.95}pt;
    margin-bottom: 2px;
  }}
  ul.bullets {{
    margin-left: 18px;
    list-style-type: disc;
    margin-bottom: 3px;
  }}
  ul.bullets li {{
    margin-bottom: 1.5px;
    text-align: justify;
  }}
  .skills-block {{
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
    <div class="section-title">Professional Summary</div>
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
    <div class="item-row-1">
      <div>{esc(edu.institution)}</div>
      <div style="font-style: italic; font-weight: normal;">{esc(edu.area or '')}</div>
    </div>
    <div class="item-row-2">
      <div>{esc(edu.study_type)}</div>
      <div>{dates}</div>
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
    <div class="section-title">Experience</div>
"""
            for w in data.work:
                dates = f"{esc(w.start_date)} – {esc(w.end_date)}" if w.end_date else esc(w.start_date)
                html += f"""
    <div class="item-row-1">
      <div>{esc(w.name)}</div>
      <div style="font-style: italic; font-weight: normal;">{esc(w.location or '')}</div>
    </div>
    <div class="item-row-2">
      <div>{esc(w.position)}</div>
      <div>{dates}</div>
    </div>
"""
                if w.highlights:
                    html += '    <ul class="bullets">\n'
                    for h in w.highlights:
                        html += f"      <li>{esc(h)}</li>\n"
                    html += "    </ul>\n"
            html += "  </section>\n"

        if data.open_source:
            html += """
  <section>
    <div class="section-title">Open-Source & Leadership</div>
"""
            for os_item in data.open_source:
                html += f"""
    <div class="item-row-1">
      <div>{esc(os_item.project)}</div>
      <div style="font-style: italic; font-weight: normal;">{esc(os_item.role or '')}</div>
    </div>
"""
                if os_item.highlights:
                    html += '    <ul class="bullets">\n'
                    for h in os_item.highlights:
                        html += f"      <li>{esc(h)}</li>\n"
                    html += "    </ul>\n"
            html += "  </section>\n"

        if data.projects:
            html += """
  <section>
    <div class="section-title">Projects</div>
"""
            for p in data.projects:
                tech_str = f" | <em>{esc(', '.join(p.keywords))}</em>" if p.keywords else ""
                url_str = f' [<a href="{p.url}" target="_blank">Link</a>]' if p.url else ""
                dates = f"{esc(p.start_date)} – {esc(p.end_date)}" if p.end_date else esc(p.start_date)
                html += f"""
    <div class="item-row-1">
      <div>{esc(p.name)}{url_str}{tech_str}</div>
      <div style="font-style: italic; font-weight: normal;">{dates}</div>
    </div>
"""
                if p.highlights:
                    html += '    <ul class="bullets">\n'
                    for h in p.highlights:
                        html += f"      <li>{esc(h)}</li>\n"
                    html += "    </ul>\n"
            html += "  </section>\n"

        if data.skills:
            html += """
  <section>
    <div class="section-title">Technical Skills & Interests</div>
    <ul class="bullets" style="margin-top: 2px;">
"""
            for s in data.skills:
                html += f"      <li><strong>{esc(s.name)}:</strong> {esc(', '.join(s.keywords))}</li>\n"
            html += "    </ul>\n  </section>\n"

        if data.certificates:
            html += """
  <section>
    <div class="section-title">Certifications</div>
    <ul class="bullets" style="margin-top: 2px;">
"""
            for c in data.certificates:
                date_s = f" ({esc(c.date)})" if c.date else ""
                issuer_s = f" — {esc(c.issuer)}" if c.issuer else ""
                html += f"      <li><strong>{esc(c.name)}</strong>{issuer_s}{date_s}</li>\n"
            html += "    </ul>\n  </section>\n"

        if data.awards:
            html += """
  <section>
    <div class="section-title">Honors & Awards</div>
    <ul class="bullets" style="margin-top: 2px;">
"""
            for a in data.awards:
                date_s = f" ({esc(a.date)})" if a.date else ""
                awarder_s = f" — {esc(a.awarder)}" if a.awarder else ""
                html += f"      <li><strong>{esc(a.title)}</strong>{awarder_s}{date_s}</li>\n"
            html += "    </ul>\n  </section>\n"

        if data.publications:
            html += """
  <section>
    <div class="section-title">Publications</div>
    <ul class="bullets" style="margin-top: 2px;">
"""
            for pub in data.publications:
                html += f"      <li>{esc(pub.name)}</li>\n"
            html += "    </ul>\n  </section>\n"

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
