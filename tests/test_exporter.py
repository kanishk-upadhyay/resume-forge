"""Unit tests for ResumeExporter."""

import unittest
from pathlib import Path
from resume_forge.core.parser import LatexResumeParser
from resume_forge.core.exporter import ResumeExporter


class TestResumeExporter(unittest.TestCase):

    def setUp(self):
        sample_path = Path(__file__).parent.parent / "examples" / "kanishk_cern_fullstack_resume.tex"
        parser = LatexResumeParser(sample_path.read_text(encoding="utf-8"))
        self.data = parser.parse()
        self.exporter = ResumeExporter(self.data)

    def test_to_latex(self):
        tex = self.exporter.to_latex()
        self.assertIn(r"\begin{document}", tex)
        self.assertIn("Kanishk", tex)
        self.assertIn(r"\section{Experience}", tex)
        self.assertIn(r"\section{Education}", tex)
        self.assertIn(r"\end{document}", tex)

    def test_to_html(self):
        html = self.exporter.to_html()
        self.assertIn("<!DOCTYPE html>", html)
        self.assertIn("Latin Modern Roman", html)
        self.assertIn("Kanishk", html)
        self.assertIn("OZ Media", html)

    def test_to_markdown(self):
        md = self.exporter.to_markdown()
        self.assertIn("# Kanishk", md)
        self.assertIn("## Work Experience", md)
        self.assertIn("## Technical Skills", md)


if __name__ == "__main__":
    unittest.main()
