"""Unit tests for JobHunter and ATS API providers."""

import unittest
from unittest.mock import patch, MagicMock
import json
from pathlib import Path

from resume_forge.core.hunter import (
    JobHunter, JobPosting, HunterPreferences, BaseATSProvider, ATSProviderRegistry,
    AmazonProvider, SmartRecruitersProvider,
    GreenhouseProvider, LeverProvider, AshbyProvider, WorkdayProvider,
    AikyamProvider, HNHiringProvider, RSSFeedProvider, _clean_html,
    _match_seniority, _match_experience, _match_role
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

    @patch("urllib.request.urlopen")
    def test_aikyam_provider_mock(self, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps({
            "data": [
                {
                    "id": 42,
                    "attributes": {
                        "title": "Software Tester Intern",
                        "slug": "software-tester-intern-pratham",
                        "jobDescription": "Testing educational platforms with Python.",
                        "organization": {"data": {"attributes": {"name": "Pratham Books"}}},
                        "location": "Bengaluru, India",
                        "applyUrl": "https://aikyamjobs.org/jobs/software-tester-intern-pratham"
                    }
                }
            ]
        }).encode("utf-8")
        mock_urlopen.return_value.__enter__.return_value = mock_resp

        provider = AikyamProvider()
        jobs = provider.fetch_jobs(role="intern", location="India", limit=5)
        self.assertEqual(len(jobs), 1)
        self.assertEqual(jobs[0].title, "Software Tester Intern")
        self.assertEqual(jobs[0].company, "Pratham Books")
        self.assertEqual(jobs[0].ats_type, "aikyam")

    @patch("urllib.request.urlopen")
    def test_hn_hiring_provider_mock(self, mock_urlopen):
        story_resp = MagicMock()
        story_resp.read.return_value = json.dumps({
            "hits": [{"objectID": "98765", "title": "Ask HN: Who is hiring? (Nov 2026)"}]
        }).encode("utf-8")

        comment_resp = MagicMock()
        comment_resp.read.return_value = json.dumps({
            "hits": [
                {
                    "objectID": "111222",
                    "comment_text": "Retool | Software Engineering Intern | San Francisco / Remote | https://retool.com/careers"
                }
            ]
        }).encode("utf-8")

        mock_urlopen.return_value.__enter__.side_effect = [story_resp, comment_resp]

        provider = HNHiringProvider()
        jobs = provider.fetch_jobs(role="intern", location="remote", limit=5)
        self.assertEqual(len(jobs), 1)
        self.assertEqual(jobs[0].company, "Retool")
        self.assertEqual(jobs[0].ats_type, "hn")

    @patch("urllib.request.urlopen")
    def test_rss_feed_provider_mock(self, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.read.return_value = b"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Job Board Feed</title>
    <item>
      <title>Backend Engineer Intern</title>
      <link>https://example.com/jobs/101</link>
      <description>Work with Go and Python in a remote setting.</description>
      <guid>job-101</guid>
    </item>
  </channel>
</rss>"""
        mock_urlopen.return_value.__enter__.return_value = mock_resp

        provider = RSSFeedProvider("https://example.com/rss", "Example Board")
        jobs = provider.fetch_jobs(role="intern", location="remote", limit=5)
        self.assertEqual(len(jobs), 1)
        self.assertEqual(jobs[0].title, "Backend Engineer Intern")
        self.assertEqual(jobs[0].company, "Example Board")
        self.assertEqual(jobs[0].ats_type, "rss")

    def test_hunter_preferences_model_and_file_io(self):
        """Verifies creating, serializing, saving, and restoring HunterPreferences profiles."""
        import tempfile
        prefs = HunterPreferences(
            roles=["Platform Engineer", "Site Reliability Engineer"],
            locations=["Remote", "US", "Germany"],
            seniority="senior",
            min_experience_years=5,
            max_experience_years=10,
            exclude_titles=["manager", "director"],
            exclude_keywords=["clearance"],
            custom_boards={
                "greenhouse": ["stripe", "datadog"],
                "workday": [{"company": "nvidia", "host": "nvidia.wd5.myworkdayjobs.com", "site": "NVIDIAExternalCareerSite"}]
            }
        )
        d = prefs.to_dict()
        self.assertEqual(d["seniority"], "senior")
        self.assertEqual(d["min_experience_years"], 5)
        self.assertIn("stripe", d["custom_boards"]["greenhouse"])

        # Roundtrip JSON
        json_str = prefs.to_json()
        restored = HunterPreferences.from_json(json_str)
        self.assertEqual(restored.roles, prefs.roles)
        self.assertEqual(restored.min_experience_years, 5)

        # File IO
        with tempfile.TemporaryDirectory() as tmpdir:
            profile_path = Path(tmpdir) / "test_profile.json"
            prefs.save_file(profile_path)
            self.assertTrue(profile_path.exists())
            loaded = HunterPreferences.load_file(profile_path)
            self.assertEqual(loaded.seniority, "senior")
            self.assertEqual(len(loaded.exclude_titles), 2)

    def test_seniority_levels_filtering(self):
        """Verifies configurable seniority filters prevent title mismatches."""
        # Senior candidate search
        self.assertTrue(_match_seniority("Senior Software Engineer", target_seniority="senior"))
        self.assertTrue(_match_seniority("Staff Distributed Systems Engineer", target_seniority="senior"))
        self.assertFalse(_match_seniority("Software Engineer Intern", target_seniority="senior"))
        self.assertFalse(_match_seniority("Junior Frontend Developer", target_seniority="senior"))

        # Intern / Student search
        self.assertTrue(_match_seniority("Software Engineer Intern", target_seniority="intern"))
        self.assertFalse(_match_seniority("Senior Software Engineer", target_seniority="intern"))
        self.assertFalse(_match_seniority("Lead Architect", target_seniority="intern"))

        # Mid level search
        self.assertTrue(_match_seniority("Software Engineer II", target_seniority="mid"))
        self.assertFalse(_match_seniority("Software Engineer Intern", target_seniority="mid"))

    def test_experience_years_matching(self):
        """Verifies min and max experience constraints filter job requirements."""
        jd_junior = "Requirements: 1-2 years of experience building web apps."
        jd_mid = "Requirements: 3-5 years of experience in distributed systems."
        jd_senior = "Requirements: At least 7+ years of experience architecting large scale clusters."

        # Junior filter (max 2 years)
        self.assertTrue(_match_experience(jd_junior, max_exp=2))
        self.assertFalse(_match_experience(jd_mid, max_exp=2))
        self.assertFalse(_match_experience(jd_senior, max_exp=2))

        # Senior filter (min 5 years)
        self.assertFalse(_match_experience(jd_junior, min_exp=5))
        self.assertFalse(_match_experience(jd_mid, min_exp=5))
        self.assertTrue(_match_experience(jd_senior, min_exp=5))

    def test_custom_boards_extension(self):
        """Verifies custom ATS company boards can be plugged into JobHunter dynamically."""
        custom_boards = {
            "greenhouse": ["airbnb", "cloudflare"],
            "workday": [
                {"company": "nvidia", "host": "nvidia.wd5.myworkdayjobs.com", "site": "NVIDIAExternalCareerSite", "name": "NVIDIA"}
            ]
        }
        hunter = JobHunter(custom_boards=custom_boards)
        providers = hunter.get_providers()
        co_names = [getattr(p, "company_id", None) or getattr(p, "board_token", None) or p.name for p in providers]
        self.assertIn("airbnb", co_names)
        self.assertIn("cloudflare", co_names)
        self.assertIn("nvidia", co_names)

        # Directly targeting custom company
        hunter_nv = JobHunter(company="nvidia", custom_boards=custom_boards)
        nv_prov = hunter_nv.get_providers()
        self.assertEqual(len(nv_prov), 1)
        self.assertEqual(nv_prov[0].company_name, "NVIDIA")
        self.assertEqual(nv_prov[0].host, "nvidia.wd5.myworkdayjobs.com")

    def test_title_and_keyword_exclusions(self):
        """Verifies user-defined title and description exclusion filters."""
        self.assertFalse(_match_role("Engineering Manager", role_query="engineer", exclude_titles=["manager"]))
        self.assertTrue(_match_role("Software Engineer", role_query="engineer", exclude_titles=["manager"]))

        # Keyword exclusions in hunt
        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_resp = MagicMock()
            mock_resp.read.return_value = json.dumps({
                "jobs": [
                    {
                        "title": "Software Engineer",
                        "id_icims": "2001",
                        "job_path": "/jobs/2001",
                        "location": "US",
                        "description": "Must possess active Top Secret Polygraph clearance.",
                        "basic_qualifications": ""
                    },
                    {
                        "title": "Software Engineer",
                        "id_icims": "2002",
                        "job_path": "/jobs/2002",
                        "location": "US",
                        "description": "Build modern cloud microservices with Python and AWS.",
                        "basic_qualifications": ""
                    }
                ]
            }).encode("utf-8")
            mock_urlopen.return_value.__enter__.return_value = mock_resp

            hunter = JobHunter(company="amazon", exclude_keywords=["polygraph", "clearance"])
            postings = hunter.hunt()
            self.assertEqual(len(postings), 1)
            self.assertEqual(postings[0].id, "2002")

    def test_ats_provider_registry_and_custom_provider_plugin(self):
        """Verifies third-party or custom ATS providers can be registered dynamically via plugin architecture."""
        class MockCustomATSProvider(BaseATSProvider):
            name = "customats"
            def fetch_jobs(self, role="", location="", limit=10):
                return [
                    JobPosting(
                        id="custom_999",
                        title="Embedded Systems Architect",
                        company="CustomCorp",
                        ats_type="customats",
                        location="Remote",
                        url="https://customcorp.example/jobs/999",
                        apply_url="https://customcorp.example/jobs/999/apply",
                        description="Kernel driver development and RTOS firmware."
                    )
                ]

        # Register plugin provider
        JobHunter.register_provider("customats", MockCustomATSProvider, aliases=["custom_ats_alias"])
        self.assertTrue(ATSProviderRegistry.is_registered("customats"))
        self.assertTrue(ATSProviderRegistry.is_registered("custom_ats_alias"))
        self.assertIs(ATSProviderRegistry.get("custom_ats_alias"), MockCustomATSProvider)

        # Run JobHunter targeting the custom provider
        hunter = JobHunter(provider="customats")
        postings = hunter.hunt()
        self.assertEqual(len(postings), 1)
        self.assertEqual(postings[0].id, "custom_999")
        self.assertEqual(postings[0].ats_type, "customats")

    def test_require_keywords_filtering(self):
        """Verifies require_keywords ensures only postings containing all required keywords pass."""
        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_resp = MagicMock()
            mock_resp.read.return_value = json.dumps({
                "jobs": [
                    {
                        "title": "Software Engineer",
                        "id_icims": "3001",
                        "job_path": "/jobs/3001",
                        "location": "US",
                        "description": "Requires deep expertise in Python and Kubernetes.",
                        "basic_qualifications": ""
                    },
                    {
                        "title": "Software Engineer",
                        "id_icims": "3002",
                        "job_path": "/jobs/3002",
                        "location": "US",
                        "description": "Requires Java and AWS microservices experience.",
                        "basic_qualifications": ""
                    }
                ]
            }).encode("utf-8")
            mock_urlopen.return_value.__enter__.return_value = mock_resp

            hunter = JobHunter(company="amazon", require_keywords=["python", "kubernetes"])
            postings = hunter.hunt()
            self.assertEqual(len(postings), 1)
            self.assertEqual(postings[0].id, "3001")

    def test_custom_filter_hooks_pipeline(self):
        """Verifies users can attach arbitrary predicate filter hooks to JobHunter."""
        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_resp = MagicMock()
            mock_resp.read.return_value = json.dumps({
                "jobs": [
                    {
                        "title": "Staff Infrastructure Engineer",
                        "id_icims": "4001",
                        "job_path": "/jobs/4001",
                        "location": "US",
                        "description": "Cloud infra and distributed systems.",
                        "basic_qualifications": ""
                    },
                    {
                        "title": "Junior Backend Developer",
                        "id_icims": "4002",
                        "job_path": "/jobs/4002",
                        "location": "US",
                        "description": "Build internal tools with Python.",
                        "basic_qualifications": ""
                    }
                ]
            }).encode("utf-8")
            mock_urlopen.return_value.__enter__.return_value = mock_resp

            hunter = JobHunter(company="amazon")
            # Custom filter hook: only accept titles starting with 'Staff'
            hunter.add_filter(lambda p: p.title.startswith("Staff"))

            postings = hunter.hunt()
            self.assertEqual(len(postings), 1)
            self.assertEqual(postings[0].id, "4001")

    def test_cern_role_matching_early_career(self):
        """Verifies CERN student and early-career role synonyms match 'intern'."""
        self.assertTrue(_match_role("CERN Summer Student Programme", "intern"))
        self.assertTrue(_match_role("CERN OPENLAB Summer Student Programme", "intern"))
        self.assertTrue(_match_role("Technical Student Programme in IT", "intern"))
        self.assertTrue(_match_role("Administrative Student", "intern"))
        self.assertTrue(_match_role("Engineering Co-op", "intern"))
        self.assertTrue(_match_role("Graduate Trainee", "intern"))
        self.assertTrue(_match_role("Software Engineer Intern", "student"))

    @patch("urllib.request.urlopen")
    def test_smartrecruiters_cern_query_params(self, mock_urlopen):
        """Verifies CERN SmartRecruiters requests enforce limit=100 and suppress country=in & q=."""
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps({"content": []}).encode("utf-8")
        mock_urlopen.return_value.__enter__.return_value = mock_resp

        cern_provider = SmartRecruitersProvider("CERN", "CERN")
        cern_provider.fetch_jobs(role="intern", location="India", limit=10)

        # Inspect the URL passed to urllib
        call_args = mock_urlopen.call_args
        req = call_args[0][0]
        url = req.full_url if hasattr(req, "full_url") else str(req)

        self.assertIn("limit=100", url)
        # Verify server-side country filter is suppressed for CERN to avoid 0 results
        self.assertNotIn("country=in", url)
        self.assertNotIn("country=IN", url)
        # Verify q= is suppressed for CERN
        self.assertNotIn("q=", url)

    def test_ats_registry_plugin_discovery(self):
        """Verifies drop-in ATS providers in the plugins directory are automatically discovered."""
        import tempfile
        from resume_forge.providers.registry import ATSProviderRegistry

        with tempfile.TemporaryDirectory() as tmpdir:
            plugin_code = (
                "from resume_forge.providers.base import BaseATSProvider\n"
                "class CustomBoardProvider(BaseATSProvider):\n"
                "    name = 'customboard'\n"
                "    def fetch_jobs(self, role='', location='', limit=10):\n"
                "        return []\n"
            )
            plugin_file = Path(tmpdir) / "custom_board_plugin.py"
            plugin_file.write_text(plugin_code, encoding="utf-8")

            with patch("resume_forge.providers.registry.get_plugins_dir", return_value=Path(tmpdir)):
                ATSProviderRegistry._plugins_loaded = False
                prov_cls = ATSProviderRegistry.get("customboard")
                self.assertIsNotNone(prov_cls)
                self.assertEqual(prov_cls.name, "customboard")

    def test_multi_role_matching_and_word_boundaries(self):
        """Verifies multi-role comma separated queries and short keyword boundary matching."""
        # Multi-role OR matching
        self.assertTrue(_match_role("Software Engineer", "Backend Developer, Software Engineer"))
        self.assertTrue(_match_role("Backend Developer", "Backend Developer, Software Engineer"))
        self.assertFalse(_match_role("Data Scientist", "Backend Developer, Software Engineer"))

        # Short keyword boundary matching (prevent substring false positives)
        self.assertFalse(_match_role("Category Manager", "go"))
        self.assertFalse(_match_role("Algorithms Developer", "go"))
        self.assertTrue(_match_role("Go Developer", "go"))
        self.assertTrue(_match_role("Senior Golang / Go Engineer", "go"))

    def test_experience_matching_variations(self):
        """Verifies 'to' range, 'yrs' abbreviations, and plus quantifiers."""
        # "3 to 5 years"
        jd1 = "Requires 3 to 5 years of experience in distributed systems."
        self.assertTrue(_match_experience(jd1, min_exp=3, max_exp=5))
        self.assertFalse(_match_experience(jd1, max_exp=2))

        # "5+ yrs"
        jd2 = "Must have 5+ yrs experience with Python."
        self.assertFalse(_match_experience(jd2, max_exp=3))
        self.assertTrue(_match_experience(jd2, min_exp=5))

        # "1-3 yrs of experience"
        jd3 = "Seeking developer with 1-3 yrs of experience."
        self.assertFalse(_match_experience(jd3, min_exp=5))

    def test_plugin_discovery_resilience_to_errors(self):
        """Verifies registry ignores corrupted plugin files and leading underscore files."""
        import tempfile
        from resume_forge.providers.registry import ATSProviderRegistry

        with tempfile.TemporaryDirectory() as tmpdir:
            # 1. Broken Python syntax
            bad_file = Path(tmpdir) / "broken_plugin.py"
            bad_file.write_text("def syntax_error(:", encoding="utf-8")

            # 2. Private file starting with underscore
            priv_file = Path(tmpdir) / "_hidden.py"
            priv_file.write_text("class Hidden: pass", encoding="utf-8")

            # 3. Class without explicit name attribute
            stem_file = Path(tmpdir) / "stemnamed.py"
            stem_code = (
                "from resume_forge.providers.base import BaseATSProvider\n"
                "class StemClass(BaseATSProvider):\n"
                "    def fetch_jobs(self, role='', location='', limit=10):\n"
                "        return []\n"
            )
            stem_file.write_text(stem_code, encoding="utf-8")

            with patch("resume_forge.providers.registry.get_plugins_dir", return_value=Path(tmpdir)):
                ATSProviderRegistry._plugins_loaded = False
                # Should not crash on broken_plugin.py
                prov_cls = ATSProviderRegistry.get("stemnamed")
                self.assertIsNotNone(prov_cls)
                self.assertIsNone(ATSProviderRegistry.get("broken"))
                self.assertIsNone(ATSProviderRegistry.get("hidden"))




if __name__ == "__main__":
    unittest.main()
