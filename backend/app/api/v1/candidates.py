"""
Candidate management API endpoints (/api/v1/candidates).
"""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
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
)

logger = get_logger(__name__)

router = APIRouter()

CurrentUser = Annotated[User, Depends(get_current_user)]
DbSession = Annotated[Session, Depends(get_db)]


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
