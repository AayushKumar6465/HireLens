"""
Job opening, requirement, and candidate ranking endpoints (/api/v1/jobs).

Endpoints:
- POST /: Create a job opening with optional requirements (201 Created)
- GET /: List user's jobs with search and pagination (200 OK)
- GET /{id}: Retrieve single job details (200 OK)
- PUT /{id}: Update job details and requirements (200 OK)
- DELETE /{id}: Delete job opening (204 No Content)
- POST /{id}/extract-requirements: Suggest skills from job description (200 OK)
- POST /{id}/requirements: Add requirement to job (201 Created)
- DELETE /{id}/requirements/{requirement_id}: Delete requirement (204 No Content)
- POST /{id}/match: Trigger matching and score all parsed resumes for the job (200 OK)
- GET /{id}/ranking: Retrieve sorted and filtered candidate ranking (200 OK)
- GET /{id}/candidates/{candidate_id}/match: Retrieve candidate match breakdown (200 OK)
- GET /{id}/export.csv: Export candidate ranking as CSV with formula protection (200 OK)

Ownership:
- All operations strictly owner-scoped. Foreign jobs return HTTP 404 (admins cannot bypass).
"""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.job import Job
from app.models.user import User
from app.schemas.compare import (
    CandidateCompareItem,
    CompareRequest,
    CompareResponse,
    SkillMatrixRow,
)
from app.schemas.job import (
    ExtractRequirementsResponse,
    JobCreate,
    JobRequirementCreate,
    JobRequirementResponse,
    JobResponse,
    JobUpdate,
    MatchSummaryResponse,
    PaginatedJobsResponse,
    PaginatedRankingResponse,
    RankedCandidateItem,
)
from app.services import job_service
from app.services.matching import ranker

router = APIRouter()

DbSession = Annotated[Session, Depends(get_db)]
CurrentUser = Annotated[User, Depends(get_current_user)]


@router.post(
    "",
    response_model=JobResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new job opening",
)
def create_job(
    data: JobCreate,
    current_user: CurrentUser,
    db: DbSession,
) -> JobResponse:
    """Create a new job opening owned by the authenticated recruiter."""
    job = job_service.create_job(db=db, user=current_user, data=data)
    return JobResponse.model_validate(job)


