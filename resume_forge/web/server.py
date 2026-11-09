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
from ..core.schema import ResumeData

STATIC_DIR = Path(__file__).parent / "static"
TEMPLATES_DIR = Path(__file__).parent.parent / "templates"


class StudioRequestHandler(http.server.SimpleHTTPRequestHandler):
    """Handles Web Studio API endpoints and serves static frontend assets."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(STATIC_DIR), **kwargs)

    def do_GET(self):
        parsed_url = urllib.parse.urlparse(self.path)
        if parsed_url.path == "/api/sample":
            self._handle_get_sample()
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

    def _handle_get_sample(self):
        cern_sample = TEMPLATES_DIR / "cern_fullstack.tex"
        if cern_sample.exists():
            tex = cern_sample.read_text(encoding="utf-8")
            parser = LatexResumeParser(tex)
            data = parser.parse()
            self._send_json({"latex": tex, "resume": data.to_dict()})
        else:
            self._send_json({"error": "Sample template not found"}, 404)

    def _handle_parse(self, req_data: Dict[str, Any]):
        raw_tex = req_data.get("latex", "")
        if not raw_tex:
            self._send_json({"error": "No LaTeX content provided"}, 400)
            return

        parser = LatexResumeParser(raw_tex)
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
        data = ResumeData.from_dict(resume_dict)
        exporter = ResumeExporter(data)
        tex = exporter.to_latex()
        self._send_json({"latex": tex})

    def _handle_audit(self, req_data: Dict[str, Any]):
        resume_dict = req_data.get("resume", {})
        jd = req_data.get("job_description", "")
        data = ResumeData.from_dict(resume_dict)
        analyzer = ATSAnalyzer(data)
        report = analyzer.analyze(job_description=jd)
        self._send_json(report)

    def _handle_compile_pdf(self, req_data: Dict[str, Any]):
        resume_dict = req_data.get("resume", {})
        data = ResumeData.from_dict(resume_dict)
        font_size = float(req_data.get("font_size", 10.0))
        line_height = float(req_data.get("line_height", 1.25))
        margin = float(req_data.get("margin", 0.4))

        compiler = ResumeCompiler()
        output_pdf = STATIC_DIR / "latest_resume.pdf"
        success = compiler.compile_resume(
            data=data,
            output_pdf_path=str(output_pdf),
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
