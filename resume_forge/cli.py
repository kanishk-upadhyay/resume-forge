"""Resume Forge Command Line Interface (CLI)."""

import argparse
import sys
import os
import json
from pathlib import Path

from .core.parser import LatexResumeParser
from .core.exporter import ResumeExporter
from .core.compiler import ResumeCompiler
from .core.ats import ATSAnalyzer
from .core.schema import ResumeData
from .core.variants import VariantManager


def load_resume(input_path: str) -> ResumeData:
    path = Path(input_path)
    if not path.exists():
        print(f"Error: File not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    content = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".json":
        return ResumeData.from_json(content)
    elif path.suffix.lower() == ".tex":
        parser = LatexResumeParser(content)
        return parser.parse()
    else:
        # Try JSON first, fallback to LaTeX parser
        try:
            return ResumeData.from_json(content)
        except Exception:
            parser = LatexResumeParser(content)
            return parser.parse()


def cmd_parse(args):
    """Parses a LaTeX resume into JSON Resume."""
    resume_data = load_resume(args.input)
    json_out = resume_data.to_json(indent=2)
    
    if args.output:
        out_p = Path(args.output)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        out_p.write_text(json_out, encoding="utf-8")
        print(f"✓ Parsed '{args.input}' -> '{args.output}' ({len(resume_data.work)} jobs, {len(resume_data.projects)} projects, {len(resume_data.skills)} skill categories)")
    else:
        print(json_out)


def cmd_compile(args):
    """Compiles LaTeX or JSON resume to PDF in-house without Overleaf."""
    resume_data = load_resume(args.input)
    compiler = ResumeCompiler()
    out_pdf = args.output or "resume.pdf"

    print(f"Compiling '{args.input}' to '{out_pdf}' in-house...")

    if args.method == "tectonic" or (args.input.endswith(".tex") and args.method == "auto" and compiler.tectonic_bin):
        # Try raw LaTeX compilation
        raw_tex = Path(args.input).read_text(encoding="utf-8") if args.input.endswith(".tex") else ResumeExporter(resume_data).to_latex()
        success, msg = compiler.compile_latex_to_pdf(raw_tex, out_pdf)
        if success:
            print(f"✓ PDF compiled successfully via Tectonic: {out_pdf}")
            return

    # Default robust engine: In-house headless Chrome
    success = compiler.compile_resume(
        data=resume_data,
        output_pdf_path=out_pdf,
        font_size_pt=args.font_size,
        line_height=args.line_height,
        margin_in=args.margin
    )

    if success:
        print(f"✓ Single-page PDF compiled successfully in-house: {out_pdf}")
    else:
        print(f"✗ Failed to compile PDF. Ensure Google Chrome is installed.", file=sys.stderr)
        sys.exit(1)


def cmd_export(args):
    """Exports resume into specified format (tex, json, html, md)."""
    resume_data = load_resume(args.input)
    exporter = ResumeExporter(resume_data)

    fmt = args.format.lower()
    if fmt == "tex" or fmt == "latex":
        out_content = exporter.to_latex()
    elif fmt == "json":
        out_content = resume_data.to_json(indent=2)
    elif fmt == "html":
        out_content = exporter.to_html()
    elif fmt == "md" or fmt == "markdown":
        out_content = exporter.to_markdown()
    else:
        print(f"Error: Unknown format '{fmt}'. Choose from: tex, json, html, md", file=sys.stderr)
        sys.exit(1)

    if args.output:
        out_p = Path(args.output)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        out_p.write_text(out_content, encoding="utf-8")
        print(f"✓ Exported {fmt.upper()} to '{args.output}'")
    else:
        print(out_content)


def cmd_audit(args):
    """Runs ATS audit and single-page budget report."""
    resume_data = load_resume(args.input)
    analyzer = ATSAnalyzer(resume_data)

    jd_text = ""
    if args.jd:
        jd_p = Path(args.jd)
        if jd_p.exists():
            jd_text = jd_p.read_text(encoding="utf-8")
        else:
            jd_text = args.jd

    report = analyzer.analyze(job_description=jd_text)

    print("\n" + "=" * 55)
    print(f"  RESUME FORGE - ATS & LAYOUT AUDIT: {resume_data.basics.name or 'Candidate'}")
    print("=" * 55)
    print(f"ATS Health Score    : {report['score']} / 100")
    print(f"Page Budget         : {report['page_budget_percent']}% ({report['page_status']})")
    print(f"Estimated Content   : ~{report['estimated_lines']} lines")
    
    print("\n[+] Strengths:")
    for s in report['strengths']:
        print(f"  ✓ {s}")

    if report['suggestions']:
        print("\n[!] Recommendations:")
        for sug in report['suggestions']:
            print(f"  • {sug}")

    if report['matched_keywords']:
        print(f"\n[✓] Matched JD Keywords: {', '.join(report['matched_keywords'])}")
    if report['missing_keywords']:
        print(f"[?] Missing Target Keywords: {', '.join(report['missing_keywords'])}")

    print("=" * 55 + "\n")


def cmd_serve(args):
    """Starts the in-house Web Studio server."""
    from .web.server import run_server
    run_server(port=args.port, open_browser=not args.no_open)


def cmd_variant(args):
    """Manages tailored resume variants."""
    vm = VariantManager()
    sub = args.variant_cmd

    if sub == "list":
        variants = vm.list_variants()
        if not variants:
            print("No variants found in 'variants/' directory.")
            return
        print(f"\nAvailable Resume Variants ({len(variants)}):")
        for v in variants:
            print(f"  • {v['name']} ({v['type'].upper()}, {v['size']} bytes) -> {v['path']}")
        print("")

    elif sub == "create":
        dest = vm.create_variant(args.name, args.source)
        print(f"✓ Created variant '{args.name}' from '{args.source}' -> {dest}")

    elif sub == "diff":
        diff_output = vm.diff_variants(args.v1, args.v2)
        if not diff_output:
            print(f"Variants '{args.v1}' and '{args.v2}' are identical.")
        else:
            print(diff_output)

    elif sub == "compile":
        out = args.output or f"{args.name}_resume.pdf"
        success = vm.compile_variant(args.name, output_pdf=out)
        if success:
            print(f"✓ Variant '{args.name}' compiled successfully to '{out}'")
        else:
            print(f"✗ Failed to compile variant '{args.name}'", file=sys.stderr)
            sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        prog="resume-forge",
        description="Resume Forge: In-House LaTeX Resume Parser, Studio & Single-Page PDF Compiler"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # parse
    p_parse = subparsers.add_parser("parse", help="Parse LaTeX resume into JSON Resume")
    p_parse.add_argument("input", help="Path to input .tex file")
    p_parse.add_argument("-o", "--output", help="Output .json path (stdout if omitted)")
    p_parse.set_defaults(func=cmd_parse)

    # compile
    p_compile = subparsers.add_parser("compile", help="Compile .tex or .json to single-page PDF in-house")
    p_compile.add_argument("input", help="Path to input .tex or .json resume")
    p_compile.add_argument("-o", "--output", default="resume.pdf", help="Output PDF file path (default: resume.pdf)")
    p_compile.add_argument("--method", choices=["auto", "chrome", "tectonic"], default="auto", help="Compiler engine")
    p_compile.add_argument("--font-size", type=float, default=10.0, help="Base font size in pt (default: 10.0)")
    p_compile.add_argument("--line-height", type=float, default=1.25, help="Line height multiplier (default: 1.25)")
    p_compile.add_argument("--margin", type=float, default=0.4, help="Page margin in inches (default: 0.4)")
    p_compile.set_defaults(func=cmd_compile)

    # export
    p_export = subparsers.add_parser("export", help="Convert resume between formats (tex, json, html, md)")
    p_export.add_argument("input", help="Input file path")
    p_export.add_argument("-f", "--format", choices=["tex", "latex", "json", "html", "md", "markdown"], required=True)
    p_export.add_argument("-o", "--output", help="Output file path (stdout if omitted)")
    p_export.set_defaults(func=cmd_export)

    # audit
    p_audit = subparsers.add_parser("audit", help="Run ATS and single-page budget inspection")
    p_audit.add_argument("input", help="Path to resume file (.tex or .json)")
    p_audit.add_argument("--jd", help="Target job description text or file path")
    p_audit.set_defaults(func=cmd_audit)

    # serve
    p_serve = subparsers.add_parser("serve", help="Launch interactive in-house Web Studio (Reactive Resume style)")
    p_serve.add_argument("--port", type=int, default=8080, help="Port to bind server (default: 8080)")
    p_serve.add_argument("--no-open", action="store_true", help="Do not open browser automatically")
    p_serve.set_defaults(func=cmd_serve)

    # variant
    p_var = subparsers.add_parser("variant", help="Manage and diff tailored resume variants")
    var_sub = p_var.add_subparsers(dest="variant_cmd", required=True)

    var_list = var_sub.add_parser("list", help="List all resume variants")
    var_list.set_defaults(func=cmd_variant)

    var_create = var_sub.add_parser("create", help="Create a new variant from an existing resume")
    var_create.add_argument("name", help="Name of new variant (e.g. backend_python)")
    var_create.add_argument("--source", required=True, help="Source .tex or .json file")
    var_create.set_defaults(func=cmd_variant)

    var_diff = var_sub.add_parser("diff", help="Diff two variants")
    var_diff.add_argument("v1", help="First variant name")
    var_diff.add_argument("v2", help="Second variant name")
    var_diff.set_defaults(func=cmd_variant)

    var_compile = var_sub.add_parser("compile", help="Compile a variant to single-page PDF")
    var_compile.add_argument("name", help="Variant name to compile")
    var_compile.add_argument("-o", "--output", help="Output PDF path")
    var_compile.set_defaults(func=cmd_variant)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
