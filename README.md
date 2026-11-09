# ⚡ ResumeForge

> **In-House LaTeX Resume Parser, Reactive Studio & Single-Page PDF Compiler.**  
> *Zero cloud dependencies. No accounts. No subscriptions. Never touch Overleaf again.*

[![Tests](https://img.shields.io/badge/tests-passing-brightgreen.svg)]()
[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)]()
[![Engine](https://img.shields.io/badge/compiler-headless--chrome%20%7C%20tectonic-purple.svg)]()
[![Privacy](https://img.shields.io/badge/privacy-100%25%20offline-success.svg)]()
[![License](https://img.shields.io/badge/license-MIT-informational.svg)]()

---

## 💡 Why ResumeForge?

Online resume tools are broken:
- **Overleaf & Cloud Editors:** Force sign-ups, require manual copy-pasting, and take seconds to compile simple `.tex` files.
- **Hosted Resume Builders (rxresu.me, OpenResume, etc.):** Lock features behind cloud accounts, collect telemetry, or store sensitive PII and contact info on third-party servers.
- **AI Coding Agents:** Often regurgitate instructions like *"Open Overleaf, create a blank project, paste your resume, and download the PDF"* because they lack a localized compiler.

**ResumeForge runs entirely in-house on your machine.** It parses LaTeX resumes into standard JSON Resume, provides a local Reactive Resume-style split-screen visual editor, audits ATS compatibility, and compiles pixel-perfect, guaranteed single-page PDFs in **under 1 second**.

---

## ✨ Key Features

- ⚡ **In-House PDF Compiler:** Compiles single-page PDFs locally using headless Chrome and/or Tectonic. Uses genuine Latin Modern Roman / Computer Modern serif typography. No 5GB MacTeX installation required.
- 📜 **Bi-directional LaTeX ↔ JSON:** Ingests any LaTeX CV (Jake's Resume, Awesome-CV, CERN Fullstack, custom environments) and exports validated [JSON Resume (`resume.json`)](https://jsonresume.org/schema/).
- 📝 **Local Web Studio:** An interactive split-screen web application featuring:
  - Visual form editor for Work, Education, Open-Source, Projects, and Skills.
  - Real-time side-by-side LaTeX Latin Modern paper preview.
  - Page Budget Meter with auto-detection to prevent accidental 2-line spills onto page 2.
  - Live typography sliders (Font Size: 8.5pt–11.5pt, Margins: 0.25in–0.75in, Line Height: 1.05–1.45).
- 🎯 **Local ATS & Keyword Inspector:** Checks action verb density, quantifiable metrics, and compares your resume against any target job description.
- 🤖 **Agent & Skill Ready:** Comes with an integrated Antigravity `SKILL.md` so AI agents can compile, parse, and tailor resumes autonomously without ever suggesting Overleaf.

---

## 🚀 Quick Start

### 1. Installation
Clone and run directly with standard Python (zero external pip packages required for core features!):
```bash
git clone https://github.com/kanishk-upadhyay/resume-forge.git
cd resume-forge
chmod +x bin/resume-forge
```

### 2. Compile LaTeX to Single-Page PDF (In-House)
```bash
# Compiles your .tex resume to a single-page PDF in < 1s
./bin/resume-forge compile examples/kanishk_cern_fullstack_resume.tex -o resume.pdf
```

### 3. Parse LaTeX to Standard JSON Resume
```bash
./bin/resume-forge parse examples/kanishk_cern_fullstack_resume.tex -o resume.json
```

### 4. Run ATS & Page Budget Audit
```bash
./bin/resume-forge audit examples/kanishk_cern_fullstack_resume.tex \
  --jd "Seeking fullstack engineer with Python, C, React, Vue.js, Linux, Nginx, Docker, Git"
```
**Sample Output:**
```
=======================================================
  RESUME FORGE - ATS & LAYOUT AUDIT: Kanishk Upadhyay
=======================================================
ATS Health Score    : 100 / 100
Page Budget         : 98% (Optimal (Single Page))
Estimated Content   : ~49 lines

[+] Strengths:
  ✓ Contains 3 active profile links.
  ✓ 2 experience roles listed.
  ✓ Education section clearly specified.
  ✓ 26 technical skills categorized across 4 domains.
  ✓ 84% of bullet points start with strong action verbs.

[✓] Matched JD Keywords: linux, nginx, react, vue, git, docker, python
=======================================================
```

### 5. Launch Local Reactive Web Studio
```bash
./bin/resume-forge serve --port 8080
```
Opens `http://localhost:8080` in your browser. Edit visually or edit LaTeX raw code with real-time paper rendering and 1-click PDF download!

### 6. Hunt Verified Live Jobs & Auto-Compile Resumes (Direct ATS APIs)
Query official public JSON endpoints of Amazon Jobs, SmartRecruiters (CERN), Greenhouse (Canonical, Figma, Stripe, Databricks), and Lever (Palantir) directly with zero web scrapers or dead links:
```bash
# Hunt software internships in India/Remote and auto-compile single-page PDFs
./bin/resume-forge hunt --role "software" --location "India,Remote" --compile

# Target specific company/ATS with modular flags:
./bin/resume-forge hunt \
  --company amazon \
  --role "Software Development Engineer" \
  --location "India" \
  --limit 5 \
  --compile

./bin/resume-forge hunt \
  --company cern \
  --role "software" \
  --location "all" \
  --grad-year 2027 \
  --compile

# Export verified listings to structured JSON for automation:
./bin/resume-forge hunt --company greenhouse --json
```


---

## 🖥️ Web Studio Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           IN-HOUSE RESUME STUDIO                                │
├───────────────────────────────┬─────────────────────────────────────────────────┤
│  LEFT PANE: Editor & Engine   │  RIGHT PANE: Live A4/Letter Preview             │
│                               │                                                 │
│  [Visual Form] [Raw LaTeX]    │  ┌───────────────────────────────────────────┐  │
│  [Design]      [ATS Scanner]  │  │ KANISHK UPADHYAY                          │  │
│                               │  │ +91 7772034062 | kanishk@... | Bhopal     │  │
│  • Contact & PII              │  │ ───────────────────────────────────────── │  │
│  • Experience & Bullets       │  │ EDUCATION                                 │  │
│  • Projects & Tech Stacks     │  │ EXPERIENCE                                │  │
│  • Grouped Skills             │  │ OPEN-SOURCE CONTRIBUTIONS                 │  │
│                               │  │ PROJECTS                                  │  │
│  Page Budget: [98% - 1 Page]  │  │ TECHNICAL SKILLS                          │  │
│                               │  └───────────────────────────────────────────┘  │
│  [📥 Import .tex] [💾 Save]   │  [⚡ One-Click In-House Single-Page PDF]         │
│  [📤 Export LaTeX]            │  [📄 Export JSON Resume] [📋 Copy ATS Text]     │
└───────────────────────────────┴─────────────────────────────────────────────────┘
```

---

## 🐍 Python API

You can import and automate `resume-forge` directly in your Python scripts or AI pipelines:

```python
from resume_forge.core import LatexResumeParser, ResumeCompiler, ResumeExporter, ATSAnalyzer

# 1. Parse LaTeX
tex_code = open("resume.tex").read()
parser = LatexResumeParser(tex_code)
resume_data = parser.parse()

# 2. Inspect ATS & page budget
analyzer = ATSAnalyzer(resume_data)
report = analyzer.analyze(job_description="CERN Software Engineer...")
print(f"ATS Score: {report['score']} | Page Budget: {report['page_budget_percent']}%")

# 3. Compile to single-page PDF
compiler = ResumeCompiler()
compiler.compile_resume(
    data=resume_data,
    output_pdf_path="output/kanishk_resume.pdf",
    font_size_pt=9.5,
    margin_in=0.35
)
```

---

## 🤖 AI Agent & Skill Integration

ResumeForge includes an Antigravity Agent Skill in `.gemini/skills/resume-forge/SKILL.md`.

When this skill is registered:
1. Any AI agent given a `.tex` file or asked to compile a resume will automatically run `resume-forge compile <file.tex> -o resume.pdf`.
2. Agents will **never prompt you to open Overleaf** or use cloud services.

---

## 🧪 Testing

Run the automated test suite:
```bash
python3 -m unittest discover tests
```

---

## 📜 License

MIT License. Designed and engineered by [Kanishk Upadhyay](https://github.com/kanishk-upadhyay).
