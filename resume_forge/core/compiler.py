"""In-house PDF Compiler: Compiles LaTeX and HTML resumes directly on macOS without Overleaf."""

import re
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Optional, Tuple
from .schema import ResumeData
from .exporter import ResumeExporter


class ResumeCompiler:
    """Compiles resumes to PDF using headless Chrome or local Tectonic/pdflatex."""

    CHROME_PATHS = [
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Chromium.app/Contents/MacOS/Chromium",
        "google-chrome",
        "chromium",
        "chrome"
    ]

    def __init__(self):
        self.chrome_bin = self._find_chrome()
        self.tectonic_bin = shutil.which("tectonic")
        self.pdflatex_bin = shutil.which("pdflatex")

    def _find_chrome(self) -> Optional[str]:
        for path in self.CHROME_PATHS:
            if os.path.exists(path) and os.access(path, os.X_OK):
                return path
            which_res = shutil.which(path)
            if which_res:
                return which_res
        return None

    def compile_html_to_pdf(
        self,
        html_content: str,
        output_pdf_path: str,
        margin_in: float = 0.4
    ) -> bool:
        """Uses headless Chrome to render HTML into a single-page PDF."""
        if not self.chrome_bin:
            raise RuntimeError(
                "Google Chrome or Chromium is required for HTML-to-PDF rendering. "
                "Please ensure Chrome is installed at /Applications/Google Chrome.app."
            )

        output_path = Path(output_pdf_path).resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False, encoding="utf-8") as f:
            f.write(html_content)
            temp_html = f.name

        try:
            cmd = [
                self.chrome_bin,
                "--headless=new",
                "--disable-gpu",
                "--no-sandbox",
                "--user-data-dir=/tmp/chrome-resume-forge",
                "--crash-dumps-dir=/tmp",
                "--no-pdf-header-footer",
                f"--print-to-pdf={str(output_path)}",
                f"file://{temp_html}"
            ]
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30)
            if not output_path.exists() or output_path.stat().st_size == 0:
                # Try fallback flag without =new
                cmd[1] = "--headless"
                res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30)
                
            return output_path.exists() and output_path.stat().st_size > 0
        finally:
            if os.path.exists(temp_html):
                os.remove(temp_html)

    def compile_latex_to_pdf(
        self,
        latex_content: str,
        output_pdf_path: str
    ) -> Tuple[bool, str]:
        """Compiles raw LaTeX to PDF using local tectonic or pdflatex if installed."""
        output_path = Path(output_pdf_path).resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with tempfile.TemporaryDirectory() as tmpdir:
            tex_file = Path(tmpdir) / "resume.tex"
            tex_file.write_text(latex_content, encoding="utf-8")

            # Try Tectonic first (modern, self-contained)
            if self.tectonic_bin:
                cmd = [self.tectonic_bin, str(tex_file), "-o", str(tmpdir)]
                res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                tmp_pdf = Path(tmpdir) / "resume.pdf"
                if tmp_pdf.exists():
                    shutil.copy(tmp_pdf, output_path)
                    return True, "Compiled successfully with Tectonic."
                return False, f"Tectonic error:\n{res.stderr or res.stdout}"

            # Try pdflatex
            if self.pdflatex_bin:
                cmd = [self.pdflatex_bin, "-interaction=nonstopmode", "-output-directory", tmpdir, str(tex_file)]
                res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                tmp_pdf = Path(tmpdir) / "resume.pdf"
                if tmp_pdf.exists():
                    shutil.copy(tmp_pdf, output_path)
                    return True, "Compiled successfully with pdflatex."
                return False, f"pdflatex error:\n{res.stderr or res.stdout}"

        return False, "Neither Tectonic nor pdflatex is installed on this machine."

    @staticmethod
    def get_pdf_page_count(pdf_path: str) -> int:
        """Reads generated PDF file and returns exact page count."""
        p = Path(pdf_path)
        if not p.exists():
            return 0
        try:
            data = p.read_bytes()
            pages = re.findall(rb'/Type\s*/Page\b', data)
            return len(pages)
        except Exception:
            return 0

    def compile_resume(
        self,
        data: ResumeData,
        output_pdf_path: str,
        font_size_pt: float = 10.0,
        line_height: float = 1.25,
        margin_in: float = 0.4,
        auto_fit: bool = True
    ) -> bool:
        """Generates single-page PDF directly using the in-house Chrome engine.
        
        If auto_fit=True and content overflows onto page 2, progressively scales
        font size and margins to enforce a strict single-page fit.
        """
        exporter = ResumeExporter(data)
        html = exporter.to_html(font_size_pt=font_size_pt, line_height=line_height, margin_in=margin_in)
        success = self.compile_html_to_pdf(html, output_pdf_path, margin_in=margin_in)
        if not success:
            return False

        if auto_fit:
            pages = self.get_pdf_page_count(output_pdf_path)
            if pages > 1:
                # Progressive compression tiers to achieve single-page fit
                tiers = [
                    (9.5, 1.20, 0.35),
                    (9.0, 1.15, 0.30),
                    (8.5, 1.10, 0.28),
                    (8.0, 1.05, 0.25)
                ]
                for f_pt, lh, m_in in tiers:
                    html_squeeze = exporter.to_html(font_size_pt=f_pt, line_height=lh, margin_in=m_in)
                    self.compile_html_to_pdf(html_squeeze, output_pdf_path, margin_in=m_in)
                    if self.get_pdf_page_count(output_pdf_path) <= 1:
                        break

        return True
