"""Unit tests for the ResumeForge CLI commands."""

import unittest
import tempfile
import sys
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
                self.assertIn('"email": "kanishkupadhyay22@gmail.com"', output)

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


if __name__ == "__main__":
    unittest.main()
