"""LaTeX Resume Parser: Converts raw LaTeX documents into structured ResumeData."""

import re
from typing import Dict, List, Tuple, Optional, Any
from .schema import ResumeData, Basics, WorkItem, EducationItem, ProjectItem, SkillItem, OpenSourceItem, Profile, Location


def clean_latex(text: str) -> str:
    """Removes LaTeX formatting commands, escaping, and artifacts."""
    if not text:
        return ""
    
    # Replace URLs in \href{url}{label} with label, or extract both
    text = re.sub(r'\\href\{([^}]+)\}\{([^}]+)\}', r'\2', text)
    text = re.sub(r'\\url\{([^}]+)\}', r'\1', text)
    
    # Common text styling macros
    text = re.sub(r'\\(?:textbf|textit|emph|textsc|texttt|underline|small|footnotesize|large|Large|Huge)\{([^}]+)\}', r'\1', text)
    # Double nested
    text = re.sub(r'\\(?:textbf|textit|emph|textsc|texttt)\{([^}]+)\}', r'\1', text)
    
    # Inline font switches like {\scshape text} or {\bf text}
    text = re.sub(r'\{(?:\\[a-zA-Z]+\s+)?([^}]+)\}', r'\1', text)
    
    # Remove math mode and generic commands
    text = re.sub(r'\$[^$]*\$', '', text)
    text = re.sub(r'\\[a-zA-Z]+(?:\*|\b)(?:\[[^\]]*\])?', '', text)
    
    # Unescape special characters
    replacements = [
        (r'\\&', '&'),
        (r'\\%', '%'),
        (r'\\\$', '$'),
        (r'\\#', '#'),
        (r'\\_', '_'),
        (r'\\\{', '{'),
        (r'\\\}', '}'),
        (r'~', ' '),
        (r'---', '—'),
        (r'--', '–'),
        (r'\s+', ' '),
    ]
    for pattern, repl in replacements:
        text = re.sub(pattern, repl, text)
        
    return text.strip()


def extract_hrefs(text: str) -> List[Tuple[str, str]]:
    """Extracts (url, label) pairs from \\href{url}{label}."""
    return re.findall(r'\\href\{([^}]+)\}\{([^}]+)\}', text)


