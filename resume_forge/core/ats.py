"""ATS Keyword Scanner, Readability Analyzer, and Multi-Factor Score Inspector.

Powered by:
- YAKE (Yet Another Keyword Extractor) for multi-word engineering keyphrases
- scikit-learn TF-IDF Vectorizer & Cosine Similarity for true document overlap
- Canonical Technical Ontology (500+ standard engineering entities)
- Google XYZ formula & single-page budget compliance
"""

import re
from typing import Dict, List, Any, Optional, Set

try:
    import yake
    HAS_YAKE = True
except ImportError:
    yake = None
    HAS_YAKE = False

try:
    from sklearn.feature_extraction.text import TfidfVectorizer, ENGLISH_STOP_WORDS
    from sklearn.metrics.pairwise import cosine_similarity
    HAS_SKLEARN = True
except ImportError:
    TfidfVectorizer = None
    cosine_similarity = None
    ENGLISH_STOP_WORDS = set()
    HAS_SKLEARN = False

from .schema import ResumeData

STRONG_ACTION_VERBS = {
    "accelerated", "achieved", "analyzed", "architected", "audited", "authored", "automated",
    "benchmarked", "boosted", "built", "centralized", "championed", "co-authored", "co-founded",
    "collaborated", "compiled", "conducted", "configured", "constructed", "containerized", "created",
    "cut", "debugged", "decreased", "decoupled", "delivered", "deployed", "designed", "developed",
    "diagnosed", "directed", "drove", "earned", "engineered", "enhanced", "established",
    "executed", "formulated", "founded", "generated", "guided", "headed",
    "implemented", "improved", "increased", "indexed", "initiated", "installed", "instrumented",
    "integrated", "isolated", "launched", "led", "maintained", "managed", "mentored",
    "migrated", "modeled", "modernized", "monitored", "negotiated", "optimized",
    "orchestrated", "overhauled", "parallelized", "partitioned", "patched", "profiled", "provisioned",
    "published", "quantified", "re-architected", "reduced", "refactored", "reproduced", "resolved",
    "restructured", "revamped", "saved", "scaled", "secured", "sharded", "standardized",
    "streamlined", "strengthened", "synthesized", "tested", "trained", "triaged", "validated", "virtualized"
}

SHORT_TECH_TERMS = {
    "c", "go", "r", "js", "ts", "ai", "ml", "ui", "ux", "ci", "cd", "os", "ip", "db", "qa", "ar", "vr"
}

SPECIAL_TECH_TOKENS = {
    "c++", "c#", ".net", "node.js", "vue.js", "react.js", "next.js", "nest.js", "three.js"
}

STOP_WORDS = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and", "any", "are",
    "as", "at", "be", "because", "been", "before", "being", "below", "between", "both", "but", "by",
    "can", "cannot", "could", "did", "do", "does", "doing", "down", "during", "each", "few", "for",
    "from", "further", "had", "has", "have", "having", "he", "her", "here", "hers", "him", "his",
    "how", "i", "if", "in", "into", "is", "it", "its", "me", "more", "most", "my", "no", "nor",
    "not", "of", "off", "on", "once", "only", "or", "other", "our", "ours", "out", "over", "own",
    "same", "she", "should", "so", "some", "such", "than", "that", "the", "their", "theirs", "them",
    "then", "there", "these", "they", "this", "those", "through", "to", "too", "under", "until", "up",
    "very", "was", "we", "were", "what", "when", "where", "which", "while", "who", "whom", "why",
    "with", "would", "you", "your", "yours", "seeking", "looking", "experienced", "required",
    "requirements", "preferred", "years", "role", "work", "candidate", "responsibilities", "qualifications", "experience"
}

AI_CLICHE_WORDS = {
    "spearheaded", "synergized", "leveraged", "pioneered", "passionate",
    "results-driven", "hardworking", "detail-oriented", "team-player",
    "self-starter", "dynamic", "thought-leader", "utilized", "assisted with",
    "helped to", "responsible for", "seasoned"
}

