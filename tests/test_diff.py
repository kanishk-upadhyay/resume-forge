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

    def test_education_diff(self):
        """Verify education additions, modifications, and removals."""
        from resume_forge.core.schema import EducationItem
        # Modify existing degree
        self.r2.education[0].study_type = "M.S. in Computer Science"
        self.r2.education[0].end_date = "2027"
        # Add new institution
        self.r2.education.append(EducationItem(
            institution="Stanford University",
            study_type="Graduate Certificate in Systems",
            start_date="2025",
            end_date="2026"
        ))

        res = ResumeDiffEngine.diff(self.r1, self.r2)
        edu_by_name = {e.institution: e for e in res.education}
        self.assertIn("Stanford University", edu_by_name)
        self.assertEqual(edu_by_name["Stanford University"].status, "added")

        orig_inst = self.r1.education[0].institution
        self.assertIn(orig_inst, edu_by_name)
        self.assertEqual(edu_by_name[orig_inst].status, "modified")
        self.assertEqual(edu_by_name[orig_inst].new_degree, "M.S. in Computer Science")

        term_output = res.format_terminal(color=False)
        self.assertIn("Education", term_output)
        self.assertIn("Stanford University", term_output)

    def test_open_source_and_expanded_sections_diff(self):
        """Verify diffing of open source, awards, certs, publications, languages."""
        from resume_forge.core.schema import OpenSourceItem, CertificateItem, AwardItem, PublicationItem
        self.r2.open_source.append(OpenSourceItem(
            project="linux-kernel",
            highlights=["Patched eBPF verifier bounds check."]
        ))
        self.r2.certificates.append(CertificateItem(name="CKA: Certified Kubernetes Administrator"))
        self.r2.awards.append(AwardItem(title="Turing Scholar Award"))
        self.r2.publications.append(PublicationItem(name="High-Throughput Consensus in Asynchronous Networks"))
        self.r2.languages.append("German")

        res = ResumeDiffEngine.diff(self.r1, self.r2)
        self.assertEqual(len(res.open_source), 1)
        self.assertEqual(res.open_source[0].project, "linux-kernel")
        self.assertEqual(res.open_source[0].status, "added")

        self.assertIn("CKA: Certified Kubernetes Administrator", res.certificates_added)
        self.assertIn("Turing Scholar Award", res.awards_added)
        self.assertIn("High-Throughput Consensus in Asynchronous Networks", res.publications_added)
        self.assertIn("German", res.languages_added)

        term_colored = res.format_terminal(color=True)
        self.assertIn("Open-Source Contributions", term_colored)
        self.assertIn("Certifications", term_colored)
        self.assertIn("Awards & Honors", term_colored)
        self.assertIn("Publications", term_colored)
        self.assertIn("Languages", term_colored)

    def test_empty_resumes_diff(self):
        """Verify diffing completely empty ResumeData objects handles all empty fields gracefully."""
        from resume_forge.core.schema import ResumeData
        r1 = ResumeData()
        r2 = ResumeData()
        res = ResumeDiffEngine.diff(r1, r2)
        self.assertEqual(len(res.work), 0)
        self.assertEqual(len(res.education), 0)
        self.assertEqual(len(res.projects), 0)
        self.assertEqual(len(res.open_source), 0)
        self.assertEqual(res.score_delta, 0)
        formatted = res.format_terminal(color=False)
        self.assertIn("ATS Score Delta", formatted)


if __name__ == "__main__":
    unittest.main()
