"""
Skill extraction engine with evidence recording and false-positive prevention.

Features:
- Matches against 300+ skills taxonomy from backend/data/skills_taxonomy.json
- Boundary-aware pattern matching
- False-positive guard (e.g. Java vs JavaScript, Go vs common English verb)
- Generates <= 120 character evidence snippets
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from app.core.logging import get_logger

logger = get_logger(__name__)

# Short acronyms/tokens that must NOT be matched case-insensitively in general prose
CASE_SENSITIVE_SHORT_SKILLS = {
    "c",
    "r",
    "go",
    "js",
    "ts",
    "ai",
    "ml",
    "ui",
    "ux",
    "ci",
    "cd",
}


def load_taxonomy() -> list[dict[str, Any]]:
    """Load canonical skills taxonomy from json."""
    tax_path = (
        Path(__file__).resolve().parent.parent.parent.parent
        / "data"
        / "skills_taxonomy.json"
    )
    if not tax_path.exists():
        return []
    try:
        with open(tax_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("skills", [])
    except (OSError, json.JSONDecodeError) as exc:
        logger.error("Failed to load skills taxonomy: %s", exc)
        return []


_TAXONOMY_CACHE: list[dict[str, Any]] | None = None


def get_taxonomy() -> list[dict[str, Any]]:
    global _TAXONOMY_CACHE
    if _TAXONOMY_CACHE is None:
        _TAXONOMY_CACHE = load_taxonomy()
    return _TAXONOMY_CACHE


def make_snippet(text: str, start: int, end: int, max_chars: int = 120) -> str:
    """
    Extract a concise window of text surrounding the match, bounded to max_chars.
    """
    target_len = end - start
    remaining = max_chars - target_len
    half_pad = max(remaining // 2, 0)

    snippet_start = max(0, start - half_pad)
    snippet_end = min(len(text), end + half_pad)

    snippet = text[snippet_start:snippet_end].replace("\n", " ").strip()

    # Collapse multiple whitespace
    snippet = re.sub(r"\s+", " ", snippet)

    if len(snippet) > max_chars:
        snippet = snippet[: max_chars - 3].strip() + "..."

    return snippet


def extract_skills(sections: dict[str, str]) -> list[dict[str, Any]]:
    """
    Extract skills from all resume sections with evidence snippets.

    Returns list of:
    {
        "skill": canonical_name,
        "category": category_name,
        "found_in_section": section_name,
        "match_type": "exact" | "alias",
        "snippet": snippet_text (<= 120 chars)
    }
    """
    taxonomy = get_taxonomy()
    extracted: dict[str, dict[str, Any]] = {}

    # Section priority for recording evidence: skills > experience > projects > education > summary > other
    section_priority = {
        "skills": 6,
        "experience": 5,
        "projects": 4,
        "certifications": 3,
        "education": 2,
        "summary": 1,
        "header": 0,
        "other": 0,
    }

    # Pre-sort sections by priority
    sorted_sections = sorted(
        sections.items(),
        key=lambda item: section_priority.get(item[0], 0),
        reverse=True,
    )

    for sec_name, sec_text in sorted_sections:
        if not sec_text:
            continue

        for item in taxonomy:
            canonical = item["canonical"]
            category = item.get("category", "General")
            aliases = item.get("aliases", [canonical.lower()])

            # Check each alias
            for alias in aliases:
                alias_clean = alias.strip()
                if not alias_clean:
                    continue

                # Escape special characters (e.g. C++, C#, .NET)
                escaped = re.escape(alias_clean)

                # Special boundary handling for symbols like ++ or #
                if escaped.endswith((r"\+\+", r"\#")):
                    pattern_str = rf"(?<!\w){escaped}(?!\w)"
                elif escaped.startswith(r"\."):
                    pattern_str = rf"{escaped}(?!\w)"
                else:
                    pattern_str = rf"\b{escaped}\b"

                is_short = alias_clean.lower() in CASE_SENSITIVE_SHORT_SKILLS

                # If short token and in general prose, require exact case match
                flags = 0 if (is_short and sec_name != "skills") else re.IGNORECASE
                pattern = re.compile(pattern_str, flags)

                match = pattern.search(sec_text)
                if match:
                    # Guard against false positives: Java matching inside JavaScript
                    if (
                        alias_clean.lower() == "java"
                        and "javascript"
                        in sec_text[match.start() : match.end() + 10].lower()
                    ):
                        continue

                    snippet = make_snippet(sec_text, match.start(), match.end())
                    match_type = (
                        "exact" if alias_clean.lower() == canonical.lower() else "alias"
                    )

                    # If not yet extracted, or found in a higher-priority section, save
                    existing = extracted.get(canonical)
                    current_priority = section_priority.get(sec_name, 0)
                    existing_priority = (
                        section_priority.get(existing["found_in_section"], 0)
                        if existing
                        else -1
                    )

                    if existing is None or current_priority > existing_priority:
                        extracted[canonical] = {
                            "skill": canonical,
                            "category": category,
                            "found_in_section": sec_name,
                            "match_type": match_type,
                            "snippet": snippet,
                        }
                    break

    return list(extracted.values())