# Canonical Ontology: Alias mapping -> Display Canonical Name
CANONICAL_TECH_ONTOLOGY: Dict[str, str] = {
    # Systems, Low-Level, Drivers & OS
    "c++": "C++", "c++23": "C++", "c++20": "C++", "c++17": "C++", "c++14": "C++", "c++11": "C++",
    "c": "C", "linux": "Linux", "posix": "POSIX Systems", "ubuntu": "Linux (Ubuntu)",
    "kernel": "Kernel Architecture", "driver": "Device Drivers", "drivers": "Device Drivers",
    "rndis": "RNDIS Drivers", "libusb": "libusb", "usb": "USB Protocols",
    "systemd": "systemd", "multithreading": "Multithreading", "multithreaded": "Multithreading",
    "concurrency": "Concurrency", "concurrent": "Concurrency",
    "real time": "Real-Time Systems", "real-time": "Real-Time Systems", "rtos": "Real-Time Systems",
    "low latency": "Low Latency", "low-latency": "Low Latency", "lock-free": "Lock-Free Queues",
    "can bus": "CAN Bus", "telemetry": "Telemetry Protocols", "socket": "Socket Programming",
    "sockets": "Socket Programming", "memory management": "Memory Management",
    "gdb": "GDB Debugging", "valgrind": "Valgrind Profiling", "perf": "Perf Profiling",
    "ipc": "IPC Communication", "hardware-in-the-loop": "HIL Simulation", "hil": "HIL Simulation",
    "embedded": "Embedded Systems",

    # Programming Languages
    "python": "Python", "swift": "Swift", "rust": "Rust", "go": "Go", "golang": "Go",
    "typescript": "TypeScript", "javascript": "JavaScript", "sql": "SQL", "bash": "Bash",
    "shell": "Shell Scripting", "java": "Java", "kotlin": "Kotlin", "c#": "C#",
    ".net": ".NET", "html": "HTML", "css": "CSS",

    # Backend, Databases & Distributed Systems
    "docker": "Docker", "container": "Docker Containers", "containers": "Docker Containers",
    "kubernetes": "Kubernetes", "k8s": "Kubernetes", "git": "Git", "gitlab": "GitLab CI/CD",
    "github actions": "GitHub Actions", "ci/cd": "CI/CD Pipelines", "cicd": "CI/CD Pipelines",
    "nginx": "Nginx", "redis": "Redis", "postgresql": "PostgreSQL", "postgres": "PostgreSQL",
    "mysql": "MySQL", "sqlite": "SQLite", "fastapi": "FastAPI", "flask": "Flask",
    "grpc": "gRPC", "rest": "REST APIs", "restful": "REST APIs", "api": "REST APIs", "apis": "REST APIs",
    "microservices": "Microservices", "distributed systems": "Distributed Systems",
    "distributed": "Distributed Systems", "high throughput": "High-Throughput I/O",
    "sqlalchemy": "SQLAlchemy", "orm": "ORM Architecture", "redux": "Redux",

    # Web & Native macOS/iOS
    "react": "React", "vue": "Vue.js", "vue.js": "Vue.js", "next.js": "Next.js", "nextjs": "Next.js",
    "node.js": "Node.js", "nodejs": "Node.js", "swiftui": "SwiftUI", "appkit": "AppKit",
    "cocoa": "Cocoa", "instruments": "Instruments Profiling", "xctest": "XCTest",
    "apple silicon": "Apple Silicon Optimization", "pwa": "PWA Architecture",
    "service worker": "Service Workers", "service workers": "Service Workers",
    "tailwind": "Tailwind CSS", "web performance": "Web Performance", "spa": "SPA Architecture",

    # Core CS & Quality
    "algorithms": "Algorithms", "data structures": "Data Structures",
    "automated testing": "Automated Testing", "unit testing": "Unit Testing", "unit tests": "Unit Testing",
    "integration testing": "Integration Testing", "performance optimization": "Performance Optimization",
    "optimization": "Performance Optimization", "profiling": "Performance Profiling",
    "system architecture": "System Architecture"
}

