"""ATS Keyword Scanner, Readability Analyzer, and Single-Page Budget Inspector."""

import re
from typing import Dict, List, Any
from .schema import ResumeData

STRONG_ACTION_VERBS = {
    "accelerated", "achieved", "analyzed", "architected", "authored", "automated",
    "boosted", "built", "centralized", "championed", "co-authored", "co-founded",
    "collaborated", "conducted", "constructed", "created", "cut", "debugged",
    "decreased", "delivered", "deployed", "designed", "developed", "diagnosed",
    "directed", "drove", "earned", "engineered", "enhanced", "established",
    "executed", "formulated", "founded", "generated", "guided", "headed",
    "implemented", "improved", "increased", "initiated", "installed", "integrated",
    "launched", "led", "leveraged", "maintained", "managed", "mentored",
    "migrated", "modeled", "modernized", "monitored", "negotiated", "optimized",
    "orchestrated", "overhauled", "patched", "pioneered", "published", "quantified",
    "re-architected", "reduced", "refactored", "resolved", "restructured", "revamped",
    "saved", "scaled", "secured", "spearheaded", "standardized", "streamlined",
    "strengthened", "tested", "trained"
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
    "preferred", "years", "role", "work", "candidate", "responsibilities", "qualifications", "experience",
    "needed", "ability", "strong", "plus", "plus+", "knowledge"
}

AI_CLICHE_WORDS = {
    "spearheaded", "synergized", "leveraged", "pioneered", "passionate",
    "results-driven", "hardworking", "detail-oriented", "team-player",
    "self-starter", "dynamic", "thought-leader", "utilized", "assisted with",
    "helped to", "responsible for", "seasoned"
}


