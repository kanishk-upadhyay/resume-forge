"""Structural AST Diffing and Comparison Engine for ResumeForge."""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
import difflib

from .schema import ResumeData, WorkItem, ProjectItem, SkillItem, EducationItem
from .ats import ATSAnalyzer


@dataclass
class BulletDiff:
    status: str  # 'added', 'removed', 'modified', 'unchanged'
    old_text: str = ""
    new_text: str = ""


@dataclass
class WorkDiff:
    name: str
    status: str  # 'added', 'removed', 'modified', 'unchanged'
    old_position: str = ""
    new_position: str = ""
    bullets: List[BulletDiff] = field(default_factory=list)


@dataclass
class ProjectDiff:
    name: str
    status: str  # 'added', 'removed', 'modified', 'unchanged'
    old_keywords: List[str] = field(default_factory=list)
    new_keywords: List[str] = field(default_factory=list)
    bullets: List[BulletDiff] = field(default_factory=list)


@dataclass
class ResumeDiffResult:
    """Detailed structural diff between two resumes."""
    basics_changed: Dict[str, Dict[str, str]] = field(default_factory=dict)
    work: List[WorkDiff] = field(default_factory=list)
    projects: List[ProjectDiff] = field(default_factory=list)
    skills_added: Dict[str, List[str]] = field(default_factory=dict)
    skills_removed: Dict[str, List[str]] = field(default_factory=dict)
    score_before: int = 0
    score_after: int = 0
    score_delta: int = 0
    metrics_before: int = 0
    metrics_after: int = 0
    budget_before: int = 0
    budget_after: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "basics_changed": self.basics_changed,
            "work": [
                {
                    "name": w.name,
                    "status": w.status,
                    "old_position": w.old_position,
                    "new_position": w.new_position,
                    "bullets": [
                        {"status": b.status, "old": b.old_text, "new": b.new_text}
                        for b in w.bullets
                    ]
                }
                for w in self.work
            ],
            "projects": [
                {
                    "name": p.name,
                    "status": p.status,
                    "old_keywords": p.old_keywords,
                    "new_keywords": p.new_keywords,
                    "bullets": [
                        {"status": b.status, "old": b.old_text, "new": b.new_text}
                        for b in p.bullets
                    ]
                }
                for p in self.projects
            ],
            "skills_added": self.skills_added,
            "skills_removed": self.skills_removed,
            "ats": {
                "score_before": self.score_before,
                "score_after": self.score_after,
                "score_delta": self.score_delta,
                "metrics_before": self.metrics_before,
                "metrics_after": self.metrics_after,
                "page_budget_before": self.budget_before,
                "page_budget_after": self.budget_after,
            }
        }

    def format_terminal(self, color: bool = True) -> str:
        """Renders color-coded ANSI terminal representation of the structural diff."""
        C_GREEN = "\033[92m" if color else ""
        C_RED = "\033[91m" if color else ""
        C_YELLOW = "\033[93m" if color else ""
        C_BLUE = "\033[94m" if color else ""
        C_BOLD = "\033[1m" if color else ""
        C_RESET = "\033[0m" if color else ""

        lines = []
        lines.append(f"\n{C_BOLD}======================================================================{C_RESET}")
        lines.append(f"  {C_BOLD}RESUME FORGE - STRUCTURAL AST COMPARISON{C_RESET}")
        lines.append(f"{C_BOLD}======================================================================{C_RESET}")

        # 1. ATS Score delta
        delta_str = f"+{self.score_delta}" if self.score_delta > 0 else f"{self.score_delta}"
        delta_color = C_GREEN if self.score_delta > 0 else (C_RED if self.score_delta < 0 else C_RESET)
        lines.append(f"ATS Score Delta      : {self.score_before} ➔ {self.score_after} ({delta_color}{delta_str} pts{C_RESET})")
        lines.append(f"Page Budget Delta    : {self.budget_before}% ➔ {self.budget_after}%")
        lines.append(f"Impact Metrics       : {self.metrics_before} ➔ {self.metrics_after}")

        # 2. Basics
        if self.basics_changed:
            lines.append(f"\n{C_BOLD}[Basics & Contact]{C_RESET}")
            for k, v in self.basics_changed.items():
                lines.append(f"  {C_YELLOW}~ {k}{C_RESET}: {C_RED}{v['old']}{C_RESET} ➔ {C_GREEN}{v['new']}{C_RESET}")

        # 3. Work
        if self.work:
            lines.append(f"\n{C_BOLD}[Work Experience]{C_RESET}")
            for w in self.work:
                if w.status == "added":
                    lines.append(f"  {C_GREEN}+ [Added Role] {w.name} ({w.new_position}){C_RESET}")
                    for b in w.bullets:
                        lines.append(f"      {C_GREEN}+ {b.new_text}{C_RESET}")
                elif w.status == "removed":
                    lines.append(f"  {C_RED}- [Removed Role] {w.name} ({w.old_position}){C_RESET}")
                elif w.status == "modified":
                    pos_note = f": {w.old_position} ➔ {w.new_position}" if w.old_position != w.new_position else ""
                    lines.append(f"  {C_YELLOW}~ {w.name}{pos_note}{C_RESET}")
                    for b in w.bullets:
                        if b.status == "added":
                            lines.append(f"      {C_GREEN}+ {b.new_text}{C_RESET}")
                        elif b.status == "removed":
                            lines.append(f"      {C_RED}- {b.old_text}{C_RESET}")
                        elif b.status == "modified":
                            lines.append(f"      {C_RED}- {b.old_text}{C_RESET}")
                            lines.append(f"      {C_GREEN}+ {b.new_text}{C_RESET}")

        # 4. Projects
        if self.projects:
            lines.append(f"\n{C_BOLD}[Projects]{C_RESET}")
            for p in self.projects:
                if p.status == "added":
                    lines.append(f"  {C_GREEN}+ [Added Project] {p.name}{C_RESET}")
                elif p.status == "removed":
                    lines.append(f"  {C_RED}- [Removed Project] {p.name}{C_RESET}")
                elif p.status == "modified":
                    lines.append(f"  {C_YELLOW}~ {p.name}{C_RESET}")
                    for b in p.bullets:
                        if b.status == "added":
                            lines.append(f"      {C_GREEN}+ {b.new_text}{C_RESET}")
                        elif b.status == "removed":
                            lines.append(f"      {C_RED}- {b.old_text}{C_RESET}")
                        elif b.status == "modified":
                            lines.append(f"      {C_RED}- {b.old_text}{C_RESET}")
                            lines.append(f"      {C_GREEN}+ {b.new_text}{C_RESET}")

        # 5. Skills
        if self.skills_added or self.skills_removed:
            lines.append(f"\n{C_BOLD}[Skills]{C_RESET}")
            for cat, kws in self.skills_added.items():
                lines.append(f"  {C_GREEN}+ {cat}: {', '.join(kws)}{C_RESET}")
            for cat, kws in self.skills_removed.items():
                lines.append(f"  {C_RED}- {cat}: {', '.join(kws)}{C_RESET}")

        lines.append(f"{C_BOLD}======================================================================{C_RESET}\n")
        return "\n".join(lines)


