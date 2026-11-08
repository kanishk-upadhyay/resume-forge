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

    def test_cli_nonexistent_file_handling(self):
        with patch.object(sys, 'argv', ["resume-forge", "parse", "nonexistent_file_12345.tex"]):
            with patch('sys.stderr', new=StringIO()):
                with self.assertRaises(SystemExit) as cm:
                    main()
                self.assertEqual(cm.exception.code, 1)


if __name__ == "__main__":
    unittest.main()
