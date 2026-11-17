"""Central registry and dynamic plugin discovery for ATS providers."""

import sys
import importlib.util
from pathlib import Path
from typing import Dict, List, Optional, Type
from .base import BaseATSProvider
from ..config import get_plugins_dir


class ATSProviderRegistry:
    """Central registry and dispatcher for ATS API providers and job board integrations.
    
    Supports built-in platforms, drop-in user scripts from ~/.config/resume-forge/plugins/,
    and external packages declared via entry points.
    """

    _providers: Dict[str, Type[BaseATSProvider]] = {}
    _aliases: Dict[str, str] = {}
    _plugins_loaded: bool = False

    @classmethod
    def register(cls, name: str, provider_cls: Type[BaseATSProvider], aliases: Optional[List[str]] = None) -> None:
        """Registers an ATS provider class under a canonical name and optional aliases."""
        key = name.lower().strip()
        cls._providers[key] = provider_cls
        if aliases:
            for a in aliases:
                cls._aliases[a.lower().strip()] = key

    @classmethod
    def get(cls, name: str) -> Optional[Type[BaseATSProvider]]:
        """Retrieves an ATS provider class by canonical name or alias."""
        cls._ensure_plugins_discovered()
        key = name.lower().strip()
        canon = cls._aliases.get(key, key)
        return cls._providers.get(canon)

    @classmethod
    def list_providers(cls) -> List[str]:
        """Returns all registered canonical provider names."""
        cls._ensure_plugins_discovered()
        return list(cls._providers.keys())

    @classmethod
    def is_registered(cls, name: str) -> bool:
        """Checks if a provider name or alias is registered."""
        cls._ensure_plugins_discovered()
        key = name.lower().strip()
        return key in cls._providers or key in cls._aliases

    @classmethod
    def _ensure_plugins_discovered(cls) -> None:
        """Lazy-discovers plugins from ~/.config/resume-forge/plugins/ and entry points."""
        if cls._plugins_loaded:
            return
        cls._plugins_loaded = True
        cls._discover_file_plugins()
        cls._discover_entry_point_plugins()

    @classmethod
    def _discover_file_plugins(cls) -> None:
        """Loads custom scrapers dropped into the user plugins directory."""
        plugins_dir = get_plugins_dir()
        if not plugins_dir.is_dir():
            return

        for p in plugins_dir.glob("*.py"):
            if p.name.startswith("_") or p.name == "setup.py":
                continue
            try:
                mod_name = f"resume_forge_plugin_{p.stem}"
                spec = importlib.util.spec_from_file_location(mod_name, p)
                if spec and spec.loader:
                    mod = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(mod)
                    # Inspect module for BaseATSProvider subclasses
                    for attr_name in dir(mod):
                        attr = getattr(mod, attr_name)
                        if (isinstance(attr, type) and
                                issubclass(attr, BaseATSProvider) and
                                attr is not BaseATSProvider):
                            prov_name = getattr(attr, "name", p.stem).lower()
                            cls.register(prov_name, attr)
            except Exception:
                pass

    @classmethod
    def _discover_entry_point_plugins(cls) -> None:
        """Loads third-party ATS plugins registered through setuptools entry-points."""
        try:
            if sys.version_info >= (3, 10):
                from importlib.metadata import entry_points
                eps = entry_points(group="resume_forge.providers")
            else:
                import pkg_resources
                eps = pkg_resources.iter_entry_points("resume_forge.providers")

            for ep in eps:
                try:
                    prov_cls = ep.load()
                    if (isinstance(prov_cls, type) and
                            issubclass(prov_cls, BaseATSProvider) and
                            prov_cls is not BaseATSProvider):
                        cls.register(ep.name.lower(), prov_cls)
                except Exception:
                    pass
        except Exception:
            pass
