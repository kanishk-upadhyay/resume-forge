"""Unit tests for JobHunter and ATS API providers."""

import unittest
from unittest.mock import patch, MagicMock
import json
from pathlib import Path

from resume_forge.core.hunter import (
    JobHunter, JobPosting, AmazonProvider, SmartRecruitersProvider,
    GreenhouseProvider, LeverProvider, AshbyProvider, WorkdayProvider, _clean_html
)


class TestJobHunter(unittest.TestCase):

    def test_job_posting_dict(self):
        posting = JobPosting(
            id="12345",
            title="Software Engineer Intern",
            company="Amazon",
            ats_type="amazon",
            location="Bengaluru, India",
            url="https://amazon.jobs/12345",
            apply_url="https://amazon.jobs/apply/12345",
            match_rate_percent=90,
            matched_keywords=["python", "c++"]
        )
        d = posting.to_dict()
        self.assertEqual(d["id"], "12345")
        self.assertEqual(d["title"], "Software Engineer Intern")
        self.assertEqual(d["company"], "Amazon")
        self.assertEqual(d["match_rate_percent"], 90)

    def test_clean_html(self):
        html = "<p>Looking for a <strong>Software Engineer</strong> with &amp; Python skills.</p>"
        cleaned = _clean_html(html)
        self.assertNotIn("<p>", cleaned)
        self.assertNotIn("<strong>", cleaned)
        self.assertIn("Software Engineer", cleaned)

    def test_provider_resolution(self):
        hunter_all = JobHunter(company="all")
        providers = hunter_all.get_providers()
        names = [p.name for p in providers]
        self.assertIn("amazon", names)
        self.assertIn("smartrecruiters", names)
        self.assertIn("greenhouse", names)
        self.assertIn("lever", names)
        self.assertIn("ashby", names)
        self.assertIn("workday", names)

        hunter_amazon = JobHunter(company="amazon")
        amazon_providers = hunter_amazon.get_providers()
        self.assertEqual(len(amazon_providers), 1)
        self.assertEqual(amazon_providers[0].name, "amazon")

        hunter_cern = JobHunter(company="cern")
        cern_providers = hunter_cern.get_providers()
        self.assertEqual(len(cern_providers), 1)
        self.assertEqual(cern_providers[0].name, "smartrecruiters")

        hunter_linear = JobHunter(company="linear")
        linear_providers = hunter_linear.get_providers()
        self.assertEqual(len(linear_providers), 1)
        self.assertEqual(linear_providers[0].name, "ashby")

        hunter_redhat = JobHunter(company="redhat")
        redhat_providers = hunter_redhat.get_providers()
        self.assertEqual(len(redhat_providers), 1)
        self.assertEqual(redhat_providers[0].name, "workday")

    @patch("urllib.request.urlopen")
    def test_amazon_provider_mock(self, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps({
            "jobs": [
                {
                    "title": "Software Development Engineer Intern",
                    "id_icims": "99999",
                    "job_path": "/en/jobs/99999/sde-intern",
                    "location": "Bengaluru, India",
                    "description": "Develop scalable distributed systems in Python and Java.",
                    "basic_qualifications": "Enrolled in Bachelor of Engineering."
                }
            ]
        }).encode("utf-8")
        mock_urlopen.return_value.__enter__.return_value = mock_resp

        provider = AmazonProvider()
        jobs = provider.fetch_jobs(role="intern", location="India", limit=5)
        self.assertEqual(len(jobs), 1)
        self.assertEqual(jobs[0].id, "99999")
        self.assertEqual(jobs[0].company, "Amazon")
        self.assertIn("https://www.amazon.jobs/applicant/jobs/99999/apply", jobs[0].apply_url)

    @patch("urllib.request.urlopen")
    def test_smartrecruiters_cern_mock(self, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps({
            "content": [
                {
                    "id": "744000160223950",
                    "name": "Software Engineer for CERNBox (IT-SD-GSS-2026-174-GRAP)",
                    "department": {"label": "IT"},
                    "location": {"city": "Geneva", "country": "Switzerland"}
                }
            ]
        }).encode("utf-8")
        mock_urlopen.return_value.__enter__.return_value = mock_resp

        provider = SmartRecruitersProvider("CERN", "CERN")
        jobs = provider.fetch_jobs(role="software", location="all", limit=5)
        self.assertEqual(len(jobs), 1)
        self.assertEqual(jobs[0].company, "CERN")
        self.assertIn("744000160223950", jobs[0].apply_url)

    @patch("urllib.request.urlopen")
    def test_ashby_provider_mock(self, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps({
            "jobs": [
                {
                    "id": "ashby-uuid-1234",
                    "title": "Software Engineer, Infrastructure",
                    "location": "San Francisco, CA",
                    "department": "Engineering",
                    "isRemote": True,
                    "jobUrl": "https://jobs.ashbyhq.com/linear/ashby-uuid-1234",
                    "applyUrl": "https://jobs.ashbyhq.com/linear/ashby-uuid-1234/application",
                    "descriptionPlain": "Build scalable distributed database clusters."
                }
            ]
        }).encode("utf-8")
        mock_urlopen.return_value.__enter__.return_value = mock_resp

        provider = AshbyProvider("linear", "Linear")
        jobs = provider.fetch_jobs(role="infrastructure", location="remote", limit=5)
        self.assertEqual(len(jobs), 1)
        self.assertEqual(jobs[0].id, "ashby-uuid-1234")
        self.assertEqual(jobs[0].company, "Linear")
        self.assertEqual(jobs[0].ats_type, "ashby")
        self.assertIn("application", jobs[0].apply_url)

    @patch("urllib.request.urlopen")
    def test_workday_provider_mock(self, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps({
            "total": 1,
            "jobPostings": [
                {
                    "title": "Software Engineer - OpenShift",
                    "externalPath": "/job/R-100200-engineer",
                    "locationsText": "Remote, US",
                    "remoteType": "Remote",
                    "bulletFields": ["R-100200"]
                }
            ]
        }).encode("utf-8")
        mock_urlopen.return_value.__enter__.return_value = mock_resp

        provider = WorkdayProvider("redhat", company_name="Red Hat")
        jobs = provider.fetch_jobs(role="engineer", location="US", limit=5)
        self.assertEqual(len(jobs), 1)
        self.assertEqual(jobs[0].id, "R-100200")
        self.assertEqual(jobs[0].company, "Red Hat")
        self.assertEqual(jobs[0].ats_type, "workday")
        self.assertIn("redhat.wd5.myworkdayjobs.com", jobs[0].url)
        self.assertIn("/apply", jobs[0].apply_url)

    def test_network_failure_graceful_handling(self):
        hunter = JobHunter(company="amazon")
        # In sandbox, network might fail gracefully without raising unhandled exception
        with patch("urllib.request.urlopen", side_effect=Exception("Connection refused")):
            results = hunter.hunt()
            self.assertEqual(results, [])

    @patch("urllib.request.urlopen")
    def test_grad_year_cohort_range_filtering(self, mock_urlopen):
        """Verifies graduation year matching works with ranges and description mentions."""
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps({
            "jobs": [
                {
                    "title": "Software Development Engineer Intern",
                    "id_icims": "1001",
                    "job_path": "/en/jobs/1001",
                    "location": "US",
                    "description": "Must be graduating between 2025 and 2027.",
                    "basic_qualifications": ""
                },
                {
                    "title": "Software Development Engineer Intern - Class of 2024",
                    "id_icims": "1002",
                    "job_path": "/en/jobs/1002",
                    "location": "US",
                    "description": "Targeting 2024 graduates only.",
                    "basic_qualifications": ""
                }
            ]
        }).encode("utf-8")
        mock_urlopen.return_value.__enter__.return_value = mock_resp

        # Search targeting 2026 cohort
        hunter = JobHunter(company="amazon", grad_year=2026)
        results = hunter.hunt()
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].id, "1001")


if __name__ == "__main__":
    unittest.main()
