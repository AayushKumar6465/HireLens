"""
Work experience parsing, date extraction, and overlapping period merging.

Calculates:
- Structured positions with company, title, dates, and duration in months
- Overlapping/concurrent interval merging
- True deduplicated total experience years
"""

from __future__ import annotations

import datetime
import re
from typing import Any

# Month lookup map
MONTHS = {
    "jan": 1,
    "january": 1,
    "feb": 2,
    "february": 2,
    "mar": 3,
    "march": 3,
    "apr": 4,
    "april": 4,
    "may": 5,
    "jun": 6,
    "june": 6,
    "jul": 7,
    "july": 7,
    "aug": 8,
    "august": 8,
    "sep": 9,
    "september": 9,
    "sept": 9,
    "oct": 10,
    "october": 10,
    "nov": 11,
    "november": 11,
    "dec": 12,
    "december": 12,
}

# Regex for dates: e.g. "Jan 2020 - Present", "05/2019 to 08/2021", "2018 - 2022"
DATE_RANGE_REGEX = re.compile(
    r"\b(?:(Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Sept|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?|\d{1,2})[\s/\.-]+)?(\d{4})\s*(?:–|-|to|until)\s*(?:(Present|Current|Now)|(?:(Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Sept|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?|\d{1,2})[\s/\.-]+)?(\d{4}))\b",
    re.IGNORECASE,
)


def _parse_month_year(
    month_str: str | None, year_str: str | None, default_month: int = 1
) -> tuple[int, int] | None:
    """Parse month and year into (year, month)."""
    if not year_str:
        return None
    try:
        year = int(year_str)
        if year < 1970 or year > 2050:
            return None
    except ValueError:
        return None

    month = default_month
    if month_str:
        clean_m = month_str.strip().lower()
        if clean_m.isdigit():
            m_val = int(clean_m)
            if 1 <= m_val <= 12:
                month = m_val
        elif clean_m in MONTHS:
            month = MONTHS[clean_m]

    return year, month


def merge_overlapping_intervals(
    intervals: list[tuple[int, int]],
) -> list[tuple[int, int]]:
    """
    Merge overlapping or contiguous month intervals: [(start_m, end_m), ...].

    Ensures concurrent employment does not artificially inflate total years.
    """
    if not intervals:
        return []

    # Sort by start month
    sorted_intervals = sorted(intervals, key=lambda x: (x[0], x[1]))
    merged: list[tuple[int, int]] = [sorted_intervals[0]]

    for current in sorted_intervals[1:]:
        prev_start, prev_end = merged[-1]
        curr_start, curr_end = current

        # If current interval overlaps or directly abuts previous interval
        if curr_start <= prev_end + 1:
            merged[-1] = (prev_start, max(prev_end, curr_end))
        else:
            merged.append(current)

    return merged


def parse_experience(experience_text: str) -> tuple[list[dict[str, Any]], float | None]:
    """
    Parse work experience section into structured items and total experience years.

    Returns (positions_list, total_experience_years).
    """
    if not experience_text.strip():
        return [], None

    now = datetime.datetime.now(datetime.UTC)
    current_year = now.year
    current_month = now.month
    current_month_index = current_year * 12 + current_month

    matches = list(DATE_RANGE_REGEX.finditer(experience_text))
    if not matches:
        return [], None

    positions: list[dict[str, Any]] = []
    month_intervals: list[tuple[int, int]] = []

    for i, match in enumerate(matches):
        start_month_str = match.group(1)
        start_year_str = match.group(2)
        is_present_str = match.group(3)
        end_month_str = match.group(4)
        end_year_str = match.group(5)

        start_parsed = _parse_month_year(
            start_month_str, start_year_str, default_month=1
        )
        if not start_parsed:
            continue

        s_year, s_month = start_parsed
        start_idx = s_year * 12 + s_month

        is_current = bool(is_present_str)
        if is_current:
            end_idx = current_month_index
            end_date_str = "Present"
        else:
            end_parsed = _parse_month_year(
                end_month_str, end_year_str, default_month=12
            )
            if end_parsed:
                e_year, e_month = end_parsed
                end_idx = e_year * 12 + e_month
                end_date_str = f"{e_year}-{e_month:02d}"
            else:
                end_idx = start_idx
                end_date_str = f"{s_year}-{s_month:02d}"

        # Ensure start <= end
        if end_idx < start_idx:
            start_idx, end_idx = end_idx, start_idx

        duration_months = max(1, (end_idx - start_idx) + 1)
        month_intervals.append((start_idx, end_idx))

        # Context slice for role/company description
        snippet_start = match.start()
        next_start = (
            matches[i + 1].start() if i + 1 < len(matches) else len(experience_text)
        )
        role_block = experience_text[snippet_start:next_start].strip()

        # Extract title or company from lines around the date
        lines = [line.strip() for line in role_block.split("\n") if line.strip()]
        title = lines[0] if lines else "Software Engineer"
        company = lines[1] if len(lines) > 1 else None

        positions.append(
            {
                "title": title,
                "company": company,
                "start_date": f"{s_year}-{s_month:02d}",
                "end_date": end_date_str,
                "duration_months": duration_months,
                "is_current": is_current,
                "description": role_block[:200] if role_block else None,
            }
        )

    # Merge intervals for accurate total years
    merged_intervals = merge_overlapping_intervals(month_intervals)
    total_months = sum((end - start + 1) for start, end in merged_intervals)
    total_experience_years = round(total_months / 12.0, 1) if total_months > 0 else 0.0

    return positions, total_experience_years
