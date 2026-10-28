"""
Analytics and dashboard KPI endpoints (/api/v1/analytics).
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.candidate import Candidate
from app.models.job import Job
from app.models.match_result import MatchResult
from app.models.resume import Resume
from app.models.user import User
from app.schemas.analytics import (
    DashboardStatsResponse,
    RecentCandidateItem,
    ScoreBucket,
    StatusFunnelItem,
)

router = APIRouter()

CurrentUser = Annotated[User, Depends(get_current_user)]
DbSession = Annotated[Session, Depends(get_db)]


@router.get(
    "/dashboard",
    response_model=DashboardStatsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get recruiter dashboard analytics",
)
def get_dashboard_stats(
    current_user: CurrentUser,
    db: DbSession,
) -> DashboardStatsResponse:
    """
    Compute genuine recruiter KPIs and funnel distributions from persisted data.
    Strictly scoped to the current recruiter's jobs and candidates.
    """
    # 1. Open Jobs
    open_jobs = (
        db.query(func.count(Job.id))
        .filter(Job.owner_id == current_user.id, Job.status == "open")
        .scalar()
        or 0
    )

    # 2. Total Candidates
    total_candidates = (
        db.query(func.count(Candidate.id))
        .filter(Candidate.owner_id == current_user.id)
        .scalar()
        or 0
    )

    # 3. Resumes Processed
    resumes_processed = (
        db.query(func.count(Resume.id))
        .join(Candidate, Resume.candidate_id == Candidate.id)
        .filter(Candidate.owner_id == current_user.id, Resume.parse_status == "done")
        .scalar()
        or 0
    )

    # 4. Average Match Score across user's jobs
    user_job_ids_select = select(Job.id).filter(Job.owner_id == current_user.id)
    avg_score_res = (
        db.query(func.avg(MatchResult.total_score))
        .filter(MatchResult.job_id.in_(user_job_ids_select))
        .scalar()
    )
    avg_match_score = (
        round(float(avg_score_res), 1) if avg_score_res is not None else 0.0
    )

    # 5. Score Distribution Buckets
    matches = (
        db.query(MatchResult.total_score)
        .filter(MatchResult.job_id.in_(user_job_ids_select))
        .all()
    )
    b_80_100 = 0
    b_60_79 = 0
    b_40_59 = 0
    b_under_40 = 0
    for (score,) in matches:
        if score >= 80.0:
            b_80_100 += 1
        elif score >= 60.0:
            b_60_79 += 1
        elif score >= 40.0:
            b_40_59 += 1
        else:
            b_under_40 += 1

    score_distribution = [
        ScoreBucket(range_label="80-100% (Strong)", count=b_80_100),
        ScoreBucket(range_label="60-79% (Good)", count=b_60_79),
        ScoreBucket(range_label="40-59% (Moderate)", count=b_40_59),
        ScoreBucket(range_label="<40% (Low)", count=b_under_40),
    ]

    # 6. Status Funnel
    funnel_counts = (
        db.query(Candidate.status, func.count(Candidate.id))
        .filter(Candidate.owner_id == current_user.id)
        .group_by(Candidate.status)
        .all()
    )
    funnel_map = dict(funnel_counts)
    standard_statuses = ["new", "screening", "interview", "offer", "rejected"]
    status_funnel = [
        StatusFunnelItem(status=st, count=funnel_map.get(st, 0))
        for st in standard_statuses
    ]

    # 7. Recent Candidates
    recent_matches = (
        db.query(MatchResult, Candidate, Job)
        .join(Candidate, MatchResult.candidate_id == Candidate.id)
        .join(Job, MatchResult.job_id == Job.id)
        .filter(Job.owner_id == current_user.id)
        .order_by(MatchResult.created_at.desc())
        .limit(6)
        .all()
    )
    recent_candidates = [
        RecentCandidateItem(
            candidate_id=cand.id,
            candidate_name=cand.full_name,
            job_id=j.id,
            job_title=j.title,
            total_score=m.total_score,
            status=cand.status,
            created_at=m.created_at.isoformat() if m.created_at else "",
        )
        for m, cand, j in recent_matches
    ]

    return DashboardStatsResponse(
        open_jobs=open_jobs,
        total_candidates=total_candidates,
        resumes_processed=resumes_processed,
        avg_match_score=avg_match_score,
        score_distribution=score_distribution,
        status_funnel=status_funnel,
        recent_candidates=recent_candidates,
    )
