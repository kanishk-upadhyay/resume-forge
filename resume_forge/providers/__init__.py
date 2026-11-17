"""ATS Providers subpackage for ResumeForge.

Provides a pluggable scraper interface inheriting from BaseATSProvider.
Standard providers auto-register into ATSProviderRegistry. External scrapers
can drop into ~/.config/resume-forge/plugins/ or register dynamically via
ATSProviderRegistry.register("custom", MyProvider).
"""

from .base import (
    BaseATSProvider,
    DEFAULT_HEADERS,
    ISO_COUNTRY_MAP,
    ISO_2_MAP,
    REMOTE_TERMS,
    EARLY_CAREER_SYNONYMS,
    clean_html,
    match_location,
    match_role,
    match_seniority,
    match_experience,
    match_grad_year
)
from .registry import ATSProviderRegistry
from .amazon import AmazonProvider
from .smartrecruiters import SmartRecruitersProvider
from .greenhouse import GreenhouseProvider
from .lever import LeverProvider
from .ashby import AshbyProvider
from .workday import WorkdayProvider
from .aikyam import AikyamProvider
from .hackernews import HNHiringProvider
from .rss import RSSFeedProvider

# Auto-register all standard built-in ATS providers
ATSProviderRegistry.register("amazon", AmazonProvider)
ATSProviderRegistry.register("smartrecruiters", SmartRecruitersProvider, aliases=["smartrecruiter", "sr"])
ATSProviderRegistry.register("greenhouse", GreenhouseProvider, aliases=["gh"])
ATSProviderRegistry.register("lever", LeverProvider)
ATSProviderRegistry.register("ashby", AshbyProvider)
ATSProviderRegistry.register("workday", WorkdayProvider, aliases=["wd"])
ATSProviderRegistry.register("aikyam", AikyamProvider, aliases=["aikyamjobs"])
ATSProviderRegistry.register("hn", HNHiringProvider, aliases=["yc", "hnhiring"])
ATSProviderRegistry.register("rss", RSSFeedProvider, aliases=["feed", "atom"])

__all__ = [
    "BaseATSProvider",
    "ATSProviderRegistry",
    "AmazonProvider",
    "SmartRecruitersProvider",
    "GreenhouseProvider",
    "LeverProvider",
    "AshbyProvider",
    "WorkdayProvider",
    "AikyamProvider",
    "HNHiringProvider",
    "RSSFeedProvider",
    "DEFAULT_HEADERS",
    "ISO_COUNTRY_MAP",
    "ISO_2_MAP",
    "REMOTE_TERMS",
    "EARLY_CAREER_SYNONYMS",
    "clean_html",
    "match_location",
    "match_role",
    "match_seniority",
    "match_experience",
    "match_grad_year",
]
