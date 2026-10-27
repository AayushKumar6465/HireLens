"""
Education scoring comparing candidate highest degree level against job requirements.

Pure Python function: no HTTP, ORM, or database dependencies.
"""

from __future__ import annotations

# Canonical degree rank mapping matching degree_levels.json
DEGREE_RANKS = {
    "doctorate": 5,
    "master": 4,
    "bachelor": 3,
    "associate": 2,
    "high_school": 1,
}


def calculate_education_score(
    candidate_level: str | None,
    required_level: str | None,
) -> tuple[float | None, dict[str, str | None]]:
    """
    Score candidate education level against job requirement.

    - 100 if candidate level meets or exceeds required rank
    - Scaled down proportionally if below required rank: (candidate_rank / required_rank) * 100
    - Returns None if required_level is not defined on the job opening

    Returns:
    (
        education_score: float | None,
        details: {"candidate_level": str, "required_level": str}
    )
    """
    details = {
        "candidate_level": candidate_level,
        "required_level": required_level,
    }

    if not required_level or required_level.strip().lower() not in DEGREE_RANKS:
        return None, details

    req_rank = DEGREE_RANKS[required_level.strip().lower()]
    cand_key = candidate_level.strip().lower() if candidate_level else None
    cand_rank = DEGREE_RANKS.get(cand_key, 0) if cand_key else 0

    if cand_rank >= req_rank:
        score = 100.0
    else:
        score = round((cand_rank / req_rank) * 100.0, 1)

    score = min(100.0, max(0.0, score))
    return score, details
