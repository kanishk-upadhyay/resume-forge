"""Lightweight zero-dependency HTTP server powering the In-House Web Studio."""

import http.server
import json
import socketserver
import urllib.parse
import webbrowser
import os
from pathlib import Path
from typing import Dict, Any

from ..core.parser import LatexResumeParser
from ..core.exporter import ResumeExporter
from ..core.compiler import ResumeCompiler
from ..core.ats import ATSAnalyzer
from ..core.schema import ResumeData, Basics, Location, Profile, EducationItem, WorkItem, SkillItem
from ..core.letter import CoverLetterData
from ..core.diff import ResumeDiffEngine
from ..core.fetcher import fetch_job_description
from ..templates import TemplateRegistry

STATIC_DIR = Path(__file__).parent / "static"
TEMPLATES_DIR = Path(__file__).parent.parent / "templates"


class StudioRequestHandler(http.server.SimpleHTTPRequestHandler):
    """Handles Web Studio API endpoints and serves static frontend assets."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(STATIC_DIR), **kwargs)

    def do_GET(self):
        parsed_url = urllib.parse.urlparse(self.path)
        if parsed_url.path == "/api/sample":
            query_params = urllib.parse.parse_qs(parsed_url.query)
            template_name = query_params.get("template", ["cern"])[0]
            self._handle_get_sample(template_name)
        elif parsed_url.path == "/api/templates":
            self._send_json({"templates": TemplateRegistry.list_templates()})
        else:
            super().do_GET()

    def do_POST(self):
        parsed_url = urllib.parse.urlparse(self.path)
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode("utf-8") if content_length > 0 else ""

        try:
            req_data = json.loads(body) if body else {}
        except Exception:
            req_data = {"raw": body}

        if parsed_url.path == "/api/parse":
            self._handle_parse(req_data)
        elif parsed_url.path == "/api/generate-tex":
            self._handle_generate_tex(req_data)
        elif parsed_url.path == "/api/compile-pdf":
            self._handle_compile_pdf(req_data)
        elif parsed_url.path == "/api/audit":
            self._handle_audit(req_data)
        elif parsed_url.path == "/api/fetch-jd":
            self._handle_fetch_jd(req_data)
        elif parsed_url.path == "/api/cover-letter":
            self._handle_cover_letter(req_data)
        elif parsed_url.path == "/api/diff":
            self._handle_diff(req_data)
        else:
            self.send_error(404, "Endpoint not found")

    def _send_json(self, data: Any, status: int = 200):
        resp_bytes = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(resp_bytes)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(resp_bytes)

    def _get_generic_sample_data(self) -> ResumeData:
        """Constructs a realistic, generic sample resume data object."""
        return ResumeData(
            basics=Basics(
                name="Alex Morgan",
                email="alex.morgan@example.com",
                phone="+1 (555) 019-2834",
                location=Location(city="San Francisco, CA"),
                url="https://alexmorgan.dev",
                summary="Full-stack and systems engineer specialized in distributed systems, high-concurrency microservices, and reliable cloud architectures.",
                profiles=[
                    Profile(network="GitHub", url="https://github.com/alexmorgan"),
                    Profile(network="LinkedIn", url="https://linkedin.com/in/alexmorgan")
                ]
            ),
            education=[
                EducationItem(
                    institution="University of California, Berkeley",
                    study_type="Bachelor of Science",
                    area="Computer Science",
                    start_date="2020",
                    end_date="2024",
                    highlights=["Graduated with High Distinction (GPA: 3.9/4.0)"]
                )
            ],
            work=[
                WorkItem(
                    name="CloudScale Technologies",
                    position="Software Engineer Intern",
                    location="San Francisco, CA",
                    start_date="Jun 2023",
                    end_date="Dec 2023",
                    highlights=[
                        "Engineered high-throughput event streaming services handling 100k+ messages/sec using Go and Kafka.",
                        "Optimized relational query execution plans, reducing p99 latency from 180ms to 42ms.",
                        "Architected automated CI/CD canary release pipelines with zero deployment downtime."
                    ]
                )
            ],
            skills=[
                SkillItem(category="Languages", keywords=["Go", "Python", "Rust", "TypeScript", "SQL"]),
                SkillItem(category="Infrastructure", keywords=["Kubernetes", "Docker", "AWS", "Terraform", "PostgreSQL"])
            ]
        )

    def _handle_get_sample(self, template_name: str = "cern"):
        tmpl = TemplateRegistry.get(template_name)
        sample_path = TEMPLATES_DIR / f"{tmpl.name}.tex"
        if not sample_path.exists():
            sample_path = TEMPLATES_DIR / "cern_fullstack.tex"

        if sample_path.exists():
            tex = sample_path.read_text(encoding="utf-8")
            parser = LatexResumeParser(tex)
            data = parser.parse()
            self._send_json({"latex": tex, "resume": data.to_dict(), "template": tmpl.name})
        else:
            sample_data = self._get_generic_sample_data()
            tex = tmpl.render_latex(sample_data)
            self._send_json({"latex": tex, "resume": sample_data.to_dict(), "template": tmpl.name})

    def _handle_parse(self, req_data: Dict[str, Any]):
        raw_input = req_data.get("latex") or req_data.get("raw") or ""
        if not raw_input:
            self._send_json({"error": "No content provided"}, 400)
            return

        resume_data = None
        trimmed = raw_input.strip()
        if trimmed.startswith("{"):
            try:
                resume_data = ResumeData.from_json(trimmed)
            except Exception:
                resume_data = None

        if resume_data is None:
            parser = LatexResumeParser(raw_input)
            resume_data = parser.parse()

        self._send_json({
            "resume": resume_data.to_dict(),
            "summary": {
                "name": resume_data.basics.name,
                "jobs": len(resume_data.work),
                "projects": len(resume_data.projects),
                "skills": len(resume_data.skills)
            }
        })

    def _handle_generate_tex(self, req_data: Dict[str, Any]):
        resume_dict = req_data.get("resume", {})
        template = req_data.get("template", "cern")
        data = ResumeData.from_dict(resume_dict)
        exporter = ResumeExporter(data)
        tex = exporter.to_latex(template=template)
        self._send_json({"latex": tex, "template": template})

    def _handle_audit(self, req_data: Dict[str, Any]):
        resume_dict = req_data.get("resume", {})
        jd = req_data.get("job_description", "")
        data = ResumeData.from_dict(resume_dict)
        analyzer = ATSAnalyzer(data)
        report = analyzer.analyze(job_description=jd)
        self._send_json(report)

    def _handle_fetch_jd(self, req_data: Dict[str, Any]):
        url = req_data.get("url", "").strip()
        if not url:
            self._send_json({"error": "No URL provided"}, 400)
            return
        try:
            text = fetch_job_description(url)
            self._send_json({"text": text, "length": len(text)})
        except Exception as e:
            self._send_json({"error": str(e)}, 500)

    def _handle_cover_letter(self, req_data: Dict[str, Any]):
        resume_dict = req_data.get("resume", {})
        company = req_data.get("company", "Target Company")
        role = req_data.get("role", "Software Engineer")
        template = req_data.get("template", "cern")
        data = ResumeData.from_dict(resume_dict)
        letter_data = CoverLetterData.from_resume(data, company=company, role=role)
        tmpl = TemplateRegistry.get(template)
        tex = tmpl.render_cover_letter_latex(letter_data)
        html = tmpl.render_cover_letter_html(letter_data)
        self._send_json({
            "data": letter_data.to_dict(),
            "latex": tex,
            "html": html,
            "template": template
        })

    def _handle_diff(self, req_data: Dict[str, Any]):
        r1_dict = req_data.get("old_resume", {})
        r2_dict = req_data.get("new_resume", {})
        r1 = ResumeData.from_dict(r1_dict)
        r2 = ResumeData.from_dict(r2_dict)
        diff_res = ResumeDiffEngine.diff(r1, r2)
        self._send_json(diff_res.to_dict())

    def _handle_compile_pdf(self, req_data: Dict[str, Any]):
        resume_dict = req_data.get("resume", {})
        template = req_data.get("template", "cern")
        doc_type = req_data.get("doc_type", "resume")
        data = ResumeData.from_dict(resume_dict)
        font_size = float(req_data.get("font_size", 10.0))
        line_height = float(req_data.get("line_height", 1.25))
        margin = float(req_data.get("margin", 0.4))

        compiler = ResumeCompiler()
        output_pdf = STATIC_DIR / "latest_resume.pdf"

        if doc_type == "cover_letter":
            letter_dict = req_data.get("letter")
            if letter_dict:
                letter = CoverLetterData.from_dict(letter_dict)
            else:
                company = req_data.get("company", "Target Company")
                role = req_data.get("role", "Software Engineer")
                letter = CoverLetterData.from_resume(data, company=company, role=role)
            success = compiler.compile_cover_letter(
                data=letter,
                output_pdf_path=str(output_pdf),
                template=template
            )
        else:
            success = compiler.compile_resume(
                data=data,
                output_pdf_path=str(output_pdf),
                template=template,
                font_size_pt=font_size,
                line_height=line_height,
                margin_in=margin,
                auto_fit=True
            )

        if success and output_pdf.exists():
            pages = compiler.get_pdf_page_count(str(output_pdf))
            self._send_json({
                "success": True,
                "pdf_url": "/latest_resume.pdf",
                "pages": pages,
                "message": f"Single-page PDF compiled successfully in-house ({pages} page)!"
            })
        else:
            self._send_json({
                "success": False,
                "error": "PDF compilation failed. Verify Google Chrome is installed."
            }, 500)


def run_server(port: int = 8080, open_browser: bool = True):
    """Starts local server and opens browser."""
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", port), StudioRequestHandler) as httpd:
        url = f"http://localhost:{port}"
        print(f"\n=======================================================")
        print(f"  RESUME FORGE - In-House Reactive Resume Studio")
        print(f"  Running locally at: {url}")
        print(f"  Zero cloud dependencies | No sign-in required")
        print(f"=======================================================\n")
        if open_browser:
            webbrowser.open(url)
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down Resume Forge studio.")
