"""Comprehensive edge case unit tests for ResumeForge (Parser, Exporter, ATS, Compiler)."""

import unittest
from resume_forge.core.parser import LatexResumeParser, clean_latex
from resume_forge.core.exporter import ResumeExporter
from resume_forge.core.ats import ATSAnalyzer
from resume_forge.core.schema import ResumeData, Basics, WorkItem, EducationItem, ProjectItem, SkillItem


class TestEdgeCases(unittest.TestCase):

    def test_special_tech_tokens_ats_matching(self):
        """Verify C++, C#, .NET, Node.js are accurately matched without confusing with C or JS."""
        data = ResumeData(
            basics=Basics(name="Dev Expert"),
            work=[WorkItem(name="Tech", position="Dev", highlights=["Built distributed services in C++ and Node.js."])],
            skills=[SkillItem(name="Langs", keywords=["C++", "Node.js", "Python"])]
        )
        analyzer = ATSAnalyzer(data)

        # JD asks for C++, Node.js, and C#
        jd = "Seeking a senior engineer with strong C++, Node.js, and C# background."
        report = analyzer.analyze(job_description=jd)

        matched = report["matched_keywords"]
        missing = report["missing_keywords"]

        self.assertIn("c++", matched)
        self.assertIn("node.js", matched)
        self.assertIn("c#", missing)  # Candidate only has C++, not C#

    def test_comma_formatted_metrics_detection(self):
        """Verify comma-separated metrics and high volume figures are recognized."""
        data = ResumeData(
            basics=Basics(name="Scale Engineer"),
            work=[
                WorkItem(
                    name="FinTech",
                    position="Architect",
                    highlights=[
                        "Engineered payment gateway processing $1,500,000 in transactions daily.",
                        "Scaled backend microservices to handle 250,000+ requests per second with sub-5ms latency."
                    ]
                )
            ]
        )
        analyzer = ATSAnalyzer(data)
        report = analyzer.analyze()
        self.assertTrue(any("2 bullets contain quantifiable impact metrics" in s for s in report["strengths"]))

    def test_latex_exporter_no_double_escaping(self):
        """Verify already escaped characters like \\% or \\_ are not double-escaped to \\\\%."""
        data = ResumeData(
            basics=Basics(name="Escaped User", email="user_name@example.com"),
            work=[
                WorkItem(
                    name="Acme Corp",
                    position="Engineer",
                    highlights=[
                        r"Reduced API response latency by 35\% and saved \$50K in compute costs.",
                        r"Configured database\_cluster\_config with 99.9\% uptime."
                    ]
                )
            ]
        )
        exporter = ResumeExporter(data)
        tex = exporter.to_latex()

        # Should contain \% and \$ and \_, but NEVER \\% or \\$ or \\_
        self.assertIn(r"35\%", tex)
        self.assertNotIn(r"35\\%", tex)
        self.assertIn(r"\$50K", tex)
        self.assertNotIn(r"\\$50K", tex)
        self.assertIn(r"database\_cluster\_config", tex)
        self.assertNotIn(r"database\\_cluster", tex)

    def test_html_exporter_xss_and_template_tag_safety(self):
        """Verify developer generics like <T> or <templates> are escaped so they render properly in HTML."""
        data = ResumeData(
            basics=Basics(name="C++ Specialist"),
            work=[
                WorkItem(
                    name="Systems Inc",
                    position="Senior Developer",
                    highlights=[
                        "Implemented modern C++ template metaprogramming <typename T>.",
                        "Constructed microservices with Python <aiohttp> & Redis."
                    ]
                )
            ],
            skills=[SkillItem(name="Core", keywords=["C++ <templates>", "HTML & CSS"])]
        )
        exporter = ResumeExporter(data)
        html = exporter.to_html()

        # <typename T> must be escaped to &lt;typename T&gt;
        self.assertIn("&lt;typename T&gt;", html)
        self.assertNotIn("<typename T>", html)
        self.assertIn("&lt;aiohttp&gt;", html)
        self.assertIn("HTML &amp; CSS", html)

    def test_url_with_query_params_and_anchors(self):
        """Verify URLs with query params, underscores, and anchors parse cleanly."""
        raw_tex = r"""
        \documentclass{article}
        \begin{document}
        \textbf{\Huge Web Developer} \\
        \href{https://example.com/api?user_id=123&session_token=abc_xyz#overview}{Project Documentation}
        \section{Experience}
        \resumeSubheading{Lead Dev}{2024}{Tech Corp}{Remote}
        \end{document}
        """
        parser = LatexResumeParser(raw_tex)
        data = parser.parse()
        self.assertEqual(data.basics.name, "Web Developer")
        urls = [p.url for p in data.basics.profiles] + [data.basics.url]
        self.assertTrue(any("user_id=123" in u for u in urls))

    def test_sections_in_unusual_order(self):
        """Verify parser functions seamlessly when sections are inverted (Skills first, Education last)."""
        inverted_tex = r"""
        \documentclass{article}
        \begin{document}
        \textbf{\Huge Inverted Candidate} \\
        candidate@example.com

        \section{Technical Skills}
        \textbf{Languages}{: Rust, C++, Python}

        \section{Projects}
        \resumeProjectHeading{\textbf{Core Engine} $|$ \emph{Rust}}{2024}
        \resumeItemListStart
        \resumeItem{Implemented distributed raft consensus.}
        \resumeItemListEnd

        \section{Experience}
        \resumeSubheading{Consensus Corp}{Remote}{Systems Engineer}{2023 -- 2024}
        \resumeItemListStart
        \resumeItem{Optimized memory layout.}
        \resumeItemListEnd

        \section{Education}
        \resumeSubheading{MIT}{Cambridge, MA}{B.S. in Computer Science}{2019 -- 2023}
        \end{document}
        """
        parser = LatexResumeParser(inverted_tex)
        data = parser.parse()

        self.assertEqual(data.basics.name, "Inverted Candidate")
        self.assertEqual(len(data.skills), 1)
        self.assertEqual(len(data.projects), 1)
        self.assertEqual(len(data.work), 1)
        self.assertEqual(len(data.education), 1)
        self.assertEqual(data.skills[0].keywords, ["Rust", "C++", "Python"])
        self.assertEqual(data.projects[0].name, "Core Engine")

    def test_date_variations(self):
        """Verify various date format splits."""
        p = LatexResumeParser("")
        s1, e1 = p._split_dates("Aug 2023 – Present")
        self.assertEqual(s1, "Aug 2023")
        self.assertEqual(e1, "Present")

        s2, e2 = p._split_dates("2023 to 2027 (Expected)")
        self.assertEqual(s2, "2023")
        self.assertIn("2027", e2)

        s3, e3 = p._split_dates("Fall 2024")
        self.assertEqual(s3, "Fall 2024")
        self.assertEqual(e3, "")

    def test_iso_and_hyphenated_date_preservation(self):
        """Verify ISO and hyphenated month-year dates are not split internally."""
        p = LatexResumeParser("")
        s1, e1 = p._split_dates("2023-01 - 2023-08")
        self.assertEqual(s1, "2023-01")
        self.assertEqual(e1, "2023-08")

        s2, e2 = p._split_dates("2023-01-15 -- 2023-08-30")
        self.assertEqual(s2, "2023-01-15")
        self.assertEqual(e2, "2023-08-30")

        s3, e3 = p._split_dates("Jan 2022-Present")
        self.assertEqual(s3, "Jan 2022")
        self.assertEqual(e3, "Present")

    def test_diacritics_and_accents_preservation(self):
        """Verify international accents and LaTeX diacritics are properly converted to unicode."""
        self.assertEqual(clean_latex(r"Pok\'edex"), "Pokédex")
        self.assertEqual(clean_latex(r"Pok\'{e}dex"), "Pokédex")
        self.assertEqual(clean_latex(r"Luki\v{c}"), "Lukič")
        self.assertEqual(clean_latex(r"Fran\c{c}ois"), "François")
        self.assertEqual(clean_latex(r"M\"uller"), "Müller")
        self.assertEqual(clean_latex(r"M\"{u}ller"), "Müller")
        self.assertEqual(clean_latex(r"Pe\~na"), "Peña")

    def test_awesome_cv_5_arg_cventry_and_cvskill(self):
        """Verify Awesome-CV format with 5-arg \cventry and \cvskill is parsed."""
        raw = r"""
        \documentclass{awesome-cv}
        \name{Alice}{Smith}
        \position{Cloud Architect}
        \email{alice@example.com}
        \mobile{+1 555-0199}
        \github{alicesmith}
        \begin{document}
        \cvsection{Summary}
        Distributed systems architect with 8+ years experience.
        \cvsection{Experience}
        \begin{cventries}
          \cventry
            {Staff SRE}
            {CloudCorp}
            {Zurich, Switzerland}
            {Mar. 2024 - Present}
            {
              \begin{cvitems}
                \item {Designed and deployed global Kubernetes clusters.}
                \item {Reduced p99 latency by 35\% across all microservices.}
              \end{cvitems}
            }
        \end{cventries}
        \cvsection{Skills}
        \begin{cvskills}
          \cvskill
            {Languages}
            {Go, Rust, Python, C++}
        \end{cvskills}
        \end{document}
        """
        parser = LatexResumeParser(raw)
        data = parser.parse()
        self.assertEqual(data.basics.name, "Alice Smith")
        self.assertEqual(data.basics.label, "Cloud Architect")
        self.assertEqual(data.basics.email, "alice@example.com")
        self.assertIn("alicesmith", [p.username for p in data.basics.profiles])
        self.assertIn("Distributed systems architect", data.basics.summary)
        self.assertEqual(len(data.work), 1)
        self.assertEqual(data.work[0].name, "CloudCorp")
        self.assertEqual(data.work[0].position, "Staff SRE")
        self.assertEqual(len(data.work[0].highlights), 2)
        self.assertEqual(len(data.skills), 1)
        self.assertEqual(data.skills[0].keywords, ["Go", "Rust", "Python", "C++"])

    def test_hyperlinked_project_heading_nested_braces(self):
        """Verify \resumeProjectHeading with nested \textbf{\href{...}{Title}} parses without dropping."""
        raw = r"""
        \documentclass{article}
        \begin{document}
        \section{Projects}
        \resumeProjectHeading
          {\textbf{\href{https://github.com/alice/k8s-mesh}{K8sMesh}} $|$ \emph{Go, eBPF}}{Jan 2024}
        \resumeItemListStart
          \resumeItem{Engineered zero-overhead service mesh in Go.}
        \resumeItemListEnd
        \end{document}
        """
        parser = LatexResumeParser(raw)
        data = parser.parse()
        self.assertEqual(len(data.projects), 1)
        self.assertEqual(data.projects[0].name, "K8sMesh")
        self.assertEqual(data.projects[0].url, "https://github.com/alice/k8s-mesh")
        self.assertEqual(data.projects[0].keywords, ["Go", "eBPF"])
        self.assertEqual(len(data.projects[0].highlights), 1)

    def test_nested_formatting_bullets(self):
        """Verify deeply nested formatting in \resumeItem is extracted cleanly."""
        raw = r"""
        \documentclass{article}
        \begin{document}
        \section{Experience}
        \resumeSubheading{Role}{2024}{Company}{Loc}
        \resumeItemListStart
          \resumeItem{Implemented \textbf{\href{https://example.com}{\underline{ZeroCopy Engine}}} in C++.}
        \resumeItemListEnd
        \end{document}
        """
        parser = LatexResumeParser(raw)
        data = parser.parse()
        self.assertEqual(len(data.work), 1)
        self.assertEqual(len(data.work[0].highlights), 1)
        self.assertIn("Implemented ZeroCopy Engine in C++.", data.work[0].highlights[0])

    def test_tabular_skills_parsing(self):
        """Verify tabular LaTeX skills format is extracted cleanly."""
        raw = r"""
        \documentclass{article}
        \begin{document}
        \section{Skills}
        \begin{tabular}{ll}
        \textbf{Languages:} & Go, Python, C++, Rust \\
        \textbf{Cloud Tools:} & Docker, Kubernetes, Terraform \\
        \end{tabular}
        \end{document}
        """
        parser = LatexResumeParser(raw)
        data = parser.parse()
        self.assertEqual(len(data.skills), 2)
        self.assertEqual(data.skills[0].name, "Languages")
        self.assertEqual(data.skills[0].keywords, ["Go", "Python", "C++", "Rust"])
        self.assertEqual(data.skills[1].name, "Cloud Tools")

    def test_ats_formatted_bullets_and_expanded_verbs(self):
        """Verify ATS action verb detection handles \textbf, markdown bold, and compound verbs like Led, Co-founded."""
        data = ResumeData(
            basics=Basics(name="Leader Dev", email="l@example.com", phone="1234567890"),
            work=[
                WorkItem(
                    name="Startup",
                    position="Lead",
                    highlights=[
                        r"\textbf{Led} engineering team of 10 developers.",
                        "**Built** distributed cache layer serving 100,000 requests per second.",
                        "Co-founded cloud infrastructure guild across 4 business units."
                    ]
                )
            ]
        )
        analyzer = ATSAnalyzer(data)
        report = analyzer.analyze()
        self.assertTrue(any("100% of bullet points start with strong action verbs" in s for s in report["strengths"]))

    def test_tailor_mid_sentence_passive_voice(self):
        """Verify BulletTailor handles mid-sentence passive phrases appropriately."""
        from resume_forge.core.tailor import BulletTailor
        data = ResumeData(
            basics=Basics(name="Dev"),
            work=[
                WorkItem(
                    name="Corp",
                    position="Backend Dev",
                    highlights=["Built API backend and was responsible for database indexing."]
                )
            ]
        )
        tailor = BulletTailor(data)
        result = tailor.tailor(job_description="Database indexing backend")
        suggestions = result["suggestions"]
        self.assertGreaterEqual(len(suggestions), 1)
        improved = suggestions[0]["improved"]
        self.assertIn("spearheaded", improved)
        self.assertNotIn("was responsible for", improved)


if __name__ == "__main__":
    unittest.main()
