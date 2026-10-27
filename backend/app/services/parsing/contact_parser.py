"""
Contact information extraction from resume header and text.

Extracts:
- Email address (RFC 5322 regex)
- Phone numbers (domestic & international patterns)
- Professional URLs (LinkedIn, GitHub, portfolio)
- Candidate name (positional and title-case heuristics from header)
"""

from __future__ import annotations

import re
from typing import Any

EMAIL_PATTERN = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b")

# Matches phone numbers in international (+XX), bracketed, hyphenated, or dotted formats
PHONE_PATTERN = re.compile(
    r"(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"
)

LINK_PATTERN = re.compile(
    r"\b(?:https?://)?(?:www\.)?(github\.com/[A-Za-z0-9_-]+|linkedin\.com/in/[A-Za-z0-9_-]+|[A-Za-z0-9_-]+\.(?:dev|io|me|tech|com))\b",
    re.IGNORECASE,
)

NON_NAME_WORDS = {
    "resume",
    "curriculum",
    "vitae",
    "cv",
    "profile",
    "contact",
    "summary",
    "experience",
    "education",
    "skills",
    "projects",
    "objective",
    "email",
    "phone",
    "address",
    "page",
    "developer",
    "engineer",
}


def extract_email(text: str) -> str | None:
    """Extract primary email address from text."""
    matches = EMAIL_PATTERN.findall(text)
    if matches:
        return matches[0].strip().lower()
    return None


def extract_phone(text: str) -> str | None:
    """Extract primary phone number from text."""
    matches = PHONE_PATTERN.findall(text)
    if matches:
        # Sanitize whitespace
        return re.sub(r"\s+", " ", matches[0].strip())
    return None


def extract_links(text: str) -> list[str]:
    """Extract social and portfolio links."""
    matches = LINK_PATTERN.findall(text)
    links: list[str] = []
    seen: set[str] = set()
    for m in matches:
        url = m.strip()
        if not url.startswith(("http://", "https://")):
            url = f"https://{url}"
        if url.lower() not in seen:
            seen.add(url.lower())
            links.append(url)
    return links


def extract_name(header_text: str, fallback_filename: str = "") -> str:
    """
    Extract candidate full name using title-case positional heuristics from the header section.

    Looks at the first 5 non-empty lines before any contact details or body text.
    """
    lines = [line.strip() for line in header_text.split("\n") if line.strip()]

    for line in lines[:5]:
        # Strip bullets or non-alpha punctuation
        clean_line = re.sub(r"^[\*\-•·\s]+", "", line).strip()

        # Reject lines with email or phone or URLs
        if (
            EMAIL_PATTERN.search(clean_line)
            or PHONE_PATTERN.search(clean_line)
            or "http" in clean_line.lower()
        ):
            continue

        words = clean_line.split()

        # Legitimate candidate names are usually 2 to 4 words
        if 2 <= len(words) <= 4:
            # Check that line doesn't contain forbidden keywords
            has_forbidden = any(w.lower() in NON_NAME_WORDS for w in words)
            if has_forbidden:
                continue

            # Ensure words look like names (mostly alphabetic, capitalized)
            is_valid_name = all(re.match(r"^[A-Z][a-zA-Z'\-\.]*$", w) for w in words)
            if is_valid_name:
                return " ".join(words)

    # Fallback: clean original filename if available
    if fallback_filename:
        stem = re.sub(r"[-_]", " ", fallback_filename).split(".")[0].strip()
        stem_words = [
            w.capitalize() for w in stem.split() if w.lower() not in NON_NAME_WORDS
        ]
        if 1 <= len(stem_words) <= 4:
            return " ".join(stem_words)

    return "Candidate"


def parse_contact_info(
    text: str, sections: dict[str, str], original_filename: str = ""
) -> dict[str, Any]:
    """Extract all candidate contact information."""
    header = sections.get("header", "")
    email = extract_email(text)
    phone = extract_phone(text)
    links = extract_links(text)
    name = extract_name(header if header else text, fallback_filename=original_filename)

    return {
        "full_name": name,
        "email": email,
        "phone": phone,
        "links": links,
    }
