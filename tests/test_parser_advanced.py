"""Advanced stress tests for LatexResumeParser (ModernCV, Jake's Resume, edge cases)."""

import unittest
from resume_forge.core.parser import LatexResumeParser, clean_latex


class TestAdvancedParser(unittest.TestCase):

    def test_clean_latex_nested_and_escapes(self):
        raw = r"\textbf{\href{https://github.com}{\underline{GitHub Link}}} \& More"
        cleaned = clean_latex(raw)
        self.assertEqual(cleaned, "GitHub Link & More")

        raw_math = r"\textbf{Project} $|$ \emph{React, Node.js}"
        cleaned = clean_latex(raw_math)
        self.assertEqual(cleaned, "Project | React, Node.js")

        raw_dashes = r"Dates: 2023---2024 -- Present~Location"
        cleaned = clean_latex(raw_dashes)
        self.assertEqual(cleaned, "Dates: 2023—2024 – Present Location")

        raw_symbols = r"P99 latency $\le$ 15\mu s \quad jitter \pm 2ms \qquad throughput \neq 0"
        cleaned_symbols = clean_latex(raw_symbols)
        self.assertIn("15µs", cleaned_symbols)
        self.assertIn("±", cleaned_symbols)
        self.assertIn("≠", cleaned_symbols)

    def test_jakes_resume_template(self):
        jakes_tex = r"""
        \documentclass[letterpaper,11pt]{article}
        \begin{document}
        \begin{center}
            \textbf{\Huge \scshape Alex Mercer} \\ \vspace{1pt}
            \small 123-456-7890 $|$ \href{mailto:alex@example.com}{\underline{alex@example.com}} $|$ 
            \href{https://linkedin.com/in/alex}{\underline{linkedin.com/in/alex}} $|$
            \href{https://github.com/alex}{\underline{github.com/alex}}
        \end{center}

        \section{Education}
          \resumeSubHeadingListStart
            \resumeSubheading
              {State University}{San Jose, CA}
              {Bachelor of Science in Computer Science}{Aug. 2020 -- May 2024}
          \resumeSubHeadingListEnd

        \section{Experience}
          \resumeSubHeadingListStart
            \resumeSubheading
              {Amazon}{Seattle, WA}
              {Software Development Engineer}{Aug. 2024 -- Present}
              \resumeItemListStart
                \resumeItem{Developed high-throughput data processing service in Java and AWS.}
                \resumeItem{Reduced p99 query latency by 45\% across distributed clusters.}
              \resumeItemListEnd
          \resumeSubHeadingListEnd

        \section{Projects}
          \resumeSubHeadingListStart
            \resumeProjectHeading
              {\textbf{GitWatcher} $|$ \emph{Go, Redis, Docker, gRPC}}{June 2023 -- Aug. 2023}
              \resumeItemListStart
                \resumeItem{Engineered distributed event-driven monitoring daemon.}
              \resumeItemListEnd
          \resumeSubHeadingListEnd

        \section{Technical Skills}
         \begin{itemize}[leftmargin=0.15in, label={}]
            \small{\item{
             \textbf{Languages}{: Java, Go, Python, C++, SQL} \\
             \textbf{Frameworks}{: Spring Boot, React, Docker, Kubernetes}
            }}
         \end{itemize}
        \end{document}
        """
        parser = LatexResumeParser(jakes_tex)
        data = parser.parse()

        # Basics
        self.assertEqual(data.basics.name, "Alex Mercer")
        self.assertEqual(data.basics.email, "alex@example.com")
        self.assertEqual(data.basics.phone, "123-456-7890")

        # Education
        self.assertEqual(len(data.education), 1)
        self.assertIn("State University", data.education[0].institution)
        self.assertIn("Computer Science", data.education[0].study_type)

        # Experience
        self.assertEqual(len(data.work), 1)
        self.assertEqual(data.work[0].name, "Amazon")
        self.assertEqual(data.work[0].location, "Seattle, WA")
        self.assertEqual(data.work[0].position, "Software Development Engineer")
        self.assertEqual(len(data.work[0].highlights), 2)
        self.assertIn("latency by 45%", data.work[0].highlights[1])

        # Projects
        self.assertEqual(len(data.projects), 1)
        self.assertEqual(data.projects[0].name, "GitWatcher")
        self.assertIn("Go", data.projects[0].keywords)
        self.assertIn("Redis", data.projects[0].keywords)

        # Skills
        self.assertEqual(len(data.skills), 2)
        self.assertEqual(data.skills[0].name, "Languages")
        self.assertIn("Java", data.skills[0].keywords)
        self.assertIn("C++", data.skills[0].keywords)

    def test_cventry_moderncv_style(self):
        cventry_tex = r"""
        \documentclass{moderncv}
        \name{Elena}{Rostova}
        \email{elena@example.com}
        \phone{+1 (555) 019-2834}

        \begin{document}
        \section{Experience}
        \cventry{2022--2025}{Senior Backend Engineer}{Stripe}{Dublin, Ireland}{}{
        \begin{itemize}
        \item Architected real-time fraud detection pipeline processing \$10B+ volume.
        \item Automated database failover and shard rebalancing with zero downtime.
        \end{itemize}
        }

        \section{Education}
        \cventry{2018--2022}{B.Sc. in Software Engineering}{Trinity College}{Dublin}{First Class Honours}{}

        \section{Skills}
        \item \textbf{Languages:} Python, Rust, Go, SQL
        \item \textbf{Tools:} Kubernetes, Terraform, PostgreSQL
        \end{document}
        """
        parser = LatexResumeParser(cventry_tex)
        data = parser.parse()

        self.assertIn("Elena", data.basics.name)
        self.assertEqual(data.basics.email, "elena@example.com")
        self.assertEqual(len(data.work), 1)
        self.assertEqual(data.work[0].position, "Senior Backend Engineer")
        self.assertEqual(data.work[0].name, "Stripe")
        self.assertEqual(len(data.work[0].highlights), 2)

    def test_malformed_and_edge_case_latex(self):
        # Empty text
        p1 = LatexResumeParser("")
        d1 = p1.parse()
        self.assertEqual(d1.basics.name, "")
        self.assertEqual(len(d1.work), 0)

        # Comment-heavy text
        p2 = LatexResumeParser(r"""
        % Entire file is comments
        % \textbf{\Huge Fake Name}
        % \section{Experience}
        \textbf{\Huge Real Name}
        real@example.com
        """)
        d2 = p2.parse()
        self.assertEqual(d2.basics.name, "Real Name")
        self.assertEqual(d2.basics.email, "real@example.com")

    def test_bracket_and_nested_brace_title_parsing(self):
        """Verifies no stray opening or closing braces remain in titles, headings, or exports."""
        from resume_forge.core.exporter import ResumeExporter
        from resume_forge.core.schema import Basics

        test_cases = [
            r"\textbf{\Huge \scshape {Kanishk Upadhyay}}",
            r"{\Huge \scshape {Kanishk Upadhyay}}",
            r"\textbf{\Huge {Kanishk Upadhyay}}",
            r"{\Huge {Kanishk Upadhyay}}",
            r"\textbf{{\Huge \scshape {Kanishk Upadhyay}}}",
            r"\name{{Kanishk}}{{Upadhyay}}",
            r"\namesection{{Kanishk}}{{Upadhyay}}{}",
            r"\author{{Kanishk Upadhyay}}",
            r"\Huge \textbf{{Kanishk Upadhyay}}",
            r"\begin{center} \textbf{\Huge \scshape {Kanishk Upadhyay}} \end{center}",
        ]

        for tc in test_cases:
            parser = LatexResumeParser(tc)
            data = parser.parse()
            name = data.basics.name
            self.assertEqual(name, "Kanishk Upadhyay", f"Failed for {tc}")
            self.assertNotIn("{", name)
            self.assertNotIn("}", name)

            exporter = ResumeExporter(data)
            html = exporter.to_html()
            self.assertIn("<title>Kanishk Upadhyay - Resume</title>", html)
            self.assertIn("<h1>Kanishk Upadhyay</h1>", html)
            self.assertNotIn("<title>{", html)
            self.assertNotIn("<h1>{", html)

            md = exporter.to_markdown()
            self.assertTrue(md.startswith("# Kanishk Upadhyay"))

            tex = exporter.to_latex()
            self.assertIn(r"\textbf{\Huge \scshape Kanishk Upadhyay}", tex)

        # Direct schema sanitization test
        b = Basics(name="{Kanishk Upadhyay}")
        self.assertEqual(b.name, "Kanishk Upadhyay")
        b2 = Basics(label="{Software Engineer}")
        self.assertEqual(b2.label, "Software Engineer")

    def test_technical_skills_colons_and_macros(self):
        """Verifies skills parsing when colons are inside bold and macros like \\texttt or \\& are present."""
        tex = r"""
        \documentclass{article}
        \begin{document}
        \section{Technical Skills}
        \begin{itemize}[leftmargin=0.15in, label={}]
            \small{\item{
             \textbf{Languages:}{ Python, C++, Go, TypeScript, SQL} \\
             \textbf{Frameworks:}{ FastAPI, React 19, Node.js, Express} \\
             \textbf{Developer Tools:}{ Git, Docker, Kubernetes, \texttt{systemd}, Linux \& Nginx} \\
             \textbf{Libraries:}{ PyTorch, NumPy, Pandas, RDKit}
            }}
        \end{itemize}
        \end{document}
        """
        parser = LatexResumeParser(tex)
        data = parser.parse()

        self.assertEqual(len(data.skills), 4)
        cat_names = [s.name for s in data.skills]
        self.assertIn("Languages", cat_names)
        self.assertIn("Frameworks", cat_names)
        self.assertIn("Developer Tools", cat_names)
        self.assertIn("Libraries", cat_names)

        dev_tools = next(s for s in data.skills if s.name == "Developer Tools")
        self.assertIn("Docker", dev_tools.keywords)
        self.assertIn("systemd", dev_tools.keywords)
        self.assertIn("Linux & Nginx", dev_tools.keywords)

    def test_projects_standard_latex_fallback(self):
        """Verifies standard LaTeX project definitions with tech stack and bullets."""
        tex = r"""
        \documentclass{article}
        \begin{document}
        \section{Projects}
        \textbf{SmartSpend} \ $\cdot$ \ \textit{FastAPI, React 19, PostgreSQL} \hfill \href{https://github.com/example/smartspend}{github.com/example/smartspend}
        \begin{itemize}
            \item Developed a financial tracking system with FastAPI and React 19.
            \item Implemented real-time categorization with 99% accuracy.
        \end{itemize}

        \textbf{CloudOps Engine} $|$ \textit{Go, Docker, Kubernetes} \hfill \textit{Jan 2024 -- Present}
        \begin{itemize}
            \item Built distributed worker orchestrator in Go.
        \end{itemize}
        \end{document}
        """
        parser = LatexResumeParser(tex)
        data = parser.parse()

        self.assertEqual(len(data.projects), 2)
        p1 = data.projects[0]
        self.assertEqual(p1.name, "SmartSpend")
        self.assertIn("FastAPI", p1.keywords)
        self.assertIn("React 19", p1.keywords)
        self.assertEqual(p1.url, "https://github.com/example/smartspend")
        self.assertEqual(len(p1.highlights), 2)

        p2 = data.projects[1]
        self.assertEqual(p2.name, "CloudOps Engine")
        self.assertIn("Go", p2.keywords)
        self.assertIn("Kubernetes", p2.keywords)
        self.assertEqual(p2.start_date, "Jan 2024")
        self.assertEqual(p2.end_date, "Present")
        self.assertEqual(len(p2.highlights), 1)

    def test_work_experience_two_line_header(self):
        """Verifies two-line role headers capture company, position, location, and dates."""
        tex = r"""
        \documentclass{article}
        \begin{document}
        \section{Experience}
        \textbf{OZ Media} \hfill \textit{Jun 2025 -- Dec 2025} \\
        \textit{Software Developer Intern} \hfill \textit{Bhopal, India}
        \begin{itemize}
            \item Developed full-stack features using React and FastAPI.
            \item Optimized SQL queries reducing response times by 35%.
        \end{itemize}

        \textbf{DCare Technologies} \hfill \textit{Remote} \\
        \textit{Frontend Engineer} \hfill \textit{Jan 2024 -- May 2025}
        \begin{itemize}
            \item Built responsive web applications using Vue.js.
        \end{itemize}
        \end{document}
        """
        parser = LatexResumeParser(tex)
        data = parser.parse()

        self.assertEqual(len(data.work), 2)
        w1 = data.work[0]
        self.assertEqual(w1.name, "OZ Media")
        self.assertEqual(w1.position, "Software Developer Intern")
        self.assertEqual(w1.location, "Bhopal, India")
        self.assertEqual(w1.start_date, "Jun 2025")
        self.assertEqual(w1.end_date, "Dec 2025")
        self.assertEqual(len(w1.highlights), 2)

        w2 = data.work[1]
        self.assertEqual(w2.name, "DCare Technologies")
        self.assertEqual(w2.position, "Frontend Engineer")
        self.assertEqual(w2.location, "Remote")
        self.assertEqual(w2.start_date, "Jan 2024")
        self.assertEqual(w2.end_date, "May 2025")
        self.assertEqual(len(w2.highlights), 1)

    def test_education_grouping_no_duplicate_entries(self):
        """Verifies multi-line education headers do not produce duplicate records."""
        tex = r"""
        \documentclass{article}
        \begin{document}
        \section{Education}
        \textbf{Barkatullah University} \hfill \textit{Bhopal, India} \\
        Bachelor of Engineering (B.E.), Computer Science \hfill \textit{2023 -- 2027}
        \begin{itemize}
            \item Relevant Coursework: Data Structures, Operating Systems, Database Systems.
            \item CGPA: 8.5/10.
        \end{itemize}
        \end{document}
        """
        parser = LatexResumeParser(tex)
        data = parser.parse()

        self.assertEqual(len(data.education), 1)
        edu = data.education[0]
        self.assertEqual(edu.institution, "Barkatullah University")
        self.assertIn("Bachelor of Engineering", edu.study_type)
        self.assertEqual(edu.area, "Bhopal, India")
        self.assertEqual(edu.start_date, "2023")
        self.assertEqual(edu.end_date, "2027")
        self.assertEqual(len(edu.highlights), 2)

    def test_open_source_individual_project_headings(self):
        """Verifies individual open-source project headings are kept distinct and routed properly."""
        tex = r"""
        \documentclass{article}
        \begin{document}
        \section{Systems \& Open-Source Engineering}
        \textbf{GitLab Core} $|$ \textit{Core Contributor} \hfill \href{https://gitlab.com/gitlab-org/gitlab}{gitlab.com/gitlab-org/gitlab}
        \begin{itemize}
            \item Fixed database migration query performance affecting 50M+ users.
            \item Implemented asynchronous background runner for webhook events.
        \end{itemize}

        \textbf{Yatoro CLI} $|$ \textit{Creator \& Lead Maintainer} \hfill \href{https://github.com/example/yatoro}{github.com/example/yatoro}
        \begin{itemize}
            \item Authored high-throughput terminal-based AI runner in Go and Rust.
        \end{itemize}
        \end{document}
        """
        parser = LatexResumeParser(tex)
        data = parser.parse()

        self.assertEqual(len(data.open_source), 2)
        os1 = data.open_source[0]
        self.assertEqual(os1.project, "GitLab Core")
        self.assertEqual(os1.role, "Core Contributor")
        self.assertEqual(os1.url, "https://gitlab.com/gitlab-org/gitlab")
        self.assertEqual(len(os1.highlights), 2)

        os2 = data.open_source[1]
        self.assertEqual(os2.project, "Yatoro CLI")
        self.assertEqual(os2.role, "Creator & Lead Maintainer")
        self.assertEqual(os2.url, "https://github.com/example/yatoro")
        self.assertEqual(len(os2.highlights), 1)


if __name__ == "__main__":
    unittest.main()
