"""Tech Minimalist Resume Template - Stripe & Vercel Product Aesthetic."""

import re
from typing import List
from .base import BaseTemplate
from ..core.schema import ResumeData


class MinimalistTemplate(BaseTemplate):
    """Tech Minimalist Resume Template.
    
    Modern product-tech aesthetic inspired by Stripe, Vercel, and Linear.
    Features geometric Inter typography, subtle slate accent borders,
    monospaced tech stack pills, and balanced breathing room.
    """

    name = "minimalist"
    display_name = "Tech Minimalist (Stripe / Vercel)"
    description = "Modern design-forward product aesthetic with Inter font and sleek monospaced tech tags."
    category = "Product & Startups"
    target_roles = ["Frontend Engineer", "Full-Stack Engineer", "Product Engineer", "Platform Engineer", "Founding Engineer"]
    default_font_size = 9.8
    default_line_height = 1.30
    default_margin = 0.42

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
            r"\usepackage[margin=0.42in]{geometry}",
            r"\usepackage{titlesec}",
            r"\usepackage{enumitem}",
            r"\usepackage{xcolor}",
            r"\usepackage[hidelinks]{hyperref}",
            r"\usepackage{tabularx}",
            r"\usepackage{fancyhdr}",
            r"% Modern Clean Typography",
            r"\usepackage[scaled=0.94]{helvet}",
            r"\renewcommand{\familydefault}{\sfdefault}",
            r"\pagestyle{empty}",
            r"\raggedbottom",
            r"\raggedright",
            r"\setlength{\tabcolsep}{0in}",
            "",
            r"% Slate Color Palette",
            r"\definecolor{slate900}{RGB}{15,23,42}",
            r"\definecolor{slate600}{RGB}{71,85,105}",
            r"\definecolor{slate400}{RGB}{148,163,184}",
            r"\definecolor{blue600}{RGB}{37,99,235}",
            "",
            r"% Modern Section Styling",
            r"\titleformat{\section}",
            r"  {\vspace{-3pt}\fontsize{11}{13}\bfseries\color{slate900}\uppercase}",
            r"  {}{0em}{}[\vspace{1pt}\color{slate400}\titlerule\vspace{2pt}]",
            r"\titlespacing*{\section}{0pt}{6pt}{4pt}",
            "",
            r"% List item spacing",
            r"\setlist[itemize]{leftmargin=1.1em, itemsep=-1pt, topsep=1pt, parsep=0pt, partopsep=0pt}",
            "",
            r"\begin{document}",
            "",
            r"%----------HEADER----------",
            rf"{{\LARGE \textbf{{\color{{slate900}} {esc(safe_name)}}}}} \\[2pt]",
            rf"{{\small \color{{slate600}} {contact_line}}}",
            r"\vspace{-2pt}",
            ""
        ]

        if b.summary:
            tex.append(r"\section{About}")
            tex.append(f"{{\\color{{slate900}} {esc(b.summary)}}}\n")

        if data.work:
            tex.append(r"\section{Experience}")
            for w in data.work:
                dates = f"{w.start_date} -- {w.end_date}" if w.end_date else w.start_date
                tex.append(r"\noindent\begin{tabular*}{\textwidth}{@{\extracolsep{\fill}}lr}")
                tex.append(rf"  \textbf{{{esc(w.position)}}} $\cdot$ \textbf{{{esc(w.name)}}} & {{\color{{slate600}}\small {esc(dates)}}} \\")
                if w.location:
                    tex.append(rf"  {{\color{{slate600}}\small {esc(w.location)}}} & \\")
                tex.append(r"\end{tabular*}\vspace{-2pt}")
                if w.highlights:
                    tex.append(r"\begin{itemize}")
                    for h in w.highlights:
                        tex.append(rf"  \item {esc(h)}")
                    tex.append(r"\end{itemize}\vspace{3pt}")
            tex.append("")

        if data.projects:
            tex.append(r"\section{Projects}")
            for p in data.projects:
                dates = f"{p.start_date} -- {p.end_date}" if p.end_date else p.start_date
                tech = f" [{esc(', '.join(p.keywords))}]" if p.keywords else ""
                url_s = f" [\\href{{{p.url}}}{{Link}}]" if p.url else ""
                tex.append(r"\noindent\begin{tabular*}{\textwidth}{@{\extracolsep{\fill}}lr}")
                tex.append(rf"  \textbf{{{esc(p.name)}}}{url_s} {{\color{{slate600}}\footnotesize\texttt{{{esc(tech)}}}}} & {{\color{{slate600}}\small {esc(dates)}}} \\")
                tex.append(r"\end{tabular*}\vspace{-2pt}")
                if p.highlights:
                    tex.append(r"\begin{itemize}")
                    for h in p.highlights:
                        tex.append(rf"  \item {esc(h)}")
                    tex.append(r"\end{itemize}\vspace{3pt}")
            tex.append("")

        if data.open_source:
            tex.append(r"\section{Open-Source}")
            for os_item in data.open_source:
                tex.append(r"\noindent\begin{tabular*}{\textwidth}{@{\extracolsep{\fill}}lr}")
                tex.append(rf"  \textbf{{{esc(os_item.project)}}} $\cdot$ {{\color{{slate600}} {esc(os_item.role or '')}}} & \\")
                tex.append(r"\end{tabular*}\vspace{-2pt}")
                if os_item.highlights:
                    tex.append(r"\begin{itemize}")
                    for h in os_item.highlights:
                        tex.append(rf"  \item {esc(h)}")
                    tex.append(r"\end{itemize}\vspace{3pt}")
            tex.append("")

        if data.skills:
            tex.append(r"\section{Technical Stack}")
            tex.append(r"\begin{itemize}")
            for s in data.skills:
                tex.append(rf"  \item \textbf{{{esc(s.name)}}}: {esc(', '.join(s.keywords))}")
            tex.append(r"\end{itemize}\vspace{3pt}")
            tex.append("")

        if data.education:
            tex.append(r"\section{Education}")
            for edu in data.education:
                dates = f"{edu.start_date} -- {edu.end_date}" if edu.end_date else edu.start_date
                tex.append(r"\noindent\begin{tabular*}{\textwidth}{@{\extracolsep{\fill}}lr}")
                tex.append(rf"  \textbf{{{esc(edu.institution)}}} & {{\color{{slate600}}\small {esc(dates)}}} \\")
                tex.append(rf"  {{\color{{slate600}} {esc(edu.study_type)}}} $\cdot$ {esc(edu.area or '')} & \\")
                tex.append(r"\end{tabular*}\vspace{-2pt}")
                if edu.highlights:
                    tex.append(r"\begin{itemize}")
                    for h in edu.highlights:
                        tex.append(rf"  \item {esc(h)}")
                    tex.append(r"\end{itemize}\vspace{3pt}")
            tex.append("")

        if data.certificates:
            tex.append(r"\section{Certifications}")
            tex.append(r"\begin{itemize}")
            for c in data.certificates:
                date_s = f" ({esc(c.date)})" if c.date else ""
                issuer_s = f" -- {esc(c.issuer)}" if c.issuer else ""
                tex.append(rf"  \item \textbf{{{esc(c.name)}}}{issuer_s}{date_s}")
            tex.append(r"\end{itemize}\vspace{3pt}")
            tex.append("")

        if data.awards:
            tex.append(r"\section{Honors \& Recognition}")
            tex.append(r"\begin{itemize}")
            for a in data.awards:
                date_s = f" ({esc(a.date)})" if a.date else ""
                awarder_s = f" -- {esc(a.awarder)}" if a.awarder else ""
                tex.append(rf"  \item \textbf{{{esc(a.title)}}}{awarder_s}{date_s}")
            tex.append(r"\end{itemize}\vspace{3pt}")
            tex.append("")

        if data.publications:
            tex.append(r"\section{Publications}")
            tex.append(r"\begin{itemize}")
            for pub in data.publications:
                tex.append(rf"  \item {esc(pub.name)}")
            tex.append(r"\end{itemize}\vspace{3pt}")
            tex.append("")

        if data.languages:
            tex.append(r"\section{Languages}")
            lang_strs = [f"{esc(l.language)} ({esc(l.fluency)})" if l.fluency else esc(l.language) for l in data.languages]
            tex.append(rf"\noindent{{\small {', '.join(lang_strs)}}}\vspace{{3pt}}")
            tex.append("")

        tex.append(r"\end{document}")
        return "\n".join(tex)

    def render_html(
        self,
        data: ResumeData,
        font_size_pt: float = 9.8,
        line_height: float = 1.30,
        margin_in: float = 0.42
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
<title>{esc(safe_name)} - Resume (Tech Minimalist)</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
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
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    font-size: {font_size_pt}pt;
    line-height: {line_height};
    color: #0f172a;
    background: #fff;
    -webkit-print-color-adjust: exact;
  }}
  .resume-page {{
    width: 100%;
    margin: 0 auto;
    background: #fff;
  }}
  header {{
    text-align: left;
    margin-bottom: 8px;
    padding-bottom: 4px;
    border-bottom: 2px solid #0f172a;
  }}
  h1 {{
    font-size: {font_size_pt * 1.9}pt;
    font-weight: 700;
    letter-spacing: -0.5px;
    color: #0f172a;
    margin-bottom: 2px;
  }}
  .contact-bar {{
    font-size: {font_size_pt * 0.9}pt;
    color: #475569;
  }}
  .contact-bar a {{
    color: #2563eb;
    text-decoration: none;
  }}
  section {{
    margin-top: 7px;
  }}
  .section-title {{
    font-size: {font_size_pt * 1.05}pt;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 1.2px;
    color: #0f172a;
    border-bottom: 1px solid #cbd5e1;
    padding-bottom: 2px;
    margin-bottom: 4px;
  }}
  .item-header {{
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    font-weight: 600;
    margin-top: 4px;
  }}
  .item-title {{
    color: #0f172a;
  }}
  .item-date {{
    font-size: {font_size_pt * 0.9}pt;
    color: #64748b;
    font-weight: normal;
  }}
  .item-subheader {{
    font-size: {font_size_pt * 0.92}pt;
    color: #475569;
    margin-bottom: 2px;
  }}
  ul.bullets {{
    margin-left: 15px;
    list-style-type: square;
    margin-bottom: 3px;
  }}
  ul.bullets li {{
    margin-bottom: 2px;
    text-align: justify;
    color: #1e293b;
  }}
  .tag {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.82em;
    background: #f1f5f9;
    color: #0f172a;
    padding: 1px 5px;
    border-radius: 3px;
    margin-left: 4px;
  }}
  .skills-box p {{
    margin-bottom: 3px;
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
    <div class="section-title">About</div>
    <p style="text-align: justify; margin-top: 3px; color: #334155;">{esc(b.summary)}</p>
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
    <div class="item-header">
      <div class="item-title">{esc(w.position)} &middot; {esc(w.name)}</div>
      <div class="item-date">{dates}</div>
    </div>
"""
                if w.location:
                    html += f'    <div class="item-subheader">{esc(w.location)}</div>\n'
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
                tags = "".join(f'<span class="tag">{esc(k)}</span>' for k in p.keywords[:4]) if p.keywords else ""
                url_str = f' <a href="{p.url}" target="_blank" style="color: #2563eb; text-decoration: none;">[↗]</a>' if p.url else ""
                dates = f"{esc(p.start_date)} – {esc(p.end_date)}" if p.end_date else esc(p.start_date)
                html += f"""
    <div class="item-header">
      <div class="item-title">{esc(p.name)}{url_str} {tags}</div>
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
    <div class="section-title">Open-Source</div>
"""
            for os_item in data.open_source:
                role_str = f" &middot; {esc(os_item.role)}" if os_item.role else ""
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

        if data.skills:
            html += """
  <section>
    <div class="section-title">Technical Stack</div>
    <div class="skills-box" style="margin-top: 3px;">
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
    <div class="item-header">
      <div class="item-title">{esc(edu.institution)}</div>
      <div class="item-date">{dates}</div>
    </div>
    <div class="item-subheader">{esc(edu.study_type)} &middot; {esc(edu.area)}</div>
"""
                if edu.highlights:
                    html += '    <ul class="bullets">\n'
                    for h in edu.highlights:
                        html += f"      <li>{esc(h)}</li>\n"
                    html += "    </ul>\n"
            html += "  </section>\n"

        if data.certificates:
            html += """
  <section>
    <div class="section-title">Certifications</div>
    <ul class="bullets" style="margin-top: 3px;">
"""
            for c in data.certificates:
                date_s = f" ({esc(c.date)})" if c.date else ""
                issuer_s = f" — {esc(c.issuer)}" if c.issuer else ""
                html += f"      <li><strong>{esc(c.name)}</strong>{issuer_s}{date_s}</li>\n"
            html += "    </ul>\n  </section>\n"

        if data.awards:
            html += """
  <section>
    <div class="section-title">Honors & Recognition</div>
    <ul class="bullets" style="margin-top: 3px;">
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
    <ul class="bullets" style="margin-top: 3px;">
"""
            for pub in data.publications:
                html += f"      <li>{esc(pub.name)}</li>\n"
            html += "    </ul>\n  </section>\n"

        if data.languages:
            html += """
  <section>
    <div class="section-title">Languages</div>
    <p style="margin-top: 3px;">
"""
            lang_strs = [f"{esc(l.language)} ({esc(l.fluency)})" if l.fluency else esc(l.language) for l in data.languages]
            html += f"      {', '.join(lang_strs)}\n    </p>\n  </section>\n"

        html += """
</div>
</body>
</html>
"""
        return html
