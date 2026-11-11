"""Unit tests for CoverLetterData, template renderers, and single-page compilation."""

import unittest
import tempfile
from pathlib import Path

from resume_forge.core.parser import LatexResumeParser
from resume_forge.core.schema import ResumeData
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

    def test_empty_highlights_safe_synthesis(self):
        """Verify resumes with empty or whitespace-only bullets do not trigger IndexError."""
        resume_sparse = LatexResumeParser(Path(__file__).parent.parent / "examples" / "kanishk_cern_fullstack_resume.tex").parse()
        for w in resume_sparse.work:
            w.highlights = ["", "   "]
        for p in resume_sparse.projects:
            p.highlights = ["", "\t\n"]
        for o in resume_sparse.open_source:
            o.highlights = [""]

        letter = CoverLetterData.from_resume(resume_sparse, company="DeepMind", role="Research Engineer")
        self.assertIn("DeepMind", letter.opening)
        self.assertIn("Research Engineer", letter.opening)
        self.assertGreater(len(letter.body_paragraphs), 0)

    def test_latex_macro_stripping_in_cover_letter(self):
        """Verify LaTeX tags are cleaned from candidate highlights in synthesized letter."""
        resume_latex = LatexResumeParser(Path(__file__).parent.parent / "examples" / "kanishk_cern_fullstack_resume.tex").parse()
        resume_latex.work[0].highlights = [r"\textbf{Engineered} a high-performance \href{https://cern.ch}{C++ engine} with 99\% uptime."]
        letter = CoverLetterData.from_resume(resume_latex, company="Apple", role="Systems Architect")
        full_text = " ".join(letter.body_paragraphs)
        self.assertNotIn(r"\textbf", full_text)
        self.assertNotIn(r"\href", full_text)
        self.assertIn("engineered a high-performance c++ engine with 99% uptime", full_text.lower())

    def test_latex_cover_letter_parser(self):
        """Verify parsing raw LaTeX cover letters into CoverLetterData."""
        from resume_forge.core.letter import LatexCoverLetterParser
        raw_tex = r"""
\documentclass[11pt,a4paper]{article}
\begin{document}
{\LARGE \textbf{Alex Morgan}} \\
Email: alex@example.com | Phone: +1 555-0123

\today

\textbf{Hiring Manager} \\
Acme Corp \\
San Francisco, CA

\textbf{Dear Hiring Manager,}

I am writing to express my strong interest in the Senior Platform Engineer role at Acme Corp.

Over the past 6 years, I built fault-tolerant distributed infrastructure handling 50k QPS. At my previous company, I spearheaded the migration to Kubernetes, decreasing cloud expenditure by 32%.

I admire Acme's dedication to open-source reliability tooling and would love to contribute to your core systems team.

Thank you for your time and consideration.

Sincerely, \\
Alex Morgan
\end{document}
"""
        parser = LatexCoverLetterParser(raw_tex)
        data = parser.parse()
        self.assertEqual(data.sender.name, "Alex Morgan")
        self.assertEqual(data.sender.email, "alex@example.com")
        self.assertEqual(data.sender.phone, "+1 555-0123")
        self.assertEqual(data.salutation, "Dear Hiring Manager,")
        self.assertIn("Senior Platform Engineer role at Acme Corp", data.opening)
        self.assertIn("Over the past 6 years", " ".join(data.body_paragraphs))
        self.assertEqual(data.sign_off, "Sincerely,")

    def test_empty_resume_cover_letter_synthesis(self):
        """Verify cover letter generation never crashes on an empty ResumeData object."""
        empty_resume = ResumeData()
        letter = CoverLetterData.from_resume(empty_resume, company="DeepMind", role="Research Scientist")
        self.assertEqual(letter.sender.name, "Candidate")
        self.assertIn("DeepMind", letter.opening)
        self.assertIn("Research Scientist", letter.opening)
        self.assertGreater(len(letter.body_paragraphs), 0)
        self.assertIn("DeepMind", letter.closing)

    def test_empty_latex_cover_letter_parser(self):
        """Verify parsing empty or malformed LaTeX returns safe defaults without exception."""
        from resume_forge.core.letter import LatexCoverLetterParser
        data = LatexCoverLetterParser("").parse()
        self.assertEqual(data.sender.name, "Candidate")
        self.assertEqual(data.salutation, "Dear Hiring Team,")
        self.assertEqual(data.sign_off, "Sincerely,")
        self.assertGreater(len(data.opening), 0)
        self.assertGreater(len(data.closing), 0)


if __name__ == "__main__":
    unittest.main()