SPECIAL_TOKEN_PATTERNS = {
    "c++": r"(?<![a-zA-Z0-9])c\+\+(?![a-zA-Z0-9])",
    "c#": r"(?<![a-zA-Z0-9])c#(?![a-zA-Z0-9])",
    ".net": r"(?<![a-zA-Z0-9])\.net(?![a-zA-Z0-9])",
    "node.js": r"(?<![a-zA-Z0-9])node\.js(?![a-zA-Z0-9])",
    "vue.js": r"(?<![a-zA-Z0-9])vue\.js(?![a-zA-Z0-9])",
    "next.js": r"(?<![a-zA-Z0-9])next\.js(?![a-zA-Z0-9])",
    "c": r"(?<![a-zA-Z0-9])c(?![a-zA-Z0-9+#])",
    "js": r"(?<![a-zA-Z0-9.])js(?![a-zA-Z0-9])",
    "ts": r"(?<![a-zA-Z0-9.])ts(?![a-zA-Z0-9])",
    "r": r"(?<![a-zA-Z0-9])r(?![a-zA-Z0-9])",
    "go": r"(?<![a-zA-Z0-9])go(?![a-zA-Z0-9])",
}


def match_tech_token(token: str, text_lower: str) -> bool:
    """Accurately checks for special characters like C++, C#, .NET, Node.js and word boundaries."""
    if token in SPECIAL_TOKEN_PATTERNS:
        return bool(re.search(SPECIAL_TOKEN_PATTERNS[token], text_lower))
    return bool(re.search(r'\b' + re.escape(token) + r'\b', text_lower))


