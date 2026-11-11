"""Base template interface and shared formatting utilities for ResumeForge."""

from abc import ABC, abstractmethod
import re
from html import escape as html_escape
from typing import List, Optional, Dict, Any
from ..core.schema import ResumeData


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
