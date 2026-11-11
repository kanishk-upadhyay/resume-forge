"""Template Registry: Central registry and dispatcher for ResumeForge templates."""

from typing import Dict, List, Optional, Type, Any
from pathlib import Path

from .base import BaseTemplate
from .cern import CernTemplate
from .harvard import HarvardTemplate
from .jakes import JakesTemplate
from .minimalist import MinimalistTemplate
from .quant import QuantTemplate
from .awesome import AwesomeCvTemplate
from .academic import AcademicTemplate


class TemplateRegistry:
    """Manages available resume templates and provides dynamic lookup."""

    _templates: Dict[str, BaseTemplate] = {}

    @classmethod
    def register(cls, template: BaseTemplate) -> None:
        """Registers a template instance."""
        cls._templates[template.name.lower()] = template

    @classmethod
    def get(cls, name: Optional[str] = None) -> BaseTemplate:
        """Retrieves a template by name, defaulting to 'cern' if not found or empty."""
        cls._ensure_initialized()
        if not name:
            return cls._templates["cern"]
        
        normalized = name.strip().lower()
        # Aliases
        alias_map = {
            "default": "cern",
            "overleaf": "cern",
            "cern_fullstack": "cern",
            "jake": "jakes",
            "jakes_resume": "jakes",
            "ivy": "harvard",
            "ivy_league": "harvard",
            "fas": "harvard",
            "stripe": "minimalist",
            "vercel": "minimalist",
            "linear": "minimalist",
            "citadel": "quant",
            "jane_street": "quant",
            "wallstreet": "quant",
            "posquit0": "awesome",
            "awesome-cv": "awesome",
            "awesome_cv": "awesome",
            "ieee": "academic",
            "research": "academic",
            "cv": "academic"
        }
        target = alias_map.get(normalized, normalized)
        return cls._templates.get(target, cls._templates["cern"])

    @classmethod
    def list_templates(cls) -> List[Dict[str, Any]]:
        """Returns metadata list of all available templates."""
        cls._ensure_initialized()
        results = []
        for tmpl in cls._templates.values():
            results.append({
                "name": tmpl.name,
                "display_name": tmpl.display_name,
                "description": tmpl.description,
                "category": tmpl.category,
                "target_roles": tmpl.target_roles,
                "default_font_size": tmpl.default_font_size,
                "default_line_height": tmpl.default_line_height,
                "default_margin": tmpl.default_margin
            })
        return results

    @classmethod
    def get_template_names(cls) -> List[str]:
        """Returns list of all canonical template names."""
        cls._ensure_initialized()
        return list(cls._templates.keys())

    @classmethod
    def _ensure_initialized(cls) -> None:
        """Initializes standard templates if not already registered."""
        if not cls._templates:
            cls.register(CernTemplate())
            cls.register(HarvardTemplate())
            cls.register(JakesTemplate())
            cls.register(MinimalistTemplate())
            cls.register(QuantTemplate())
            cls.register(AwesomeCvTemplate())
            cls.register(AcademicTemplate())


# Auto-initialize standard templates on module load
TemplateRegistry._ensure_initialized()
