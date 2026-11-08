"""Unit tests for BulletTailor engine."""

import unittest
from resume_forge.core.tailor import BulletTailor
from resume_forge.core.schema import ResumeData, Basics, WorkItem, ProjectItem


class TestBulletTailor(unittest.TestCase):

    def setUp(self):
        self.data = ResumeData(
            basics=Basics(name="Candidate"),
            work=[
                WorkItem(
                    name="Startup Inc",
                    position="Junior Dev",
                    highlights=[
                        "Responsible for maintaining legacy Python servers.",
                        "Helped with building React interfaces."
                    ]
                )
            ],
            projects=[
                ProjectItem(
                    name="API Engine",
                    highlights=[
                        "Engineered high-throughput service handling 50,000 requests per second."
                    ]
                )
            ]
        )
        self.tailor = BulletTailor(self.data)

    def test_weak_phrase_replacement(self):
        result = self.tailor.tailor(job_description="Looking for Python and React developers.")
        suggestions = result["suggestions"]
        self.assertGreaterEqual(len(suggestions), 2)

        # First bullet should replace "Responsible for" with "Engineered"
        s0 = suggestions[0]
        self.assertIn("Engineered", s0["improved"])
        self.assertNotIn("Responsible for", s0["improved"])

        # Second bullet should replace "Helped with" with "Developed"
        s1 = suggestions[1]
        self.assertIn("Developed", s1["improved"])
        self.assertNotIn("Helped with", s1["improved"])

    def test_already_strong_bullet_with_metric(self):
        result = self.tailor.tailor(job_description="Distributed systems")
        suggestions = result["suggestions"]
        # The project bullet already has "Engineered" + "50,000 requests per second" metric
        proj_suggestions = [s for s in suggestions if s["section"] == "projects"]
        self.assertEqual(len(proj_suggestions), 0)

    def test_apply_improvements(self):
        result = self.tailor.tailor(job_description="Python React")
        suggestions = result["suggestions"]
        self.tailor.apply_improvements(suggestions[:1])

        # Work bullet 0 should now be updated
        self.assertIn("Engineered", self.data.work[0].highlights[0])


if __name__ == "__main__":
    unittest.main()
