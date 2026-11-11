"""Unit tests for ATSAnalyzer."""

import unittest
from resume_forge.core.ats import ATSAnalyzer
from resume_forge.core.schema import ResumeData, Basics, WorkItem, EducationItem, SkillItem, ProjectItem


class TestATSAnalyzer(unittest.TestCase):

    def setUp(self):
        self.data = ResumeData(
            basics=Basics(
                name="Kanishk Upadhyay",
                email="kanishk@example.com",
                phone="+91 7772034062"
            ),
            work=[
                WorkItem(
                    name="OZ Media",
                    position="Software Developer Intern",
                    start_date="06/2025",
                    end_date="12/2025",
                    highlights=[
                        "Engineered full-stack responsive web applications utilizing React and Redux.",
                        "Optimized queries with SQLAlchemy and MySQL, reducing API response times by 35%."
                    ]
                )
            ],
            education=[
                EducationItem(
                    institution="Barkatullah University",
                    study_type="Bachelor of Engineering in Computer Science",
                    start_date="2023",
                    end_date="2027"
                )
            ],
            skills=[
                SkillItem(name="Languages", keywords=["Python", "C", "JavaScript"]),
                SkillItem(name="Frameworks", keywords=["React", "Flask", "Vue.js"])
            ]
        )
        self.analyzer = ATSAnalyzer(self.data)

    def test_basic_audit_score(self):
        report = self.analyzer.analyze()
        self.assertGreaterEqual(report["score"], 80)
        self.assertIn("strengths", report)
        self.assertIn("suggestions", report)
        self.assertIn("page_budget_percent", report)

    def test_empty_resume_penalties(self):
        empty_data = ResumeData()
        analyzer = ATSAnalyzer(empty_data)
        report = analyzer.analyze()
        self.assertLess(report["score"], 60)
        self.assertTrue(any("name" in s.lower() for s in report["suggestions"]))
        self.assertTrue(any("email" in s.lower() for s in report["suggestions"]))
        self.assertTrue(any("phone" in s.lower() for s in report["suggestions"]))

    def test_quantifiable_metrics_detection(self):
        report = self.analyzer.analyze()
        # "reducing API response times by 35%" contains metric
        self.assertTrue(any("quantifiable impact metrics" in s for s in report["strengths"]))

    def test_action_verbs_detection(self):
        report = self.analyzer.analyze()
        # "Engineered" and "Optimized" are strong action verbs
        self.assertTrue(any("action verbs" in s for s in report["strengths"]))

    def test_job_description_keyword_matching(self):
        jd = "Seeking a Software Developer with experience in Python, React, Flask, and Docker for scalable services."
        report = self.analyzer.analyze(job_description=jd)
        matched = [k.lower() for k in report["matched_keywords"]]
        self.assertIn("python", matched)
        self.assertIn("react", matched)
        self.assertIn("flask", matched)
        
        # Stop words like "with", "and", "for" should NOT be counted as target keywords
        self.assertNotIn("with", matched)
        self.assertNotIn("and", matched)
        self.assertNotIn("for", matched)


    def test_advanced_metrics_and_verbs(self):
        adv_data = ResumeData(
            basics=Basics(name="Developer", email="dev@example.com", phone="1234567890"),
            work=[
                WorkItem(
                    name="Infra Corp",
                    position="Systems Engineer",
                    highlights=[
                        "Benchmarked IPC latency down to O(1) complexity across 16 cores.",
                        "Refactored microservices to guarantee zero downtime and 0 memory leaks across 50+ daemons.",
                        "Merged 30+ MRs to streamline CI pipelines achieving a 3x speedup."
                    ]
                )
            ]
        )
        report = ATSAnalyzer(adv_data).analyze()
        self.assertTrue(any("quantifiable impact metrics" in s for s in report["strengths"]))
        self.assertTrue(any("action verbs" in s for s in report["strengths"]))
        self.assertEqual(report["cliches_detected"], [])


if __name__ == "__main__":
    unittest.main()
