"""
Text normalization utilities for resume parsing.

Handles:
- Ligature unfolding (e.g. fi, fl, ffi, ffl)
- Standardizing bullet points and list markers
- Reconstructing hyphenated line breaks (e.g. devel-\nopment -> development)
- Normalizing whitespace and carriage returns
"""

from __future__ import annotations

import re

# Common typographic ligatures to ASCII sequences
LIGATURES = {
    "ﬁ": "fi",
    "ﬂ": "fl",
    "ﬀ": "ff",
    "ﬃ": "ffi",
    "ﬄ": "ffl",
    "ﬅ": "ft",
    "ﬆ": "st",
    "Æ": "AE",
    "æ": "ae",
    "Œ": "OE",
    "œ": "oe",
}

# Regex matching various unicode bullet and list marker characters
BULLET_PATTERN = re.compile(
    r"[\u2022\u2023\u25E6\u2043\u2219\u25AA\u25AB\u25CF\u25CB\u25A0\u25A1\u25C6\u25C7\u00B7]"
)


def clean_text(text: str | None) -> str:
    """
    Apply comprehensive normalization to raw extracted resume text.

    Returns sanitized, cohesive plain text.
    """
    if not text:
        return ""

    # Replace ligatures
    for lig, replacement in LIGATURES.items():
        text = text.replace(lig, replacement)

    # Normalize carriage returns and line endings
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # Reconstruct hyphenated words split across line breaks: e.g. "experi-\nence" -> "experience"
    text = re.sub(r"(\b\w+)-\n(\w+\b)", r"\1\2", text)

    # Replace bullets with a uniform bullet symbol followed by space
    text = BULLET_PATTERN.sub("\n* ", text)

    # Replace non-breaking spaces and unusual space chars
    text = re.sub(r"[\u00A0\u2000-\u200B\u202F\u205F\u3000]", " ", text)

    # Collapse multiple inline spaces/tabs to a single space
    text = re.sub(r"[ \t]+", " ", text)

    # Limit consecutive newlines to 2 (paragraph break)
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()
