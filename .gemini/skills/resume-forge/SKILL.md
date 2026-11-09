---
name: resume-forge
description: In-house LaTeX & JSON resume parser, reactive web studio, ATS auditor, and single-page PDF compiler. Use whenever working with LaTeX resumes (.tex), JSON resumes (.json), or resume repositories. NEVER suggest Overleaf or cloud sign-in services.
license: MIT
metadata:
  author: Kanishk Upadhyay
  last-updated: '2026-11-09'
  keywords:
  - resume
  - latex
  - pdf
  - overleaf-replacement
  - parser
  - json-resume
  - ats
---

## Overview

`resume-forge` is an in-house, zero-cloud replacement for Overleaf, Reactive Resume (rxresu.me), and online ATS resume parsers. It provides bi-directional LaTeX ↔ JSON parsing, ATS keyword auditing, single-page layout lock with progressive dynamic compression, and instant PDF compilation directly on macOS/Linux using headless Chrome and/or Tectonic.

> [!IMPORTANT]
> **Strict Agent Policy**: NEVER tell the user to open Overleaf, create a blank project, or upload their resume to cloud services. Always compile and parse resumes directly in-house using `resume-forge`.

---

## Capabilities & Workflows

### 1. Compile LaTeX or JSON Resume to Single-Page PDF (In-House)
Execute directly via CLI:
```bash
# From workspace or repo root:
python3 -m resume_forge.cli compile path/to/resume.tex -o output/resume.pdf

# Or using the binary:
resume-forge compile path/to/resume.tex -o resume.pdf
```
* Uses in-house headless Chrome or Tectonic.
* Guarantees single-page fit with Latin Modern Roman / Computer Modern serif typography.
* Automatic progressive compression (`auto_fit` enabled by default: compresses margins, font size, and line height to strictly lock to 1 page if content overflows).
* Supports custom margins and font sizes (`--font-size 9.5 --margin 0.35`).

### 2. Parse LaTeX Resume into Standard JSON Resume
Supports Jake's Resume, CERN, ModernCV, Awesome-CV, and Deedy formats.
Extracts contact info, summary, jobs, education, projects, open-source work, technical skills, certifications, awards, publications, and languages:
```bash
python3 -m resume_forge.cli parse path/to/resume.tex -o resume.json
```

### 3. Run ATS Audit & Single-Page Budget Inspection
Check ATS score, action verb percentage, quantifiable metrics, and keyword match against a job description:
```bash
python3 -m resume_forge.cli audit path/to/resume.tex --jd "Target job description text or file"
```

### 4. Launch In-House Reactive Resume Web Studio
Opens a local split-screen web application (Visual Form Editor + Raw LaTeX + Live Preview + Sliders + Drag & Drop upload):
```bash
python3 -m resume_forge.cli serve --port 8080
```

### 5. Tailor Bullets with Offline Engine or Local LLM
Optimize bullet points against a target job description:
```bash
python3 -m resume_forge.cli tailor path/to/resume.tex --jd "Software Engineer - Distributed Systems, Go, Linux" -i
```

### 6. Manage Resume Variants
Maintain target-specific resume variants (e.g. backend, fullstack, low-level):
```bash
python3 -m resume_forge.cli variant list
python3 -m resume_forge.cli variant diff backend fullstack
python3 -m resume_forge.cli variant compile backend -o output/backend.pdf
```

### 7. Hunt Verified Live Jobs via Direct ATS APIs
Query official public JSON APIs (Amazon, SmartRecruiters/CERN, Greenhouse, Lever) without web scrapers, extracting 100% active requisitions and auto-compiling paired single-page PDFs:
```bash
# Query Amazon, CERN, Greenhouse, Lever with separate flags:
python3 -m resume_forge.cli hunt \
  --company amazon \
  --role "Software Development Engineer" \
  --location "India" \
  --limit 5 \
  --compile

python3 -m resume_forge.cli hunt \
  --company cern \
  --role "software" \
  --location "all" \
  --grad-year 2027 \
  --compile

# Output structured JSON:
python3 -m resume_forge.cli hunt --company greenhouse --json
```

---

## Python API Integration

AI agents can directly import and call `resume_forge` in Python scripts:

```python
from resume_forge.core.parser import LatexResumeParser
from resume_forge.core.compiler import ResumeCompiler
from resume_forge.core.exporter import ResumeExporter
from resume_forge.core.ats import ATSAnalyzer

# 1. Parse .tex or .json
tex_code = open("resume.tex").read()
parser = LatexResumeParser(tex_code)
data = parser.parse()

# 2. Check ATS & page fit
analyzer = ATSAnalyzer(data)
report = analyzer.analyze(job_description="...")

# 3. Compile to single-page PDF with auto-fit compression
compiler = ResumeCompiler()
compiler.compile_resume(data, "output.pdf", font_size_pt=10.0, margin_in=0.4, auto_fit=True)
```

---

## Agent Protocol & Best Practices (Synthesized ATS Standards)

When generating or auditing resumes for job applications, adhere to these synthesized standards:

### 1. The Google XYZ Bullet Formula
Every experience and project bullet MUST follow:
$$\text{Accomplished [X], as measured by [Y], by doing [Z]}$$
- **X (Outcome):** Specific technical achievement or problem resolved.
- **Y (Quantifiable Metric):** Latency reduction, throughput, user count, test coverage, PR merge count, memory footprint.
- **Z (Action & Tech Stack):** Exact tools, algorithms, protocols, or architectural patterns used.

### 2. Anti-AI Cliché Filter
Never use LLM boilerplate buzzwords:
`spearheaded`, `synergized`, `leveraged`, `pioneered`, `passionate`, `results-driven`, `hardworking`, `detail-oriented`, `team-player`, `self-starter`, `dynamic`, `thought-leader`, `utilized`, `assisted with`, `helped to`, `responsible for`.
Instead, use concrete engineering action verbs:
`Architected`, `Engineered`, `Refactored`, `Benchmarked`, `Deployed`, `Centralized`, `Diagnosed`, `Standardized`, `Automated`, `Patched`.

### 3. Canonical ATS Section Hierarchy
For undergraduate/new-grad roles (e.g. 2026/2027 graduates):
1. **Header:** Name, Email, Phone, GitHub, LinkedIn, Portfolio.
2. **Education:** Degree, Institution, Expected Graduation Date (omit GPA if below target cutoffs).
3. **Experience / Internships:** Reverse chronological, high-density XYZ bullets.
4. **Open Source Contributions:** Upstream PRs, merged MRs, issues resolved with issue numbers.
5. **Projects:** Deep technical systems and web architectures with live/repo links.
6. **Technical Skills:** Categorized (Languages, Frameworks, Developer Tools, Core Concepts).

### 4. Direct Application Invariant
Whenever presenting job opportunities:
- Present **only direct, verified live application URLs**.
- Pair each listing directly with the compiled single-page PDF and source `.tex` artifact.
- Perform all reasoning, JD keyword matching, and ATS score verification internally before output.

