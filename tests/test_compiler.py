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

    def test_auto_fit_compression_for_overflowing_resume(self):
        """Verify overflowing multi-page content is squeezed into a strict 1-page PDF when auto_fit=True."""
        from resume_forge.core.schema import WorkItem, EducationItem, SkillItem, Basics, ResumeData
        work_items = [
            WorkItem(
                name=f"Enterprise Corp {i}",
                position="Staff Engineer",
                start_date="2020",
                end_date="2024",
                highlights=[f"Bullet {j} demonstrating architectural optimizations and scale across distributed nodes with Kubernetes." for j in range(3)]
            )
            for i in range(10)
        ]
        overflow_data = ResumeData(
            basics=Basics(name="Scale Engineer", email="eng@example.com", phone="1234567890"),
            education=[EducationItem(institution="MIT", study_type="B.S. CS", start_date="2016", end_date="2020")],
            work=work_items,
            skills=[SkillItem(name="Langs", keywords=["Go", "Python", "C++"])]
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            no_fit_pdf = Path(tmpdir) / "no_fit.pdf"
            fit_pdf = Path(tmpdir) / "with_fit.pdf"

            self.compiler.compile_resume(overflow_data, str(no_fit_pdf), auto_fit=False)
            self.compiler.compile_resume(overflow_data, str(fit_pdf), auto_fit=True)

            pages_no_fit = self.compiler.get_pdf_page_count(str(no_fit_pdf))
            pages_fit = self.compiler.get_pdf_page_count(str(fit_pdf))

            self.assertGreater(pages_no_fit, 1, "Without auto-fit, 10 jobs should spill onto page 2.")
            self.assertEqual(pages_fit, 1, "With auto-fit, content must be squeezed onto exactly 1 page.")

    def test_concurrent_compilation_profile_isolation(self):
        """Verifies multiple threads can compile simultaneously without Chrome SingletonLock collisions."""
        from concurrent.futures import ThreadPoolExecutor

        def _compile_task(idx):
            with tempfile.TemporaryDirectory() as tmpdir:
                out_pdf = Path(tmpdir) / f"thread_{idx}.pdf"
                ok = self.compiler.compile_resume(
                    data=self.data,
                    output_pdf_path=str(out_pdf),
                    font_size_pt=10.0,
                    margin_in=0.4
                )
                return ok and out_pdf.exists() and out_pdf.stat().st_size > 1000

        with ThreadPoolExecutor(max_workers=3) as pool:
            results = list(pool.map(_compile_task, range(3)))

        self.assertTrue(all(results), f"All concurrent jobs should succeed, got {results}")

    def test_compile_high_dpi_image(self):
        """Verify image compilation creates high-resolution PNG image."""
        with tempfile.TemporaryDirectory() as tmpdir:
            out_png = Path(tmpdir) / "test_screenshot.png"
            success = self.compiler.compile_image(
                data=self.data,
                output_image_path=str(out_png),
                template="minimalist",
                dpi=150
            )
            self.assertTrue(success, "Image compilation should succeed.")
            self.assertTrue(out_png.exists(), "PNG image must exist.")
            self.assertGreater(out_png.stat().st_size, 10000, "PNG image must not be empty.")

    def test_compile_all_templates_method(self):
        """Verify batch compilation generates PDFs for all registered templates."""
        with tempfile.TemporaryDirectory() as tmpdir:
            generated = self.compiler.compile_all_templates(
                data=self.data,
                output_dir=tmpdir,
                prefix="batch_test"
            )
            self.assertEqual(len(generated), 7, f"Expected 7 generated files, got {len(generated)}")
            for path in generated.values():
                p = Path(path)
                self.assertTrue(p.exists())
                self.assertGreater(p.stat().st_size, 1000)
                self.assertEqual(self.compiler.get_pdf_page_count(str(p)), 1)

    def test_compile_cover_letter_single_page_guarantee(self):
        """Verify cover letters compile to strict 1-page PDF across multiple templates."""
        from resume_forge.core.letter import CoverLetterData
        letter = CoverLetterData.from_resume(self.data, company="Anthropic", role="Alignment Researcher")
        with tempfile.TemporaryDirectory() as tmpdir:
            for tmpl in ["harvard", "jakes", "quant"]:
                pdf_path = Path(tmpdir) / f"{tmpl}_letter.pdf"
                ok = self.compiler.compile_cover_letter(letter, str(pdf_path), template=tmpl)
                self.assertTrue(ok)
                self.assertTrue(pdf_path.exists())
                self.assertEqual(self.compiler.get_pdf_page_count(str(pdf_path)), 1)


if __name__ == "__main__":
    unittest.main()
