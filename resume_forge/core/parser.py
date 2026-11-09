"""LaTeX Resume Parser: Converts raw LaTeX documents into structured ResumeData."""

import re
from typing import Dict, List, Tuple, Optional, Any
from .schema import (
    ResumeData, Basics, WorkItem, EducationItem, ProjectItem, SkillItem,
    OpenSourceItem, Profile, Location, CertificateItem, AwardItem,
    PublicationItem, LanguageItem
)


ACCENTS_MAP = {
    # Acute: \'
    r"\\\'\{?([a-zA-Z])\}?": {
        'a': 'á', 'e': 'é', 'i': 'í', 'o': 'ó', 'u': 'ú', 'y': 'ý',
        'A': 'Á', 'E': 'É', 'I': 'Í', 'O': 'Ó', 'U': 'Ú', 'Y': 'Ý'
    },
    # Grave: \`
    r"\\`\{?([a-zA-Z])\}?": {
        'a': 'à', 'e': 'è', 'i': 'ì', 'o': 'ò', 'u': 'ù',
        'A': 'À', 'E': 'È', 'I': 'Ì', 'O': 'Ò', 'U': 'Ù'
    },
    # Umlaut/Diaeresis: \"
    r'\\\"\{?([a-zA-Z])\}?': {
        'a': 'ä', 'e': 'ë', 'i': 'ï', 'o': 'ö', 'u': 'ü',
        'A': 'Ä', 'E': 'Ë', 'I': 'Ï', 'O': 'Ö', 'U': 'Ü'
    },
    # Circumflex: \^
    r"\\\^\{?([a-zA-Z])\}?": {
        'a': 'â', 'e': 'ê', 'i': 'î', 'o': 'ô', 'u': 'û',
        'A': 'Â', 'E': 'Ê', 'I': 'Î', 'O': 'Ô', 'U': 'Û'
    },
    # Tilde: \~
    r"\\~\{?([a-zA-Z])\}?": {
        'a': 'ã', 'n': 'ñ', 'o': 'õ',
        'A': 'Ã', 'N': 'Ñ', 'O': 'Õ'
    },
    # Caron: \v (letter command: must be followed by {ch} or whitespace + ch)
    r"\\v(?:\s*\{([a-zA-Z])\}|\s+([a-zA-Z]))": {
        'c': 'č', 'd': 'ď', 'e': 'ě', 'l': 'ľ', 'n': 'ň', 'r': 'ř', 's': 'š', 't': 'ť', 'z': 'ž',
        'C': 'Č', 'D': 'Ď', 'E': 'Ě', 'L': 'Ľ', 'N': 'Ň', 'R': 'Ř', 'S': 'Š', 'T': 'Ť', 'Z': 'Ž'
    },
    # Cedilla: \c (letter command: must be followed by {ch} or whitespace + ch)
    r"\\c(?:\s*\{([a-zA-Z])\}|\s+([a-zA-Z]))": {
        'c': 'ç', 'C': 'Ç', 's': 'ş', 'S': 'Ş'
    }
}


