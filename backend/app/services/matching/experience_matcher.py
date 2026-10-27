"""
Experience scoring comparing candidate total experience years against job requirements.

Pure Python function: no HTTP, ORM, or database dependencies.
"""

from __future__ import annotations


def calculate_experience_score(
    candidate_years: float | None,
    required_years: float | None,
) -> tuple[float | None, dict[str, float | None]]:
    """
    Score candidate experience against minimum required years.

    - 100 if candidate_years >= required_years
    - Scaled down proportionally below it: (candidate_years / required_years) * 100
    - Returns None if required_years is not defined on the job opening

    Returns:
    (
        experience_score: float | None,
        details: {"candidate_years": float, "required_years": float}
    )
    """
    details = {
        "candidate_years": candidate_years,
        "required_years": required_years,
    }

    if required_years is None or required_years <= 0:
        return None, details

    cand_years = (
        candidate_years
        if (candidate_years is not None and candidate_years >= 0)
        else 0.0
    )

    if cand_years >= required_years:
        score = 100.0
    else:
        score = round((cand_years / required_years) * 100.0, 1)

    score = min(100.0, max(0.0, score))
    return score, details
