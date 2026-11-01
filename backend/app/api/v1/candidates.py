"""
Candidate management API endpoints (/api/v1/candidates).
"""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.core.logging import get_logger, log_event
from app.models.audit_log import AuditLog
from app.models.candidate import Candidate
from app.models.user import User
from app.schemas.candidate import (
    CandidateBulkStatusUpdate,
    CandidateDetailResponse,
    CandidateStatusUpdate,
    PaginatedCandidatesResponse,
)
from app.services import storage_service

logger = get_logger(__name__)

router = APIRouter()

CurrentUser = Annotated[User, Depends(get_current_user)]
DbSession = Annotated[Session, Depends(get_db)]


@router.get(
    "",
    response_model=PaginatedCandidatesResponse,
    status_code=status.HTTP_200_OK,
    summary="List candidates owned by the current user",
)
def list_candidates(
    current_user: CurrentUser,
    db: DbSession,
    page: int = Query(1, ge=1, description="Page number starting at 1"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page (max 100)"),
    status_filter: str | None = Query(
        None, alias="status", description="Filter by candidate status"
    ),
    q: str | None = Query(
        None, description="Search filter for full name or email"
    ),
) -> PaginatedCandidatesResponse:
    """Retrieve a paginated list of candidates owned by the current recruiter."""
    query = db.query(Candidate).filter(Candidate.owner_id == current_user.id)
    if status_filter:
        query = query.filter(Candidate.status == status_filter)
    if q and q.strip():
        search_pattern = f"%{q.strip()}%"
        query = query.filter(
            or_(
                Candidate.full_name.ilike(search_pattern),
                Candidate.email.ilike(search_pattern),
            )
        )
    total = query.count()
    candidates = (
        query.order_by(Candidate.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return PaginatedCandidatesResponse(
        items=[CandidateDetailResponse.model_validate(c) for c in candidates],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/{id}",
    response_model=CandidateDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Get candidate profile",
)
def get_candidate(
    id: uuid.UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> Candidate:
    """Retrieve single candidate profile scoped to the current user."""
    candidate = (
        db.query(Candidate)
        .filter(Candidate.id == id, Candidate.owner_id == current_user.id)
        .first()
    )
    if not candidate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Candidate not found",
        )
    return candidate


@router.patch(
    "/{id}/status",
    response_model=CandidateDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Update candidate status",
)
def update_candidate_status(
    id: uuid.UUID,
    payload: CandidateStatusUpdate,
    current_user: CurrentUser,
    db: DbSession,
) -> Candidate:
    """
    Update a candidate's recruitment pipeline status and optional notes.
    Always strictly owner-scoped. Creates an audit log entry.
    """
    candidate = (
        db.query(Candidate)
        .filter(Candidate.id == id, Candidate.owner_id == current_user.id)
        .first()
    )
    if not candidate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Candidate not found",
        )

    old_status = candidate.status
    candidate.status = payload.status
    if payload.notes is not None:
        candidate.notes = payload.notes

    # Add audit log entry
    audit = AuditLog(
        user_id=current_user.id,
        action="candidate_status_updated",
        entity_type="candidate",
        entity_id=str(candidate.id),
        meta={"from_status": old_status, "to_status": payload.status},
    )
    db.add(audit)
    db.commit()
    db.refresh(candidate)

    log_event(
        logger,
        "candidate_status_updated",
        candidate_id=str(candidate.id),
        to_status=payload.status,
    )
    return candidate


@router.post(
    "/bulk-status",
    status_code=status.HTTP_200_OK,
    summary="Bulk update candidates status",
)
def bulk_update_status(
    payload: CandidateBulkStatusUpdate,
    current_user: CurrentUser,
    db: DbSession,
) -> dict[str, int]:
    """
    Bulk update status for a list of candidates owned by the current recruiter.
    Returns the count of successfully updated candidates.
    """
    candidates = (
        db.query(Candidate)
        .filter(
            Candidate.id.in_(payload.candidate_ids),
            Candidate.owner_id == current_user.id,
        )
        .all()
    )

    updated_count = 0
    for cand in candidates:
        old_status = cand.status
        cand.status = payload.status
        updated_count += 1

        audit = AuditLog(
            user_id=current_user.id,
            action="candidate_status_updated_bulk",
            entity_type="candidate",
            entity_id=str(cand.id),
            meta={"from_status": old_status, "to_status": payload.status},
        )
        db.add(audit)

    db.commit()

    log_event(
        logger,
        "candidates_bulk_status_updated",
        count=updated_count,
        to_status=payload.status,
    )
    return {"updated": updated_count}


@router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a candidate and their associated resume files",
)
def delete_candidate(
    id: uuid.UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> None:
    """
    Delete a candidate owned by the current user along with their resumes,
    parsed data, match results, and physical files on disk.
    Admins attempting to delete another owner's candidate receive 404.
    """
    candidate = (
        db.query(Candidate)
        .filter(Candidate.id == id, Candidate.owner_id == current_user.id)
        .first()
    )
    if not candidate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "not_found", "message": "Candidate not found."},
        )

    # Collect resume stored filenames to purge from disk after DB deletion succeeds
    stored_filenames = [
        r.stored_filename for r in candidate.resumes if r.stored_filename
    ]

    audit = AuditLog(
        user_id=current_user.id,
        action="candidate_deleted",
        entity_type="candidate",
        entity_id=str(candidate.id),
        meta={"full_name": candidate.full_name},
    )
    db.add(audit)

    # Delete database record; cascades to resumes, parsed_resumes, match_results
    db.delete(candidate)
    db.commit()

    # Safely purge associated resume files from disk
    for stored_fn in stored_filenames:
        try:
            storage_service.delete_file(stored_fn)
        except (HTTPException, OSError) as exc:
            logger.error(
                "Failed to purge disk file %s during candidate %s deletion: %s",
                stored_fn,
                id,
                exc,
            )

    log_event(
        logger,
        "candidate_deleted",
        candidate_id=str(id),
        user_id=str(current_user.id),
    )
