"""Unit tests for LatexResumeParser."""

import unittest
from pathlib import Path
from resume_forge.core.parser import LatexResumeParser, clean_latex
from resume_forge.core.schema import ResumeData


class TestLatexResumeParser(unittest.TestCase):

    def setUp(self):
        sample_path = Path(__file__).parent.parent / "examples" / "kanishk_cern_fullstack_resume.tex"
        self.tex_content = sample_path.read_text(encoding="utf-8")
        self.parser = LatexResumeParser(self.tex_content)
        self.data = self.parser.parse()

    def test_clean_latex(self):
        self.assertEqual(clean_latex(r"\textbf{Software Engineer}"), "Software Engineer")
        self.assertEqual(clean_latex(r"\href{https://github.com}{GitHub}"), "GitHub")
        self.assertEqual(clean_latex(r"Reduced latency by 35\%"), "Reduced latency by 35%")
        self.assertEqual(clean_latex(r"Data Structures \& Algorithms"), "Data Structures & Algorithms")

    def test_parse_basics(self):
        basics = self.data.basics
        self.assertIn("Kanishk", basics.name)
        self.assertIn("kanishkupadhyay22@gmail.com", basics.email)
        self.assertIn("7772034062", basics.phone)
        self.assertIn("Bhopal", basics.location.city)
        
        # Check profiles
        urls = [p.url for p in basics.profiles] + [basics.url]
        self.assertTrue(any("github.com/kanishk-upadhyay" in u for u in urls))
        self.assertTrue(any("gitlab.com/kanishk0" in u for u in urls))

    def test_parse_education(self):
        self.assertGreaterEqual(len(self.data.education), 1)
        edu = self.data.education[0]
        self.assertIn("Barkatullah", edu.institution)
        self.assertIn("Bachelor of Engineering", edu.study_type)
        self.assertGreaterEqual(len(edu.highlights), 1)

    def test_parse_work(self):
        self.assertGreaterEqual(len(self.data.work), 2)
        roles = [w.position for w in self.data.work]
        companies = [w.name for w in self.data.work]
        
        self.assertTrue(any("Software Developer Intern" in r for r in roles))
        self.assertTrue(any("OZ Media" in c for c in companies))
        self.assertTrue(any("Digigocare" in c for c in companies))
        
        # Verify bullets
        total_bullets = sum(len(w.highlights) for w in self.data.work)
        self.assertGreaterEqual(total_bullets, 4)

    def test_parse_open_source(self):
        self.assertGreaterEqual(len(self.data.open_source), 2)
        projects = [os.project for os in self.data.open_source]
        self.assertTrue(any("GitLab" in p for p in projects))
        self.assertTrue(any("Yatoro" in p for p in projects))

    def test_parse_projects(self):
        self.assertGreaterEqual(len(self.data.projects), 3)
        proj_names = [p.name for p in self.data.projects]
        self.assertTrue(any("Pokédex" in n for n in proj_names))
        self.assertTrue(any("Sector 7" in n for n in proj_names))
        self.assertTrue(any("SmartSpend" in n for n in proj_names))

    def test_parse_skills(self):
        self.assertGreaterEqual(len(self.data.skills), 3)
        cat_names = [s.name for s in self.data.skills]
        self.assertTrue(any("Languages" in c for c in cat_names))
        
        all_keywords = [k for s in self.data.skills for k in s.keywords]
        self.assertIn("Python", all_keywords)
        self.assertIn("C", all_keywords)
        self.assertIn("Swift", all_keywords)


if __name__ == "__main__":
    unittest.main()
