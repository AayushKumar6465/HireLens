"""
Candidate comparison Pydantic schemas.
"""

from __future__ import annotations

import uuid

from pydantic import BaseModel, Field


class CompareRequest(BaseModel):
    """Payload to compare multiple candidates on a job."""

    candidate_ids: list[uuid.UUID] = Field(
        ...,
        min_length=2,
        max_length=4,
        description="List of 2 to 4 candidate IDs to compare side by side",
    )


class CandidateCompareItem(BaseModel):
    """Side-by-side comparison data for an individual candidate."""

    candidate_id: uuid.UUID
    candidate_name: str
    candidate_email: str | None = None
    status: str
    total_score: float
    skill_score: float | None = None
    semantic_score: float | None = None
    experience_score: float | None = None
    education_score: float | None = None
    total_experience_years: float | None = None
    highest_degree: str | None = None
    matched_skills: list[str] = Field(default_factory=list)
    missing_required: list[str] = Field(default_factory=list)


class SkillMatrixRow(BaseModel):
    """Row in the unified comparison skill matrix."""

    skill: str
    importance: str
    candidate_status: dict[str, bool]  # candidate_id -> True/False


class CompareResponse(BaseModel):
    """Response containing side-by-side candidates and skill matrix."""

    job_id: uuid.UUID
    job_title: str
    candidates: list[CandidateCompareItem]
    skill_matrix: list[SkillMatrixRow]
