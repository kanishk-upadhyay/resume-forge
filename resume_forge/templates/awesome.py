"""Awesome-CV Resume Template - Posquit0 Executive & Senior Engineer Style."""

import re
from typing import List
from .base import BaseTemplate
from ..core.schema import ResumeData


class AwesomeCvTemplate(BaseTemplate):
    """Awesome-CV Resume Template.
    
    Inspired by Posquit0's legendary Awesome-CV (>20,000 GitHub stars).
    Features Roboto typography, accent color section rules, two-level
    subheadings, and an executive aesthetic.
    """

    name = "awesome"
    display_name = "Awesome-CV (Executive)"
    description = "Posquit0's iconic template with Roboto typography, accent color underlines, and executive styling."
    category = "Executive & Modern"
    target_roles = ["Senior Software Engineer", "Tech Lead", "Engineering Director", "DevOps Architect", "Open Source Maintainer"]
    default_font_size = 9.8
    default_line_height = 1.25
    default_margin = 0.40

    def render_latex(self, data: ResumeData) -> str:
        esc = self.escape_latex
        b = data.basics
        safe_name = self.clean_name(b.name)
        parts = safe_name.split(" ", 1)
        first_name = parts[0]
        last_name = parts[1] if len(parts) > 1 else ""

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
            r"\usepackage[margin=0.40in]{geometry}",
            r"\usepackage{xcolor}",
            r"\usepackage{titlesec}",
            r"\usepackage{enumitem}",
            r"\usepackage[hidelinks]{hyperref}",
            r"\usepackage{tabularx}",
            r"\usepackage{fancyhdr}",
            r"% Roboto or Sans-Serif font setup",
            r"\usepackage[scaled=0.94]{helvet}",
            r"\renewcommand{\familydefault}{\sfdefault}",
            r"\pagestyle{empty}",
            r"\raggedbottom",
            r"\raggedright",
            r"\setlength{\tabcolsep}{0in}",
            "",
            r"% Awesome-CV Color Palette",
            r"\definecolor{awesome-emerald}{HTML}{008080}",
            r"\definecolor{awesome-dark}{HTML}{222222}",
            r"\definecolor{awesome-gray}{HTML}{5D5D5D}",
            r"\definecolor{awesome-lightgray}{HTML}{999999}",
            "",
            r"% Section Style with Accent Bar",
            r"\newcommand{\cvsection}[1]{%",
            r"  \vspace{5pt}",
            r"  {\fontsize{11}{13}\bfseries\color{awesome-emerald}\uppercase{#1}}",
            r"  \vspace{-2pt}",
            r"  {\color{awesome-lightgray}\hrule height 0.6pt}",
            r"  \vspace{3pt}",
            r"}",
            "",
            r"% List item spacing",
            r"\setlist[itemize]{leftmargin=1.1em, itemsep=-1.5pt, topsep=1pt, parsep=0pt, partopsep=0pt}",
            "",
            r"\begin{document}",
            "",
            r"%----------HEADER----------",
            r"\begin{center}",
            rf"  {{\fontsize{{24}}{{28}}\selectfont \color{{awesome-gray}} {esc(first_name)} \textbf{{\color{{awesome-emerald}} {esc(last_name)}}}}} \\[3pt]",
            rf"  {{\small \color{{awesome-dark}} {contact_line}}}",
            r"\end{center}",
            r"\vspace{-4pt}",
            ""
        ]

        if b.summary:
            tex.append(r"\cvsection{Summary}")
            tex.append(f"{{\\color{{awesome-dark}} {esc(b.summary)}}}\n")

        if data.work:
            tex.append(r"\cvsection{Experience}")
            for w in data.work:
                dates = f"{w.start_date} -- {w.end_date}" if w.end_date else w.start_date
                tex.append(r"\noindent\begin{tabular*}{\textwidth}{@{\extracolsep{\fill}}lr}")
                tex.append(rf"  \textbf{{\color{{awesome-dark}} {esc(w.position)}}} & {{\color{{awesome-gray}}\small {esc(dates)}}} \\")
                tex.append(rf"  \textit{{\color{{awesome-emerald}} {esc(w.name)}}} & {{\color{{awesome-gray}}\small {esc(w.location or '')}}} \\")
                tex.append(r"\end{tabular*}\vspace{-2pt}")
                if w.highlights:
                    tex.append(r"\begin{itemize}")
                    for h in w.highlights:
                        tex.append(rf"  \item {esc(h)}")
                    tex.append(r"\end{itemize}\vspace{2pt}")
            tex.append("")

        if data.projects:
            tex.append(r"\cvsection{Projects}")
            for p in data.projects:
                dates = f"{p.start_date} -- {p.end_date}" if p.end_date else p.start_date
                tech = f" | \\textit{{{esc(', '.join(p.keywords))}}}" if p.keywords else ""
                url_s = f" [\\href{{{p.url}}}{{Link}}]" if p.url else ""
                tex.append(r"\noindent\begin{tabular*}{\textwidth}{@{\extracolsep{\fill}}lr}")
                tex.append(rf"  \textbf{{\color{{awesome-dark}} {esc(p.name)}}}{url_s}{tech} & {{\color{{awesome-gray}}\small {esc(dates)}}} \\")
                tex.append(r"\end{tabular*}\vspace{-2pt}")
                if p.highlights:
                    tex.append(r"\begin{itemize}")
                    for h in p.highlights:
                        tex.append(rf"  \item {esc(h)}")
                    tex.append(r"\end{itemize}\vspace{2pt}")
            tex.append("")

        if data.open_source:
            tex.append(r"\cvsection{Open-Source & Leadership}")
            for os_item in data.open_source:
                tex.append(r"\noindent\begin{tabular*}{\textwidth}{@{\extracolsep{\fill}}lr}")
                tex.append(rf"  \textbf{{\color{{awesome-dark}} {esc(os_item.project)}}} & {{\color{{awesome-emerald}} \textit{{{esc(os_item.role or '')}}}}} \\")
                tex.append(r"\end{tabular*}\vspace{-2pt}")
                if os_item.highlights:
                    tex.append(r"\begin{itemize}")
                    for h in os_item.highlights:
                        tex.append(rf"  \item {esc(h)}")
                    tex.append(r"\end{itemize}\vspace{2pt}")
            tex.append("")

        if data.skills:
            tex.append(r"\cvsection{Skills}")
            tex.append(r"\begin{itemize}")
            for s in data.skills:
                tex.append(rf"  \item \textbf{{{esc(s.name)}}}: {esc(', '.join(s.keywords))}")
            tex.append(r"\end{itemize}\vspace{2pt}")
            tex.append("")

        if data.education:
            tex.append(r"\cvsection{Education}")
            for edu in data.education:
                dates = f"{edu.start_date} -- {edu.end_date}" if edu.end_date else edu.start_date
                tex.append(r"\noindent\begin{tabular*}{\textwidth}{@{\extracolsep{\fill}}lr}")
                tex.append(rf"  \textbf{{\color{{awesome-dark}} {esc(edu.institution)}}} & {{\color{{awesome-gray}}\small {esc(dates)}}} \\")
                tex.append(rf"  \textit{{\color{{awesome-emerald}} {esc(edu.study_type)}}} & {{\color{{awesome-gray}}\small {esc(edu.area or '')}}} \\")
                tex.append(r"\end{tabular*}\vspace{-2pt}")
                if edu.highlights:
                    tex.append(r"\begin{itemize}")
                    for h in edu.highlights:
                        tex.append(rf"  \item {esc(h)}")
                    tex.append(r"\end{itemize}\vspace{2pt}")
            tex.append("")

        if data.awards:
            tex.append(r"\cvsection{Honors \& Awards}")
            tex.append(r"\begin{itemize}")
            for a in data.awards:
                date_s = f" ({esc(a.date)})" if a.date else ""
                awarder_s = f" -- {esc(a.awarder)}" if a.awarder else ""
                tex.append(rf"  \item \textbf{{{esc(a.title)}}}{awarder_s}{date_s}")
            tex.append(r"\end{itemize}\vspace{2pt}")
            tex.append("")

        if data.certificates:
            tex.append(r"\cvsection{Certifications}")
            tex.append(r"\begin{itemize}")
            for c in data.certificates:
                date_s = f" ({esc(c.date)})" if c.date else ""
                issuer_s = f" -- {esc(c.issuer)}" if c.issuer else ""
                tex.append(rf"  \item \textbf{{{esc(c.name)}}}{issuer_s}{date_s}")
            tex.append(r"\end{itemize}\vspace{2pt}")
            tex.append("")

        if data.publications:
            tex.append(r"\cvsection{Publications}")
            tex.append(r"\begin{itemize}")
            for pub in data.publications:
                tex.append(rf"  \item {esc(pub.name)}")
            tex.append(r"\end{itemize}\vspace{2pt}")
            tex.append("")

        if data.languages:
            tex.append(r"\cvsection{Languages}")
            lang_strs = [f"{esc(l.language)} ({esc(l.fluency)})" if l.fluency else esc(l.language) for l in data.languages]
            tex.append(rf"\noindent\small{{{', '.join(lang_strs)}}}\vspace{{3pt}}")
            tex.append("")

        tex.append(r"\end{document}")
        return "\n".join(tex)

    def render_html(
        self,
        data: ResumeData,
        font_size_pt: float = 9.8,
        line_height: float = 1.25,
        margin_in: float = 0.40
    ) -> str:
        esc = self.escape_html
        b = data.basics
        safe_name = self.clean_name(b.name)
        parts = safe_name.split(" ", 1)
        first_name = parts[0]
        last_name = parts[1] if len(parts) > 1 else ""

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
<title>{esc(safe_name)} - Resume (Awesome-CV)</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Roboto:ital,wght@0,300;0,400;0,500;0,700;1,400&display=swap" rel="stylesheet">
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
    font-family: 'Roboto', 'Helvetica Neue', Arial, sans-serif;
    font-size: {font_size_pt}pt;
    line-height: {line_height};
    color: #222;
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
    font-size: {font_size_pt * 2.0}pt;
    font-weight: 300;
    letter-spacing: 0.5px;
    margin-bottom: 3px;
  }}
  h1 .first {{
    color: #555;
  }}
  h1 .last {{
    font-weight: 700;
    color: #008080;
  }}
  .contact-bar {{
    font-size: {font_size_pt * 0.9}pt;
    color: #333;
  }}
  .contact-bar a {{
    color: #008080;
    text-decoration: none;
  }}
  section {{
    margin-top: 6px;
  }}
  .section-title {{
    font-size: {font_size_pt * 1.1}pt;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.6px;
    color: #008080;
    border-bottom: 1px solid #ccc;
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
    color: #008080;
    font-size: {font_size_pt * 0.95}pt;
    margin-bottom: 2px;
  }}
  .item-date, .item-loc {{
    color: #666;
    font-weight: normal;
    font-size: {font_size_pt * 0.9}pt;
  }}
  ul.bullets {{
    margin-left: 16px;
    list-style-type: circle;
    margin-bottom: 2px;
  }}
  ul.bullets li {{
    margin-bottom: 1.5px;
    text-align: justify;
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
    <h1><span class="first">{esc(first_name)}</span> <span class="last">{esc(last_name)}</span></h1>
    <div class="contact-bar">{contact_line}</div>
  </header>
"""

        if b.summary:
            html += f"""
  <section>
    <div class="section-title">Summary</div>
    <p style="text-align: justify; margin-top: 2px;">{esc(b.summary)}</p>
  </section>
"""

        if data.work:
            html += """
  <section>
    <div class="section-title">Experience</div>
"""
            for w in data.work:
                dates = f"{esc(w.start_date)} – {esc(w.end_date)}" if w.end_date else esc(w.start_date)
                html += f"""
    <div class="item-row">
      <div>{esc(w.position)}</div>
      <div class="item-date">{dates}</div>
    </div>
    <div class="item-subrow">
      <div>{esc(w.name)}</div>
      <div class="item-loc">{esc(w.location or '')}</div>
    </div>
"""
                if w.highlights:
                    html += '    <ul class="bullets">\n'
                    for h in w.highlights:
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
                url_str = f' <a href="{p.url}" target="_blank" style="color: #008080;">[Link]</a>' if p.url else ""
                dates = f"{esc(p.start_date)} – {esc(p.end_date)}" if p.end_date else esc(p.start_date)
                html += f"""
    <div class="item-row">
      <div>{esc(p.name)}{url_str}{tech_str}</div>
      <div class="item-date">{dates}</div>
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
    <div class="section-title">Open-Source & Leadership</div>
"""
            for os_item in data.open_source:
                html += f"""
    <div class="item-row">
      <div>{esc(os_item.project)}</div>
      <div class="item-subrow">{esc(os_item.role or '')}</div>
    </div>
"""
                if os_item.highlights:
                    html += '    <ul class="bullets">\n'
                    for h in os_item.highlights:
                        html += f"      <li>{esc(h)}</li>\n"
                    html += "    </ul>\n"
            html += "  </section>\n"

        if data.skills:
            html += """
  <section>
    <div class="section-title">Skills</div>
    <div class="skills-box" style="margin-top: 2px;">
"""
            for s in data.skills:
                html += f"      <p><strong>{esc(s.name)}:</strong> {esc(', '.join(s.keywords))}</p>\n"
            html += "    </div>\n  </section>\n"

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
      <div class="item-date">{dates}</div>
    </div>
    <div class="item-subrow">
      <div>{esc(edu.study_type)}</div>
      <div class="item-loc">{esc(edu.area or '')}</div>
    </div>
"""
                if edu.highlights:
                    html += '    <ul class="bullets">\n'
                    for h in edu.highlights:
                        html += f"      <li>{esc(h)}</li>\n"
                    html += "    </ul>\n"
            html += "  </section>\n"

        if data.awards:
            html += """
  <section>
    <div class="section-title">Honors & Awards</div>
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
    <div class="section-title">Certifications</div>
    <ul class="bullets">
"""
            for c in data.certificates:
                date_s = f" ({esc(c.date)})" if c.date else ""
                issuer_s = f" — {esc(c.issuer)}" if c.issuer else ""
                html += f"      <li><strong>{esc(c.name)}</strong>{issuer_s}{date_s}</li>\n"
            html += "    </ul>\n  </section>\n"

        if data.publications:
            html += """
  <section>
    <div class="section-title">Publications</div>
    <ul class="bullets">
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
