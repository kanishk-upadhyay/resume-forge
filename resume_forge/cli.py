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
from .core.letter import CoverLetterData, CoverLetterRecipient
from .core.diff import ResumeDiffEngine
from .core.fetcher import fetch_job_description
from .templates import TemplateRegistry
from .completion import generate_bash_completion, generate_zsh_completion, generate_fish_completion



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
    """Compiles LaTeX or JSON resume to PDF or Image in-house without Overleaf."""
    resume_data = load_resume(args.input)
    compiler = ResumeCompiler()
    fmt = getattr(args, "format", "pdf").lower()
    dpi = getattr(args, "dpi", 300) or 300

    # Batch all templates
    if getattr(args, "all_templates", False):
        raw_out = args.output
        if raw_out and not raw_out.endswith(f".{fmt}"):
            out_dir = Path(raw_out)
        else:
            out_dir = Path("compiled_templates")
        out_dir.mkdir(parents=True, exist_ok=True)
        print(f"Compiling all 7 templates to '{out_dir}/' in format '{fmt}'...")
        results = compiler.compile_all_templates(
            data=resume_data,
            output_dir=out_dir,
            prefix=Path(args.input).stem,
            fmt=fmt,
            dpi=dpi,
            auto_fit=not getattr(args, "no_auto_fit", False)
        )
        for t_name, out_file in results.items():
            print(f"  ✓ {t_name:<12} ➔ {Path(out_file).name}")
        print(f"✓ All {len(results)} templates compiled successfully into '{out_dir}'")
        return

    out_file = args.output or f"resume.{fmt}"
    template = getattr(args, "template", "cern")

    if fmt in ("png", "webp", "jpg", "jpeg"):
        print(f"Rendering high-DPI image ({dpi} DPI) using template '{template}' to '{out_file}'...")
        success = compiler.compile_image(
            data=resume_data,
            output_image_path=out_file,
            template=template,
            dpi=dpi,
            font_size_pt=args.font_size,
            line_height=args.line_height,
            margin_in=args.margin
        )
        if success:
            print(f"✓ High-DPI {fmt.upper()} image generated: {out_file}")
        else:
            print(f"✗ Failed to generate image.", file=sys.stderr)
            sys.exit(1)
        return

    print(f"Compiling '{args.input}' to '{out_file}' using template '{template}' in-house...")

    if args.method == "tectonic" or (args.input.endswith(".tex") and args.method == "auto" and compiler.tectonic_bin):
        # Try raw LaTeX compilation
        raw_tex = Path(args.input).read_text(encoding="utf-8") if args.input.endswith(".tex") else ResumeExporter(resume_data).to_latex(template=template)
        success, msg = compiler.compile_latex_to_pdf(raw_tex, out_file)
        if success:
            print(f"✓ PDF compiled successfully via Tectonic: {out_file}")
            return

    # Default robust engine: In-house headless Chrome
    success = compiler.compile_resume(
        data=resume_data,
        output_pdf_path=out_file,
        template=template,
        font_size_pt=args.font_size,
        line_height=args.line_height,
        margin_in=args.margin,
        auto_fit=not getattr(args, "no_auto_fit", False)
    )

    if success:
        pages = compiler.get_pdf_page_count(out_file)
        if pages == 1:
            print(f"✓ Single-page PDF compiled successfully in-house (1 page): {out_file}")
        else:
            print(f"✓ PDF compiled successfully ({pages} pages): {out_file}")
    else:
        print(f"✗ Failed to compile PDF. Ensure Google Chrome is installed.", file=sys.stderr)
        sys.exit(1)


