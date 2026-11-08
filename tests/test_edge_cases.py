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


if __name__ == "__main__":
    unittest.main()
