"""
Job opening and requirement management endpoints (/api/v1/jobs).

Endpoints:
- POST /: Create a job opening with optional requirements (201 Created)
- GET /: List user's jobs with search and pagination (200 OK)
- GET /{id}: Retrieve single job details (200 OK)
- PUT /{id}: Update job details and requirements (200 OK)
- DELETE /{id}: Delete job opening (204 No Content)
- POST /{id}/extract-requirements: Suggest skills from job description (200 OK)
- POST /{id}/requirements: Add requirement to job (201 Created)
- DELETE /{id}/requirements/{requirement_id}: Delete requirement (204 No Content)

Ownership:
- All operations strictly owner-scoped. Foreign jobs return HTTP 404 (admins cannot bypass).
"""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.job import (
    ExtractRequirementsResponse,
    JobCreate,
    JobRequirementCreate,
    JobRequirementResponse,
    JobResponse,
    JobUpdate,
    PaginatedJobsResponse,
)
from app.services import job_service

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
