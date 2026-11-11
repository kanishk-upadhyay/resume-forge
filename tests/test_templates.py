"""Unit tests for ResumeForge Template Engine and the 7 canonical templates."""

import unittest
import tempfile
from pathlib import Path

from resume_forge.core.schema import (
    ResumeData, Basics, WorkItem, EducationItem, ProjectItem, SkillItem,
    OpenSourceItem, CertificateItem, AwardItem, PublicationItem, LanguageItem,
    Location, Profile
)
from resume_forge.templates import (
    TemplateRegistry, BaseTemplate, CernTemplate, HarvardTemplate,
    JakesTemplate, MinimalistTemplate, QuantTemplate, AwesomeCvTemplate,
    AcademicTemplate
)
from resume_forge.core.compiler import ResumeCompiler
from resume_forge.core.exporter import ResumeExporter


class TestTemplateEngine(unittest.TestCase):
    """Verifies template registry, LaTeX rendering, HTML generation, and PDF compilation."""

    @classmethod
    def setUpClass(cls):
        cls.sample_data = ResumeData(
            basics=Basics(
                name="Kanishk Upadhyay",
                email="kanishkupadhyay22@gmail.com",
                phone="+91 7772034062",
                location=Location(city="Bhopal, India"),
                url="https://kanishk.pages.dev/treasures",
                summary="Systems and backend engineer focused on high-performance C++ and distributed architectures.",
                profiles=[
                    Profile(network="GitHub", url="https://github.com/kanishk-upadhyay"),
                    Profile(network="LinkedIn", url="https://linkedin.com/in/kanishk22")
                ]
            ),
            education=[
                EducationItem(
                    institution="Barkatullah University",
                    study_type="Bachelor of Engineering (B.E.)",
                    area="Computer Science",
                    start_date="2023",
                    end_date="2027",
                    highlights=["First Class with Distinction"]
                )
            ],
            work=[
                WorkItem(
                    name="OZ Media",
                    position="Software Developer Intern",
                    location="Remote",
                    start_date="Jun 2025",
                    end_date="Dec 2025",
                    highlights=[
                        "Benchmarked IPC latency across 16 cores achieving a 3x throughput improvement.",
                        "Architected zero-downtime microservices handling 50k+ requests/sec."
                    ]
                )
            ],
            projects=[
                ProjectItem(
                    name="Yatoro",
                    description="High-throughput C++ asynchronous engine",
                    keywords=["C++20", "FastAPI", "Docker", "Linux"],
                    start_date="2024",
                    highlights=["Eliminated thread contention to deliver O(1) event dispatching."]
                )
            ],
            skills=[
                SkillItem(name="Languages", keywords=["C++20", "Python", "Go", "TypeScript", "SQL"]),
                SkillItem(name="Systems & Infra", keywords=["Linux", "Docker", "GitLab CI", "Prometheus"])
            ],
            certificates=[
                CertificateItem(name="Certified Kubernetes Administrator", issuer="Linux Foundation", date="2025")
            ],
            awards=[
                AwardItem(title="First Prize Hackathon", awarder="ACM Chapter", date="2024")
            ],
            publications=[
                PublicationItem(name="High-Performance Event Dispatching in Userspace C++ (2025)")
            ],
            languages=[
                LanguageItem(language="English", fluency="Native"),
                LanguageItem(language="Hindi", fluency="Fluent")
            ]
        )

    def test_template_registry_listing(self):
        """Verifies that all 7 canonical templates are registered."""
        expected_templates = {"cern", "harvard", "jakes", "minimalist", "quant", "awesome", "academic"}
        registered = set(TemplateRegistry.get_template_names())
        for exp in expected_templates:
            self.assertIn(exp, registered, f"Missing template: {exp}")

        meta_list = TemplateRegistry.list_templates()
        self.assertGreaterEqual(len(meta_list), 7)
        for meta in meta_list:
            self.assertIn("name", meta)
            self.assertIn("display_name", meta)
            self.assertIn("description", meta)
            self.assertIn("category", meta)
            self.assertIn("target_roles", meta)
            self.assertGreater(meta["default_font_size"], 0)

    def test_template_registry_aliases_and_fallback(self):
        """Verifies alias resolution and default fallback behavior."""
        # Harvard aliases
        self.assertIsInstance(TemplateRegistry.get("harvard"), HarvardTemplate)
        self.assertIsInstance(TemplateRegistry.get("ivy"), HarvardTemplate)
        self.assertIsInstance(TemplateRegistry.get("fas"), HarvardTemplate)

        # Tech Minimalist aliases
        self.assertIsInstance(TemplateRegistry.get("minimalist"), MinimalistTemplate)
        self.assertIsInstance(TemplateRegistry.get("stripe"), MinimalistTemplate)
        self.assertIsInstance(TemplateRegistry.get("vercel"), MinimalistTemplate)

        # Quant aliases
        self.assertIsInstance(TemplateRegistry.get("quant"), QuantTemplate)
        self.assertIsInstance(TemplateRegistry.get("citadel"), QuantTemplate)
        self.assertIsInstance(TemplateRegistry.get("jane_street"), QuantTemplate)

        # Awesome-CV aliases
        self.assertIsInstance(TemplateRegistry.get("awesome"), AwesomeCvTemplate)
        self.assertIsInstance(TemplateRegistry.get("posquit0"), AwesomeCvTemplate)

        # Academic aliases
        self.assertIsInstance(TemplateRegistry.get("academic"), AcademicTemplate)
        self.assertIsInstance(TemplateRegistry.get("ieee"), AcademicTemplate)

        # Fallback to CERN
        self.assertIsInstance(TemplateRegistry.get("unknown_template_xyz"), CernTemplate)
        self.assertIsInstance(TemplateRegistry.get(""), CernTemplate)
        self.assertIsInstance(TemplateRegistry.get(None), CernTemplate)

    def test_all_templates_render_valid_latex(self):
        """Verifies that every registered template generates valid LaTeX document structure."""
        for name in TemplateRegistry.get_template_names():
            tmpl = TemplateRegistry.get(name)
            tex = tmpl.render_latex(self.sample_data)

            self.assertIn(r"\documentclass", tex, f"Template {name} missing documentclass")
            self.assertIn(r"\begin{document}", tex, f"Template {name} missing begin document")
            self.assertIn(r"\end{document}", tex, f"Template {name} missing end document")
            self.assertTrue("Kanishk" in tex or "KANISHK" in tex, f"Template {name} missing candidate name")
            self.assertIn("Barkatullah University", tex, f"Template {name} missing education")
            self.assertIn("OZ Media", tex, f"Template {name} missing company")
            self.assertIn("Yatoro", tex, f"Template {name} missing project")
            self.assertIn("C++20", tex, f"Template {name} missing skill")

    def test_all_templates_render_valid_html(self):
        """Verifies that every registered template generates valid HTML5 preview markup."""
        for name in TemplateRegistry.get_template_names():
            tmpl = TemplateRegistry.get(name)
            html = tmpl.render_html(self.sample_data)

            self.assertIn("<!DOCTYPE html>", html, f"Template {name} missing DOCTYPE")
            self.assertIn("<title>", html, f"Template {name} missing title tag")
            self.assertIn("resume-page", html, f"Template {name} missing resume-page container")
            self.assertTrue("Kanishk" in html or "KANISHK" in html, f"Template {name} missing candidate name in HTML")
            self.assertIn("kanishkupadhyay22@gmail.com", html, f"Template {name} missing email")
            self.assertIn("OZ Media", html, f"Template {name} missing work experience")

    def test_exporter_delegation_and_backward_compatibility(self):
        """Verifies that ResumeExporter seamlessly delegates to TemplateRegistry."""
        exporter = ResumeExporter(self.sample_data)

        # Default LaTeX (CERN)
        tex_default = exporter.to_latex()
        self.assertIn("resumeSubheading", tex_default)

        # Explicit Harvard LaTeX
        tex_harvard = exporter.to_latex(template="harvard")
        self.assertIn("KANISHK UPADHYAY", tex_harvard)

        # Explicit Minimalist LaTeX
        tex_min = exporter.to_latex(template="minimalist")
        self.assertIn("slate900", tex_min)

        # Backward compatible to_html positional arguments
        html_compat = exporter.to_html(10.0, 1.25, 0.4)
        self.assertIn("<!DOCTYPE html>", html_compat)

        # Template-based to_html
        html_quant = exporter.to_html(template="quant")
        self.assertIn("EB Garamond", html_quant)

    def test_chrome_single_page_pdf_compilation(self):
        """Compiles sample resume across all 7 templates and guarantees single-page output."""
        compiler = ResumeCompiler()
        if not compiler.chrome_bin:
            self.skipTest("Google Chrome not available in this test environment.")

        with tempfile.TemporaryDirectory() as tmpdir:
            for tmpl_name in TemplateRegistry.get_template_names():
                out_pdf = Path(tmpdir) / f"test_{tmpl_name}.pdf"
                success = compiler.compile_resume(
                    data=self.sample_data,
                    output_pdf_path=str(out_pdf),
                    template=tmpl_name,
                    auto_fit=True
                )
                self.assertTrue(success, f"Failed to compile PDF for template {tmpl_name}")
                self.assertTrue(out_pdf.exists())
                self.assertGreater(out_pdf.stat().st_size, 10000)

                pages = compiler.get_pdf_page_count(str(out_pdf))
                self.assertEqual(pages, 1, f"Template {tmpl_name} failed single-page budget: produced {pages} pages")


if __name__ == "__main__":
    unittest.main()
