"""Resume Forge Template Engine & Registry."""

from .base import BaseTemplate
from .cern import CernTemplate
from .harvard import HarvardTemplate
from .jakes import JakesTemplate
from .minimalist import MinimalistTemplate
from .quant import QuantTemplate
from .awesome import AwesomeCvTemplate
from .academic import AcademicTemplate
from .registry import TemplateRegistry

__all__ = [
    "BaseTemplate",
    "TemplateRegistry",
    "CernTemplate",
    "HarvardTemplate",
    "JakesTemplate",
    "MinimalistTemplate",
    "QuantTemplate",
    "AwesomeCvTemplate",
    "AcademicTemplate"
]
