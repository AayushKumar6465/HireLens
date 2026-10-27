"""
Rule-based section segmentation for resume text.

Detects canonical headings and splits text into structured sections:
- header (name, contact block)
- summary (summary, profile, objective)
- experience (work history, employment)
- education (academics, degrees)
- skills (technical skills, competencies)
- projects (personal/academic projects)
- certifications (licenses, certs, courses)
"""

from __future__ import annotations

import re

# Canonical section definitions and matching regex patterns
SECTION_PATTERNS = {
    "experience": re.compile(
        r"^(?:(?:work|professional|employment|career|relevant)\s+experience|experience|employment\s+history|work\s+history|work\s+background)\b",
        re.IGNORECASE,
    ),
    "education": re.compile(
        r"^(?:education|academic\s+(?:background|history|qualifications)|educational\s+qualifications|academics|qualifications|degrees)\b",
        re.IGNORECASE,
    ),
    "skills": re.compile(
        r"^(?:technical\s+skills|core\s+competencies|key\s+skills|skills\s*(?:&|and)\s*technologies|skills|technologies|proficiencies|tools\s*(?:&|and)\s*technologies)\b",
        re.IGNORECASE,
    ),
    "projects": re.compile(
        r"^(?:projects|personal\s+projects|academic\s+projects|key\s+projects|portfolio)\b",
        re.IGNORECASE,
    ),
    "certifications": re.compile(
        r"^(?:certifications|certificates|licenses|courses|accreditations|credentials)\b",
        re.IGNORECASE,
    ),
    "summary": re.compile(
        r"^(?:professional\s+summary|executive\s+summary|summary|profile|about\s+me|objective|career\s+objective)\b",
        re.IGNORECASE,
    ),
}


def split_sections(text: str) -> dict[str, str]:
    """
    Split normalized resume text into structured canonical sections.

    Returns a dictionary of {section_name: section_text}.
    """
    lines = text.split("\n")
    sections: dict[str, list[str]] = {
        "header": [],
        "summary": [],
        "experience": [],
        "education": [],
        "skills": [],
        "projects": [],
        "certifications": [],
        "other": [],
    }

    current_section = "header"

    for line in lines:
        stripped = line.strip()
        if not stripped:
            if current_section:
                sections[current_section].append("")
            continue

        # Check if line matches a section heading
        # A heading line is typically short (<= 60 chars) and doesn't contain sentence punctuation
        if len(stripped) <= 60 and not stripped.endswith((".", ",", ";")):
            clean_heading = re.sub(r"[:\-_#\*\(\)]", "", stripped).strip()
            matched_section = None

            for sec_name, pattern in SECTION_PATTERNS.items():
                if pattern.match(clean_heading):
                    matched_section = sec_name
                    break

            if matched_section:
                current_section = matched_section
                continue

        sections[current_section].append(line)

    # Clean up empty lines and join sections
    result: dict[str, str] = {}
    for sec_name, sec_lines in sections.items():
        joined = "\n".join(sec_lines).strip()
        if joined:
            result[sec_name] = joined

    return result
