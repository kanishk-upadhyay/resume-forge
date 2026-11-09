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
from .core.tailor import BulletTailor
from .core.hunter import JobHunter



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
        margin_in=args.margin,
        auto_fit=not getattr(args, "no_auto_fit", False)
    )

    if success:
        pages = compiler.get_pdf_page_count(out_pdf)
        if pages == 1:
            print(f"✓ Single-page PDF compiled successfully in-house (1 page): {out_pdf}")
        else:
            print(f"✓ PDF compiled successfully ({pages} pages): {out_pdf}")
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


def cmd_tailor(args):
    """Tailors resume bullet points to match a target job description."""
    resume_data = load_resume(args.input)
    
    jd_text = ""
    if args.jd:
        jd_p = Path(args.jd)
        if jd_p.exists():
            jd_text = jd_p.read_text(encoding="utf-8")
        else:
            jd_text = args.jd
    else:
        print("Error: Target job description (--jd) is required for tailoring.", file=sys.stderr)
        sys.exit(1)

    tailor_engine = BulletTailor(resume_data)
    result = tailor_engine.tailor(job_description=jd_text, provider=args.provider)
    suggestions = result.get("suggestions", [])

    print(f"\n=======================================================")
    print(f"  RESUME FORGE - BULLET TAILOR ENGINE ({result.get('provider').upper()})")
    print(f"=======================================================")
    print(f"Target Skills Extracted: {', '.join(result.get('target_skills', []))}")
    print(f"Improvement Suggestions Found: {len(suggestions)}\n")

    accepted = []
    for idx, s in enumerate(suggestions, 1):
        print(f"[{idx}] {s.get('context')}")
        print(f"    - Original : {s.get('original')}")
        print(f"    + Improved : {s.get('improved')}")
        for r in s.get("reasons", []):
            print(f"      • Reason: {r}")

        if args.interactive:
            choice = input("    Apply this rewrite? [y/N/q]: ").strip().lower()
            if choice == "y":
                accepted.append(s)
                print("    ✓ Staged for update.")
            elif choice == "q":
                print("    Exiting interactive review.")
                break
        elif args.apply_all:
            accepted.append(s)

        print("")

    if accepted:
        updated_data = tailor_engine.apply_improvements(accepted)
        if args.output:
            out_p = Path(args.output)
            out_p.parent.mkdir(parents=True, exist_ok=True)
            if out_p.suffix.lower() == ".json":
                out_p.write_text(updated_data.to_json(indent=2), encoding="utf-8")
            else:
                out_p.write_text(ResumeExporter(updated_data).to_latex(), encoding="utf-8")
            print(f"✓ Applied {len(accepted)} improvements -> '{args.output}'")
        else:
            print(f"✓ Applied {len(accepted)} improvements. (Use -o to save to file)")
    else:
        print("No changes applied.")


def cmd_hunt(args):
    """Directly queries official public ATS APIs for verified live openings and pairs with resumes."""
    print(f"Hunting verified live requisitions (Company: {args.company}, Role: '{args.role}', Location: '{args.location}')...")
    hunter = JobHunter(
        company=args.company,
        role=args.role,
        location=args.location,
        grad_year=args.grad_year,
        limit=args.limit,
        compile_resumes=args.compile,
        base_resume_path=args.base_resume,
        output_dir=args.output_dir
    )
    postings = hunter.hunt()

    if args.json:
        print(json.dumps([p.to_dict() for p in postings], indent=2))
        return

    if not postings:
        print("No matching active openings found matching criteria.")
        return

    print(f"\n✓ Found {len(postings)} verified live openings from official ATS APIs:\n")
    for i, p in enumerate(postings, 1):
        print(f"[{i}] {p.company} — {p.title}")
        print(f"    Location:   {p.location}")
        print(f"    Direct URL: {p.url}")
        print(f"    Apply URL:  {p.apply_url}")
        if p.match_rate_percent:
            print(f"    JD Match:   {p.match_rate_percent}% keyword alignment")
        if p.paired_resume_pdf:
            print(f"    Paired PDF: {p.paired_resume_pdf}")
        print("")


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
    p_compile.add_argument("--no-auto-fit", action="store_true", help="Disable automatic single-page font/margin compression")
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

    # tailor
    p_tailor = subparsers.add_parser("tailor", help="Optimize bullet points against a target job description")
    p_tailor.add_argument("input", help="Path to resume file (.tex or .json)")
    p_tailor.add_argument("--jd", required=True, help="Target job description text or file path")
    p_tailor.add_argument("--provider", choices=["rule_based", "ollama"], default="rule_based", help="Tailoring provider (default: rule_based)")
    p_tailor.add_argument("-i", "--interactive", action="store_true", help="Prompt to accept each improvement interactively")
    p_tailor.add_argument("--apply-all", action="store_true", help="Automatically accept all suggested rewrites")
    p_tailor.add_argument("-o", "--output", help="Output path for tailored resume (.tex or .json)")
    p_tailor.set_defaults(func=cmd_tailor)

    # hunt
    p_hunt = subparsers.add_parser("hunt", help="Query official ATS APIs (Amazon, SmartRecruiters, Greenhouse, Lever) for live jobs")
    p_hunt.add_argument("-c", "--company", default="all", help="Target company or ATS (all, amazon, cern, greenhouse, lever, canonical, figma, stripe, databricks, palantir)")
    p_hunt.add_argument("-r", "--role", default="software", help="Target role/title keywords (e.g. 'software intern', 'sde', 'engineer')")
    p_hunt.add_argument("-l", "--location", default="India,Remote", help="Target location (e.g. 'India,Remote', 'Switzerland', 'all')")
    p_hunt.add_argument("-g", "--grad-year", type=int, default=2027, help="Target graduation cohort year (default: 2027)")
    p_hunt.add_argument("-n", "--limit", type=int, default=5, help="Maximum postings per source (default: 5)")
    p_hunt.add_argument("--compile", action="store_true", help="Auto-tailor and compile paired single-page PDFs via ResumeCompiler")
    p_hunt.add_argument("-b", "--base-resume", help="Base resume path to tailor from (.tex or .json)")
    p_hunt.add_argument("-o", "--output-dir", default="output/hunt", help="Output directory for compiled PDFs and reports (default: output/hunt)")
    p_hunt.add_argument("--json", action="store_true", help="Output results in JSON format")
    p_hunt.set_defaults(func=cmd_hunt)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
