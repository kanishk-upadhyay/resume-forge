"""Unit tests for CoverLetterData, template renderers, and single-page compilation."""

import unittest
import tempfile
from pathlib import Path

from resume_forge.core.parser import LatexResumeParser
from resume_forge.core.letter import CoverLetterData, CoverLetterRecipient
from resume_forge.core.compiler import ResumeCompiler
from resume_forge.templates import TemplateRegistry


class TestCoverLetter(unittest.TestCase):

    def setUp(self):
        sample_path = Path(__file__).parent.parent / "examples" / "kanishk_cern_fullstack_resume.tex"
        self.resume = LatexResumeParser(sample_path.read_text(encoding="utf-8")).parse()
        self.compiler = ResumeCompiler()

    def test_cover_letter_synthesis(self):
        letter = CoverLetterData.from_resume(
            self.resume,
            company="Jane Street",
            role="Quant Developer",
            recipient_name="Quant Hiring Team"
        )
        self.assertEqual(letter.sender.name, "Kanishk Upadhyay")
        self.assertEqual(letter.recipient.company, "Jane Street")
        self.assertEqual(letter.job_title, "Quant Developer")
        self.assertIn("Jane Street", letter.opening)
        self.assertIn("Quant Developer", letter.opening)
        self.assertGreater(len(letter.body_paragraphs), 0)
        self.assertIn("Jane Street", letter.closing)

    def test_serialization_roundtrip(self):
        letter = CoverLetterData.from_resume(self.resume, company="Stripe", role="Backend Engineer")
        d = letter.to_dict()
        reconstructed = CoverLetterData.from_dict(d)
        self.assertEqual(reconstructed.sender.name, letter.sender.name)
        self.assertEqual(reconstructed.recipient.company, "Stripe")
        self.assertEqual(len(reconstructed.body_paragraphs), len(letter.body_paragraphs))

        json_str = letter.to_json()
        reconstructed_json = CoverLetterData.from_json(json_str)
        self.assertEqual(reconstructed_json.sender.email, letter.sender.email)

    def test_latex_rendering_across_all_templates(self):
        letter = CoverLetterData.from_resume(self.resume, company="Google", role="Staff Engineer")
        for tmpl_meta in TemplateRegistry.list_templates():
            tmpl = TemplateRegistry.get(tmpl_meta["name"])
            tex = tmpl.render_cover_letter_latex(letter)
            self.assertIn(r"\begin{document}", tex, f"Template {tmpl.name} must produce valid LaTeX.")
            self.assertIn(r"\end{document}", tex)
            self.assertIn("Kanishk Upadhyay", tex)
            self.assertIn("Google", tex)

    def test_html_rendering_across_all_templates(self):
        letter = CoverLetterData.from_resume(self.resume, company="CERN", role="Fellow")
        for tmpl_meta in TemplateRegistry.list_templates():
            tmpl = TemplateRegistry.get(tmpl_meta["name"])
            html = tmpl.render_cover_letter_html(letter)
            self.assertIn("<!DOCTYPE html>", html)
            self.assertIn("Kanishk Upadhyay", html)
            self.assertIn("CERN", html)

    def test_single_page_pdf_compilation(self):
        letter = CoverLetterData.from_resume(self.resume, company="Citadel", role="Low Latency C++")
        with tempfile.TemporaryDirectory() as tmpdir:
            out_pdf = Path(tmpdir) / "citadel_letter.pdf"
            success = self.compiler.compile_cover_letter(letter, str(out_pdf), template="quant")
            self.assertTrue(success, "Cover letter PDF compilation must succeed.")
            self.assertTrue(out_pdf.exists())
            self.assertEqual(ResumeCompiler.get_pdf_page_count(str(out_pdf)), 1, "Cover letter must strictly be 1 page.")


if __name__ == "__main__":
    unittest.main()
