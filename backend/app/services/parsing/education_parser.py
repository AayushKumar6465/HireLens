"""
Education extraction and highest degree normalization.

Extracts:
- Degree title and field of study
- Canonical degree level based on degree_levels.json
- Graduation year and institution name
- Normalized highest_degree achieved
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from app.core.logging import get_logger

logger = get_logger(__name__)


def load_degree_levels() -> list[dict[str, Any]]:
    """Load canonical degree hierarchy."""
    path = (
        Path(__file__).resolve().parent.parent.parent.parent
        / "data"
        / "degree_levels.json"
    )
    if not path.exists():
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("levels", [])
    except (OSError, json.JSONDecodeError) as exc:
        logger.error("Failed to load degree levels: %s", exc)
        return []


_DEGREE_LEVELS_CACHE: list[dict[str, Any]] | None = None


def get_degree_levels() -> list[dict[str, Any]]:
    global _DEGREE_LEVELS_CACHE
    if _DEGREE_LEVELS_CACHE is None:
        _DEGREE_LEVELS_CACHE = load_degree_levels()
    return _DEGREE_LEVELS_CACHE


YEAR_PATTERN = re.compile(r"\b(19\d{2}|20\d{2})\b")
FIELD_PATTERNS = [
    re.compile(
        r"\b(?:in|of)\s+([A-Za-z\s]{3,35}(?:Engineering|Science|Technology|Arts|Business|Administration|Management|Studies))\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(Computer\s+Science|Information\s+Technology|Data\s+Science|Electrical\s+Engineering|Mechanical\s+Engineering|Software\s+Engineering)\b",
        re.IGNORECASE,
    ),
]


def parse_education(
    education_text: str, full_text: str = ""
) -> tuple[list[dict[str, Any]], str | None]:
    """
    Parse education section into structured education records and determine highest degree.

    Returns (education_list, highest_degree_key).
    """
    target_text = education_text if education_text.strip() else full_text
    if not target_text.strip():
        return [], None

    levels = get_degree_levels()
    # Sort levels by rank descending
    sorted_levels = sorted(levels, key=lambda x: x.get("rank", 0), reverse=True)

    extracted_records: list[dict[str, Any]] = []
    highest_rank = -1
    highest_degree_key: str | None = None

    lines = [line.strip() for line in target_text.split("\n") if line.strip()]

    for line in lines:
        for lvl in sorted_levels:
            key = lvl["key"]
            rank = lvl["rank"]
            aliases = lvl.get("aliases", [key])

            matched_alias = None
            for alias in aliases:
                pattern = rf"\b{re.escape(alias)}\b"
                if re.search(pattern, line, re.IGNORECASE):
                    matched_alias = alias
                    break

            if matched_alias:
                # Extract graduation year
                year_match = YEAR_PATTERN.search(line)
                grad_year = int(year_match.group(1)) if year_match else None

                # Extract field of study
                field_of_study = None
                for fp in FIELD_PATTERNS:
                    fm = fp.search(line)
                    if fm:
                        field_of_study = fm.group(1).strip()
                        break

                record = {
                    "degree": line[:80],
                    "degree_level": key,
                    "field_of_study": field_of_study or "General Studies",
                    "institution": None,
                    "graduation_year": grad_year,
                }
                extracted_records.append(record)

                if rank > highest_rank:
                    highest_rank = rank
                    highest_degree_key = key
                break

    return extracted_records, highest_degree_key