def clean_latex(text: str) -> str:
    """Removes LaTeX formatting commands, escaping, and artifacts."""
    if not text:
        return ""
    
    # 1. Unescape LaTeX diacritics & accent macros before stripping general commands
    for pattern, char_map in ACCENTS_MAP.items():
        def _repl(m, cm=char_map):
            ch = m.group(1) or m.group(2) or (m.group(3) if len(m.groups()) >= 3 else "")
            return cm.get(ch, ch)
        text = re.sub(pattern, _repl, text)

    text = re.sub(r'\\aa\b', 'å', text)
    text = re.sub(r'\\AA\b', 'Å', text)
    text = re.sub(r'\\ss\b', 'ß', text)
    text = re.sub(r'\\o\b', 'ø', text)
    text = re.sub(r'\\O\b', 'Ø', text)
    text = re.sub(r'\\ae\b', 'æ', text)
    text = re.sub(r'\\AE\b', 'Æ', text)

    # 2. Convert LaTeX non-breaking tie '~' to space before restoring math/text tildes
    text = text.replace('~', ' ')

    # 3. Normalize math-mode vertical dividers, quotes, and symbols
    text = re.sub(r'\$\s*(?:\\vert|\|)\s*\$', ' | ', text)
    text = re.sub(r'\$\s*\\sim\s*\$|\\sim\b', '~', text)
    text = re.sub(r'\$\s*\\pm\s*\$|\\pm\b', '±', text)
    text = re.sub(r'\$\s*\\times\s*\$|\\times\b', '×', text)
    text = re.sub(r'\$\s*\\(?:le|leq)\s*\$|\\(?:le|leq)\b', '≤', text)
    text = re.sub(r'\$\s*\\(?:ge|geq)\s*\$|\\(?:ge|geq)\b', '≥', text)
    text = re.sub(r'\$\s*\\approx\s*\$|\\approx\b', '≈', text)
    text = re.sub(r'\\textasciitilde\{\}?|\\textasciitilde\b', '~', text)
    text = re.sub(r'\\textasciicircum\{\}?|\\textasciicircum\b', '^', text)
    text = re.sub(r'\\textbar\{\}?|\\textbar\b', '|', text)
    text = re.sub(r'\\slash\{\}?|\\slash\b', '/', text)
    text = re.sub(r'\\textbullet\{\}?|\\bullet\b|\\cdot\b', '•', text)
    
    # Normalize LaTeX quotation marks: ``word'' -> "word", `word' -> 'word'
    text = re.sub(r"``((?:[^']|'(?!'))*)''", r'"\1"', text)
    text = re.sub(r"`([^']*)'", r"'\1'", text)
    
    # 4. Extract labels from \href{url}{label} with nested brace support
    href_pattern = r'\\href\s*\{((?:[^{}]|\{[^{}]*\})*)\}\s*\{((?:[^{}]|\{[^{}]*\})*)\}'
    while re.search(href_pattern, text):
        text = re.sub(href_pattern, r'\2', text)
    text = re.sub(r'\\url\s*\{([^}]+)\}', r'\1', text)
    
    # 5. Iteratively peel text styling macros (textbf, textit, emph, underline, etc.)
    macro_pattern = r'\\(?:textbf|textit|emph|textsc|texttt|underline|small|footnotesize|large|Large|Huge|scshape)\s*\{((?:[^{}]|\{[^{}]*\})*)\}'
    for _ in range(6):
        if not re.search(macro_pattern, text):
            break
        text = re.sub(macro_pattern, r'\1', text)
    
    # 6. Iteratively peel inline font switches and grouping braces like {\scshape text}, {\bf text}, or {text}
    group_pattern = r'\{(?:\\[a-zA-Z]+\s+)?([^{}]+)\}'
    for _ in range(6):
        if not re.search(group_pattern, text):
            break
        text = re.sub(group_pattern, r'\1', text)
    
    # 7. Math mode unwrapping: retain inner content (e.g. $10B -> 10B)
    text = re.sub(r'\$([^$]*)\$', r'\1', text)
    
    # 8. Unescape LaTeX punctuation spacing and linebreaks
    # \\ with optional spacing like \\[5pt] or \\
    text = re.sub(r'\\\\(?:\s*\[[^\]]*\])?', ' ', text)
    # Spacing commands: \, \: \; \! \ \- \/
    text = re.sub(r'\\[,:; ]', ' ', text)
    text = re.sub(r'\\!', '', text)
    text = re.sub(r'\\-', '', text)
    text = re.sub(r'\\/', '', text)
    
    # Remove remaining backslash commands (e.g. \vspace{...}, \hspace{...}, \hfill)
    text = re.sub(r'\\[a-zA-Z]+(?:\*|\b)(?:\[[^\]]*\])?(?:\{[^{}]*\})?', '', text)
    
    # 9. Unescape special characters
    replacements = [
        (r'\\&', '&'),
        (r'\\%', '%'),
        (r'\\\$', '$'),
        (r'\\#', '#'),
        (r'\\_', '_'),
        (r'\\\{', '{'),
        (r'\\\}', '}'),
        (r'\\textless\{\}?', '<'),
        (r'\\textgreater\{\}?', '>'),
        (r'---', '—'),
        (r'--', '–'),
        (r'\s+', ' '),
    ]
    for pattern, repl in replacements:
        text = re.sub(pattern, repl, text)
        
    # 10. Strip outer enclosing balanced braces
    text = text.strip()
    while text.startswith('{') and text.endswith('}'):
        depth = 0
        balanced = True
        for ch in text[:-1]:
            if ch == '{':
                depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0:
                    balanced = False
                    break
        if balanced and depth == 1:
            text = text[1:-1].strip()
        else:
            break

    return text.strip()