@router.get(
    "",
    response_model=PaginatedJobsResponse,
    status_code=status.HTTP_200_OK,
    summary="List job openings owned by the current user",
)
def list_jobs(
    current_user: CurrentUser,
    db: DbSession,
    page: int = Query(1, ge=1, description="Page number starting at 1"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page (max 100)"),
    q: str | None = Query(
        None, description="Search filter for title, department, or description"
    ),
    status_filter: str | None = Query(
        None, alias="status", description="Filter by status (open/closed)"
    ),
) -> PaginatedJobsResponse:
    """Retrieve a paginated list of jobs owned by the current recruiter."""
    jobs, total = job_service.list_jobs(
        db=db,
        user=current_user,
        page=page,
        page_size=page_size,
        q=q,
        status=status_filter,
    )
    return PaginatedJobsResponse(
        items=[JobResponse.model_validate(j) for j in jobs],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/{id}",
    response_model=JobResponse,
    status_code=status.HTTP_200_OK,
    summary="Get job opening details by ID",
)
def get_job(
    id: uuid.UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> JobResponse:
    """Retrieve full details of a specific job. Returns 404 for foreign jobs."""
    job = job_service.get_job(db=db, user=current_user, job_id=id)
    return JobResponse.model_validate(job)


@router.put(
    "/{id}",
    response_model=JobResponse,
    status_code=status.HTTP_200_OK,
    summary="Update a job opening",
)
def update_job(
    id: uuid.UUID,
    data: JobUpdate,
    current_user: CurrentUser,
    db: DbSession,
) -> JobResponse:
    """Update fields and requirements of a job. Returns 404 for foreign jobs."""
    job = job_service.update_job(db=db, user=current_user, job_id=id, data=data)
    return JobResponse.model_validate(job)


@router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a job opening",
)
def delete_job(
    id: uuid.UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> None:
    """Delete a job opening owned by the user. Returns 404 for foreign jobs."""
    job_service.delete_job(db=db, user=current_user, job_id=id)


@router.post(
    "/{id}/extract-requirements",
    response_model=ExtractRequirementsResponse,
    status_code=status.HTTP_200_OK,
    summary="Extract suggested requirements from job description",
)
def extract_requirements(
    id: uuid.UUID,
    current_user: CurrentUser,
    db: DbSession,
    save: bool = Query(
        False, description="Whether to automatically save extracted skills to the job"
    ),
) -> ExtractRequirementsResponse:
    """Analyze job title and description to extract skills, experience, and degree level."""
    return job_service.extract_requirements_from_description(
        db=db,
        user=current_user,
        job_id=id,
        save=save,
    )


@router.post(
    "/{id}/requirements",
    response_model=JobRequirementResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a requirement to a job opening",
)
def add_requirement(
    id: uuid.UUID,
    data: JobRequirementCreate,
    current_user: CurrentUser,
    db: DbSession,
) -> JobRequirementResponse:
    """Add a requirement skill to the specified job. Returns 404 for foreign jobs."""
    req = job_service.add_requirement(db=db, user=current_user, job_id=id, data=data)
    return JobRequirementResponse.model_validate(req)


@router.delete(
    "/{id}/requirements/{requirement_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a requirement from a job opening",
)
def delete_requirement(
    id: uuid.UUID,
    requirement_id: uuid.UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> None:
    """Remove a requirement skill from a job. Returns 404 for foreign jobs."""
    job_service.delete_requirement(
        db=db,
        user=current_user,
        job_id=id,
        requirement_id=requirement_id,
    )


@router.post(
    "/{id}/match",
    response_model=MatchSummaryResponse,
    status_code=status.HTTP_200_OK,
    summary="Trigger scoring and ranking for all parsed resumes in job",
)
def trigger_matching(
    id: uuid.UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> MatchSummaryResponse:
    """Calculate match scores and explanations for all parsed candidate resumes."""
    results = ranker.score_all_resumes_for_job(db=db, user=current_user, job_id=id)
    return MatchSummaryResponse(
        job_id=id,
        total_scored=len(results),
        message=f"Scored {len(results)} candidate resume(s).",
    )


@router.get(
    "/{id}/ranking",
    response_model=PaginatedRankingResponse,
    status_code=status.HTTP_200_OK,
    summary="Get candidate ranking for a job opening",
)
def get_ranking(
    id: uuid.UUID,
    current_user: CurrentUser,
    db: DbSession,
    min_score: float | None = Query(
        None, ge=0.0, le=100.0, description="Minimum total score"
    ),
    skill: str | None = Query(
        None, description="Filter candidates matching specific skill"
    ),
    min_exp: float | None = Query(
        None, ge=0.0, description="Minimum experience sub-score"
    ),
    candidate_status: str | None = Query(
        None, alias="status", description="Filter by candidate status"
    ),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
) -> PaginatedRankingResponse:
    """Retrieve explainable candidate rankings for a job with filtering."""
    items, total = ranker.get_job_ranking(
        db=db,
        user=current_user,
        job_id=id,
        min_score=min_score,
        skill_filter=skill,
        min_exp=min_exp,
        status_filter=candidate_status,
        page=page,
        page_size=page_size,
    )
    return PaginatedRankingResponse(
        items=[RankedCandidateItem(**item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/{id}/candidates/{candidate_id}/match",
    response_model=RankedCandidateItem,
    status_code=status.HTTP_200_OK,
    summary="Get candidate match details and breakdown for a job",
)
def get_candidate_match(
    id: uuid.UUID,
    candidate_id: uuid.UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> RankedCandidateItem:
    """Retrieve full explanation breakdown for a specific candidate on a job."""
    items, _ = ranker.get_job_ranking(
        db=db, user=current_user, job_id=id, page=1, page_size=1000
    )
    for it in items:
        if it["candidate_id"] == str(candidate_id):
            return RankedCandidateItem(**it)

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Candidate match not found for this job opening.",
    )


@router.get(
    "/{id}/export.csv",
    status_code=status.HTTP_200_OK,
    summary="Export candidate ranking as CSV",
)
def export_csv(
    id: uuid.UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> Response:
    """Export ranking table as a CSV download protected against formula injection."""
    csv_content = ranker.export_ranking_csv(db=db, user=current_user, job_id=id)
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="job_{id}_ranking.csv"'},
    )


@router.post(
    "/{id}/compare",
    response_model=CompareResponse,
    status_code=status.HTTP_200_OK,
    summary="Compare candidates side-by-side",
)
def compare_candidates(
    id: uuid.UUID,
    payload: CompareRequest,
    current_user: CurrentUser,
    db: DbSession,
) -> CompareResponse:
    """
    Compare 2 to 4 candidates side-by-side on a job opening.
    Builds a unified skill matrix and compares composite sub-scores.
    """
    job = db.query(Job).filter(Job.id == id, Job.owner_id == current_user.id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job opening not found.",
        )

    # Retrieve all ranked candidates for the job
    items, _ = ranker.get_job_ranking(
        db=db, user=current_user, job_id=id, page=1, page_size=1000
    )
    items_by_cand_id = {it["candidate_id"]: it for it in items}

    target_cand_ids = [str(cid) for cid in payload.candidate_ids]
    compared_candidates: list[CandidateCompareItem] = []

    for cid_str in target_cand_ids:
        it = items_by_cand_id.get(cid_str)
        if not it:
            continue
        breakdown = it.get("breakdown", {})
        matched_skills_names = [s["skill"] for s in breakdown.get("matched_skills", [])]
        missing_req = breakdown.get("missing_required", [])

        exp_info = breakdown.get("experience", {})
        edu_info = breakdown.get("education", {})

        comp_item = CandidateCompareItem(
            candidate_id=uuid.UUID(it["candidate_id"]),
            candidate_name=it["candidate_name"],
            candidate_email=it.get("candidate_email"),
            status=it.get("candidate_status", "new"),
            total_score=it["total_score"],
            skill_score=it.get("skill_score"),
            semantic_score=it.get("semantic_score"),
            experience_score=it.get("experience_score"),
            education_score=it.get("education_score"),
            total_experience_years=exp_info.get("candidate_years"),
            highest_degree=edu_info.get("candidate_level"),
            matched_skills=matched_skills_names,
            missing_required=missing_req,
        )
        compared_candidates.append(comp_item)

    if len(compared_candidates) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least 2 valid candidates must be selected for comparison.",
        )

    # Build skill matrix across all job requirements
    job_reqs = {r.skill: r.importance for r in job.requirements}
    all_skills_seen = list(job_reqs.keys())
    for c in compared_candidates:
        for s in c.matched_skills:
            if s not in all_skills_seen:
                all_skills_seen.append(s)

    skill_matrix: list[SkillMatrixRow] = []
    for skill_name in all_skills_seen:
        importance = job_reqs.get(skill_name, "extra")
        cand_status = {
            str(c.candidate_id): (skill_name in c.matched_skills)
            for c in compared_candidates
        }
        skill_matrix.append(
            SkillMatrixRow(
                skill=skill_name,
                importance=importance,
                candidate_status=cand_status,
            )
        )

    return CompareResponse(
        job_id=job.id,
        job_title=job.title,
        candidates=compared_candidates,
        skill_matrix=skill_matrix,
    )
