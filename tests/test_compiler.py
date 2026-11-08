"""Unit tests for ResumeCompiler (in-house single-page PDF compilation)."""

import unittest
import tempfile
from pathlib import Path
from resume_forge.core.parser import LatexResumeParser
from resume_forge.core.compiler import ResumeCompiler


class TestResumeCompiler(unittest.TestCase):

    def setUp(self):
        sample_path = Path(__file__).parent.parent / "examples" / "kanishk_cern_fullstack_resume.tex"
        parser = LatexResumeParser(sample_path.read_text(encoding="utf-8"))
        self.data = parser.parse()
        self.compiler = ResumeCompiler()

    def test_chrome_detection(self):
        self.assertIsNotNone(self.compiler.chrome_bin, "Google Chrome should be detected on macOS.")

    def test_compile_resume_to_pdf(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            out_pdf = Path(tmpdir) / "test_resume.pdf"
            success = self.compiler.compile_resume(
                data=self.data,
                output_pdf_path=str(out_pdf),
                font_size_pt=10.0,
                line_height=1.25,
                margin_in=0.4
            )
            self.assertTrue(success, "Compilation should succeed via in-house Chrome engine.")
            self.assertTrue(out_pdf.exists(), "Output PDF must exist.")
            self.assertGreater(out_pdf.stat().st_size, 1000, "PDF must not be empty.")


if __name__ == "__main__":
    unittest.main()
