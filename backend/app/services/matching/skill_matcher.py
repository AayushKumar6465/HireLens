"""
Skill matching algorithm with weighted importance and evidence tracking.

Pure Python function: no HTTP, ORM, or database dependencies.
"""

from __future__ import annotations

from typing import Any


def match_skills(
    job_requirements: list[dict[str, Any]],
    candidate_skills: list[dict[str, Any]],
) -> tuple[float | None, list[dict[str, Any]], list[str], list[str], list[str]]:
    """
    Match candidate skills against job requirements.

    Weights:
    - 'required' importance weighs 2x 'preferred' importance
    - Score = (matched_weight / total_weight) * 100

    Returns:
    (
        skill_score: float | None,
        matched_skills: list[dict],
        missing_required: list[str],
        missing_preferred: list[str],
        extra_skills: list[str]
    )
    """
    if not job_requirements:
        all_candidate_skills = [
            s.get("skill", "") for s in candidate_skills if s.get("skill")
        ]
        return None, [], [], [], all_candidate_skills

    # Index candidate skills by lower-cased canonical name
    candidate_map = {
        s.get("skill", "").strip().lower(): s
        for s in candidate_skills
        if s.get("skill")
    }

    total_weight = 0.0
    matched_weight = 0.0

    matched_skills: list[dict[str, Any]] = []
    missing_required: list[str] = []
    missing_preferred: list[str] = []
    matched_req_skills: set[str] = set()

    for req in job_requirements:
        skill_name = req.get("skill", "").strip()
        importance = req.get("importance", "required").lower()
        base_weight = float(req.get("weight", 1.0))

        multiplier = 2.0 if importance == "required" else 1.0
        effective_weight = base_weight * multiplier
        total_weight += effective_weight

        skill_key = skill_name.lower()
        if skill_key in candidate_map:
            matched_weight += effective_weight
            cand_skill = candidate_map[skill_key]
            matched_req_skills.add(skill_key)

            matched_skills.append(
                {
                    "skill": skill_name,
                    "importance": importance,
                    "found_in": cand_skill.get("found_in_section", "skills"),
                    "match_type": cand_skill.get("match_type", "exact"),
                    "snippet": cand_skill.get("snippet", ""),
                }
            )
        else:
            if importance == "required":
                missing_required.append(skill_name)
            else:
                missing_preferred.append(skill_name)

    # Extra candidate skills not in job requirements
    extra_skills = [
        s.get("skill", "")
        for k, s in candidate_map.items()
        if k not in matched_req_skills and s.get("skill")
    ]

    skill_score = (
        round((matched_weight / total_weight) * 100.0, 1) if total_weight > 0 else 100.0
    )
    skill_score = min(100.0, max(0.0, skill_score))

    return (
        skill_score,
        matched_skills,
        missing_required,
        missing_preferred,
        extra_skills,
    )