class ATSAnalyzer:
    """Analyzes resume data for ATS compatibility, action verbs, metrics, and page budgeting."""

    def __init__(self, data: ResumeData):
        self.data = data

    def analyze(self, job_description: str = "") -> Dict[str, Any]:
        """Runs a complete ATS audit of the resume."""
        score = 100
        suggestions = []
        strengths = []

        # 1. Contact Info Audit
        b = self.data.basics
        if not b.name:
            score -= 20
            suggestions.append("Missing candidate name.")
        if not b.email:
            score -= 15
            suggestions.append("Missing email address.")
        if not b.phone:
            score -= 10
            suggestions.append("Missing phone number.")
        if not b.profiles:
            score -= 5
            suggestions.append("Consider adding GitHub or LinkedIn profile links.")
        else:
            strengths.append(f"Contains {len(b.profiles)} active profile links.")

        # 2. Section Checks
        if not self.data.work:
            score -= 15
            suggestions.append("No work experience or internships detected.")
        else:
            strengths.append(f"{len(self.data.work)} experience roles listed.")

        if not self.data.education:
            score -= 10
            suggestions.append("No education section detected.")
        else:
            strengths.append("Education section clearly specified.")

        if not self.data.skills:
            score -= 10
            suggestions.append("No categorized skills section detected.")
        else:
            total_skills = sum(len(s.keywords) for s in self.data.skills)
            strengths.append(f"{total_skills} technical skills categorized across {len(self.data.skills)} domains.")

        # 3. Action Verb & Impact Metric Audit
        all_bullets = []
        for w in self.data.work:
            all_bullets.extend(w.highlights)
        for p in self.data.projects:
            all_bullets.extend(p.highlights)
        for os_item in self.data.open_source:
            all_bullets.extend(os_item.highlights)

        action_verb_count = 0
        metric_count = 0

        metric_pattern = re.compile(
            r'(?:\b\d+(?:\.\d+)?%(?!\w)|\$\d+(?:\.\d+)?[kKmMbB]?|\b\d+(?:\.\d+)?\s*(?:x|X)\b|\b\d+(?:\.\d+)?(?:,\d+)*\s*[kKmMbB]?(?:\+)?\s*(?:users|requests|qps|rps|ms|seconds|minutes|hours|days|lines|stars|commits|prs|tests|benchmarks|queries|downloads|clients|subscribers)\b)',
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

        total_bullets = len(all_bullets)
        if total_bullets > 0:
            verb_pct = (action_verb_count / total_bullets) * 100
            if verb_pct < 50:
                score -= 10
                suggestions.append(f"Only {int(verb_pct)}% of bullets begin with strong action verbs. Use verbs like 'Engineered', 'Optimized', 'Standardized'.")
            else:
                strengths.append(f"{int(verb_pct)}% of bullet points start with strong action verbs.")

            if metric_count >= 1:
                strengths.append(f"{metric_count} bullets contain quantifiable impact metrics.")
            if metric_count < 2:
                suggestions.append("Consider adding more quantifiable metrics (e.g. 'reduced latency by 40%', 'served 10,000+ users', 'improved throughput').")

        # 4. Anti-AI Buzzword & Cliché Audit
        found_cliches = []
        for bullet in all_bullets:
            bullet_lower = bullet.lower()
            for cliche in AI_CLICHE_WORDS:
                if re.search(rf'\b{re.escape(cliche)}\b', bullet_lower):
                    if cliche not in found_cliches:
                        found_cliches.append(cliche)

        if found_cliches:
            score -= min(10, len(found_cliches) * 2)
            suggestions.append(f"Detected {len(found_cliches)} weak buzzwords ({', '.join(found_cliches)}). Replace with concrete technical verbs (e.g. 'architected', 'diagnosed', 'refactored').")
        else:
            strengths.append("Zero AI clichés or generic buzzwords detected.")

        # 5. Job Description Keyword Matching (Optional)
        matched_keywords = []
        missing_keywords = []
        match_rate = 100
        if job_description:
            jd_lower = job_description.lower()
            special_matched = [tok for tok in SPECIAL_TECH_TOKENS if tok in jd_lower]

            raw_jd_words = set(re.findall(r'\b[a-zA-Z]{3,}\b|\b[a-zA-Z]{1,2}\b', jd_lower))
            target_keywords = list(special_matched) + [
                w for w in raw_jd_words
                if (w in SHORT_TECH_TERMS or (len(w) >= 3 and w not in STOP_WORDS))
            ]
            resume_text = " ".join([
                b.name, b.summary,
                " ".join(all_bullets),
                " ".join([k for s in self.data.skills for k in s.keywords])
            ]).lower()

            for kw in target_keywords:
                if kw in SPECIAL_TECH_TOKENS:
                    if kw in resume_text:
                        matched_keywords.append(kw)
                    else:
                        missing_keywords.append(kw)
                elif len(kw) <= 2:
                    if re.search(rf'\b{re.escape(kw)}\b', resume_text):
                        matched_keywords.append(kw)
                    else:
                        missing_keywords.append(kw)
                else:
                    if kw in resume_text:
                        matched_keywords.append(kw)
                    else:
                        missing_keywords.append(kw)

            if target_keywords:
                match_rate = int((len(matched_keywords) / max(1, len(target_keywords))) * 100)
                if match_rate >= 70:
                    strengths.append(f"High JD keyword match: {match_rate}% keyword alignment.")

        # 6. Page Budget Estimation (assuming letter size, 10pt font)
        # Roughly 48-52 content lines fit on a single page with 0.4in margins
        estimated_lines = 4  # Header
        estimated_lines += len(self.data.education) * 3 + sum(len(e.highlights) for e in self.data.education)
        estimated_lines += len(self.data.work) * 3 + sum(len(w.highlights) for w in self.data.work)
        estimated_lines += len(self.data.open_source) * 2 + sum(len(o.highlights) for o in self.data.open_source)
        estimated_lines += len(self.data.projects) * 3 + sum(len(p.highlights) for p in self.data.projects)
        estimated_lines += len(self.data.skills) * 2

        page_budget_pct = min(150, int((estimated_lines / 50.0) * 100))
        page_status = "Optimal (Single Page)"
        if page_budget_pct > 105:
            page_status = "Warning: Likely overflowing to Page 2"
            suggestions.append(f"Content volume is at {page_budget_pct}% of a single page. Trim 3-5 bullets or reduce line-height to guarantee 1-page fit.")
        elif page_budget_pct < 70:
            page_status = "Spare Room: Plenty of space for more projects or metrics"

        return {
            "score": max(20, min(100, score)),
            "match_rate_percent": match_rate,
            "page_budget_percent": page_budget_pct,
            "page_status": page_status,
            "estimated_lines": estimated_lines,
            "strengths": strengths,
            "suggestions": suggestions,
            "cliches_detected": found_cliches,
            "matched_keywords": matched_keywords[:15],
            "missing_keywords": missing_keywords[:10]
        }

    @property
    def experience_count(self) -> int:
        return len(self.data.work)