class ResumeDiffEngine:
    """Computes AST-level diffs between two ResumeData instances."""

    @classmethod
    def diff(cls, old_data: ResumeData, new_data: ResumeData) -> ResumeDiffResult:
        result = ResumeDiffResult()

        # 1. Compare Basics
        b1, b2 = old_data.basics, new_data.basics
        for attr in ("name", "email", "phone", "summary"):
            v1, v2 = getattr(b1, attr, "") or "", getattr(b2, attr, "") or ""
            if v1 != v2:
                result.basics_changed[attr] = {"old": v1, "new": v2}

        # 2. Compare Work
        old_work_map = {w.name.lower().strip(): w for w in old_data.work}
        new_work_map = {w.name.lower().strip(): w for w in new_data.work}

        # Check removed and modified work
        for key, w_old in old_work_map.items():
            if key not in new_work_map:
                result.work.append(WorkDiff(name=w_old.name, status="removed", old_position=w_old.position))
            else:
                w_new = new_work_map[key]
                bullet_diffs = cls._diff_bullets(w_old.highlights, w_new.highlights)
                pos_changed = (w_old.position != w_new.position)
                if bullet_diffs or pos_changed:
                    result.work.append(WorkDiff(
                        name=w_new.name,
                        status="modified",
                        old_position=w_old.position,
                        new_position=w_new.position,
                        bullets=bullet_diffs
                    ))

        # Check added work
        for key, w_new in new_work_map.items():
            if key not in old_work_map:
                b_diffs = [BulletDiff(status="added", new_text=b) for b in w_new.highlights]
                result.work.append(WorkDiff(
                    name=w_new.name,
                    status="added",
                    new_position=w_new.position,
                    bullets=b_diffs
                ))

        # 3. Compare Projects
        old_proj_map = {p.name.lower().strip(): p for p in old_data.projects}
        new_proj_map = {p.name.lower().strip(): p for p in new_data.projects}

        for key, p_old in old_proj_map.items():
            if key not in new_proj_map:
                result.projects.append(ProjectDiff(name=p_old.name, status="removed"))
            else:
                p_new = new_proj_map[key]
                bullet_diffs = cls._diff_bullets(p_old.highlights, p_new.highlights)
                if bullet_diffs:
                    result.projects.append(ProjectDiff(
                        name=p_new.name,
                        status="modified",
                        old_keywords=p_old.keywords,
                        new_keywords=p_new.keywords,
                        bullets=bullet_diffs
                    ))

        for key, p_new in new_proj_map.items():
            if key not in old_proj_map:
                b_diffs = [BulletDiff(status="added", new_text=b) for b in p_new.highlights]
                result.projects.append(ProjectDiff(
                    name=p_new.name,
                    status="added",
                    new_keywords=p_new.keywords,
                    bullets=b_diffs
                ))

        # 4. Compare Skills
        old_skills_map = {s.name.lower().strip(): set(s.keywords) for s in old_data.skills}
        new_skills_map = {s.name.lower().strip(): set(s.keywords) for s in new_data.skills}

        all_cats = set(old_skills_map.keys()) | set(new_skills_map.keys())
        for cat in all_cats:
            k1 = old_skills_map.get(cat, set())
            k2 = new_skills_map.get(cat, set())
            added = sorted(list(k2 - k1))
            removed = sorted(list(k1 - k2))
            if added:
                result.skills_added[cat.title()] = added
            if removed:
                result.skills_removed[cat.title()] = removed

        # 5. Calculate ATS scores
        ats1 = ATSAnalyzer(old_data).analyze()
        ats2 = ATSAnalyzer(new_data).analyze()

        result.score_before = ats1["score"]
        result.score_after = ats2["score"]
        result.score_delta = ats2["score"] - ats1["score"]
        result.budget_before = ats1["page_budget_percent"]
        result.budget_after = ats2["page_budget_percent"]

        # Metric counts
        result.metrics_before = sum(1 for s in ats1["strengths"] if "impact metrics" in s.lower())
        result.metrics_after = sum(1 for s in ats2["strengths"] if "impact metrics" in s.lower())

        return result

    @classmethod
    def _diff_bullets(cls, old_bullets: List[str], new_bullets: List[str]) -> List[BulletDiff]:
        diffs = []
        matcher = difflib.SequenceMatcher(None, old_bullets, new_bullets)
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == "equal":
                continue
            elif tag == "replace":
                for old_b, new_b in zip(old_bullets[i1:i2], new_bullets[j1:j2]):
                    diffs.append(BulletDiff(status="modified", old_text=old_b, new_text=new_b))
                if (i2 - i1) > (j2 - j1):
                    for old_b in old_bullets[i1 + (j2 - j1):i2]:
                        diffs.append(BulletDiff(status="removed", old_text=old_b))
                elif (j2 - j1) > (i2 - i1):
                    for new_b in new_bullets[j1 + (i2 - i1):j2]:
                        diffs.append(BulletDiff(status="added", new_text=new_b))
            elif tag == "delete":
                for old_b in old_bullets[i1:i2]:
                    diffs.append(BulletDiff(status="removed", old_text=old_b))
            elif tag == "insert":
                for new_b in new_bullets[j1:j2]:
                    diffs.append(BulletDiff(status="added", new_text=new_b))
        return diffs
