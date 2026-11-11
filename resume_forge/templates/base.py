"""Base template interface and shared formatting utilities for ResumeForge."""

from abc import ABC, abstractmethod
import re
from html import escape as html_escape
from typing import List, Optional, Dict, Any, TYPE_CHECKING
from ..core.schema import ResumeData

if TYPE_CHECKING:
    from ..core.letter import CoverLetterData


class BaseTemplate(ABC):
    """Abstract base class for all resume presentation templates."""

    name: str = "base"
    display_name: str = "Base Template"
    description: str = "Base resume template"
    category: str = "General"
    target_roles: List[str] = []
    default_font_size: float = 10.0
    default_line_height: float = 1.25
    default_margin: float = 0.4

    @staticmethod
    def escape_latex(s: Optional[str]) -> str:
        """Escapes special LaTeX characters while avoiding double-escaping."""
        if not s:
            return ""
        s = re.sub(r'(?<!\\)&', r'\&', s)
        s = re.sub(r'(?<!\\)%', r'\%', s)
        s = re.sub(r'(?<!\\)\$', r'\$', s)
        s = re.sub(r'(?<!\\)#', r'\#', s)
        s = re.sub(r'(?<!\\)_', r'\_', s)
        s = s.replace('<', r'\textless{}').replace('>', r'\textgreater{}')
        return s

    @staticmethod
    def escape_html(s: Optional[str]) -> str:
        """HTML escapes text cleanly."""
        return html_escape(s or "")

    @staticmethod
    def clean_name(name: Optional[str]) -> str:
        """Strips LaTeX formatting artifacts from candidate name."""
        return re.sub(r'[{}]', '', name or "").strip()

    @staticmethod
    def clean_url(url: Optional[str]) -> str:
        """Strips protocol prefix from URL for clean display."""
        if not url:
            return ""
        return re.sub(r'^https?://', '', url).rstrip('/')

    @classmethod
    def get_profile_url(cls, p) -> str:
        """Returns valid profile URL, inferring standard URLs from username if empty."""
        if getattr(p, "url", None):
            return p.url
        username = getattr(p, "username", "")
        if not username:
            return ""
        net = (getattr(p, "network", "") or "").lower()
        if "github" in net:
            return f"https://github.com/{username}"
        if "linkedin" in net:
            return f"https://linkedin.com/in/{username}"
        if "gitlab" in net:
            return f"https://gitlab.com/{username}"
        if "twitter" in net or net == "x":
            return f"https://x.com/{username}"
        return ""

    @abstractmethod
    def render_latex(self, data: ResumeData) -> str:
        """Renders ResumeData to production LaTeX code."""
        pass

    @abstractmethod
    def render_html(
        self,
        data: ResumeData,
        font_size_pt: float = 10.0,
        line_height: float = 1.25,
        margin_in: float = 0.4
    ) -> str:
        """Renders ResumeData to pixel-perfect HTML for headless Chrome printing."""
        pass

    def render_cover_letter_latex(self, data: "CoverLetterData") -> str:
        """Renders CoverLetterData to production LaTeX matching this template's typography."""
        b = data.sender
        r = data.recipient
        esc = self.escape_latex

        links = []
        if b.phone:
            links.append(esc(b.phone))
        if b.email:
            links.append(r"\href{mailto:" + esc(b.email) + "}{" + esc(b.email) + "}")
        if b.url:
            links.append(r"\href{" + esc(b.url) + "}{" + esc(self.clean_url(b.url)) + "}")
        for p in b.profiles:
            p_url = self.get_profile_url(p)
            if p_url:
                links.append(r"\href{" + esc(p_url) + "}{" + esc(p.network) + "}")

        contact_line = " $|$ ".join(links)
        name_clean = esc(self.clean_name(b.name))

        recipient_block = []
        if r.name:
            recipient_block.append(r"\textbf{" + esc(r.name) + r"}\\")
        if r.title:
            recipient_block.append(esc(r.title) + r"\\")
        if r.company:
            recipient_block.append(r"\textbf{" + esc(r.company) + r"}\\")
        if r.address:
            recipient_block.append(esc(r.address) + r"\\")
        if r.city:
            recipient_block.append(esc(r.city) + r"\\")
        recipient_tex = "\n".join(recipient_block)

        body_tex = "\n\n".join([esc(p) for p in data.body_paragraphs])

        return rf"""\documentclass[10pt,letterpaper]{{article}}
\usepackage[utf8]{{inputenc}}
\usepackage[T1]{{fontenc}}
\usepackage[margin={self.default_margin:.2f}in]{{geometry}}
\usepackage{{hyperref}}
\usepackage{{enumitem}}
\usepackage{{parskip}}

\hypersetup{{
    colorlinks=true,
    linkcolor=black,
    urlcolor=black,
}}

\pagestyle{{empty}}

\begin{{document}}

% --- HEADER (Matching {self.display_name}) ---
\begin{{center}}
    {{\LARGE \textbf{{{name_clean}}}}} \\[4pt]
    \small {contact_line}
\end{{center}}

\vspace{{10pt}}
\hrule
\vspace{{16pt}}

% --- DATE & RECIPIENT ---
\textbf{{{esc(data.date)}}}

\vspace{{10pt}}
{recipient_tex}

\vspace{{14pt}}

% --- SALUTATION ---
\textbf{{{esc(data.salutation)}}}

\vspace{{8pt}}

% --- BODY PARAGRAPHS ---
{esc(data.opening)}

\vspace{{8pt}}
{body_tex}

\vspace{{8pt}}
{esc(data.closing)}

\vspace{{18pt}}

% --- SIGN-OFF ---
{esc(data.sign_off)} \\[24pt]
\textbf{{{name_clean}}}

\end{{document}}
"""

    def render_cover_letter_html(
        self,
        data: "CoverLetterData",
        font_size_pt: Optional[float] = None,
        line_height: Optional[float] = None,
        margin_in: Optional[float] = None
    ) -> str:
        """Renders CoverLetterData to pixel-perfect HTML matching this template."""
        f_size = font_size_pt or self.default_font_size
        l_height = line_height or self.default_line_height
        m_in = margin_in or self.default_margin

        b = data.sender
        r = data.recipient
        esc = self.escape_html

        links = []
        if b.phone:
            links.append(esc(b.phone))
        if b.email:
            links.append(f'<a href="mailto:{esc(b.email)}">{esc(b.email)}</a>')
        if b.url:
            links.append(f'<a href="{esc(b.url)}">{esc(self.clean_url(b.url))}</a>')
        for p in b.profiles:
            p_url = self.get_profile_url(p)
            if p_url:
                links.append(f'<a href="{esc(p_url)}">{esc(p.network)}</a>')

        contact_html = " &bull; ".join(links)
        name_clean = esc(self.clean_name(b.name))

        recipient_lines = []
        if r.name:
            recipient_lines.append(f"<strong>{esc(r.name)}</strong>")
        if r.title:
            recipient_lines.append(esc(r.title))
        if r.company:
            recipient_lines.append(f"<strong>{esc(r.company)}</strong>")
        if r.address:
            recipient_lines.append(esc(r.address))
        if r.city:
            recipient_lines.append(esc(r.city))
        recipient_html = "<br>".join(recipient_lines)

        paragraphs_html = "".join([f"<p>{esc(p)}</p>" for p in data.body_paragraphs])

        # Typography per template
        font_stack = "'Computer Modern', 'Latin Modern Roman', 'Times New Roman', serif"
        if self.name in ("jakes", "minimalist", "awesome"):
            font_stack = "-apple-system, BlinkMacSystemFont, 'Inter', 'Segoe UI', Roboto, sans-serif"
        elif self.name in ("harvard", "quant"):
            font_stack = "'EB Garamond', 'Garamond', 'Georgia', serif"

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>{name_clean} - Cover Letter ({self.display_name})</title>
<style>
  @page {{
    size: letter;
    margin: 0;
  }}
  * {{
    box-sizing: border-box;
    margin: 0;
    padding: 0;
  }}
  body {{
    font-family: {font_stack};
    font-size: {f_size}pt;
    line-height: {l_height};
    color: #111827;
    background: #ffffff;
    padding: {m_in}in;
    width: 8.5in;
    min-height: 11in;
    margin: 0 auto;
    -webkit-font-smoothing: antialiased;
  }}
  .header {{
    text-align: center;
    border-bottom: 1.5px solid #111827;
    padding-bottom: 8px;
    margin-bottom: 16px;
  }}
  .name {{
    font-size: 20pt;
    font-weight: 700;
    letter-spacing: 0.5px;
    margin-bottom: 4px;
    text-transform: uppercase;
  }}
  .contact {{
    font-size: 9pt;
    color: #374151;
  }}
  .contact a {{
    color: inherit;
    text-decoration: none;
  }}
  .meta-block {{
    margin-bottom: 16px;
    font-size: 10pt;
    line-height: 1.4;
  }}
  .date {{
    font-weight: 600;
    margin-bottom: 8px;
  }}
  .salutation {{
    font-weight: 600;
    margin-bottom: 12px;
  }}
  .content p {{
    margin-bottom: 12px;
    text-align: justify;
  }}
  .sign-off {{
    margin-top: 24px;
    line-height: 1.5;
  }}
  .signature {{
    font-weight: 700;
    margin-top: 28px;
  }}
</style>
</head>
<body>
  <div class="header">
    <div class="name">{name_clean}</div>
    <div class="contact">{contact_html}</div>
  </div>

  <div class="meta-block">
    <div class="date">{esc(data.date)}</div>
    <div>{recipient_html}</div>
  </div>

  <div class="salutation">{esc(data.salutation)}</div>

  <div class="content">
    <p>{esc(data.opening)}</p>
    {paragraphs_html}
    <p>{esc(data.closing)}</p>
  </div>

  <div class="sign-off">
    <div>{esc(data.sign_off)}</div>
    <div class="signature">{name_clean}</div>
  </div>
</body>
</html>
"""
