"""Resume Tailor Engine: Analyzes bullets against job descriptions and generates high-impact rewrites."""

import re
import json
import urllib.request
import urllib.error
from typing import Dict, List, Any, Optional, Tuple
from .schema import ResumeData, WorkItem, ProjectItem
from .ats import ATSAnalyzer, STRONG_ACTION_VERBS, SHORT_TECH_TERMS, STOP_WORDS

WEAK_PHRASES_MAP = {
    r"\b(?:responsible for|tasked with|assigned to)\s+": ("Engineered ", "spearheaded"),
    r"\b(?:worked on|helped with|assisted with|assisted in)\s+": ("Developed ", "accelerated"),
    r"\b(?:was involved in|participated in)\s+": ("Collaborated on ", "orchestrated"),
    r"\b(?:handled|managed routine)\s+": ("Automated and maintained ", "streamlined"),
    r"\b(?:made|did|created simple)\s+": ("Constructed ", "deployed")
}


class BulletTailor:
    """Tailors resume bullet points to align with job descriptions using offline heuristics or local LLMs."""

    def __init__(self, data: ResumeData):
        self.data = data
        self.analyzer = ATSAnalyzer(data)

    def tailor(
        self,
        job_description: str,
        provider: str = "rule_based",
        ollama_model: str = "llama3.2"
    ) -> Dict[str, Any]:
        """Analyzes all bullet points and suggests tailored improvements."""
        # 1. Extract target keywords from JD
        jd_lower = job_description.lower()
        raw_words = set(re.findall(r'\b[a-zA-Z]{3,}\b|\b[a-zA-Z]{1,2}\b', jd_lower))
        target_skills = [
            w for w in raw_words
            if (w in SHORT_TECH_TERMS or (len(w) >= 3 and w not in STOP_WORDS))
        ]

        if provider == "ollama":
            suggestions = self._tailor_ollama(job_description, ollama_model)
            if suggestions:
                return {
                    "provider": "ollama",
                    "model": ollama_model,
                    "target_skills": target_skills[:15],
                    "suggestions": suggestions
                }
            # Fallback to rule_based if Ollama unavailable
            provider = "rule_based (fallback)"

        suggestions = self._tailor_rule_based(target_skills)
        return {
            "provider": provider,
            "target_skills": target_skills[:15],
            "suggestions": suggestions
        }

    def _tailor_rule_based(self, target_skills: List[str]) -> List[Dict[str, Any]]:
        """100% offline, deterministic heuristic bullet enhancer."""
        suggestions = []
        skills_queue = [s.title() for s in target_skills]

        # Scan work experience
        for w_idx, work in enumerate(self.data.work):
            for b_idx, bullet in enumerate(work.highlights):
                suggestion = self._enhance_single_bullet(
                    bullet,
                    context=f"{work.position} @ {work.name}",
                    skills_pool=skills_queue,
                    section="work",
                    item_idx=w_idx,
                    bullet_idx=b_idx
                )
                if suggestion:
                    suggestions.append(suggestion)

        # Scan projects
        for p_idx, proj in enumerate(self.data.projects):
            for b_idx, bullet in enumerate(proj.highlights):
                suggestion = self._enhance_single_bullet(
                    bullet,
                    context=f"Project: {proj.name}",
                    skills_pool=skills_queue,
                    section="projects",
                    item_idx=p_idx,
                    bullet_idx=b_idx
                )
                if suggestion:
                    suggestions.append(suggestion)

        return suggestions

    def _enhance_single_bullet(
        self,
        bullet: str,
        context: str,
        skills_pool: List[str],
        section: str,
        item_idx: int,
        bullet_idx: int
    ) -> Optional[Dict[str, Any]]:
        """Examines an individual bullet for weak verbs, missing metrics, and missing keywords."""
        needs_improvement = False
        reasons = []
        improved = bullet.strip()

        # Check 1: Weak leading phrases
        leading_weak = [
            (r'^\s*(?:was\s+)?(?:responsible for|tasked with|assigned to)\s+', 'Engineered '),
            (r'^\s*(?:worked on|helped with|assisted with|assisted in)\s+', 'Developed '),
            (r'^\s*(?:was involved in|participated in)\s+', 'Collaborated on '),
            (r'^\s*(?:handled|managed routine)\s+', 'Automated and maintained '),
            (r'^\s*(?:made|did|created simple)\s+', 'Constructed ')
        ]
        for weak_pattern, replacement in leading_weak:
            if re.search(weak_pattern, improved, re.IGNORECASE):
                improved = re.sub(weak_pattern, replacement, improved, count=1, flags=re.IGNORECASE)
                needs_improvement = True
                reasons.append("Replaced weak or passive opening phrase with an assertive action verb.")
                break

        # Check 1b: Mid-sentence passive phrases
        mid_weak = [
            (r'\bwas responsible for\s+', 'spearheaded '),
            (r'\bresponsible for\s+', 'directing '),
            (r'\bhelped with\s+', 'accelerating '),
            (r'\bassisted in\s+', 'facilitating ')
        ]
        for weak_pattern, replacement in mid_weak:
            if re.search(weak_pattern, improved, re.IGNORECASE):
                improved = re.sub(weak_pattern, replacement, improved, count=1, flags=re.IGNORECASE)
                needs_improvement = True
                reasons.append("Replaced passive phrasing with an active verb.")
                break

        # Check 2: First word should be a strong past-tense action verb
        clean_first = re.sub(r'\\[a-zA-Z]+(?:\*|\b)(?:\[[^\]]*\])?(?:\{[^{}]*\})?', '', improved)
        clean_first = clean_first.replace('**', '').replace('__', '').replace('*', '')
        words = re.findall(r'\b[a-zA-Z]+(?:-[a-zA-Z]+)?\b', clean_first)
        if words and words[0].lower() not in STRONG_ACTION_VERBS:
            needs_improvement = True
            reasons.append(f"Opening word '{words[0]}' is not a recognized impact verb.")

        # Check 3: Missing quantifiable metrics
        has_metric = bool(re.search(
            r'(?:\b\d+(?:\.\d+)?%(?!\w)|\$\d+(?:\.\d+)?[kKmMbB]?|\b\d+(?:\.\d+)?\s*(?:x|X)\b|\b\d+(?:,\d+)*(?:\+)?\s*(?:users|requests|qps|rps|ms|seconds|minutes|hours|days|lines|stars|commits|prs|tests|benchmarks|queries)\b)',
            improved,
            re.IGNORECASE
        ))
        if not has_metric:
            needs_improvement = True
            reasons.append("Missing quantifiable outcomes or performance metrics.")
            if not improved.endswith("."):
                improved += "."
            improved += " [e.g. improving query throughput by 30% / serving 10,000+ users]."

        if needs_improvement:
            return {
                "section": section,
                "item_index": item_idx,
                "bullet_index": bullet_idx,
                "context": context,
                "original": bullet,
                "improved": improved,
                "reasons": reasons
            }

        return None

    def _tailor_ollama(self, job_description: str, model: str) -> Optional[List[Dict[str, Any]]]:
        """Calls local Ollama daemon if running on localhost:11434."""
        bullets_payload = []
        for w in self.data.work:
            for b in w.highlights:
                bullets_payload.append(f"Work ({w.position}): {b}")
        for p in self.data.projects:
            for b in p.highlights:
                bullets_payload.append(f"Project ({p.name}): {b}")

        prompt = f"""You are an elite technical resume editor.
Given this Target Job Description:
\"\"\"{job_description[:1500]}\"\"\"

Rewrite each resume bullet point to maximize impact, use strong past-tense action verbs, and highlight relevant technologies.
Return ONLY valid JSON matching this format:
[
  {{"original": "original text", "improved": "rewritten bullet starting with strong verb and metric", "rationale": "reason"}}
]

Bullet points to improve:
{json.dumps(bullets_payload[:6], indent=2)}
"""
        req_body = json.dumps({
            "model": model,
            "prompt": prompt,
            "stream": False,
            "format": "json"
        }).encode("utf-8")

        try:
            req = urllib.request.Request(
                "http://localhost:11434/api/generate",
                data=req_body,
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                response_text = data.get("response", "")
                parsed_json = json.loads(response_text)
                if isinstance(parsed_json, list):
                    return parsed_json
        except Exception:
            return None
        return None

    def apply_improvements(self, accepted_suggestions: List[Dict[str, Any]]) -> ResumeData:
        """Applies accepted bullet suggestions back onto the ResumeData object."""
        for sug in accepted_suggestions:
            sec = sug.get("section")
            i_idx = sug.get("item_index")
            b_idx = sug.get("bullet_index")
            new_text = sug.get("improved")

            if sec == "work" and i_idx < len(self.data.work):
                w = self.data.work[i_idx]
                if b_idx < len(w.highlights):
                    w.highlights[b_idx] = new_text

            elif sec == "projects" and i_idx < len(self.data.projects):
                p = self.data.projects[i_idx]
                if b_idx < len(p.highlights):
                    p.highlights[b_idx] = new_text

        return self.data
