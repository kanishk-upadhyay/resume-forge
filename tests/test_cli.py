"""Unit tests for the ResumeForge CLI commands."""

import unittest
import tempfile
import sys
import os
import json
from pathlib import Path
from io import StringIO
from unittest.mock import patch

from resume_forge.cli import main


class TestCLI(unittest.TestCase):

    def setUp(self):
        self.tex_file = str(Path(__file__).parent.parent / "examples" / "kanishk_cern_fullstack_resume.tex")

    def test_cli_parse_stdout(self):
        with patch.object(sys, 'argv', ["resume-forge", "parse", self.tex_file]):
            with patch('sys.stdout', new=StringIO()) as fake_out:
                main()
                output = fake_out.getvalue()
                self.assertIn('"name": "Kanishk Upadhyay"', output)
                self.assertIn('"email":', output)
                self.assertIn(".com", output)

    def test_cli_parse_file_output(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            out_json = Path(tmpdir) / "output.json"
            with patch.object(sys, 'argv', ["resume-forge", "parse", self.tex_file, "-o", str(out_json)]):
                with patch('sys.stdout', new=StringIO()):
                    main()
            self.assertTrue(out_json.exists())
            content = out_json.read_text(encoding="utf-8")
            self.assertIn("Kanishk", content)

    def test_cli_export_formats(self):
        for fmt in ["md", "html", "tex"]:
            with patch.object(sys, 'argv', ["resume-forge", "export", self.tex_file, "-f", fmt]):
                with patch('sys.stdout', new=StringIO()) as fake_out:
                    main()
                    out = fake_out.getvalue()
                    self.assertGreater(len(out), 100)
                    if fmt == "md":
                        self.assertIn("# Kanishk", out)
                    elif fmt == "html":
                        self.assertIn("<!DOCTYPE html>", out)
                    elif fmt == "tex":
                        self.assertIn(r"\begin{document}", out)

    def test_cli_audit(self):
        with patch.object(sys, 'argv', ["resume-forge", "audit", self.tex_file, "--jd", "Python and C developer"]):
            with patch('sys.stdout', new=StringIO()) as fake_out:
                main()
                output = fake_out.getvalue()
                self.assertIn("ATS Health Score", output)
                self.assertIn("Optimal (Single Page)", output)

    def test_cli_compile_pdf(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            out_pdf = Path(tmpdir) / "cli_test.pdf"
            with patch.object(sys, 'argv', ["resume-forge", "compile", self.tex_file, "-o", str(out_pdf)]):
                with patch('sys.stdout', new=StringIO()):
                    main()
            self.assertTrue(out_pdf.exists())
            self.assertGreater(out_pdf.stat().st_size, 1000)

    def test_cli_template_commands(self):
        # template list
        with patch.object(sys, 'argv', ["resume-forge", "template", "list"]):
            with patch('sys.stdout', new=StringIO()) as fake_out:
                main()
                out = fake_out.getvalue()
                self.assertIn("harvard", out)
                self.assertIn("jakes", out)
                self.assertIn("minimalist", out)
                self.assertIn("quant", out)
                self.assertIn("awesome", out)
                self.assertIn("academic", out)

        # template info
        with patch.object(sys, 'argv', ["resume-forge", "template", "info", "harvard"]):
            with patch('sys.stdout', new=StringIO()) as fake_out:
                main()
                out = fake_out.getvalue()
                self.assertIn("Harvard Classic", out)
                self.assertIn("Ivy League", out)

        # export with template
        with patch.object(sys, 'argv', ["resume-forge", "export", self.tex_file, "-f", "tex", "-t", "harvard"]):
            with patch('sys.stdout', new=StringIO()) as fake_out:
                main()
                out = fake_out.getvalue()
                self.assertIn("KANISHK UPADHYAY", out)

    def test_cli_diff_command(self):
        json_file = str(Path(__file__).parent.parent / "examples" / "resume.json")
        with patch.object(sys, 'argv', ["resume-forge", "diff", self.tex_file, json_file, "--no-color"]):
            with patch('sys.stdout', new=StringIO()) as fake_out:
                main()
                out = fake_out.getvalue()
                self.assertIn("STRUCTURAL AST COMPARISON", out)
                self.assertIn("ATS Score Delta", out)

        # Diff JSON output format
        with patch.object(sys, 'argv', ["resume-forge", "diff", self.tex_file, json_file, "--json"]):
            with patch('sys.stdout', new=StringIO()) as fake_out:
                main()
                out = fake_out.getvalue()
                self.assertIn('"score_delta"', out)
                self.assertIn('"basics_changed"', out)

    def test_cli_letter_command(self):
        with patch.object(sys, 'argv', ["resume-forge", "letter", "create", self.tex_file, "-c", "Google", "-r", "Staff Engineer", "-t", "harvard"]):
            with patch('sys.stdout', new=StringIO()) as fake_out:
                main()
                out = fake_out.getvalue()
                self.assertIn("Google", out)
                self.assertIn("Staff Engineer", out)

        # Letter compile from .tex
        with tempfile.TemporaryDirectory() as tmpdir:
            letter_tex = Path(tmpdir) / "custom_letter.tex"
            letter_tex.write_text(r"""
\documentclass{article}
\begin{document}
{\Large \textbf{Grace Hopper}} \\
grace@navy.mil
\today
\textbf{Dear Admiral,}
I am writing to report on compiler optimization achievements.
Sincerely, \\ Grace Hopper
\end{document}
""", encoding="utf-8")
            out_pdf = Path(tmpdir) / "letter.pdf"
            with patch.object(sys, 'argv', ["resume-forge", "letter", "compile", str(letter_tex), "-o", str(out_pdf), "-t", "harvard"]):
                with patch('sys.stdout', new=StringIO()):
                    main()
            self.assertTrue(out_pdf.exists())
            self.assertGreater(out_pdf.stat().st_size, 1000)

    def test_cli_audit_with_live_jd_url(self):
        html_page = """<html><body><div><h1>Staff Distributed Systems Engineer</h1>
        <p>Requirements: 5+ years with C++, Rust, Raft, Paxos, distributed consensus.</p></div></body></html>"""
        from unittest.mock import MagicMock
        mock_resp = MagicMock()
        mock_resp.read.return_value = html_page.encode("utf-8")
        mock_resp.__enter__.return_value = mock_resp

        with patch("resume_forge.core.fetcher.urllib.request.urlopen", return_value=mock_resp):
            with patch.object(sys, 'argv', ["resume-forge", "audit", self.tex_file, "--jd-url", "https://jobs.example.com/staff-systems"]):
                with patch('sys.stdout', new=StringIO()) as fake_out:
                    main()
                    out = fake_out.getvalue()
                    self.assertIn("ATS Health Score", out)

    def test_cli_completion_command(self):
        for shell in ["bash", "zsh", "fish"]:
            with patch.object(sys, 'argv', ["resume-forge", "completion", shell]):
                with patch('sys.stdout', new=StringIO()) as fake_out:
                    main()
                    out = fake_out.getvalue()
                    self.assertIn("resume-forge", out)
                    self.assertIn("harvard", out)

    def test_cli_compile_image(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            out_png = Path(tmpdir) / "resume_img.png"
            with patch.object(sys, 'argv', ["resume-forge", "compile", self.tex_file, "-f", "png", "--dpi", "150", "-o", str(out_png)]):
                with patch('sys.stdout', new=StringIO()):
                    main()
            self.assertTrue(out_png.exists())
            self.assertGreater(out_png.stat().st_size, 5000)

    def test_cli_compile_all_templates(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.object(sys, 'argv', ["resume-forge", "compile", self.tex_file, "--all-templates", "-o", tmpdir]):
                with patch('sys.stdout', new=StringIO()):
                    main()
            compiled_files = list(Path(tmpdir).glob("*.pdf"))
            self.assertEqual(len(compiled_files), 7, f"Expected 7 template PDFs, got {compiled_files}")


    def test_cli_nonexistent_file_handling(self):
        with patch.object(sys, 'argv', ["resume-forge", "parse", "nonexistent_file_12345.tex"]):
            with patch('sys.stderr', new=StringIO()):
                with self.assertRaises(SystemExit) as cm:
                    main()
                self.assertEqual(cm.exception.code, 1)

    def test_cli_hunt_save_and_load_profile(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            profile_path = Path(tmpdir) / "profile.json"
            # 1. Save profile
            with patch.object(sys, 'argv', [
                "resume-forge", "hunt",
                "--save-profile", str(profile_path),
                "-r", "Backend Engineer",
                "-l", "Remote,US",
                "-s", "senior",
                "--min-exp", "5",
                "--max-exp", "10",
                "--exclude-titles", "manager,director",
                "--require-keywords", "python,fastapi"
            ]):
                with patch('sys.stdout', new=StringIO()) as fake_out:
                    main()
                    out = fake_out.getvalue()
                    self.assertIn("Saved hunter profile preferences", out)
            self.assertTrue(profile_path.exists())
            saved_data = json.loads(profile_path.read_text(encoding="utf-8"))
            self.assertEqual(saved_data["seniority"], "senior")
            self.assertEqual(saved_data["min_experience_years"], 5)
            self.assertIn("manager", saved_data["exclude_titles"])
            self.assertIn("python", saved_data["require_keywords"])

            # 2. Run hunt using saved profile
            from unittest.mock import MagicMock
            mock_resp = MagicMock()
            mock_resp.read.return_value = json.dumps({"jobs": []}).encode("utf-8")
            with patch("urllib.request.urlopen", return_value=mock_resp):
                with patch.object(sys, 'argv', [
                    "resume-forge", "hunt",
                    "--profile", str(profile_path),
                    "-p", "amazon",
                    "--json"
                ]):
                    with patch('sys.stdout', new=StringIO()) as fake_out:
                        main()
                        out = fake_out.getvalue()
                        self.assertEqual(json.loads(out), [])

    def test_cli_init_non_interactive_tex(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            out_tex = Path(tmpdir) / "my_resume.tex"
            profile_json = Path(tmpdir) / "custom_pref.json"
            with patch.object(sys, 'argv', [
                "resume-forge", "init",
                "--non-interactive",
                "--name", "Ada Lovelace",
                "--email", "ada@example.com",
                "--role", "Systems Engineer",
                "--location", "London, UK",
                "--seniority", "entry",
                "-t", "cern",
                "-o", str(out_tex),
                "-p", str(profile_json)
            ]):
                with patch('sys.stdout', new=StringIO()) as fake_out:
                    main()
                    out = fake_out.getvalue()
                    self.assertIn("SETUP COMPLETE", out)

            self.assertTrue(out_tex.exists())
            content = out_tex.read_text(encoding="utf-8")
            self.assertIn("Ada Lovelace", content)
            self.assertIn(r"\begin{document}", content)

            self.assertTrue(profile_json.exists())
            p_data = json.loads(profile_json.read_text(encoding="utf-8"))
            self.assertIn("Systems Engineer", p_data["roles"])
            self.assertEqual(p_data["seniority"], "entry")
            self.assertEqual(p_data["base_resume_path"], str(out_tex))

    def test_cli_init_non_interactive_json(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            out_json = Path(tmpdir) / "my_resume.json"
            profile_json = Path(tmpdir) / "pref.json"
            with patch.object(sys, 'argv', [
                "resume-forge", "init",
                "--non-interactive",
                "--name", "Grace Hopper",
                "-f", "json",
                "-t", "harvard",
                "-o", str(out_json),
                "-p", str(profile_json)
            ]):
                with patch('sys.stdout', new=StringIO()) as fake_out:
                    main()
                    out = fake_out.getvalue()
                    self.assertIn("SETUP COMPLETE", out)

            self.assertTrue(out_json.exists())
            data = json.loads(out_json.read_text(encoding="utf-8"))
            self.assertEqual(data["basics"]["name"], "Grace Hopper")

    def test_cli_init_existing_resume_kept(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            out_tex = Path(tmpdir) / "existing.tex"
            out_tex.write_text("% MY CUSTOM PRE-EXISTING RESUME", encoding="utf-8")
            profile_json = Path(tmpdir) / "pref.json"
            with patch.object(sys, 'argv', [
                "resume-forge", "init",
                "--non-interactive",
                "-o", str(out_tex),
                "-p", str(profile_json)
            ]):
                with patch('sys.stdout', new=StringIO()) as fake_out:
                    main()
                    out = fake_out.getvalue()
                    self.assertIn("already exists", out)

            # Ensure pre-existing content was NOT overwritten
            self.assertEqual(out_tex.read_text(encoding="utf-8"), "% MY CUSTOM PRE-EXISTING RESUME")

    def test_cli_init_force_overwrite(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            out_tex = Path(tmpdir) / "existing.tex"
            out_tex.write_text("% PRE-EXISTING", encoding="utf-8")
            profile_json = Path(tmpdir) / "pref.json"
            with patch.object(sys, 'argv', [
                "resume-forge", "init",
                "--non-interactive",
                "--force",
                "--name", "Linus Torvalds",
                "-o", str(out_tex),
                "-p", str(profile_json)
            ]):
                with patch('sys.stdout', new=StringIO()):
                    main()

            # Ensure pre-existing content WAS overwritten
            self.assertIn("Linus Torvalds", out_tex.read_text(encoding="utf-8"))

    def test_cli_init_local_flag(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cwd = Path.cwd()
            try:
                os.chdir(tmpdir)
                out_tex = Path("my_res.tex")
                with patch.object(sys, 'argv', [
                    "resume-forge", "init",
                    "--non-interactive",
                    "--local",
                    "-o", str(out_tex)
                ]):
                    with patch('sys.stdout', new=StringIO()):
                        main()
                local_pref = Path("preferences.json")
                self.assertTrue(local_pref.exists())
                p_data = json.loads(local_pref.read_text(encoding="utf-8"))
                self.assertEqual(p_data["base_resume_path"], "my_res.tex")
            finally:
                os.chdir(cwd)

    def test_cli_init_interactive_wizard(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            out_tex = Path(tmpdir) / "wizard.tex"
            profile_json = Path(tmpdir) / "wizard_pref.json"
            inputs = [
                "Barbara Liskov",       # Full Name
                "barbara@example.com",  # Email
                "Distributed Systems",  # Role
                "Boston, MA",           # Location
                "senior",               # Seniority
                "quant",                # Template
                "tex"                   # Format
            ]
            with patch("sys.stdin.isatty", return_value=True):
                with patch("builtins.input", side_effect=inputs):
                    with patch.object(sys, 'argv', [
                        "resume-forge", "init",
                        "-o", str(out_tex),
                        "-p", str(profile_json)
                    ]):
                        with patch('sys.stdout', new=StringIO()) as fake_out:
                            main()
                            out = fake_out.getvalue()
                            self.assertIn("RESUME FORGE INITIALIZATION WIZARD", out)
                            self.assertIn("SETUP COMPLETE", out)

            self.assertTrue(out_tex.exists())
            content = out_tex.read_text(encoding="utf-8")
            self.assertIn("BARBARA LISKOV", content)
            self.assertIn("barbara@example.com", content)
            p_data = json.loads(profile_json.read_text(encoding="utf-8"))
            self.assertIn("Distributed Systems", p_data["roles"])
            self.assertEqual(p_data["seniority"], "senior")

    def test_cli_init_interactive_cancelled(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            out_tex = Path(tmpdir) / "wizard.tex"
            with patch("sys.stdin.isatty", return_value=True):
                with patch("builtins.input", side_effect=KeyboardInterrupt):
                    with patch.object(sys, 'argv', ["resume-forge", "init", "-o", str(out_tex)]):
                        with patch('sys.stdout', new=StringIO()) as fake_out:
                            with self.assertRaises(SystemExit) as cm:
                                main()
                            self.assertEqual(cm.exception.code, 0)
                            self.assertIn("cancelled", fake_out.getvalue())
            self.assertFalse(out_tex.exists())




if __name__ == "__main__":
    unittest.main()
