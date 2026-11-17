"""Unit tests for ResumeForge configuration and path resolution."""

import unittest
import os
import sys
from pathlib import Path
from unittest.mock import patch

from resume_forge.config import (
    get_config_dir,
    get_preferences_path,
    get_plugins_dir,
    get_default_output_dir,
)


class TestConfig(unittest.TestCase):
    """Tests for platform-aware path resolution and user decoupling."""

    def test_get_config_dir_xdg(self):
        with patch.dict(os.environ, {"XDG_CONFIG_HOME": "/tmp/custom_xdg"}):
            with patch("sys.platform", "linux"):
                cfg = get_config_dir()
                self.assertEqual(cfg, Path("/tmp/custom_xdg/resume-forge"))

    def test_get_config_dir_unix_fallback(self):
        env = dict(os.environ)
        env.pop("XDG_CONFIG_HOME", None)
        with patch.dict(os.environ, env, clear=True):
            with patch("sys.platform", "darwin"):
                cfg = get_config_dir()
                self.assertEqual(cfg, Path.home() / ".config" / "resume-forge")

    def test_get_config_dir_windows(self):
        win_appdata = "C:\\Users\\TestUser\\AppData\\Roaming"
        with patch.dict(os.environ, {"APPDATA": win_appdata}):
            with patch("sys.platform", "win32"):
                cfg = get_config_dir()
                self.assertEqual(cfg, Path(win_appdata) / "resume-forge")

    def test_get_preferences_path(self):
        local_p = get_preferences_path(local=True)
        self.assertEqual(local_p, Path("preferences.json"))

        global_p = get_preferences_path(local=False)
        self.assertEqual(global_p, get_config_dir() / "preferences.json")

    def test_get_plugins_dir(self):
        p_dir = get_plugins_dir()
        self.assertEqual(p_dir, get_config_dir() / "plugins")

    def test_get_default_output_dir(self):
        out_dir = get_default_output_dir()
        self.assertTrue(out_dir.exists())
        self.assertTrue(out_dir.is_dir())


if __name__ == "__main__":
    unittest.main()
