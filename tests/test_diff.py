"""Unit tests for ResumeDiffEngine structural comparison."""

import unittest
from pathlib import Path
import copy

from resume_forge.core.parser import LatexResumeParser
from resume_forge.core.diff import ResumeDiffEngine
from resume_forge.core.schema import WorkItem, ProjectItem, SkillItem


class TestResumeDiffEngine(unittest.TestCase):

    def setUp(self):
        sample_path = Path(__file__).parent.parent / "examples" / "kanishk_cern_fullstack_resume.tex"
        self.r1 = LatexResumeParser(sample_path.read_text(encoding="utf-8")).parse()
        self.r2 = copy.deepcopy(self.r1)

    def test_identical_resumes_diff(self):
        res = ResumeDiffEngine.diff(self.r1, self.r2)
        self.assertEqual(len(res.basics_changed), 0)
        self.assertEqual(len(res.work), 0)
        self.assertEqual(len(res.projects), 0)
        self.assertEqual(len(res.skills_added), 0)
        self.assertEqual(len(res.skills_removed), 0)
        self.assertEqual(res.score_delta, 0)

    def test_basics_change_detection(self):
        self.r2.basics.email = "kanishk_systems@google.com"
        self.r2.basics.phone = "+1 555-0199"
        res = ResumeDiffEngine.diff(self.r1, self.r2)
        self.assertIn("email", res.basics_changed)
        self.assertEqual(res.basics_changed["email"]["new"], "kanishk_systems@google.com")
        self.assertIn("phone", res.basics_changed)

    def test_work_experience_diff(self):
        # Modify existing job
        self.r2.work[0].highlights.append("Engineered low-latency C++ trading gateway reducing p99 by 40%.")
        # Add new job
        self.r2.work.append(WorkItem(name="Citadel", position="Quant Intern", highlights=["Implemented market data parser."]))
        res = ResumeDiffEngine.diff(self.r1, self.r2)

        work_names = {w.name: w for w in res.work}
        self.assertIn("Citadel", work_names)
        self.assertEqual(work_names["Citadel"].status, "added")

        modified_job = work_names[self.r1.work[0].name]
        self.assertEqual(modified_job.status, "modified")
        added_bullets = [b for b in modified_job.bullets if b.status == "added"]
        self.assertEqual(len(added_bullets), 1)
        self.assertIn("low-latency", added_bullets[0].new_text)

    def test_skills_diff(self):
        self.r2.skills[0].keywords.append("Rust")
        self.r2.skills[0].keywords.remove("C")
        res = ResumeDiffEngine.diff(self.r1, self.r2)
        cat_name = self.r1.skills[0].name.title()
        self.assertIn(cat_name, res.skills_added)
        self.assertIn("Rust", res.skills_added[cat_name])
        self.assertIn(cat_name, res.skills_removed)
        self.assertIn("C", res.skills_removed[cat_name])

    def test_format_terminal_and_dict(self):
        self.r2.basics.email = "new_email@example.com"
        res = ResumeDiffEngine.diff(self.r1, self.r2)
        term_colored = res.format_terminal(color=True)
        self.assertIn("STRUCTURAL AST COMPARISON", term_colored)
        self.assertIn("\033[", term_colored)

        term_plain = res.format_terminal(color=False)
        self.assertNotIn("\033[", term_plain)

        d = res.to_dict()
        self.assertIn("basics_changed", d)
        self.assertIn("ats", d)


if __name__ == "__main__":
    unittest.main()
