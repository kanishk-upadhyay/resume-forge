"""Wall Street & Quant Dense Resume Template - Citadel & Jane Street Aesthetic."""

import re
from typing import List
from .base import BaseTemplate
from ..core.schema import ResumeData


class QuantTemplate(BaseTemplate):
    """Wall Street & Quant Dense Resume Template.
    
    Maximum density layout designed for Quantitative Trading firms, Hedge Funds,
    and High-Performance C++ Systems engineering (Citadel, Jane Street, Two Sigma).
    Features tight 0.32in margins, Garamond typography, zero extraneous whitespace,
    and prominent metrics.
    """

    name = "quant"
    display_name = "Wall Street & Quant Dense"
    description = "Ultra-dense Garamond layout for Quant Developers, Low-Latency C++, and Trading Firms."
    category = "Quant & Finance"
    target_roles = ["Quant Developer", "C++ Systems Engineer", "Hedge Fund Intern", "Algorithmic Trader", "Infra Core"]
    default_font_size = 9.5
    default_line_height = 1.18
    default_margin = 0.32

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

        contact_line = " $|$ ".join(contact_items)

        tex = [
            r"\documentclass[9.5pt,letterpaper]{article}",
            r"\usepackage[utf8]{inputenc}",
            r"\usepackage[T1]{fontenc}",
            r"\usepackage{ebgaramond}",
            r"\usepackage[margin=0.32in]{geometry}",
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
            r"% High-Density Quant Section Style",
            r"\titleformat{\section}",
            r"  {\vspace{-5pt}\scshape\bfseries\fontsize{10.5}{12}\selectfont}",
            r"  {}{0em}{}[\vspace{1pt}\titlerule\vspace{2pt}]",
            r"\titlespacing*{\section}{0pt}{4pt}{2pt}",
            "",
            r"% Dense list spacing",
            r"\setlist[itemize]{leftmargin=1.1em, itemsep=-2pt, topsep=1pt, parsep=0pt, partopsep=0pt}",
            "",
            r"\begin{document}",
            "",
            r"%----------HEADER----------",
            r"\begin{center}",
            rf"  {{\fontsize{{16}}{{18}}\selectfont \textbf{{{esc(safe_name)}}}}} \\[2pt]",
            rf"  {{\footnotesize {contact_line}}}",
            r"\end{center}",
            r"\vspace{-6pt}",
            ""
        ]

        if b.summary:
            tex.append(r"\section{Summary}")
            tex.append(f"{{\\small {esc(b.summary)}}}\n")

        # In Quant, Education is prioritized upfront for GPA / Math / CS rankings
        if data.education:
            tex.append(r"\section{Education}")
            for edu in data.education:
                dates = f"{edu.start_date} -- {edu.end_date}" if edu.end_date else edu.start_date
                tex.append(r"\noindent\begin{tabular*}{\textwidth}{@{\extracolsep{\fill}}lr}")
                tex.append(rf"  \textbf{{{esc(edu.institution)}}} & \textbf{{{esc(dates)}}} \\")
                tex.append(rf"  \textit{{{esc(edu.study_type)}}}, {esc(edu.area or '')} & \textit{{{esc(edu.highlights[0] if edu.highlights else '')}}} \\")
                tex.append(r"\end{tabular*}\vspace{-2pt}")
                if len(edu.highlights) > 1:
                    tex.append(r"\begin{itemize}")
                    for h in edu.highlights[1:]:
                        tex.append(rf"  \item {esc(h)}")
                    tex.append(r"\end{itemize}")
            tex.append("")

        if data.work:
            tex.append(r"\section{Professional Experience}")
            for w in data.work:
                dates = f"{w.start_date} -- {w.end_date}" if w.end_date else w.start_date
                tex.append(r"\noindent\begin{tabular*}{\textwidth}{@{\extracolsep{\fill}}lr}")
                tex.append(rf"  \textbf{{{esc(w.name)}}} & \textbf{{{esc(dates)}}} \\")
                tex.append(rf"  \textit{{{esc(w.position)}}} & \textit{{{esc(w.location or '')}}} \\")
                tex.append(r"\end{tabular*}\vspace{-2pt}")
                if w.highlights:
                    tex.append(r"\begin{itemize}")
                    for h in w.highlights:
                        tex.append(rf"  \item {esc(h)}")
                    tex.append(r"\end{itemize}")
            tex.append("")

        if data.projects:
            tex.append(r"\section{Quantitative & Systems Projects}")
            for p in data.projects:
                dates = f"{p.start_date} -- {p.end_date}" if p.end_date else p.start_date
                tech = f" [{esc(', '.join(p.keywords))}]" if p.keywords else ""
                url_s = f" [\\href{{{p.url}}}{{Link}}]" if p.url else ""
                tex.append(r"\noindent\begin{tabular*}{\textwidth}{@{\extracolsep{\fill}}lr}")
                tex.append(rf"  \textbf{{{esc(p.name)}}}{url_s} \textit{{{esc(tech)}}} & \textbf{{{esc(dates)}}} \\")
                tex.append(r"\end{tabular*}\vspace{-2pt}")
                if p.highlights:
                    tex.append(r"\begin{itemize}")
                    for h in p.highlights:
                        tex.append(rf"  \item {esc(h)}")
                    tex.append(r"\end{itemize}")
            tex.append("")

        if data.skills:
            tex.append(r"\section{Technical Skills}")
            tex.append(r"\begin{itemize}")
            for s in data.skills:
                tex.append(rf"  \item \textbf{{{esc(s.name)}}}: {esc(', '.join(s.keywords))}")
            tex.append(r"\end{itemize}")
            tex.append("")

        if data.open_source:
            tex.append(r"\section{Open-Source Systems Engineering}")
            for os_item in data.open_source:
                tex.append(r"\noindent\begin{tabular*}{\textwidth}{@{\extracolsep{\fill}}lr}")
                tex.append(rf"  \textbf{{{esc(os_item.project)}}} & \textit{{{esc(os_item.role or '')}}} \\")
                tex.append(r"\end{tabular*}\vspace{-2pt}")
                if os_item.highlights:
                    tex.append(r"\begin{itemize}")
                    for h in os_item.highlights:
                        tex.append(rf"  \item {esc(h)}")
                    tex.append(r"\end{itemize}")
            tex.append("")

        if data.awards:
            tex.append(r"\section{Honors, Olympiads & Awards}")
            tex.append(r"\begin{itemize}")
            for a in data.awards:
                date_s = f" ({esc(a.date)})" if a.date else ""
                awarder_s = f" -- {esc(a.awarder)}" if a.awarder else ""
                tex.append(rf"  \item \textbf{{{esc(a.title)}}}{awarder_s}{date_s}")
            tex.append(r"\end{itemize}")
            tex.append("")

        if data.certificates:
            tex.append(r"\section{Certifications}")
            tex.append(r"\begin{itemize}")
            for c in data.certificates:
                date_s = f" ({esc(c.date)})" if c.date else ""
                issuer_s = f" -- {esc(c.issuer)}" if c.issuer else ""
                tex.append(rf"  \item \textbf{{{esc(c.name)}}}{issuer_s}{date_s}")
            tex.append(r"\end{itemize}")
            tex.append("")

        if data.publications:
            tex.append(r"\section{Publications}")
            tex.append(r"\begin{itemize}")
            for pub in data.publications:
                tex.append(rf"  \item {esc(pub.name)}")
            tex.append(r"\end{itemize}")
            tex.append("")

        if data.languages:
            tex.append(r"\section{Languages}")
            lang_strs = [f"{esc(l.language)} ({esc(l.fluency)})" if l.fluency else esc(l.language) for l in data.languages]
            tex.append(rf"\noindent\footnotesize{{{', '.join(lang_strs)}}}\vspace{{2pt}}")
            tex.append("")

        tex.append(r"\end{document}")
        return "\n".join(tex)

    def render_html(
        self,
        data: ResumeData,
        font_size_pt: float = 9.5,
        line_height: float = 1.18,
        margin_in: float = 0.32
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

        contact_line = " | ".join(contact_html)

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>{esc(safe_name)} - Resume (Quant Dense)</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=EB+Garamond:ital,wght@0,400;0,600;0,700;1,400;1,600&display=swap" rel="stylesheet">
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
    font-family: 'EB Garamond', Garamond, 'Times New Roman', serif;
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
    margin-bottom: 4px;
  }}
  h1 {{
    font-size: {font_size_pt * 1.6}pt;
    font-weight: 700;
    letter-spacing: 0.5px;
    text-transform: uppercase;
    margin-bottom: 1px;
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
    margin-top: 4px;
  }}
  .section-title {{
    font-size: {font_size_pt * 1.05}pt;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.4px;
    border-bottom: 1px solid #000;
    padding-bottom: 1px;
    margin-bottom: 2px;
  }}
  .item-row {{
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    font-weight: 600;
    margin-top: 2px;
  }}
  .item-subrow {{
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    font-style: italic;
    font-size: {font_size_pt * 0.95}pt;
    margin-bottom: 1px;
  }}
  ul.bullets {{
    margin-left: 14px;
    list-style-type: disc;
    margin-bottom: 2px;
  }}
  ul.bullets li {{
    margin-bottom: 1px;
    text-align: justify;
  }}
  .skills-line {{
    font-size: {font_size_pt * 0.95}pt;
    margin-bottom: 1px;
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
    <div class="section-title">Summary</div>
    <p style="text-align: justify; margin-top: 1px;">{esc(b.summary)}</p>
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
      <div>{dates}</div>
    </div>
    <div class="item-subrow">
      <div>{esc(edu.study_type)}, {esc(edu.area)}</div>
      <div>{esc(edu.highlights[0] if edu.highlights else '')}</div>
    </div>
"""
                if len(edu.highlights) > 1:
                    html += '    <ul class="bullets">\n'
                    for h in edu.highlights[1:]:
                        html += f"      <li>{esc(h)}</li>\n"
                    html += "    </ul>\n"
            html += "  </section>\n"

        if data.work:
            html += """
  <section>
    <div class="section-title">Professional Experience</div>
"""
            for w in data.work:
                dates = f"{esc(w.start_date)} – {esc(w.end_date)}" if w.end_date else esc(w.start_date)
                html += f"""
    <div class="item-row">
      <div>{esc(w.name)}</div>
      <div>{dates}</div>
    </div>
    <div class="item-subrow">
      <div>{esc(w.position)}</div>
      <div>{esc(w.location or '')}</div>
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
    <div class="section-title">Quantitative & Systems Projects</div>
"""
            for p in data.projects:
                tech_str = f" [<em>{esc(', '.join(p.keywords))}</em>]" if p.keywords else ""
                url_str = f' [<a href="{p.url}" target="_blank">Link</a>]' if p.url else ""
                dates = f"{esc(p.start_date)} – {esc(p.end_date)}" if p.end_date else esc(p.start_date)
                html += f"""
    <div class="item-row">
      <div>{esc(p.name)}{url_str}{tech_str}</div>
      <div>{dates}</div>
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
"""
            for s in data.skills:
                html += f'    <div class="skills-line"><strong>{esc(s.name)}:</strong> {esc(", ".join(s.keywords))}</div>\n'
            html += "  </section>\n"

        if data.open_source:
            html += """
  <section>
    <div class="section-title">Open-Source Systems Engineering</div>
"""
            for os_item in data.open_source:
                html += f"""
    <div class="item-row">
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

        if data.awards:
            html += """
  <section>
    <div class="section-title">Honors, Olympiads & Awards</div>
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
    <p style="margin-top: 1px;">
"""
            lang_strs = [f"{esc(l.language)} ({esc(l.fluency)})" if l.fluency else esc(l.language) for l in data.languages]
            html += f"      {', '.join(lang_strs)}\n    </p>\n  </section>\n"

        html += """
</div>
</body>
</html>
"""
        return html
