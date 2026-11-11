"""Unit tests for the ResumeForge local Web Studio request handler (in-memory, no socket required)."""

import unittest
import json
from io import BytesIO
from unittest.mock import MagicMock, patch
from pathlib import Path

from resume_forge.web.server import StudioRequestHandler


class DummyStudioHandler(StudioRequestHandler):
    """Subclass that bypasses TCP socket init for pure in-memory testing."""

    def __init__(self):
        self.rfile = BytesIO()
        self.wfile = BytesIO()
        self.headers = {}
        self.path = ""
        self._response_status = None
        self._response_headers = {}

    def send_response(self, code, message=None):
        self._response_status = code

    def send_header(self, keyword, value):
        self._response_headers[keyword] = value

    def end_headers(self):
        pass

    def send_error(self, code, message=None, explain=None):
        self._response_status = code
        self.wfile.write(json.dumps({"error": message or "Error"}).encode("utf-8"))


class TestStudioServer(unittest.TestCase):

    def test_get_sample_endpoint(self):
        handler = DummyStudioHandler()
        handler.path = "/api/sample"
        handler.do_GET()

        self.assertEqual(handler._response_status, 200)
        resp_data = json.loads(handler.wfile.getvalue().decode("utf-8"))
        self.assertIn("latex", resp_data)
        self.assertIn("resume", resp_data)
        self.assertIn("Kanishk", resp_data["resume"]["basics"]["name"])

    def test_post_parse_endpoint(self):
        sample_tex = r"""
        \documentclass{article}
        \begin{document}
        \textbf{\Huge John Doe} \\
        john@example.com
        \section{Experience}
        \resumeSubheading{Software Engineer}{2024}{Tech Corp}{San Francisco}
        \resumeItemListStart
        \resumeItem{Built cloud services}
        \resumeItemListEnd
        \end{document}
        """
        payload = json.dumps({"latex": sample_tex}).encode("utf-8")
        handler = DummyStudioHandler()
        handler.path = "/api/parse"
        handler.headers = {"Content-Length": str(len(payload))}
        handler.rfile = BytesIO(payload)

        handler.do_POST()

        self.assertEqual(handler._response_status, 200)
        resp_data = json.loads(handler.wfile.getvalue().decode("utf-8"))
        self.assertEqual(resp_data["resume"]["basics"]["name"], "John Doe")
        self.assertEqual(resp_data["resume"]["basics"]["email"], "john@example.com")
        self.assertEqual(len(resp_data["resume"]["work"]), 1)

    def test_post_generate_tex_endpoint(self):
        resume_obj = {
            "basics": {"name": "Alice Smith", "email": "alice@example.com"},
            "work": [{"name": "Innovate Co", "position": "Lead Architect", "highlights": ["Designed architecture"]}]
        }
        payload = json.dumps({"resume": resume_obj}).encode("utf-8")
        handler = DummyStudioHandler()
        handler.path = "/api/generate-tex"
        handler.headers = {"Content-Length": str(len(payload))}
        handler.rfile = BytesIO(payload)

        handler.do_POST()

        self.assertEqual(handler._response_status, 200)
        resp_data = json.loads(handler.wfile.getvalue().decode("utf-8"))
        self.assertIn(r"\begin{document}", resp_data["latex"])
        self.assertIn("Alice Smith", resp_data["latex"])

    def test_post_audit_endpoint(self):
        resume_obj = {
            "basics": {"name": "Bob Taylor", "email": "bob@example.com", "phone": "1234567890"},
            "work": [{"name": "Acme", "position": "Engineer", "highlights": ["Engineered distributed cache reducing latency by 40%"]}],
            "skills": [{"name": "Languages", "keywords": ["Go", "Python"]}]
        }
        payload = json.dumps({"resume": resume_obj, "job_description": "Go engineer needed"}).encode("utf-8")
        handler = DummyStudioHandler()
        handler.path = "/api/audit"
        handler.headers = {"Content-Length": str(len(payload))}
        handler.rfile = BytesIO(payload)

        handler.do_POST()

        self.assertEqual(handler._response_status, 200)
        resp_data = json.loads(handler.wfile.getvalue().decode("utf-8"))
        self.assertGreaterEqual(resp_data["score"], 80)
        self.assertIn("go", [k.lower() for k in resp_data["matched_keywords"]])

    def test_post_compile_pdf_endpoint(self):
        resume_obj = {
            "basics": {"name": "Carol Danvers", "email": "carol@example.com"},
            "work": [{"name": "Starforce", "position": "Pilot", "highlights": ["Led flight operations"]}],
            "education": [{"institution": "Air Force Academy", "study_type": "B.S."}],
            "skills": [{"name": "Abilities", "keywords": ["Flight", "Navigation"]}]
        }
        payload = json.dumps({
            "resume": resume_obj,
            "font_size": 9.5,
            "line_height": 1.2,
            "margin": 0.4
        }).encode("utf-8")
        handler = DummyStudioHandler()
        handler.path = "/api/compile-pdf"
        handler.headers = {"Content-Length": str(len(payload))}
        handler.rfile = BytesIO(payload)

        handler.do_POST()

        self.assertEqual(handler._response_status, 200)
        resp_data = json.loads(handler.wfile.getvalue().decode("utf-8"))
        self.assertTrue(resp_data["success"])
        self.assertIn("pdf_url", resp_data)

    def test_post_parse_json_direct(self):
        """Verify server /api/parse handles raw JSON resume payload seamlessly."""
        json_resume = {
            "basics": {"name": "Grace Hopper", "email": "hopper@navy.mil"},
            "work": [{"name": "US Navy", "position": "Rear Admiral", "startDate": "1943", "endDate": "1986", "highlights": ["Pioneered compilers"]}]
        }
        payload = json.dumps({"raw": json.dumps(json_resume)}).encode("utf-8")
        handler = DummyStudioHandler()
        handler.path = "/api/parse"
        handler.headers = {"Content-Length": str(len(payload))}
        handler.rfile = BytesIO(payload)

        handler.do_POST()

        self.assertEqual(handler._response_status, 200)
        resp_data = json.loads(handler.wfile.getvalue().decode("utf-8"))
        self.assertEqual(resp_data["resume"]["basics"]["name"], "Grace Hopper")
        self.assertEqual(len(resp_data["resume"]["work"]), 1)
        self.assertEqual(resp_data["resume"]["work"][0]["start_date"], "1943")

    def test_get_templates_endpoint(self):
        handler = DummyStudioHandler()
        handler.path = "/api/templates"
        handler.do_GET()

        self.assertEqual(handler._response_status, 200)
        resp_data = json.loads(handler.wfile.getvalue().decode("utf-8"))
        self.assertIn("templates", resp_data)
        tmpl_names = [t["name"] for t in resp_data["templates"]]
        self.assertIn("harvard", tmpl_names)
        self.assertIn("jakes", tmpl_names)
        self.assertIn("minimalist", tmpl_names)
        self.assertIn("quant", tmpl_names)
        self.assertIn("awesome", tmpl_names)
        self.assertIn("academic", tmpl_names)

    def test_get_sample_harvard_endpoint(self):
        handler = DummyStudioHandler()
        handler.path = "/api/sample?template=harvard"
        handler.do_GET()

        self.assertEqual(handler._response_status, 200)
        resp_data = json.loads(handler.wfile.getvalue().decode("utf-8"))
        self.assertIn("latex", resp_data)
        self.assertIn("harvard", resp_data["latex"].lower())

    def test_404_not_found(self):
        handler = DummyStudioHandler()
        handler.path = "/api/nonexistent_endpoint"
        handler.do_POST()

        self.assertEqual(handler._response_status, 404)


if __name__ == "__main__":
    unittest.main()