def cmd_export(args):
    """Exports resume into specified format (tex, json, html, md)."""
    resume_data = load_resume(args.input)
    exporter = ResumeExporter(resume_data)
    fmt = args.format.lower()

    if getattr(args, "all_templates", False):
        out_dir = Path(args.output or "exported_templates")
        out_dir.mkdir(parents=True, exist_ok=True)
        print(f"Exporting all templates to '{out_dir}/' in format '{fmt}'...")
        for tmpl_meta in TemplateRegistry.list_templates():
            t_name = tmpl_meta["name"]
            ext = "tex" if fmt in ("tex", "latex") else fmt
            out_file = out_dir / f"{Path(args.input).stem}_{t_name}.{ext}"
            if fmt in ("tex", "latex"):
                content = exporter.to_latex(template=t_name)
            elif fmt == "html":
                content = exporter.to_html(template=t_name)
            elif fmt == "json":
                content = resume_data.to_json(indent=2)
            else:
                content = exporter.to_markdown()
            out_file.write_text(content, encoding="utf-8")
            print(f"  ✓ {t_name:<12} ➔ {out_file.name}")
        print(f"✓ Exported all templates to '{out_dir}'")
        return

    template = getattr(args, "template", "cern")
    if fmt == "tex" or fmt == "latex":
        out_content = exporter.to_latex(template=template)
    elif fmt == "json":
        out_content = resume_data.to_json(indent=2)
    elif fmt == "html":
        out_content = exporter.to_html(template=template)
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
        try:
            jd_text = fetch_job_description(args.jd)
        except Exception as e:
            print(f"Notice: Failed to fetch online JD ({e}); using raw string input.", file=sys.stderr)
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
        try:
            jd_text = fetch_job_description(args.jd)
        except Exception as e:
            print(f"Notice: Failed to fetch online JD ({e}); using raw string input.", file=sys.stderr)
            jd_text = args.jd
    else:
        print("Error: Target job description (--jd/--jd-url) is required for tailoring.", file=sys.stderr)
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
    target_info = []
    if args.company:
        target_info.append(f"Company: {args.company}")
    if args.provider and args.provider != "all":
        target_info.append(f"Provider: {args.provider}")
    if args.role:
        target_info.append(f"Role: '{args.role}'")
    if args.location:
        target_info.append(f"Location: '{args.location}'")
    if args.grad_year:
        target_info.append(f"Cohort: {args.grad_year}")

    filter_desc = f" ({', '.join(target_info)})" if target_info else ""
    print(f"Hunting verified live requisitions via ATS APIs{filter_desc}...")
    hunter = JobHunter(
        company=args.company,
        provider=args.provider,
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


def cmd_diff(args):
    """Computes a structural AST-level diff between two resumes."""
    r1 = load_resume(args.v1)
    r2 = load_resume(args.v2)
    diff_res = ResumeDiffEngine.diff(r1, r2)

    if getattr(args, "json", False):
        print(json.dumps(diff_res.to_dict(), indent=2, ensure_ascii=False))
    else:
        use_color = not getattr(args, "no_color", False)
        print(diff_res.format_terminal(color=use_color))


def cmd_letter(args):
    """Synthesizes, exports, or compiles tailored single-page cover letters matching resume templates."""
    sub = args.letter_cmd
    template = getattr(args, "template", "cern")
    tmpl = TemplateRegistry.get(template)

    if sub == "create":
        resume_data = load_resume(args.input)
        company = getattr(args, "company", "") or "Target Company"
        role = getattr(args, "role", "") or "Software Engineer"
        recipient = getattr(args, "recipient", "") or ""
        city = getattr(args, "city", "") or ""

        letter_data = CoverLetterData.from_resume(
            resume=resume_data,
            company=company,
            role=role,
            recipient_name=recipient,
            city=city
        )

        out_path = args.output
        if not out_path:
            print(letter_data.to_json())
            return

        out_p = Path(out_path)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        ext = out_p.suffix.lower()

        if ext == ".json":
            out_p.write_text(letter_data.to_json(), encoding="utf-8")
            print(f"✓ Created cover letter JSON data: {out_p}")
        elif ext in (".tex", ".latex"):
            tex = tmpl.render_cover_letter_latex(letter_data)
            out_p.write_text(tex, encoding="utf-8")
            print(f"✓ Created cover letter LaTeX ({template}): {out_p}")
        elif ext == ".pdf":
            compiler = ResumeCompiler()
            compiler.compile_cover_letter(letter_data, str(out_p), template=template)
            print(f"✓ Compiled single-page cover letter PDF ({template}): {out_p}")
        elif ext == ".html":
            html = tmpl.render_cover_letter_html(letter_data)
            out_p.write_text(html, encoding="utf-8")
            print(f"✓ Created cover letter HTML ({template}): {out_p}")
        else:
            out_p.write_text(letter_data.to_json(), encoding="utf-8")
            print(f"✓ Created cover letter: {out_p}")

    elif sub == "compile":
        in_p = Path(args.input)
        if in_p.suffix.lower() == ".json":
            letter_data = CoverLetterData.from_json(in_p.read_text(encoding="utf-8"))
        elif in_p.suffix.lower() in (".tex", ".latex"):
            content = in_p.read_text(encoding="utf-8")
            if "Dear " in content or "Cover Letter" in content or "Sincerely" in content or "Regards" in content:
                from .core.letter import LatexCoverLetterParser
                letter_data = LatexCoverLetterParser(content).parse()
            else:
                resume_data = load_resume(args.input)
                letter_data = CoverLetterData.from_resume(
                    resume_data,
                    company=getattr(args, "company", "") or "Target Company",
                    role=getattr(args, "role", "") or "Software Engineer"
                )
        else:
            resume_data = load_resume(args.input)
            letter_data = CoverLetterData.from_resume(
                resume_data,
                company=getattr(args, "company", "") or "Target Company",
                role=getattr(args, "role", "") or "Software Engineer"
            )

        out_pdf = args.output or "cover_letter.pdf"
        compiler = ResumeCompiler()
        success = compiler.compile_cover_letter(letter_data, out_pdf, template=template)
        if success:
            print(f"✓ Compiled single-page cover letter PDF ({template}): {out_pdf}")
        else:
            print("✗ Failed to compile cover letter PDF.", file=sys.stderr)
            sys.exit(1)

    elif sub == "export":
        in_p = Path(args.input)
        if in_p.suffix.lower() == ".json":
            letter_data = CoverLetterData.from_json(in_p.read_text(encoding="utf-8"))
        elif in_p.suffix.lower() in (".tex", ".latex"):
            content = in_p.read_text(encoding="utf-8")
            if "Dear " in content or "Cover Letter" in content or "Sincerely" in content or "Regards" in content:
                from .core.letter import LatexCoverLetterParser
                letter_data = LatexCoverLetterParser(content).parse()
            else:
                resume_data = load_resume(args.input)
                letter_data = CoverLetterData.from_resume(
                    resume_data,
                    company=getattr(args, "company", "") or "Target Company",
                    role=getattr(args, "role", "") or "Software Engineer"
                )
        else:
            resume_data = load_resume(args.input)
            letter_data = CoverLetterData.from_resume(
                resume_data,
                company=getattr(args, "company", "") or "Target Company",
                role=getattr(args, "role", "") or "Software Engineer"
            )

        fmt = getattr(args, "format", "tex").lower()
        if fmt in ("tex", "latex"):
            content = tmpl.render_cover_letter_latex(letter_data)
        elif fmt == "html":
            content = tmpl.render_cover_letter_html(letter_data)
        elif fmt == "json":
            content = letter_data.to_json()
        else:
            content = f"{letter_data.salutation}\n\n{letter_data.opening}\n\n" + "\n\n".join(letter_data.body_paragraphs) + f"\n\n{letter_data.closing}\n\n{letter_data.sign_off}\n{letter_data.sender.name}"

        if args.output:
            out_p = Path(args.output)
            out_p.parent.mkdir(parents=True, exist_ok=True)
            out_p.write_text(content, encoding="utf-8")
            print(f"✓ Exported cover letter {fmt.upper()} ({template}) to '{args.output}'")
        else:
            print(content)


def cmd_completion(args):
    """Outputs shell autocompletion script."""
    shell = (getattr(args, "shell", "") or "bash").lower()
    if shell == "zsh":
        print(generate_zsh_completion())
    elif shell == "fish":
        print(generate_fish_completion())
    else:
        print(generate_bash_completion())


def cmd_template(args):
    """Lists and inspects available resume presentation templates."""
    from .templates import TemplateRegistry
    sub = args.template_cmd

    if sub == "list":
        templates = TemplateRegistry.list_templates()
        print("\n" + "=" * 70)
        print("  RESUME FORGE - AVAILABLE TEMPLATES")
        print("=" * 70)
        for t in templates:
            print(f"• {t['name']:<12} [{t['category']}] - {t['display_name']}")
            print(f"    Description: {t['description']}")
            print(f"    Target:      {', '.join(t['target_roles'][:3])}")
            print(f"    Defaults:    font={t['default_font_size']}pt | line={t['default_line_height']} | margin={t['default_margin']}in")
            print("")
        print("Use `-t <name>` with `compile` or `export` to select a template.")
        print("=" * 70 + "\n")
    elif sub == "info":
        tmpl = TemplateRegistry.get(args.name)
        print(f"\nTemplate:     {tmpl.name} ({tmpl.display_name})")
        print(f"Category:     {tmpl.category}")
        print(f"Description:  {tmpl.description}")
        print(f"Target Roles: {', '.join(tmpl.target_roles)}")
        print(f"Defaults:     font_size={tmpl.default_font_size}pt, line_height={tmpl.default_line_height}, margin={tmpl.default_margin}in\n")


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
    p_compile = subparsers.add_parser("compile", help="Compile .tex or .json to single-page PDF or high-DPI image in-house")
    p_compile.add_argument("input", help="Path to input .tex or .json resume")
    p_compile.add_argument("-o", "--output", default=None, help="Output destination path (default: resume.pdf or output folder)")
    p_compile.add_argument("-t", "--template", default="cern", help="Template style: cern, harvard, jakes, minimalist, quant, awesome, academic (default: cern)")
    p_compile.add_argument("-f", "--format", choices=["pdf", "png", "webp", "jpg", "jpeg"], default="pdf", help="Output file format (default: pdf)")
    p_compile.add_argument("--dpi", type=int, default=300, help="DPI resolution for image screenshot rendering (default: 300)")
    p_compile.add_argument("--all-templates", action="store_true", help="Compile across all 7 canonical templates into destination folder")
    p_compile.add_argument("--method", choices=["auto", "chrome", "tectonic"], default="auto", help="Compiler engine")
    p_compile.add_argument("--font-size", type=float, default=None, help="Base font size in pt (default: template default)")
    p_compile.add_argument("--line-height", type=float, default=None, help="Line height multiplier (default: template default)")
    p_compile.add_argument("--margin", type=float, default=None, help="Page margin in inches (default: template default)")
    p_compile.add_argument("--no-auto-fit", action="store_true", help="Disable automatic single-page font/margin compression")
    p_compile.set_defaults(func=cmd_compile)

    # export
    p_export = subparsers.add_parser("export", help="Convert resume between formats (tex, json, html, md)")
    p_export.add_argument("input", help="Input file path")
    p_export.add_argument("-f", "--format", choices=["tex", "latex", "json", "html", "md", "markdown"], required=True)
    p_export.add_argument("-t", "--template", default="cern", help="Template style: cern, harvard, jakes, minimalist, quant, awesome, academic (default: cern)")
    p_export.add_argument("--all-templates", action="store_true", help="Export across all templates into output folder")
    p_export.add_argument("-o", "--output", help="Output file path (stdout if omitted)")
    p_export.set_defaults(func=cmd_export)

    # audit
    p_audit = subparsers.add_parser("audit", help="Run ATS and single-page budget inspection")
    p_audit.add_argument("input", help="Path to resume file (.tex or .json)")
    p_audit.add_argument("--jd", "--jd-url", dest="jd", help="Target job description text, file path, or live URL")
    p_audit.set_defaults(func=cmd_audit)

    # diff
    p_diff = subparsers.add_parser("diff", help="Compute structural AST diff between two resumes")
    p_diff.add_argument("v1", help="First resume file path (.tex or .json)")
    p_diff.add_argument("v2", help="Second resume file path (.tex or .json)")
    p_diff.add_argument("--json", action="store_true", help="Output machine-readable JSON diff")
    p_diff.add_argument("--no-color", action="store_true", help="Disable ANSI terminal colors")
    p_diff.set_defaults(func=cmd_diff)

    # letter
    p_letter = subparsers.add_parser("letter", help="Synthesize, export, or compile tailored single-page cover letters")
    letter_sub = p_letter.add_subparsers(dest="letter_cmd", required=True)

    let_create = letter_sub.add_parser("create", help="Create a tailored cover letter from resume")
    let_create.add_argument("input", help="Base resume path (.tex or .json)")
    let_create.add_argument("-c", "--company", default="Target Company", help="Target company name")
    let_create.add_argument("-r", "--role", default="Software Engineer", help="Target role title")
    let_create.add_argument("--recipient", default="", help="Hiring manager or team name")
    let_create.add_argument("--city", default="", help="Company city/location")
    let_create.add_argument("-t", "--template", default="cern", help="Template typography style")
    let_create.add_argument("-o", "--output", help="Output file path (.json, .tex, .pdf, .html)")
    let_create.set_defaults(func=cmd_letter)

    let_compile = letter_sub.add_parser("compile", help="Compile cover letter to single-page PDF")
    let_compile.add_argument("input", help="Cover letter JSON or base resume file")
    let_compile.add_argument("-c", "--company", default="Target Company", help="Company name (if synthesizing from resume)")
    let_compile.add_argument("-r", "--role", default="Software Engineer", help="Role title (if synthesizing from resume)")
    let_compile.add_argument("-t", "--template", default="cern", help="Template typography style")
    let_compile.add_argument("-o", "--output", default="cover_letter.pdf", help="Output PDF path")
    let_compile.set_defaults(func=cmd_letter)

    let_export = letter_sub.add_parser("export", help="Export cover letter to LaTeX, HTML, or JSON")
    let_export.add_argument("input", help="Cover letter JSON or base resume file")
    let_export.add_argument("-f", "--format", choices=["tex", "latex", "html", "json", "txt"], default="tex")
    let_export.add_argument("-t", "--template", default="cern", help="Template typography style")
    let_export.add_argument("-c", "--company", default="Target Company", help="Company name (if synthesizing from resume)")
    let_export.add_argument("-r", "--role", default="Software Engineer", help="Role title (if synthesizing from resume)")
    let_export.add_argument("-o", "--output", help="Output file path (stdout if omitted)")
    let_export.set_defaults(func=cmd_letter)

    # completion
    p_comp = subparsers.add_parser("completion", help="Generate shell autocompletion script (bash, zsh, fish)")
    p_comp.add_argument("shell", choices=["bash", "zsh", "fish"], default="bash", nargs="?", help="Shell type (default: bash)")
    p_comp.set_defaults(func=cmd_completion)

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
    p_tailor.add_argument("--jd", "--jd-url", dest="jd", required=True, help="Target job description text, file path, or live URL")
    p_tailor.add_argument("--provider", choices=["rule_based", "ollama"], default="rule_based", help="Tailoring provider (default: rule_based)")
    p_tailor.add_argument("-i", "--interactive", action="store_true", help="Prompt to accept each improvement interactively")
    p_tailor.add_argument("--apply-all", action="store_true", help="Automatically accept all suggested rewrites")
    p_tailor.add_argument("-o", "--output", help="Output path for tailored resume (.tex or .json)")
    p_tailor.set_defaults(func=cmd_tailor)

    # hunt
    p_hunt = subparsers.add_parser("hunt", help="Query official ATS APIs (Greenhouse, Lever, SmartRecruiters, Amazon, Ashby, Workday) for live jobs")
    p_hunt.add_argument("-p", "--provider", choices=["all", "greenhouse", "lever", "smartrecruiters", "amazon", "ashby", "workday"], default="all", help="ATS platform provider (default: all)")
    p_hunt.add_argument("-c", "--company", default="", help="Target company or board identifier (e.g. 'canonical', 'linear', 'ramp', 'redhat', 'cern', 'amazon')")
    p_hunt.add_argument("-r", "--role", default="", help="Role/title keyword filter (e.g. 'software engineer', 'intern', 'backend')")
    p_hunt.add_argument("-l", "--location", default="", help="Target location / country filter (e.g. 'Remote', 'US', 'Germany', 'India')")
    p_hunt.add_argument("-g", "--grad-year", type=int, default=None, help="Target graduation cohort year filter (e.g. 2026, 2027)")
    p_hunt.add_argument("-n", "--limit", type=int, default=5, help="Maximum postings per source (default: 5)")
    p_hunt.add_argument("--compile", action="store_true", help="Auto-tailor and compile paired single-page PDFs via ResumeCompiler")
    p_hunt.add_argument("-b", "--base-resume", help="Base resume path to tailor from (.tex or .json)")
    p_hunt.add_argument("-o", "--output-dir", default="output/hunt", help="Output directory for compiled PDFs and reports (default: output/hunt)")
    p_hunt.add_argument("--json", action="store_true", help="Output results in JSON format")
    p_hunt.set_defaults(func=cmd_hunt)

    # template
    p_tmpl = subparsers.add_parser("template", help="List and inspect available resume presentation templates")
    tmpl_sub = p_tmpl.add_subparsers(dest="template_cmd", required=True)

    tmpl_list = tmpl_sub.add_parser("list", help="List all available templates")
    tmpl_list.set_defaults(func=cmd_template)

    tmpl_info = tmpl_sub.add_parser("info", help="Show details of a specific template")
    tmpl_info.add_argument("name", help="Template name (e.g. harvard, jakes, minimalist, quant, awesome, academic, cern)")
    tmpl_info.set_defaults(func=cmd_template)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