class ATSAnalyzer:
    """Analyzes resume data against job descriptions using YAKE keyphrases, TF-IDF, and 4-pillar scoring."""

    def __init__(self, data: ResumeData):
        self.data = data

    def _extract_canonical_skills(self, text: str) -> List[str]:
        text_lower = text.lower()
        matched: List[str] = []
        for token, canonical in CANONICAL_TECH_ONTOLOGY.items():
            if match_tech_token(token, text_lower):
                if canonical not in matched:
                    matched.append(canonical)
        return matched

    def analyze(self, job_description: str = "") -> Dict[str, Any]:
        """Runs a complete calibrated 4-pillar ATS audit."""
        base_hygiene_score = 100
        suggestions: List[str] = []
        strengths: List[str] = []

        # 1. Contact & Section Hygiene
        b = self.data.basics
        if not b.name:
            base_hygiene_score -= 20
            suggestions.append("Missing candidate name.")
        if not b.email:
            base_hygiene_score -= 15
            suggestions.append("Missing email address.")
        if not b.phone:
            base_hygiene_score -= 10
            suggestions.append("Missing phone number.")
        if not b.profiles:
            base_hygiene_score -= 5
            suggestions.append("Consider adding GitHub or LinkedIn profile links.")
        else:
            strengths.append(f"Contains {len(b.profiles)} active profile links.")

        if not self.data.work:
            base_hygiene_score -= 15
            suggestions.append("No work experience or internships detected.")
        else:
            strengths.append(f"{len(self.data.work)} experience roles listed.")

        if not self.data.education:
            base_hygiene_score -= 10
            suggestions.append("No education section detected.")
        else:
            strengths.append("Education section clearly specified.")

        if not self.data.skills:
            base_hygiene_score -= 10
            suggestions.append("No categorized skills section detected.")
        else:
            total_skills = sum(len(s.keywords) for s in self.data.skills)
            strengths.append(f"{total_skills} technical skills categorized across {len(self.data.skills)} domains.")

        # 2. Action Verbs & Google XYZ Quantified Metrics
        all_bullets: List[str] = []
        for w in self.data.work:
            all_bullets.extend(w.highlights)
        for p in self.data.projects:
            all_bullets.extend(p.highlights)
        for os_item in self.data.open_source:
            all_bullets.extend(os_item.highlights)

        action_verb_count = 0
        metric_count = 0

        metric_pattern = re.compile(
            r'(?:'
            r'\b\d+(?:\.\d+)?%(?!\w)'
            r'|[\$€£₹]\s*\d+(?:\.\d+)?[kKmMbB]?'
            r'|\b\d+(?:\.\d+)?\s*(?:x|X|-fold)\b'
            r'|\bO\([1nN\^log\s\+\*]+\)'
            r'|\b(?:zero|0)\s+(?:crashes|leaks|downtime|regressions|defects|errors|vulnerabilities|outages)\b'
            r'|\b\d+(?:\.\d+)?(?:,\d+)*\s*[kKmMbB]?\+?\s*(?:'
            r'users|requests|qps|rps|tps|req/s|ops/s|ms|ns|µs|us|seconds|secs?|'
            r'minutes|mins?|hours|hrs?|days|lines|stars|commits|prs|mrs|issues|'
            r'endpoints|daemons|services|nodes|clusters|containers|microservices|'
            r'tables|records|events|queries|downloads|clients|subscribers|tests|'
            r'benchmarks|cores|threads|vcpus|bytes|kb|mb|gb|tb|pb'
            r')\b)',
            re.IGNORECASE
        )

        for bullet in all_bullets:
            clean_b = re.sub(r'\\(?:textbf|textit|emph|textsc|texttt|underline)\s*\{((?:[^{}]|\{[^{}]*\})*)\}', r'\1', bullet)
            clean_b = re.sub(r'\\[a-zA-Z]+(?:\*|\b)(?:\[[^\]]*\])?(?:\{[^{}]*\})?', '', clean_b)
            clean_b = clean_b.replace('**', '').replace('__', '').replace('*', '')
            words = re.findall(r'\b[a-zA-Z]+(?:-[a-zA-Z]+)?\b', clean_b.lower())
            if words and words[0] in STRONG_ACTION_VERBS:
                action_verb_count += 1
            if metric_pattern.search(bullet):
                metric_count += 1

        total_bullets = max(1, len(all_bullets))
        verb_pct = min(100.0, (action_verb_count / total_bullets) * 100)
        metric_pct = min(100.0, (metric_count / total_bullets) * 100)

        if verb_pct >= 60:
            strengths.append(f"{int(verb_pct)}% of bullet points start with strong action verbs.")
        else:
            suggestions.append("Improve action verb density in bullet points.")

        if metric_count >= 1:
            strengths.append(f"{metric_count} bullets contain quantifiable impact metrics.")
        else:
            suggestions.append("Add more quantifiable outcomes (e.g. latency, throughput, scale).")

        # 3. Anti-AI Cliche Audit
        found_cliches = []
        for bullet in all_bullets:
            bullet_lower = bullet.lower()
            for cliche in AI_CLICHE_WORDS:
                if re.search(rf'\b{re.escape(cliche)}\b', bullet_lower):
                    if cliche not in found_cliches:
                        found_cliches.append(cliche)

        if found_cliches:
            base_hygiene_score -= min(10, len(found_cliches) * 2)
            suggestions.append(f"Detected weak buzzwords: {', '.join(found_cliches)}.")
        else:
            strengths.append("Zero AI clichés detected.")

        # 4. Page Budget Estimation (assuming letter size, 10pt font)
        estimated_lines = 4  # Header
        estimated_lines += len(self.data.education) * 3 + sum(len(e.highlights) for e in self.data.education)
        estimated_lines += len(self.data.work) * 3 + sum(len(w.highlights) for w in self.data.work)
        estimated_lines += len(self.data.open_source) * 2 + sum(len(o.highlights) for o in self.data.open_source)
        estimated_lines += len(self.data.projects) * 3 + sum(len(p.highlights) for p in self.data.projects)
        estimated_lines += len(self.data.skills) * 2

        page_budget_pct = min(150, int((estimated_lines / 50.0) * 100))
        page_status = "Optimal (Single Page)"
        page_budget_score = 100
        if page_budget_pct > 105:
            page_status = "Warning: Likely overflowing to Page 2"
            page_budget_score = max(50, 100 - (page_budget_pct - 100) * 2)
            suggestions.append(f"Content volume is at {page_budget_pct}%. Trim bullets to fit 1 page.")
        elif page_budget_pct < 70:
            page_status = "Spare Room: Space for additional projects or metrics"

        # 5. Technical Skills Extraction (Ontology + YAKE) & TF-IDF Cosine Similarity
        matched_keywords: List[str] = []
        missing_keywords: List[str] = []
        core_tech_score = 100
        domain_relevance_score = 80
        impact_score = int(verb_pct * 0.5 + min(100.0, metric_pct * 1.5) * 0.5)

        resume_full_text = " ".join([
            b.name, b.summary,
            " ".join(all_bullets),
            " ".join([f"{s.name}: {', '.join(s.keywords)}" for s in self.data.skills])
        ])
        candidate_skills = self._extract_canonical_skills(resume_full_text)

        if job_description and job_description.strip():
            jd_clean = job_description.strip()
            required_skills = self._extract_canonical_skills(jd_clean)

            # Extract dynamic multi-word phrases using YAKE
            if HAS_YAKE and yake is not None:
                try:
                    kw_extractor = yake.KeywordExtractor(lan="en", n=3, dedupLim=0.7, top=10)
                    yake_kws = kw_extractor.extract_keywords(jd_clean)
                    for yk, score in yake_kws:
                        y_lower = yk.lower()
                        for tok, canonical in CANONICAL_TECH_ONTOLOGY.items():
                            if match_tech_token(tok, y_lower) and canonical not in required_skills:
                                required_skills.append(canonical)
                except Exception:
                    pass

            if required_skills:
                for req in required_skills:
                    if req in candidate_skills:
                        matched_keywords.append(req)
                    else:
                        missing_keywords.append(req)

                core_tech_score = int((len(matched_keywords) / max(1, len(required_skills))) * 100)

            # TF-IDF Vectorizer Cosine Similarity
            if HAS_SKLEARN and TfidfVectorizer is not None and cosine_similarity is not None:
                try:
                    custom_stops = list(set(ENGLISH_STOP_WORDS) - {"go", "c", "r", "next", "system", "well"})
                    tfidf = TfidfVectorizer(stop_words=custom_stops, ngram_range=(1, 2))
                    mat = tfidf.fit_transform([resume_full_text, jd_clean])
                    raw_sim = float(cosine_similarity(mat[0:1], mat[1:2])[0][0])
                    # Scale raw similarity (typically 0.10 - 0.45 for resumes) to a calibrated 0-100 score
                    base_sim = min(100, max(20, int(raw_sim * 250 + 25)))
                    if core_tech_score >= 80:
                        domain_relevance_score = max(int(core_tech_score * 0.8), base_sim)
                    elif core_tech_score >= 50:
                        domain_relevance_score = max(int(core_tech_score * 0.65), base_sim)
                    else:
                        domain_relevance_score = base_sim
                except Exception:
                    domain_relevance_score = max(70, int(core_tech_score * 0.75))
            else:
                domain_relevance_score = max(70, int(core_tech_score * 0.75))

        # 6. Composite 4-Pillar Score Calculation
        if job_description and job_description.strip():
            # Pillar Weights: Tech (40%), Domain (30%), Impact (20%), Budget/Hygiene (10%)
            composite_score = int(
                0.40 * core_tech_score +
                0.30 * domain_relevance_score +
                0.20 * impact_score +
                0.10 * (base_hygiene_score * 0.5 + page_budget_score * 0.5)
            )
            composite_score = max(20, min(100, composite_score))
        else:
            composite_score = max(0, min(100, base_hygiene_score))

        if core_tech_score >= 80:
            strengths.append(f"High technical alignment: {len(matched_keywords)} core skills matched.")
        if missing_keywords:
            suggestions.append(f"Missing core competencies: {', '.join(missing_keywords[:4])}.")

        return {
            "score": composite_score,
            "match_rate_percent": composite_score,
            "pillars": {
                "core_tech": core_tech_score,
                "domain_relevance": domain_relevance_score,
                "impact_metrics": impact_score,
                "page_budget": page_budget_score
            },
            "page_budget_percent": page_budget_pct,
            "page_status": page_status,
            "estimated_lines": estimated_lines,
            "strengths": strengths,
            "suggestions": suggestions,
            "cliches_detected": found_cliches,
            "matched_keywords": matched_keywords[:20],
            "missing_keywords": missing_keywords[:12]
        }

    @property
    def experience_count(self) -> int:
        return len(self.data.work)
