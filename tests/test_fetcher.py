"""Unit tests for JobDescriptionFetcher and HTML cleaning."""

import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import tempfile

from resume_forge.core.fetcher import fetch_job_description, clean_html_to_text, fetch_lever_job, fetch_greenhouse_job


class TestJobDescriptionFetcher(unittest.TestCase):

    def test_fetch_raw_string(self):
        text = "Looking for Senior Distributed Systems Engineer with Go and Linux."
        res = fetch_job_description(text)
        self.assertEqual(res, text)

    def test_fetch_local_file(self):
        with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as f:
            f.write("Role: Backend Engineer\nRequirements: Python, C++")
            p = f.name
        res = fetch_job_description(p)
        self.assertIn("Backend Engineer", res)
        self.assertIn("Python, C++", res)

    def test_clean_html_to_text(self):
        html = """
        <html>
            <head><title>Job</title><script>alert('xss');</script></head>
            <body>
                <nav><a href="/">Home</a></nav>
                <h1>Software Engineer</h1>
                <p>We are hiring a <strong>Systems Engineer</strong>.</p>
                <ul>
                    <li>5+ years with Linux</li>
                    <li>Experience with C and Rust</li>
                </ul>
                <footer>Copyright 2026</footer>
            </body>
        </html>
        """
        cleaned = clean_html_to_text(html)
        self.assertNotIn("alert", cleaned)
        self.assertNotIn("Home", cleaned)
        self.assertNotIn("Copyright 2026", cleaned)
        self.assertIn("Software Engineer", cleaned)
        self.assertIn("5+ years with Linux", cleaned)
        self.assertIn("Experience with C and Rust", cleaned)

    @patch("urllib.request.urlopen")
    def test_lever_api_mock(self, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.read.return_value = b'{"text": "Distributed Systems Engineer", "descriptionPlain": "Build large scale infra", "lists": [{"text": "Requirements", "content": "Linux, Kubernetes"}]}'
        mock_resp.__enter__.return_value = mock_resp
        mock_urlopen.return_value = mock_resp

        res = fetch_lever_job("https://jobs.lever.co/stripe/abc-123")
        self.assertIsNotNone(res)
        self.assertIn("Distributed Systems Engineer", res)
        self.assertIn("Linux, Kubernetes", res)

    @patch("urllib.request.urlopen")
    def test_greenhouse_api_mock(self, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.read.return_value = b'{"title": "Kernel Engineer", "content": "<p>Deep familiarity with eBPF, TCP/IP, and kernel modules.</p>"}'
        mock_resp.__enter__.return_value = mock_resp
        mock_urlopen.return_value = mock_resp

        res = fetch_greenhouse_job("https://boards.greenhouse.io/canonical/jobs/456789")
        self.assertIsNotNone(res)
        self.assertIn("Kernel Engineer", res)
        self.assertIn("eBPF", res)


if __name__ == "__main__":
    unittest.main()
