"""Unit tests for ResumeData schema serialization and round-tripping."""

import unittest
import json
from resume_forge.core.schema import (
    ResumeData, Basics, WorkItem, EducationItem, ProjectItem, SkillItem, OpenSourceItem, Location, Profile
)


class TestResumeSchema(unittest.TestCase):

    def setUp(self):
        self.resume = ResumeData(
            basics=Basics(
                name="Kanishk Upadhyay",
                label="Fullstack Systems Engineer",
                email="kanishkupadhyay22@gmail.com",
                phone="+91 7772034062",
                url="https://kanishk.pages.dev/treasures",
                summary="Passionate engineer building high-impact systems.",
                location=Location(city="Bhopal", region="MP", country_code="IN"),
                profiles=[
                    Profile(network="GitHub", username="kanishk-upadhyay", url="https://github.com/kanishk-upadhyay"),
                    Profile(network="GitLab", username="kanishk0", url="https://gitlab.com/kanishk0")
                ]
            ),
            work=[
                WorkItem(
                    name="OZ Media",
                    position="Software Developer Intern",
                    url="https://ozmedia.example.com",
                    start_date="06/2025",
                    end_date="12/2025",
                    location="Remote",
                    highlights=["Engineered React/Flask web applications."]
                )
            ],
            education=[
                EducationItem(
                    institution="Barkatullah University",
                    area="Bhopal",
                    study_type="Bachelor of Engineering in Computer Science",
                    start_date="2023",
                    end_date="2027",
                    courses=["Data Structures", "Operating Systems"]
                )
            ],
            projects=[
                ProjectItem(
                    name="Pokédex",
                    description="Offline-first PWA",
                    keywords=["Vanilla JS", "Service Worker"],
                    url="https://kanishk-pokedex.surge.sh",
                    highlights=["Levenshtein distance fuzzy search"]
                )
            ],
            skills=[
                SkillItem(name="Languages", keywords=["Python", "C", "Swift", "JavaScript"])
            ],
            open_source=[
                OpenSourceItem(
                    project="GitLab",
                    role="Core Contributor",
                    url="https://gitlab.com/kanishk0",
                    highlights=["Implemented Vue.js design tokens."]
                )
            ]
        )

    def test_to_dict_and_from_dict_roundtrip(self):
        d = self.resume.to_dict()
        self.assertIsInstance(d, dict)
        self.assertEqual(d["basics"]["name"], "Kanishk Upadhyay")
        self.assertEqual(len(d["basics"]["profiles"]), 2)
        self.assertEqual(d["work"][0]["name"], "OZ Media")
        self.assertEqual(d["education"][0]["courses"], ["Data Structures", "Operating Systems"])

        # Reconstruct
        restored = ResumeData.from_dict(d)
        self.assertEqual(restored.basics.name, self.resume.basics.name)
        self.assertEqual(restored.basics.location.city, "Bhopal")
        self.assertEqual(len(restored.work), 1)
        self.assertEqual(restored.work[0].highlights, ["Engineered React/Flask web applications."])
        self.assertEqual(len(restored.open_source), 1)
        self.assertEqual(restored.open_source[0].project, "GitLab")

    def test_json_serialization(self):
        json_str = self.resume.to_json(indent=2)
        parsed_json = json.loads(json_str)
        self.assertEqual(parsed_json["basics"]["email"], "kanishkupadhyay22@gmail.com")

        restored = ResumeData.from_json(json_str)
        self.assertEqual(restored.basics.email, self.resume.basics.email)
        self.assertEqual(restored.projects[0].keywords, ["Vanilla JS", "Service Worker"])

    def test_resilience_to_missing_and_unknown_fields(self):
        partial_dict = {
            "basics": {
                "name": "Jane Doe",
                "unknown_extra_field": "ignore_me"
            },
            "work": [
                {"name": "Tech Corp", "position": "Senior Dev", "unexpected_attr": 42}
            ],
            "random_top_level": "should_not_crash"
        }
        # Should parse gracefully without raising KeyError or TypeError
        obj = ResumeData.from_dict(partial_dict)
        self.assertEqual(obj.basics.name, "Jane Doe")
        self.assertEqual(obj.basics.email, "")
        self.assertEqual(len(obj.work), 1)
        self.assertEqual(obj.work[0].name, "Tech Corp")


if __name__ == "__main__":
    unittest.main()
