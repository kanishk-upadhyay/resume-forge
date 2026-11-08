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


if __name__ == "__main__":
    unittest.main()
