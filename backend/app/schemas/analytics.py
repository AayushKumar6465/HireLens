"""
Analytics and dashboard Pydantic schemas.
"""

from __future__ import annotations

import uuid

from pydantic import BaseModel, Field


class ScoreBucket(BaseModel):
    """Distribution bucket for match scores."""

    range_label: str
    count: int


class StatusFunnelItem(BaseModel):
    """Candidate count in recruitment status funnel."""

    status: str
    count: int


class RecentCandidateItem(BaseModel):
    """Recent candidate match preview item."""

    candidate_id: uuid.UUID
    candidate_name: str
    job_id: uuid.UUID
    job_title: str
    total_score: float
    status: str
    created_at: str


class DashboardStatsResponse(BaseModel):
    """Consolidated KPI and analytics figures for recruiter dashboard."""

    open_jobs: int = 0
    total_candidates: int = 0
    resumes_processed: int = 0
    avg_match_score: float = 0.0
    score_distribution: list[ScoreBucket] = Field(default_factory=list)
    status_funnel: list[StatusFunnelItem] = Field(default_factory=list)
    recent_candidates: list[RecentCandidateItem] = Field(default_factory=list)
