"""In-house PDF Compiler: Compiles LaTeX and HTML resumes directly on macOS without Overleaf."""

import re
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Optional, Tuple, Union, Dict, TYPE_CHECKING
from .schema import ResumeData
from .exporter import ResumeExporter

if TYPE_CHECKING:
    from .letter import CoverLetterData


class ResumeCompiler:
    """Compiles resumes to PDF using headless Chrome or local Tectonic/pdflatex."""

    CHROME_PATHS = [
        # macOS system paths
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Chromium.app/Contents/MacOS/Chromium",
        "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
        "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
        "/Applications/Arc.app/Contents/MacOS/Arc",
        # macOS user-level paths
        os.path.expanduser("~/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"),
        os.path.expanduser("~/Applications/Chromium.app/Contents/MacOS/Chromium"),
        os.path.expanduser("~/Applications/Brave Browser.app/Contents/MacOS/Brave Browser"),
        os.path.expanduser("~/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge"),
        # Linux standard paths & binaries
        "/usr/bin/google-chrome",
        "/usr/bin/google-chrome-stable",
        "/usr/bin/chromium",
        "/usr/bin/chromium-browser",
        "/usr/bin/brave-browser",
        "/usr/bin/microsoft-edge",
        "google-chrome",
        "google-chrome-stable",
        "chromium",
        "chromium-browser",
        "brave-browser",
        "brave",
        "microsoft-edge",
        "msedge",
        "chrome",
        # Windows standard paths
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe",
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
            with tempfile.TemporaryDirectory(prefix="chrome-user-data-") as user_data_dir:
                cmd = [
                    self.chrome_bin,
                    "--headless=new",
                    "--disable-gpu",
                    "--no-sandbox",
                    f"--user-data-dir={user_data_dir}",
                    f"--crash-dumps-dir={user_data_dir}",
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
        """Reads generated PDF file and returns exact page count with stream fallback."""
        p = Path(pdf_path)
        if not p.exists():
            return 0
        try:
            data = p.read_bytes()
            # 1. Direct Page object count
            pages = re.findall(rb'/Type\s*/Page\b', data)
            if pages:
                return len(pages)
            # 2. Check Pages catalog /Count entry (for PDFs with compressed /ObjStm)
            count_match = re.search(rb'/Type\s*/Pages\b[^>]*?/Count\s+(\d+)', data)
            if count_match:
                return int(count_match.group(1))
            count_match2 = re.search(rb'/Count\s+(\d+)[^>]*?/Type\s*/Pages\b', data)
            if count_match2:
                return int(count_match2.group(1))
            return 0
        except Exception:
            return 0

    def compile_resume(
        self,
        data: ResumeData,
        output_pdf_path: str,
        template: str = "cern",
        font_size_pt: Optional[float] = None,
        line_height: Optional[float] = None,
        margin_in: Optional[float] = None,
        auto_fit: bool = True
    ) -> bool:
        """Generates single-page PDF directly using the in-house Chrome engine.
        
        If auto_fit=True and content overflows onto page 2, progressively scales
        font size and margins to enforce a strict single-page fit.
        """
        exporter = ResumeExporter(data)
        html = exporter.to_html(template=template, font_size_pt=font_size_pt, line_height=line_height, margin_in=margin_in)
        effective_margin = margin_in if margin_in is not None else 0.4
        success = self.compile_html_to_pdf(html, output_pdf_path, margin_in=effective_margin)
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
                    html_squeeze = exporter.to_html(template=template, font_size_pt=f_pt, line_height=lh, margin_in=m_in)
                    self.compile_html_to_pdf(html_squeeze, output_pdf_path, margin_in=m_in)
                    if self.get_pdf_page_count(output_pdf_path) <= 1:
                        break

        return True

    def compile_cover_letter(
        self,
        data: Optional["CoverLetterData"] = None,
        output_pdf_path: str = "",
        template: str = "cern",
        font_size_pt: Optional[float] = None,
        line_height: Optional[float] = None,
        margin_in: Optional[float] = None,
        auto_fit: bool = True,
        letter: Optional["CoverLetterData"] = None
    ) -> bool:
        """Generates single-page cover letter PDF using template typography."""
        target_letter = data or letter
        if not target_letter:
            raise ValueError("A CoverLetterData instance must be provided via 'data' or 'letter'.")
        from ..templates import TemplateRegistry
        tmpl = TemplateRegistry.get(template)
        html = tmpl.render_cover_letter_html(
            target_letter,
            font_size_pt=font_size_pt,
            line_height=line_height,
            margin_in=margin_in
        )
        effective_margin = margin_in if margin_in is not None else tmpl.default_margin
        success = self.compile_html_to_pdf(html, output_pdf_path, margin_in=effective_margin)
        if not success:
            return False

        if auto_fit and self.get_pdf_page_count(output_pdf_path) > 1:
            tiers = [
                (9.5, 1.20, 0.35),
                (9.0, 1.15, 0.30),
                (8.5, 1.10, 0.28)
            ]
            for f_pt, lh, m_in in tiers:
                html_sq = tmpl.render_cover_letter_html(data, font_size_pt=f_pt, line_height=lh, margin_in=m_in)
                self.compile_html_to_pdf(html_sq, output_pdf_path, margin_in=m_in)
                if self.get_pdf_page_count(output_pdf_path) <= 1:
                    break

        return True

    def compile_html_to_image(
        self,
        html_content: str,
        output_image_path: str,
        dpi: int = 300
    ) -> bool:
        """Renders HTML into a high-DPI image (PNG, WebP, JPG) using headless Chrome screenshot."""
        if not self.chrome_bin:
            raise RuntimeError(
                "Google Chrome or Chromium is required for image rendering. "
                "Please ensure Chrome is installed."
            )

        output_path = Path(output_image_path).resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)

        scale = max(1.0, dpi / 96.0)
        width_px = int(8.5 * dpi)
        height_px = int(11.0 * dpi)

        with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False, encoding="utf-8") as f:
            f.write(html_content)
            temp_html = f.name

        try:
            with tempfile.TemporaryDirectory(prefix="chrome-img-data-") as user_data_dir:
                cmd = [
                    self.chrome_bin,
                    "--headless=new",
                    "--disable-gpu",
                    "--no-sandbox",
                    f"--user-data-dir={user_data_dir}",
                    f"--crash-dumps-dir={user_data_dir}",
                    f"--window-size={width_px},{height_px}",
                    f"--force-device-scale-factor={scale:.2f}",
                    "--hide-scrollbars",
                    f"--screenshot={str(output_path)}",
                    f"file://{temp_html}"
                ]
                subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30)
                if not output_path.exists() or output_path.stat().st_size == 0:
                    cmd[1] = "--headless"
                    subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30)

                return output_path.exists() and output_path.stat().st_size > 0
        finally:
            if os.path.exists(temp_html):
                os.remove(temp_html)

    def compile_image(
        self,
        data: ResumeData,
        output_image_path: str,
        template: str = "cern",
        dpi: int = 300,
        font_size_pt: Optional[float] = None,
        line_height: Optional[float] = None,
        margin_in: Optional[float] = None
    ) -> bool:
        """Renders resume to a high-DPI image using the selected template."""
        exporter = ResumeExporter(data)
        html = exporter.to_html(template=template, font_size_pt=font_size_pt, line_height=line_height, margin_in=margin_in)
        return self.compile_html_to_image(html, output_image_path, dpi=dpi)

    def compile_all_templates(
        self,
        data: ResumeData,
        output_dir: Union[str, Path],
        prefix: str = "resume",
        fmt: str = "pdf",
        dpi: int = 200,
        auto_fit: bool = True
    ) -> Dict[str, str]:
        """Compiles resume data across all registered templates in batch.
        
        Returns a dictionary mapping template names to generated file paths.
        """
        from ..templates import TemplateRegistry
        out_p = Path(output_dir)
        out_p.mkdir(parents=True, exist_ok=True)
        results = {}
        for tmpl_meta in TemplateRegistry.list_templates():
            t_name = tmpl_meta["name"]
            out_file = out_p / f"{prefix}_{t_name}.{fmt}"
            if fmt in ("png", "webp", "jpg", "jpeg"):
                ok = self.compile_image(data, str(out_file), template=t_name, dpi=dpi)
            else:
                ok = self.compile_resume(data, str(out_file), template=t_name, auto_fit=auto_fit)
            if ok and out_file.exists():
                results[t_name] = str(out_file)
        return results
