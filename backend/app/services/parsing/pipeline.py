"""
Resume parsing pipeline orchestrator.

Coordinates:
- Text extraction (pdfplumber/pymupdf fallback or docx)
- Text normalization and cleaning
- Heading-based section segmentation
- Contact details extraction (name, email, phone, links)
- Skills extraction with snippet evidence and false-positive prevention
- Experience date normalization and overlapping period merging
- Education degree extraction and highest degree classification
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.services.parsing.contact_parser import parse_contact_info
from app.services.parsing.education_parser import parse_education
from app.services.parsing.experience_parser import parse_experience
from app.services.parsing.extractor import extract_document_text
from app.services.parsing.section_splitter import split_sections
from app.services.parsing.skill_parser import extract_skills
from app.utils.text_cleaning import clean_text


@dataclass
class ParsedResumeData:
    """Complete structured extraction result."""

    raw_text: str
    contact_info: dict[str, Any]
    skills: list[dict[str, Any]]
    experience: list[dict[str, Any]]
    education: list[dict[str, Any]]
    total_experience_years: float | None
    highest_degree: str | None
    sections: dict[str, str]
    parser_version: str = "1.0.0"


def parse_resume_document(
    file_path: Path, extension: str, original_filename: str = ""
) -> ParsedResumeData:
    """
    Execute full deterministic parsing pipeline on an uploaded resume document.

    Raises ScannedOrEmptyError or ParsingError on extraction/structural failures.
    """
    # 1. Extract raw text
    raw_text = extract_document_text(file_path, extension)

    # 2. Normalize and clean text
    cleaned = clean_text(raw_text)

    # 3. Split sections
    sections = split_sections(cleaned)

    # 4. Extract contact details
    contact = parse_contact_info(cleaned, sections, original_filename=original_filename)

    # 5. Extract skills with evidence
    skills = extract_skills(sections)

    # 6. Parse work experience & calculate merged years
    experience_text = sections.get("experience", "")
    positions, total_exp = parse_experience(experience_text)

    # 7. Parse education & determine highest degree level
    education_text = sections.get("education", "")
    education_records, highest_degree = parse_education(
        education_text, full_text=cleaned
    )

    return ParsedResumeData(
        raw_text=cleaned,
        contact_info=contact,
        skills=skills,
        experience=positions,
        education=education_records,
        total_experience_years=total_exp,
        highest_degree=highest_degree,
        sections=sections,
        parser_version="1.0.0",
    )
