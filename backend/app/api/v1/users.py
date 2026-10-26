"""
User administration API endpoints (/api/v1/users).

Endpoints:
- GET /: Paginated list of users (Admin only)
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_role
from app.models.user import User
from app.schemas.user import PaginatedUsersResponse, UserResponse

router = APIRouter()

DbSession = Annotated[Session, Depends(get_db)]
AdminUser = Annotated[User, Depends(require_role("admin"))]


@router.get(
    "",
    response_model=PaginatedUsersResponse,
    status_code=status.HTTP_200_OK,
    summary="List users with pagination (Admin only)",
)
def list_users(
    current_admin: AdminUser,
    db: DbSession,
    page: int = Query(1, ge=1, description="Page number starting at 1"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page (max 100)"),
) -> PaginatedUsersResponse:
    """
    Retrieve a paginated list of registered users.

    Accessible to administrators only. Returns safe user fields (never hashes or tokens).
    """
    total = db.query(User).count()
    users = (
        db.query(User)
        .order_by(User.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return PaginatedUsersResponse(
        items=[UserResponse.model_validate(u) for u in users],
        total=total,
        page=page,
        page_size=page_size,
    )