def extract_braced_args(text: str, start_pos: int, max_args: int = 1) -> Tuple[List[str], int]:
    """Extracts balanced braced arguments {arg1}{arg2}... from a LaTeX command."""
    args = []
    i = start_pos
    n = len(text)
    while len(args) < max_args:
        # Skip whitespace and comments
        while i < n and (text[i].isspace() or text[i] == '%'):
            if text[i] == '%':
                while i < n and text[i] != '\n':
                    i += 1
            else:
                i += 1
        if i >= n or text[i] != '{':
            break
        depth = 1
        i += 1
        arg_start = i
        while i < n and depth > 0:
            if text[i] == '\\' and i + 1 < n:
                i += 2
                continue
            if text[i] == '{':
                depth += 1
            elif text[i] == '}':
                depth -= 1
            i += 1
        if depth == 0:
            args.append(text[arg_start:i-1])
        else:
            break
    return args, i


def extract_hrefs(text: str) -> List[Tuple[str, str]]:
    """Extracts (url, label) pairs from \\href{url}{label} with optional whitespace."""
    return re.findall(r'\\href\s*\{((?:[^{}]|\{[^{}]*\})*)\}\s*\{((?:[^{}]|\{[^{}]*\})*)\}', text)


class LatexResumeParser:
    """Intelligent multi-strategy parser for LaTeX CVs and Resumes."""

    def __init__(self, latex_content: str):
        self.raw = latex_content
        self.cleaned = self._strip_comments(latex_content)

    def _strip_comments(self, content: str) -> str:
        """Strips out LaTeX comment lines and trailing comments, while protecting unescaped % after numbers."""
        # Auto-escape unescaped % preceded by digits to prevent truncating bullets with percentage metrics
        content = re.sub(r'(\d+)\s*%(?=[a-zA-Z\s.,;:!?)])', r'\1\\%', content)
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
        certificates = []
        awards = []
        publications = []
        languages = []

        for title, body in sections:
            lower_title = title.lower()
            if any(k in lower_title for k in ("summary", "objective", "about me", "profile", "professional summary")):
                clean_body = clean_latex(body).strip()
                if clean_body and not basics.summary:
                    basics.summary = clean_body
            elif any(k in lower_title for k in ("experience", "employment", "work", "history")):
                work.extend(self._parse_work(body))
            elif any(k in lower_title for k in ("education", "academics", "qualifications")):
                education.extend(self._parse_education(body))
            elif any(k in lower_title for k in ("project", "work samples")):
                projects.extend(self._parse_projects(body))
            elif any(k in lower_title for k in ("skill", "competenc", "technologies", "tech stack")):
                skills.extend(self._parse_skills(body))
            elif any(k in lower_title for k in ("open source", "contributions", "community")):
                open_source.extend(self._parse_open_source(body))
            elif any(k in lower_title for k in ("certificate", "certification", "licenses")):
                certificates.extend(self._parse_certificates(body))
            elif any(k in lower_title for k in ("award", "honor", "achievement")):
                awards.extend(self._parse_awards(body))
            elif any(k in lower_title for k in ("publication", "paper", "research")):
                publications.extend(self._parse_publications(body))
            elif any(k in lower_title for k in ("language", "spoken languages")):
                languages.extend(self._parse_languages(body))
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
            open_source=open_source,
            certificates=certificates,
            awards=awards,
            publications=publications,
            languages=languages
        )

    def _parse_basics(self) -> Basics:
        """Extracts candidate contact information, headline, and web profiles."""
        basics = Basics()
        
        # Determine header block before first section
        if r"\begin{document}" in self.cleaned:
            after_doc = self.cleaned.split(r"\begin{document}", 1)[1]
            first_sec_match = re.search(r'\\(?:section|cvsection)\b', after_doc)
            header_text = after_doc[:first_sec_match.start()] if first_sec_match else after_doc[:2500]
        else:
            first_sec_match = re.search(r'\\(?:section|cvsection)\b', self.cleaned)
            header_text = self.cleaned[:first_sec_match.start()] if first_sec_match else self.cleaned[:2500]

        # 1. Name heuristics with balanced brace extraction
        # ModernCV \name{First}{Last} or Deedy \namesection{First}{Last}{...}
        m_name = re.search(r'\\(?:name|namesection)\b', header_text) or re.search(r'\\(?:name|namesection)\b', self.cleaned)
        if m_name:
            source_tex = header_text if m_name.string is header_text else self.cleaned
            args, _ = extract_braced_args(source_tex, m_name.end(), max_args=2)
            if len(args) >= 2:
                n1 = clean_latex(args[0]).strip("{} \t\r\n")
                n2 = clean_latex(args[1]).strip("{} \t\r\n")
                if n1 or n2:
                    basics.name = f"{n1} {n2}".strip()
            elif len(args) == 1:
                basics.name = clean_latex(args[0]).strip("{} \t\r\n")

        # ModernCV \firstname{...} and \familyname{...}
        if not basics.name:
            m_fn = re.search(r'\\firstname\b', header_text)
            m_ln = re.search(r'\\familyname\b', header_text)
            if m_fn and m_ln:
                fn_args, _ = extract_braced_args(header_text, m_fn.end(), max_args=1)
                ln_args, _ = extract_braced_args(header_text, m_ln.end(), max_args=1)
                if fn_args and ln_args:
                    n1 = clean_latex(fn_args[0]).strip("{} \t\r\n")
                    n2 = clean_latex(ln_args[0]).strip("{} \t\r\n")
                    if n1 or n2:
                        basics.name = f"{n1} {n2}".strip()

        # \textbf{...} containing \Huge, \huge, \LARGE, \Large, or \scshape
        if not basics.name:
            for m in re.finditer(r'\\textbf\b', header_text):
                args, _ = extract_braced_args(header_text, m.end(), max_args=1)
                if args:
                    inner = args[0]
                    inner_line = re.split(r'\\\\|\n', inner)[0]
                    if re.search(r'\\(?:Huge|huge|LARGE|Large|scshape)\b', inner) or m.start() < 300:
                        candidate = clean_latex(inner_line).strip("{} \t\r\n")
                        candidate = re.sub(r'[{}]', '', candidate).strip()
                        if candidate and len(candidate.split()) <= 6:
                            basics.name = candidate
                            break

        # {\Huge ...} or {\huge ...}
        if not basics.name:
            m_huge = re.search(r'\{\s*\\(?:Huge|huge|LARGE|Large)\b', header_text)
            if m_huge:
                args, _ = extract_braced_args(header_text, m_huge.start(), max_args=1)
                if args:
                    inner_line = re.split(r'\\\\|\n', args[0])[0]
                    candidate = clean_latex(inner_line).strip("{} \t\r\n")
                    candidate = re.sub(r'[{}]', '', candidate).strip()
                    if candidate and len(candidate.split()) <= 6:
                        basics.name = candidate

        # \Huge \textbf{...} or \huge \textbf{...}
        if not basics.name:
            m_size_before = re.search(r'\\(?:Huge|huge|LARGE|Large)\s*\\textbf\b', header_text)
            if m_size_before:
                m_tb = re.search(r'\\textbf\b', header_text[m_size_before.start():])
                if m_tb:
                    args, _ = extract_braced_args(header_text, m_size_before.start() + m_tb.end(), max_args=1)
                    if args:
                        inner_line = re.split(r'\\\\|\n', args[0])[0]
                        candidate = clean_latex(inner_line).strip("{} \t\r\n")
                        candidate = re.sub(r'[{}]', '', candidate).strip()
                        if candidate:
                            basics.name = candidate

        # \centerline{...}
        if not basics.name:
            m_cl = re.search(r'\\centerline\b', header_text)
            if m_cl:
                args, _ = extract_braced_args(header_text, m_cl.end(), max_args=1)
                if args:
                    inner_line = re.split(r'\\\\|\n', args[0])[0]
                    candidate = clean_latex(inner_line).strip("{} \t\r\n")
                    candidate = re.sub(r'[{}]', '', candidate).strip()
                    if candidate and len(candidate.split()) <= 6:
                        basics.name = candidate

        # \author{...} or \title{...}
        if not basics.name:
            for macro in [r'\\author\b', r'\\title\b']:
                m_meta = re.search(macro, header_text)
                if m_meta:
                    args, _ = extract_braced_args(header_text, m_meta.end(), max_args=1)
                    if args:
                        candidate = clean_latex(args[0]).strip("{} \t\r\n")
                        candidate = re.sub(r'[{}]', '', candidate).strip()
                        if candidate and len(candidate.split()) <= 6:
                            basics.name = candidate
                            break

        # Fallback regex
        if not basics.name:
            name_match = re.search(r'\\textbf\{\s*\\(?:Huge|huge|LARGE|Large)\s*(?:\\scshape\s*)?([^}]+)\}', self.cleaned)
            if not name_match:
                name_match = re.search(r'\{\s*\\(?:Huge|huge|LARGE|Large)\s*(?:\\scshape\s*)?([^}]+)\}', self.cleaned)
            if not name_match:
                name_match = re.search(r'\\(?:Huge\s*\\textbf|huge\s*\\textbf|name)\{([^}]+)\}', self.cleaned)
            if not name_match:
                name_match = re.search(r'\\author\{([^}]+)\}', self.cleaned)
            if not name_match:
                name_match = re.search(r'\\(?:Huge|huge|LARGE|Large)\s*(?:\\scshape\s*)?\{?([a-zA-Z\s.-]+)', self.cleaned)
            if name_match:
                basics.name = clean_latex(name_match.group(1))

        # Absolute guarantee: Strip any leftover curly braces from name
        if basics.name:
            basics.name = re.sub(r'[{}]', '', basics.name).strip()
            basics.name = re.sub(r'\s+', ' ', basics.name)
            
        # 2. Headline / Position (e.g. Awesome-CV \position{Software Engineer})
        pos_match = re.search(r'\\position\b', self.cleaned)
        if pos_match:
            pos_args, _ = extract_braced_args(self.cleaned, pos_match.end(), max_args=1)
            if pos_args:
                basics.label = clean_latex(pos_args[0]).strip("{} \t\r\n")
        else:
            pos_regex = re.search(r'\\position\{([^}]+)\}', self.cleaned)
            if pos_regex:
                basics.label = clean_latex(pos_regex.group(1)).strip("{} \t\r\n")
        if basics.label:
            basics.label = re.sub(r'[{}]', '', basics.label).strip()

        # 3. Email (Standard, \email{...}, or ModernCV)
        email_match = re.search(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', self.cleaned)
        if email_match:
            basics.email = email_match.group(0).strip()
        else:
            em_macro = re.search(r'\\email\{([^}]+)\}', self.cleaned)
            if em_macro:
                basics.email = clean_latex(em_macro.group(1)).strip()
            
        # 4. Phone (International, standard format, or \mobile{...})
        phone_match = re.search(r'(?:\+\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}|\+\d{1,3}\s*\d{9,11}', self.cleaned)
        if phone_match:
            basics.phone = phone_match.group(0).strip()
        else:
            mob_macro = re.search(r'\\mobile\{([^}]+)\}', self.cleaned)
            if mob_macro:
                basics.phone = clean_latex(mob_macro.group(1)).strip()
            
        # 5. Links / Profiles & Dedicated CV macros (\homepage, \github, \linkedin, \gitlab)
        # Search for \href contact links in the header block (after \begin{document} before first section)
        if r"\begin{document}" in self.cleaned:
            after_doc = self.cleaned.split(r"\begin{document}", 1)[1]
            first_sec_match = re.search(r'\\(?:section|cvsection)\b', after_doc)
            header_text = after_doc[:first_sec_match.start()] if first_sec_match else after_doc[:2000]
        else:
            first_sec_match = re.search(r'\\(?:section|cvsection)\b', self.cleaned)
            header_text = self.cleaned[:first_sec_match.start()] if first_sec_match else self.cleaned[:2000]

        hrefs = extract_hrefs(header_text)
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

        # Check Awesome-CV macros in document (frequently placed in preamble before \begin{document})
        hp_match = re.search(r'\\homepage\{([^}]+)\}', self.cleaned)
        if hp_match and not basics.url:
            hp_url = clean_latex(hp_match.group(1)).strip()
            if not hp_url.startswith("http"):
                hp_url = "https://" + hp_url
            basics.url = hp_url

        gh_match = re.search(r'\\github\{([^}]+)\}', self.cleaned)
        if gh_match and not any(p.network == "GitHub" for p in basics.profiles):
            uname = clean_latex(gh_match.group(1)).strip()
            basics.profiles.append(Profile(network="GitHub", username=uname, url=f"https://github.com/{uname}"))

        li_match = re.search(r'\\linkedin\{([^}]+)\}', self.cleaned)
        if li_match and not any(p.network == "LinkedIn" for p in basics.profiles):
            uname = clean_latex(li_match.group(1)).strip()
            basics.profiles.append(Profile(network="LinkedIn", username=uname, url=f"https://linkedin.com/in/{uname}"))

        gl_match = re.search(r'\\gitlab\{([^}]+)\}', self.cleaned)
        if gl_match and not any(p.network == "GitLab" for p in basics.profiles):
            uname = clean_latex(gl_match.group(1)).strip()
            basics.profiles.append(Profile(network="GitLab", username=uname, url=f"https://gitlab.com/{uname}"))

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
        # Pattern 1: \resumeItem with balanced brace extraction
        pos = 0
        while True:
            idx = text.find(r'\resumeItem', pos)
            if idx == -1:
                break
            args, next_pos = extract_braced_args(text, idx + len(r'\resumeItem'), 1)
            if args:
                c = clean_latex(args[0])
                if c:
                    bullets.append(c)
                pos = next_pos
            else:
                pos = idx + len(r'\resumeItem')

        if bullets:
            return bullets

        # Pattern 2: \item ...
        items = re.split(r'\\item\b', text)
        for item in items[1:]:
            clean_item = re.split(r'\\end\{(?:itemize|enumerate|cvitems|tightemize)\}', item)[0]
            clean_item = re.sub(r'^\s*\{((?:[^{}]|\{[^{}]*\})*)\}', r'\1', clean_item)
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
                if any(m in a2.lower() for m in ("202", "present", "jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec", "–", "-")):
                    role, dates, company, location = a1, a2, a3, a4
                else:
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

        # Pattern 2: \cventry (supports both Awesome-CV 5-arg and ModernCV 6-arg formats)
        pos = 0
        while True:
            idx = body.find(r'\cventry', pos)
            if idx == -1:
                break
            args, next_pos = extract_braced_args(body, idx + len(r'\cventry'), 6)
            if len(args) == 6:
                dates, role, company, location, notes, desc = [clean_latex(m) for m in args]
                bullets = self._parse_bullets(args[5])
                if not bullets and desc.strip():
                    bullets = [desc.strip()]
                start_date, end_date = self._split_dates(dates)
                work_items.append(WorkItem(
                    name=company,
                    position=role,
                    location=location,
                    start_date=start_date,
                    end_date=end_date,
                    highlights=bullets
                ))
                pos = next_pos
            elif len(args) == 5:
                role, company, location, dates, desc_raw = [clean_latex(m) for m in args]
                bullets = self._parse_bullets(args[4])
                if not bullets and desc_raw.strip():
                    bullets = [desc_raw.strip()]
                start_date, end_date = self._split_dates(dates)
                work_items.append(WorkItem(
                    name=company,
                    position=role,
                    location=location,
                    start_date=start_date,
                    end_date=end_date,
                    highlights=bullets
                ))
                pos = next_pos
            else:
                pos = idx + len(r'\cventry')

        if work_items:
            return work_items

        # Pattern 3: Deedy format \runsubsection{Company} \descript{| Role} \location{Dates | Loc}
        if r"\runsubsection" in body:
            blocks = re.split(r'(?=\\runsubsection\b)', body)
            for block in blocks:
                if not block.strip():
                    continue
                co_match = re.search(r'\\runsubsection\{([^}]+)\}', block)
                desc_match = re.search(r'\\descript\{([^}]+)\}', block)
                loc_match = re.search(r'\\location\{([^}]+)\}', block)
                bullets = self._parse_bullets(block)
                if co_match:
                    company = clean_latex(co_match.group(1))
                    role = clean_latex(desc_match.group(1)).lstrip('|').strip() if desc_match else ""
                    raw_loc = clean_latex(loc_match.group(1)) if loc_match else ""
                    loc_parts = [p.strip() for p in raw_loc.split('|')]
                    dates = loc_parts[0] if loc_parts else ""
                    location = loc_parts[1] if len(loc_parts) > 1 else ""
                    start_date, end_date = self._split_dates(dates)
                    work_items.append(WorkItem(
                        name=company,
                        position=role,
                        location=location,
                        start_date=start_date,
                        end_date=end_date,
                        highlights=bullets
                    ))
            if work_items:
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

        # Pattern 2: \cventry (supports ModernCV 6-arg and Awesome-CV 5-arg)
        pos = 0
        while True:
            idx = body.find(r'\cventry', pos)
            if idx == -1:
                break
            args, next_pos = extract_braced_args(body, idx + len(r'\cventry'), 6)
            if len(args) == 6:
                dates, degree, inst, loc, notes, desc = [clean_latex(m) for m in args]
                bullets = self._parse_bullets(args[5])
                if not bullets and desc.strip():
                    bullets = [desc.strip()]
                start_date, end_date = self._split_dates(dates)
                edu_items.append(EducationItem(
                    institution=inst,
                    study_type=degree,
                    area=loc,
                    start_date=start_date,
                    end_date=end_date,
                    score=notes,
                    highlights=bullets
                ))
                pos = next_pos
            elif len(args) == 5:
                degree, inst, loc, dates, desc_raw = [clean_latex(m) for m in args]
                bullets = self._parse_bullets(args[4])
                if not bullets and desc_raw.strip():
                    bullets = [desc_raw.strip()]
                start_date, end_date = self._split_dates(dates)
                edu_items.append(EducationItem(
                    institution=inst,
                    study_type=degree,
                    area=loc,
                    start_date=start_date,
                    end_date=end_date,
                    highlights=bullets
                ))
                pos = next_pos
            else:
                pos = idx + len(r'\cventry')

        if edu_items:
            return edu_items

        # Pattern 3: Deedy format \runsubsection{University} \descript{| Degree} \location{Dates | Loc}
        if r"\runsubsection" in body:
            blocks = re.split(r'(?=\\runsubsection\b)', body)
            for block in blocks:
                if not block.strip():
                    continue
                inst_match = re.search(r'\\runsubsection\{([^}]+)\}', block)
                desc_match = re.search(r'\\descript\{([^}]+)\}', block)
                loc_match = re.search(r'\\location\{([^}]+)\}', block)
                bullets = self._parse_bullets(block)
                if inst_match:
                    inst = clean_latex(inst_match.group(1))
                    deg = clean_latex(desc_match.group(1)).lstrip('|').strip() if desc_match else ""
                    raw_loc = clean_latex(loc_match.group(1)) if loc_match else ""
                    loc_parts = [p.strip() for p in raw_loc.split('|')]
                    dates = loc_parts[0] if loc_parts else ""
                    area = loc_parts[1] if len(loc_parts) > 1 else ""
                    start_date, end_date = self._split_dates(dates)
                    edu_items.append(EducationItem(
                        institution=inst,
                        study_type=deg,
                        area=area,
                        start_date=start_date,
                        end_date=end_date,
                        highlights=bullets
                    ))
            if edu_items:
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
        
        # Pattern 1: \resumeProjectHeading with balanced brace extraction
        pos = 0
        while True:
            idx = body.find(r'\resumeProjectHeading', pos)
            if idx == -1:
                break
            args, next_pos = extract_braced_args(body, idx + len(r'\resumeProjectHeading'), 2)
            if len(args) >= 2:
                header_raw = args[0]
                date_raw = clean_latex(args[1])
                next_heading_idx = body.find(r'\resumeProjectHeading', next_pos)
                block_end = next_heading_idx if next_heading_idx != -1 else len(body)
                bullets = self._parse_bullets(body[next_pos:block_end])

                clean_header = re.sub(r'\$\s*(?:\\vert|\|)\s*\$', '|', header_raw)
                parts = [clean_latex(p).replace('$', '').strip() for p in clean_header.split('|')]
                name = parts[0].rstrip('|').strip() if parts else "Project"
                keywords = [k.strip() for k in parts[1].split(',') if k.strip()] if len(parts) > 1 else []
                
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
                pos = next_pos
            else:
                pos = idx + len(r'\resumeProjectHeading')

        if projects:
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

        # 1. Awesome-CV \cvskill{Category}{Skills}
        pos = 0
        while True:
            idx = body.find(r'\cvskill', pos)
            if idx == -1:
                break
            args, next_pos = extract_braced_args(body, idx + len(r'\cvskill'), 2)
            if len(args) >= 2:
                cat_name = clean_latex(args[0]).rstrip(':').strip()
                raw_items = clean_latex(args[1])
                keywords = [k.strip() for k in re.split(r'[,|•]', raw_items) if k.strip()]
                if keywords:
                    skills.append(SkillItem(name=cat_name, keywords=keywords))
                pos = next_pos
            else:
                pos = idx + len(r'\cvskill')

        if skills:
            return skills
        
        # 2. Line-based, itemized, and tabular patterns
        lines = body.splitlines()
        for line in lines:
            line_clean = line.strip()
            if not line_clean:
                continue

            # Tabular pattern: \textbf{Languages:} & Python, C++, Go \\
            tab_match = re.search(r'\\textbf\{([^}]+)\}:?\s*&\s*([^\\]+)', line_clean)
            if tab_match:
                cat_name = clean_latex(tab_match.group(1)).rstrip(':').strip()
                raw_items = clean_latex(tab_match.group(2))
                keywords = [k.strip() for k in re.split(r'[,|•]', raw_items) if k.strip()]
                if keywords:
                    skills.append(SkillItem(name=cat_name, keywords=keywords))
                continue
            
            # Match \textbf{Category}{: Item1, Item2} or \textbf{Category}: Item1, Item2
            cat_match = re.search(r'\\textbf\{([^}]+)\}\s*(?:\{:?\s*|:\s*)([^}\\]+)', line_clean)
            if cat_match:
                cat_name = clean_latex(cat_match.group(1)).rstrip(':').strip()
                raw_items = clean_latex(cat_match.group(2))
                keywords = [k.strip() for k in re.split(r'[,|•]', raw_items) if k.strip()]
                if keywords:
                    skills.append(SkillItem(name=cat_name, keywords=keywords))
            else:
                # \item \textbf{Category:} Item1, Item2
                simple_match = re.search(r'\\item\s*\\textbf\{([^}]+)\}\s*[:\-]\s*(.*)', line_clean)
                if simple_match:
                    cat_name = clean_latex(simple_match.group(1)).rstrip(':').strip()
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

    def _parse_certificates(self, body: str) -> List[CertificateItem]:
        """Parses certifications and licenses."""
        certs = []
        sub_pat = r'\\resumeSubheading\s*\{((?:[^{}]|\{[^{}]*\})*)\}\s*\{((?:[^{}]|\{[^{}]*\})*)\}\s*\{((?:[^{}]|\{[^{}]*\})*)\}\s*\{((?:[^{}]|\{[^{}]*\})*)\}'
        for m in re.finditer(sub_pat, body):
            a1, a2, a3, a4 = [clean_latex(s) for s in m.groups()]
            certs.append(CertificateItem(name=a1, date=a2, issuer=a3))
        if certs:
            return certs

        bullets = self._parse_bullets(body)
        for b in bullets:
            date_match = re.search(r'\((\d{4}(?:[-/]\d{2})?)\)', b)
            date = date_match.group(1) if date_match else ""
            clean_name = re.sub(r'\(\d{4}(?:[-/]\d{2})?\)', '', b).strip().rstrip('–-')
            certs.append(CertificateItem(name=clean_name, date=date))
        return certs

    def _parse_awards(self, body: str) -> List[AwardItem]:
        """Parses honors, awards, and hackathon accomplishments."""
        awards = []
        pos = 0
        while True:
            idx = body.find(r'\cvhonor', pos)
            if idx == -1:
                break
            args, next_pos = extract_braced_args(body, idx + len(r'\cvhonor'), 4)
            if len(args) == 4:
                award, event, loc, date = [clean_latex(s) for s in args]
                awards.append(AwardItem(title=award, awarder=event, date=date, summary=loc))
                pos = next_pos
            else:
                pos = idx + len(r'\cvhonor')
        if awards:
            return awards

        bullets = self._parse_bullets(body)
        for b in bullets:
            date_match = re.search(r'\((\d{4})\)', b)
            date = date_match.group(1) if date_match else ""
            title = re.sub(r'\(\d{4}\)', '', b).strip().rstrip('–-')
            awards.append(AwardItem(title=title, date=date))
        return awards

    def _parse_publications(self, body: str) -> List[PublicationItem]:
        """Parses publications and research papers."""
        pubs = []
        bullets = self._parse_bullets(body)
        for b in bullets:
            date_match = re.search(r'\b(19\d{2}|20\d{2})\b', b)
            date = date_match.group(0) if date_match else ""
            pubs.append(PublicationItem(name=b, release_date=date))
        return pubs

    def _parse_languages(self, body: str) -> List[LanguageItem]:
        """Parses spoken and natural languages."""
        langs = []
        bullets = self._parse_bullets(body)
        for b in bullets:
            parts = re.split(r'[,;]', b)
            for p in parts:
                m = re.match(r'([A-Za-z\s]+)(?:\(([^)]+)\)|:\s*([A-Za-z\s]+))', p.strip())
                if m:
                    lang = m.group(1).strip()
                    fluency = (m.group(2) or m.group(3) or "").strip()
                    langs.append(LanguageItem(language=lang, fluency=fluency))
                elif p.strip():
                    langs.append(LanguageItem(language=p.strip()))
        return langs

    def _split_dates(self, date_str: str) -> Tuple[str, str]:
        """Normalizes date ranges like '06/2025 -- 12/2025' or 'May 2023 - Present' without breaking ISO dates."""
        if not date_str:
            return "", ""
        # Delimiters: –, —, --, " to ", " - ", or dash between year and month/present
        parts = re.split(r'\s*(?:–|—|--|\s+to\s+|\s+-\s+|(?<=\d)-(?=[a-zA-Z]))\s*', date_str)
        if len(parts) >= 2:
            return parts[0].strip(), parts[1].strip()
        return date_str.strip(), ""
