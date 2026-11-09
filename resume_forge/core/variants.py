"""Resume Variant Manager: Manage, compare, and compile multiple resume flavors."""

import shutil
import difflib
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from .parser import LatexResumeParser
from .compiler import ResumeCompiler
from .schema import ResumeData


class VariantManager:
    """Manages tailored resume variants (e.g. cern_fullstack, systems_lowlevel)."""

    def __init__(self, base_dir: Optional[str] = None):
        self.base_dir = Path(base_dir).resolve() if base_dir else Path.cwd()
        self.variants_dir = self.base_dir / "variants"
        self.variants_dir.mkdir(parents=True, exist_ok=True)

    def list_variants(self) -> List[Dict[str, str]]:
        """Lists all available resume variants (.tex or .json)."""
        variants = []
        for p in sorted(self.variants_dir.glob("*.*")):
            if p.suffix.lower() in (".tex", ".json"):
                variants.append({
                    "name": p.stem,
                    "filename": p.name,
                    "type": p.suffix.lower().lstrip("."),
                    "path": str(p),
                    "size": p.stat().st_size
                })
        return variants

    def create_variant(self, name: str, source_path: str) -> Path:
        """Creates a new variant by copying an existing resume file."""
        src = Path(source_path).resolve()
        if not src.exists():
            raise FileNotFoundError(f"Source resume file not found: {source_path}")

        safe_name = Path(name).name
        dest = self.variants_dir / f"{safe_name}{src.suffix}"
        shutil.copy(src, dest)
        return dest

    def get_variant_path(self, name: str) -> Optional[Path]:
        """Finds the path to a variant by name."""
        safe_name = Path(name).name
        for ext in (".tex", ".json"):
            candidate = self.variants_dir / f"{safe_name}{ext}"
            if candidate.exists():
                return candidate
        return None

    def diff_variants(self, name1: str, name2: str) -> str:
        """Computes a unified diff between two resume variants."""
        p1 = self.get_variant_path(name1)
        p2 = self.get_variant_path(name2)
        if not p1 or not p2:
            raise FileNotFoundError(f"One or both variants not found: '{name1}', '{name2}'")

        text1 = p1.read_text(encoding="utf-8").splitlines(keepends=True)
        text2 = p2.read_text(encoding="utf-8").splitlines(keepends=True)

        diff = difflib.unified_diff(
            text1, text2,
            fromfile=f"variant:{name1}",
            tofile=f"variant:{name2}"
        )
        return "".join(diff)

    def compile_variant(self, name: str, output_pdf: Optional[str] = None) -> bool:
        """Compiles a specific variant to PDF."""
        p = self.get_variant_path(name)
        if not p:
            raise FileNotFoundError(f"Variant '{name}' not found.")

        compiler = ResumeCompiler()
        content = p.read_text(encoding="utf-8")
        if p.suffix.lower() == ".json":
            data = ResumeData.from_json(content)
        else:
            parser = LatexResumeParser(content)
            data = parser.parse()

        out = output_pdf or str(self.base_dir / f"{name}_resume.pdf")
        return compiler.compile_resume(data, out)