class LatexResumeParser:
    """Intelligent multi-strategy parser for LaTeX CVs and Resumes."""

    def __init__(self, latex_content: str):
        self.raw = latex_content
        self.cleaned = self._strip_comments(latex_content)

    def _strip_comments(self, content: str) -> str:
        """Strips out LaTeX comment lines and trailing comments."""
        lines = []
        for line in content.splitlines():
            # Avoid matching escaped \%
            parts = re.split(r'(?<!\\)%', line)
            if parts:
                lines.append(parts[0])
        return "\n".join(lines)

    def parse(self) -> ResumeData:
        """Parses the full LaTeX document into a structured ResumeData object."""
        basics = self._parse_basics()
        sections = self._split_sections()
        
        work = []
        education = []
        projects = []
        skills = []
        open_source = []

        for title, body in sections:
            lower_title = title.lower()
            if any(k in lower_title for k in ("experience", "employment", "work", "history")):
                work.extend(self._parse_work(body))
            elif any(k in lower_title for k in ("education", "academics", "qualifications")):
                education.extend(self._parse_education(body))
            elif any(k in lower_title for k in ("project", "work samples")):
                projects.extend(self._parse_projects(body))
            elif any(k in lower_title for k in ("skill", "competenc", "technologies", "tech stack")):
                skills.extend(self._parse_skills(body))
            elif any(k in lower_title for k in ("open source", "contributions", "community")):
                open_source.extend(self._parse_open_source(body))
            else:
                # Default heuristics: check if looks like projects or experience
                if "\\resumeSubheading" in body or "\\cventry" in body:
                    work.extend(self._parse_work(body))
                elif "bullet" in body or "\\resumeItem" in body:
                    projects.extend(self._parse_projects(body))

        return ResumeData(
            basics=basics,
            work=work,
            education=education,
            projects=projects,
            skills=skills,
            open_source=open_source
        )

    def _parse_basics(self) -> Basics:
        """Extracts candidate contact information, headline, and web profiles."""
        basics = Basics()
        
        # 1. Name heuristics
        # \textbf{\Huge \scshape Kanishk Upadhyay} or \textbf{\Huge Kanishk Upadhyay}
        name_match = re.search(r'\\textbf\{\s*\\(?:Huge|huge|LARGE|Large)\s*(?:\\scshape\s*)?([^}]+)\}', self.cleaned)
        if not name_match:
            # {\Huge \scshape Kanishk Upadhyay}
            name_match = re.search(r'\{\s*\\(?:Huge|huge|LARGE|Large)\s*(?:\\scshape\s*)?([^}]+)\}', self.cleaned)
        if not name_match:
            # \Huge \textbf{Kanishk Upadhyay} or \name{Kanishk Upadhyay}
            name_match = re.search(r'\\(?:Huge\s*\\textbf|huge\s*\\textbf|name)\{([^}]+)\}', self.cleaned)
        if not name_match:
            name_match = re.search(r'\\author\{([^}]+)\}', self.cleaned)
        if name_match:
            basics.name = clean_latex(name_match.group(1))
            
        # 2. Email
        email_match = re.search(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', self.cleaned)
        if email_match:
            basics.email = email_match.group(0).strip()
            
        # 3. Phone (International or standard format)
        phone_match = re.search(r'(?:\+\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}|\+\d{1,3}\s*\d{9,11}', self.cleaned)
        if phone_match:
            basics.phone = phone_match.group(0).strip()
            
        # 4. Links / Profiles
        hrefs = extract_hrefs(self.cleaned)
        seen_urls = set()
        for url, label in hrefs:
            if "mailto:" in url or url == basics.email:
                continue
            if url in seen_urls:
                continue
            seen_urls.add(url)
            
            clean_lbl = clean_latex(label)
            if "github.com" in url:
                basics.profiles.append(Profile(network="GitHub", username=url.split("github.com/")[-1].strip("/"), url=url))
            elif "gitlab.com" in url:
                basics.profiles.append(Profile(network="GitLab", username=url.split("gitlab.com/")[-1].strip("/"), url=url))
            elif "linkedin.com" in url:
                basics.profiles.append(Profile(network="LinkedIn", username=url.split("linkedin.com/in/")[-1].strip("/"), url=url))
            elif any(k in url for k in ("nekoweb.org", "pages.dev", "github.io", "reocities.xyz")) or "http" in url:
                if not basics.url:
                    basics.url = url
                else:
                    basics.profiles.append(Profile(network="Portfolio", username=clean_lbl or "Portfolio", url=url))

        # 5. Location heuristics - search after \begin{document}
        doc_body = self.cleaned.split(r"\begin{document}")[-1] if r"\begin{document}" in self.cleaned else self.cleaned
        loc_matches = re.finditer(r'([A-Za-z\s]+,\s*[A-Za-z\s]+(?:\s*\d{5,6})?)', doc_body[:1500])
        for match in loc_matches:
            candidate_loc = clean_latex(match.group(1)).strip()
            # Verify candidate matches typical city/country indicators or is under the header
            if any(c in candidate_loc.lower() for c in ("bhopal", "india", "san francisco", "new york", "london", "bangalore", "delhi", "berlin", "geneva", "cern", "remote", "usa", "ca", "uk", "germany", "switzerland")):
                basics.location = Location(city=candidate_loc)
                break

        return basics

    def _split_sections(self) -> List[Tuple[str, str]]:
        """Splits LaTeX content by \\section{...} or \\cvsection{...} headers."""
        pattern = r'\\(?:section|cvsection)\*?\{([^}]+)\}'
        matches = list(re.finditer(pattern, self.cleaned))
        if not matches:
            return []

        sections = []
        for i, match in enumerate(matches):
            title = clean_latex(match.group(1))
            start = match.end()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(self.cleaned)
            body = self.cleaned[start:end]
            sections.append((title, body))
        return sections

    def _parse_bullets(self, text: str) -> List[str]:
        """Extracts bullet points from \\resumeItem{...} or \\item ..."""
        bullets = []
        # Pattern 1: \resumeItem{...}
        resume_items = re.findall(r'\\resumeItem\{((?:[^{}]|\{[^{}]*\})*)\}', text)
        if resume_items:
            for item in resume_items:
                c = clean_latex(item)
                if c:
                    bullets.append(c)
            return bullets

        # Pattern 2: \item ...
        items = re.split(r'\\item\b', text)
        for item in items[1:]:
            # stop before \end{itemize} or next environment
            clean_item = re.split(r'\\end\{(?:itemize|enumerate)\}', item)[0]
            c = clean_latex(clean_item)
            if c:
                bullets.append(c)
        return bullets

    def _parse_work(self, body: str) -> List[WorkItem]:
        """Parses experience blocks."""
        work_items = []
        
        # Subheading regex: \resumeSubheading{arg1}{arg2}{arg3}{arg4}
        subheading_pattern = r'\\resumeSubheading\s*\{((?:[^{}]|\{[^{}]*\})*)\}\s*\{((?:[^{}]|\{[^{}]*\})*)\}\s*\{((?:[^{}]|\{[^{}]*\})*)\}\s*\{((?:[^{}]|\{[^{}]*\})*)\}'
        matches = list(re.finditer(subheading_pattern, body))

        if matches:
            for i, match in enumerate(matches):
                a1, a2, a3, a4 = [clean_latex(m) for m in match.groups()]
                start = match.end()
                end = matches[i + 1].start() if i + 1 < len(matches) else len(body)
                sub_body = body[start:end]
                bullets = self._parse_bullets(sub_body)

                # Heuristic: Check whether a1 is Role or Company
                # Commonly: {Role}{Dates}{Company}{Location} OR {Company}{Location}{Role}{Dates}
                if any(m in a2.lower() for m in ("202", "present", "jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec", "–", "-")):
                    # a1 = Role, a2 = Dates, a3 = Company, a4 = Location
                    role, dates, company, location = a1, a2, a3, a4
                else:
                    # a1 = Company, a2 = Location, a3 = Role, a4 = Dates
                    company, location, role, dates = a1, a2, a3, a4

                start_date, end_date = self._split_dates(dates)

                work_items.append(WorkItem(
                    name=company,
                    position=role,
                    location=location,
                    start_date=start_date,
                    end_date=end_date,
                    highlights=bullets
                ))
            return work_items

        # Fallback: custom tabular or \textbf headings
        blocks = re.split(r'(?=\\textbf\{[^}]+\}\s*\\hfill)', body)
        for block in blocks:
            if not block.strip():
                continue
            head_match = re.search(r'\\textbf\{([^}]+)\}\s*\\hfill\s*([^\\]+)', block)
            if head_match:
                title = clean_latex(head_match.group(1))
                dates = clean_latex(head_match.group(2))
                bullets = self._parse_bullets(block)
                start_date, end_date = self._split_dates(dates)
                work_items.append(WorkItem(
                    name=title,
                    position="",
                    start_date=start_date,
                    end_date=end_date,
                    highlights=bullets
                ))

        return work_items

    def _parse_education(self, body: str) -> List[EducationItem]:
        """Parses education blocks."""
        edu_items = []
        subheading_pattern = r'\\resumeSubheading\s*\{((?:[^{}]|\{[^{}]*\})*)\}\s*\{((?:[^{}]|\{[^{}]*\})*)\}\s*\{((?:[^{}]|\{[^{}]*\})*)\}\s*\{((?:[^{}]|\{[^{}]*\})*)\}'
        matches = list(re.finditer(subheading_pattern, body))

        if matches:
            for i, match in enumerate(matches):
                a1, a2, a3, a4 = [clean_latex(m) for m in match.groups()]
                start = match.end()
                end = matches[i + 1].start() if i + 1 < len(matches) else len(body)
                bullets = self._parse_bullets(body[start:end])

                if any(m in a2.lower() for m in ("202", "present", "–", "-")):
                    inst, dates, degree, loc = a1, a2, a3, a4
                else:
                    inst, loc, degree, dates = a1, a2, a3, a4

                start_date, end_date = self._split_dates(dates)
                edu_items.append(EducationItem(
                    institution=inst,
                    study_type=degree,
                    start_date=start_date,
                    end_date=end_date,
                    highlights=bullets
                ))
            return edu_items

        # Fallback
        lines = [line.strip() for line in body.splitlines() if line.strip()]
        for line in lines:
            c = clean_latex(line)
            if len(c) > 5 and any(k in c.lower() for k in ("university", "bachelor", "degree", "college", "school", "b.e", "b.tech")):
                edu_items.append(EducationItem(institution=c))

        return edu_items

    def _parse_projects(self, body: str) -> List[ProjectItem]:
        """Parses project blocks."""
        projects = []
        
        # Pattern 1: \resumeProjectHeading{\textbf{Name} $|$ \emph{Tech}}{Date}
        heading_pattern = r'\\resumeProjectHeading\s*\{((?:[^{}]|\{[^{}]*\})*)\}\s*\{((?:[^{}]|\{[^{}]*\})*)\}'
        matches = list(re.finditer(heading_pattern, body))

        if matches:
            for i, match in enumerate(matches):
                header_raw = match.group(1)
                date_raw = clean_latex(match.group(2))
                start = match.end()
                end = matches[i + 1].start() if i + 1 < len(matches) else len(body)
                bullets = self._parse_bullets(body[start:end])

                # Split name and tech: \textbf{Pokédex} $|$ \emph{Vanilla JS}
                parts = [clean_latex(p) for p in header_raw.split('|')]
                name = parts[0] if parts else "Project"
                keywords = [k.strip() for k in parts[1].split(',')] if len(parts) > 1 else []
                
                # Check for URLs
                hrefs = extract_hrefs(header_raw)
                url = hrefs[0][0] if hrefs else ""

                start_date, end_date = self._split_dates(date_raw)
                projects.append(ProjectItem(
                    name=name,
                    keywords=keywords,
                    url=url,
                    start_date=start_date,
                    end_date=end_date,
                    highlights=bullets
                ))
            return projects

        # Pattern 2: \resumeSubheading format for projects
        subheading_pattern = r'\\resumeSubheading\s*\{((?:[^{}]|\{[^{}]*\})*)\}\s*\{((?:[^{}]|\{[^{}]*\})*)\}\s*\{((?:[^{}]|\{[^{}]*\})*)\}\s*\{((?:[^{}]|\{[^{}]*\})*)\}'
        matches = list(re.finditer(subheading_pattern, body))
        if matches:
            for i, match in enumerate(matches):
                a1, a2, a3, a4 = [clean_latex(m) for m in match.groups()]
                start = match.end()
                end = matches[i + 1].start() if i + 1 < len(matches) else len(body)
                bullets = self._parse_bullets(body[start:end])
                projects.append(ProjectItem(
                    name=a1,
                    description=a3,
                    start_date=a2,
                    highlights=bullets
                ))
            return projects

        return projects

    def _parse_skills(self, body: str) -> List[SkillItem]:
        """Parses categorized skill sets."""
        skills = []
        
        # Common pattern: \textbf{Category}{: Item1, Item2, Item3}
        lines = body.splitlines()
        for line in lines:
            line_clean = line.strip()
            if not line_clean:
                continue
            
            # Match \textbf{Category}{: Item1, Item2} or \textbf{Category}: Item1, Item2
            cat_match = re.search(r'\\textbf\{([^}]+)\}\s*(?:\{:?\s*|:\s*)([^}\\]+)', line_clean)
            if cat_match:
                cat_name = clean_latex(cat_match.group(1)).rstrip(':')
                raw_items = clean_latex(cat_match.group(2))
                keywords = [k.strip() for k in re.split(r'[,|•]', raw_items) if k.strip()]
                if keywords:
                    skills.append(SkillItem(name=cat_name, keywords=keywords))
            else:
                # \item \textbf{Category:} Item1, Item2
                simple_match = re.search(r'\\item\s*\\textbf\{([^}]+)\}\s*[:\-]\s*(.*)', line_clean)
                if simple_match:
                    cat_name = clean_latex(simple_match.group(1)).rstrip(':')
                    raw_items = clean_latex(simple_match.group(2))
                    keywords = [k.strip() for k in re.split(r'[,|•]', raw_items) if k.strip()]
                    if keywords:
                        skills.append(SkillItem(name=cat_name, keywords=keywords))

        return skills

    def _parse_open_source(self, body: str) -> List[OpenSourceItem]:
        """Parses open-source contributions."""
        os_items = []
        subheading_pattern = r'\\resumeSubheading\s*\{((?:[^{}]|\{[^{}]*\})*)\}\s*\{((?:[^{}]|\{[^{}]*\})*)\}\s*\{((?:[^{}]|\{[^{}]*\})*)\}\s*\{((?:[^{}]|\{[^{}]*\})*)\}'
        matches = list(re.finditer(subheading_pattern, body))

        if matches:
            for i, match in enumerate(matches):
                a1, a2, a3, a4 = [clean_latex(m) for m in match.groups()]
                start = match.end()
                end = matches[i + 1].start() if i + 1 < len(matches) else len(body)
                bullets = self._parse_bullets(body[start:end])
                os_items.append(OpenSourceItem(
                    project=a1,
                    role=a3,
                    highlights=bullets
                ))
            return os_items
            
        bullets = self._parse_bullets(body)
        if bullets:
            os_items.append(OpenSourceItem(project="Community Contributions", highlights=bullets))

        return os_items

    def _split_dates(self, date_str: str) -> Tuple[str, str]:
        """Normalizes date ranges like '06/2025 -- 12/2025' or 'May 2023 - Present'."""
        if not date_str:
            return "", ""
        parts = re.split(r'\s*(?:–|—|--|-|to)\s*', date_str)
        if len(parts) >= 2:
            return parts[0].strip(), parts[1].strip()
        return date_str.strip(), ""
