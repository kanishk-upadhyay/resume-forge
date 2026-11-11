"""CERN / Overleaf Classic Fullstack Resume Template."""

import re
from typing import List
from .base import BaseTemplate
from ..core.schema import ResumeData


class CernTemplate(BaseTemplate):
    """CERN / Overleaf Classic Fullstack Resume Template.
    
    Traditional academic/systems serif layout with Latin Modern Roman font,
    small-caps section titles, solid horizontal rules, and balanced tables.
    """

    name = "cern"
    display_name = "CERN Classic Fullstack"
    description = "Classic academic single-column serif template popular at CERN and European labs."
    category = "Systems & Research"
    target_roles = ["Systems Engineer", "Backend Engineer", "Research Fellow", "Fullstack Developer"]

    def render_latex(self, data: ResumeData) -> str:
        esc = self.escape_latex
        b = data.basics
        safe_name = self.clean_name(b.name)

        contact_items = []
        if b.phone:
            contact_items.append(esc(b.phone))
        if b.email:
            contact_items.append(r'\href{mailto:' + b.email + '}{' + esc(b.email) + '}')
        if b.location.city:
            contact_items.append(esc(b.location.city))
        if b.url:
            contact_items.append(r'\href{' + b.url + '}{' + esc(self.clean_url(b.url)) + '}')
        for p in b.profiles:
            p_url = self.get_profile_url(p)
            if p_url:
                contact_items.append(r'\href{' + p_url + '}{' + esc(self.clean_url(p_url)) + '}')
            elif p.username or p.network:
                contact_items.append(esc(p.username or p.network))

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
            rf"    \textbf{{\Huge \scshape {esc(safe_name)}}} \\ \vspace{{1pt}}",
            rf"    \small {contact_line}",
            r"\end{center}",
            ""
        ]

        if b.summary:
            tex.append(r"%-----------SUMMARY-----------")
            tex.append(r"\section{Professional Summary}")
            tex.append(rf"{esc(b.summary)}")
            tex.append(r"\vspace{-4pt}")
            tex.append("")

        if data.education:
            tex.append(r"%-----------EDUCATION-----------")
            tex.append(r"\section{Education}")
            tex.append(r"\resumeSubHeadingListStart")
            for edu in data.education:
                dates = f"{edu.start_date} -- {edu.end_date}" if edu.end_date else edu.start_date
                tex.append(rf"  \resumeSubheading{{{esc(edu.institution)}}}{{{esc(dates)}}}{{{esc(edu.study_type)}}}{{{esc(edu.area)}}}")
                if edu.highlights:
                    tex.append(r"  \resumeItemListStart")
                    for h in edu.highlights:
                        tex.append(rf"    \resumeItem{{{esc(h)}}}")
                    tex.append(r"  \resumeItemListEnd")
            tex.append(r"\resumeSubHeadingListEnd")
            tex.append("")

        if data.work:
            tex.append(r"%-----------EXPERIENCE-----------")
            tex.append(r"\section{Experience}")
            tex.append(r"\resumeSubHeadingListStart")
            for w in data.work:
                dates = f"{w.start_date} -- {w.end_date}" if w.end_date else w.start_date
                tex.append(rf"  \resumeSubheading{{{esc(w.position)}}}{{{esc(dates)}}}{{{esc(w.name)}}}{{{esc(w.location)}}}")
                if w.highlights:
                    tex.append(r"  \resumeItemListStart")
                    for h in w.highlights:
                        tex.append(rf"    \resumeItem{{{esc(h)}}}")
                    tex.append(r"  \resumeItemListEnd")
            tex.append(r"\resumeSubHeadingListEnd")
            tex.append("")

        if data.open_source:
            tex.append(r"%-----------OPEN-SOURCE CONTRIBUTIONS-----------")
            tex.append(r"\section{Open-Source Contributions}")
            tex.append(r"\resumeSubHeadingListStart")
            for os_item in data.open_source:
                tex.append(rf"  \resumeSubheading{{{esc(os_item.project)}}}{{}}{{{esc(os_item.role)}}}{{}}")
                if os_item.highlights:
                    tex.append(r"  \resumeItemListStart")
                    for h in os_item.highlights:
                        tex.append(rf"    \resumeItem{{{esc(h)}}}")
                    tex.append(r"  \resumeItemListEnd")
            tex.append(r"\resumeSubHeadingListEnd")
            tex.append("")

        if data.projects:
            tex.append(r"%-----------PROJECTS-----------")
            tex.append(r"\section{Projects}")
            tex.append(r"\resumeSubHeadingListStart")
            for p in data.projects:
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

        if data.skills:
            tex.append(r"%-----------TECHNICAL SKILLS-----------")
            tex.append(r"\section{Technical Skills}")
            tex.append(r"\begin{itemize}[leftmargin=0.15in, label={}]")
            tex.append(r"    \small{\item{")
            for s in data.skills:
                tex.append(rf"     \textbf{{{esc(s.name)}}}{{: {esc(', '.join(s.keywords))}}} \\")
            tex.append(r"    }}")
            tex.append(r"\end{itemize}")
            tex.append("")

        if data.certificates:
            tex.append(r"%-----------CERTIFICATIONS-----------")
            tex.append(r"\section{Certifications}")
            tex.append(r"\begin{itemize}[leftmargin=0.15in, label={}]")
            for c in data.certificates:
                date_str = f" ({c.date})" if c.date else ""
                issuer_str = f" -- {c.issuer}" if c.issuer else ""
                tex.append(rf"    \item \small{{\textbf{{{esc(c.name)}}}{esc(issuer_str)}{esc(date_str)}}}")
            tex.append(r"\end{itemize}")
            tex.append("")

        if data.awards:
            tex.append(r"%-----------HONORS & AWARDS-----------")
            tex.append(r"\section{Honors \& Awards}")
            tex.append(r"\begin{itemize}[leftmargin=0.15in, label={}]")
            for a in data.awards:
                date_str = f" ({a.date})" if a.date else ""
                awarder_str = f" -- {a.awarder}" if a.awarder else ""
                tex.append(rf"    \item \small{{\textbf{{{esc(a.title)}}}{esc(awarder_str)}{esc(date_str)}}}")
            tex.append(r"\end{itemize}")
            tex.append("")

        if data.publications:
            tex.append(r"%-----------PUBLICATIONS-----------")
            tex.append(r"\section{Publications}")
            tex.append(r"\begin{itemize}[leftmargin=0.15in, label={}]")
            for pub in data.publications:
                tex.append(rf"    \item \small{{{esc(pub.name)}}}")
            tex.append(r"\end{itemize}")
            tex.append("")

        if data.languages:
            tex.append(r"%-----------LANGUAGES-----------")
            tex.append(r"\section{Languages}")
            tex.append(r"\begin{itemize}[leftmargin=0.15in, label={}]")
            lang_strs = [f"{esc(l.language)} ({esc(l.fluency)})" if l.fluency else esc(l.language) for l in data.languages]
            tex.append(rf"    \item \small{{{', '.join(lang_strs)}}}")
            tex.append(r"\end{itemize}")
            tex.append("")

        tex.append(r"\end{document}")
        return "\n".join(tex)

    def render_html(
        self,
        data: ResumeData,
        font_size_pt: float = 10.0,
        line_height: float = 1.25,
        margin_in: float = 0.4
    ) -> str:
        esc = self.escape_html
        b = data.basics
        safe_name = self.clean_name(b.name)

        contact_html = []
        if b.phone:
            contact_html.append(f"<span>{esc(b.phone)}</span>")
        if b.email:
            contact_html.append(f'<a href="mailto:{b.email}">{esc(b.email)}</a>')
        if b.location.city:
            contact_html.append(f"<span>{esc(b.location.city)}</span>")
        if b.url:
            contact_html.append(f'<a href="{b.url}" target="_blank">{esc(self.clean_url(b.url))}</a>')
        for p in b.profiles:
            p_url = self.get_profile_url(p)
            clean_u = self.clean_url(p_url) if p_url else (p.username or "")
            if p_url:
                contact_html.append(f'<a href="{p_url}" target="_blank">{esc(p.network)}: {esc(clean_u)}</a>')
            elif clean_u:
                contact_html.append(f'<span>{esc(p.network)}: {esc(clean_u)}</span>')

        contact_line = " | ".join(contact_html)

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>{esc(safe_name)} - Resume</title>
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
    background: #fff;
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
  }}
  .item-date {{
    font-size: {font_size_pt * 0.95}pt;
    white-space: nowrap;
  }}
  .item-subheader {{
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    font-style: italic;
    font-size: {font_size_pt * 0.95}pt;
    color: #222;
    margin-bottom: 2px;
  }}
  ul.bullets {{
    margin-left: 15px;
    list-style-type: disc;
    margin-bottom: 2px;
  }}
  ul.bullets li {{
    margin-bottom: 1.5px;
    text-align: justify;
  }}
  .skills-list {{
    font-size: {font_size_pt * 0.95}pt;
  }}
  .skills-list p {{
    margin-bottom: 2px;
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
    <div class="item-header">
      <div class="item-title">{esc(edu.institution)}</div>
      <div class="item-date">{dates}</div>
    </div>
    <div class="item-subheader">
      <div>{esc(edu.study_type)}</div>
      <div>{esc(edu.area)}</div>
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
    <div class="item-header">
      <div class="item-title">{esc(w.position)}</div>
      <div class="item-date">{dates}</div>
    </div>
    <div class="item-subheader">
      <div>{esc(w.name)}</div>
      <div>{esc(w.location)}</div>
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
    <div class="section-title">Open-Source Contributions</div>
"""
            for os_item in data.open_source:
                role_str = f" ({esc(os_item.role)})" if os_item.role else ""
                html += f"""
    <div class="item-header">
      <div class="item-title">{esc(os_item.project)}{role_str}</div>
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
                url_str = f' <a href="{p.url}" target="_blank" style="color: #0d47a1; text-decoration: none;">[Link]</a>' if p.url else ""
                dates = f"{esc(p.start_date)} – {esc(p.end_date)}" if p.end_date else esc(p.start_date)
                html += f"""
    <div class="item-header">
      <div class="item-title">{esc(p.name)}{url_str}{tech_str}</div>
      <div class="item-date">{dates}</div>
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
    <div class="section-title">Technical Skills</div>
    <div class="skills-list" style="margin-top: 2px;">
"""
            for s in data.skills:
                html += f"      <p><strong>{esc(s.name)}:</strong> {esc(', '.join(s.keywords))}</p>\n"
            html += "    </div>\n  </section>\n"

        if data.certificates:
            html += """
  <section>
    <div class="section-title">Certifications</div>
    <ul class="bullets" style="margin-top: 2px;">
"""
            for c in data.certificates:
                date_str = f" ({esc(c.date)})" if c.date else ""
                issuer_str = f" — {esc(c.issuer)}" if c.issuer else ""
                html += f"      <li><strong>{esc(c.name)}</strong>{issuer_str}{date_str}</li>\n"
            html += "    </ul>\n  </section>\n"

        if data.awards:
            html += """
  <section>
    <div class="section-title">Honors & Awards</div>
    <ul class="bullets" style="margin-top: 2px;">
"""
            for a in data.awards:
                date_str = f" ({esc(a.date)})" if a.date else ""
                awarder_str = f" — {esc(a.awarder)}" if a.awarder else ""
                html += f"      <li><strong>{esc(a.title)}</strong>{awarder_str}{date_str}</li>\n"
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
