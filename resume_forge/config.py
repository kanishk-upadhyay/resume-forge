"""User configuration, platform directory resolution, and path decoupling for ResumeForge.

Provides standard XDG paths on Linux/macOS (~/.config/resume-forge/) and
%APPDATA%/resume-forge/ on Windows, decoupling all personal directories.
"""

import os
import sys
from pathlib import Path
from typing import Optional


def get_config_dir() -> Path:
    """Returns the platform-specific user configuration directory.
    
    - Windows: %APPDATA%/resume-forge (or ~/.config/resume-forge fallback)
    - macOS/Linux: $XDG_CONFIG_HOME/resume-forge or ~/.config/resume-forge
    """
    if sys.platform == "win32":
        appdata = os.environ.get("APPDATA")
        if appdata:
            base = Path(appdata)
        else:
            base = Path.home() / "AppData" / "Roaming"
    else:
        xdg_config = os.environ.get("XDG_CONFIG_HOME")
        if xdg_config:
            base = Path(xdg_config)
        else:
            base = Path.home() / ".config"

    config_dir = base / "resume-forge"
    return config_dir


def get_preferences_path(local: bool = False) -> Path:
    """Returns the default preferences JSON path (local project or user-global)."""
    if local:
        return Path("preferences.json")
    return get_config_dir() / "preferences.json"


def get_plugins_dir() -> Path:
    """Returns the user plugins directory for external scraper drops."""
    return get_config_dir() / "plugins"


def get_default_output_dir() -> Path:
    """Returns a safe, writable output directory for compiled resumes and hunt reports."""
    # If the local directory has an output directory or is writable, use ./output
    try:
        local_out = Path("output")
        local_out.mkdir(parents=True, exist_ok=True)
        test_file = local_out / ".write_test"
        test_file.touch()
        test_file.unlink()
        return local_out
    except Exception:
        # Fall back to user configuration directory
        fallback = get_config_dir() / "output"
        fallback.mkdir(parents=True, exist_ok=True)
        return fallback
