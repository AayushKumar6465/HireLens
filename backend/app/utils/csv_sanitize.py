"""
CSV formula-injection sanitizer.

Prevents CSV/Spreadsheet injection attacks (CWE-1236).
Cells starting with =, +, -, @, or tab/CR characters are neutralized with a leading single quote or tab.
"""

from __future__ import annotations

from typing import Any

DANGEROUS_PREFIXES = ("=", "+", "-", "@", "\t", "\r")


def sanitize_csv_cell(value: Any) -> str:
    """
    Sanitize an individual CSV cell value against formula injection.

    If the string begins with any trigger character (=, +, -, @), prefix it with a single quote.
    """
    if value is None:
        return ""
    text = str(value).strip()
    if text.startswith(DANGEROUS_PREFIXES):
        return f"'{text}"
    return text
