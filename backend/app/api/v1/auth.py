"""
Authentication API endpoints (/api/v1/auth).

Endpoints:
- POST /register: Recruiter registration (201 Created)
- POST /login: JSON credential login with slowapi rate limiting (200 OK)
- POST /refresh: Token exchange for fresh access token (200 OK)
- GET /me: Protected current user profile (200 OK)
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.core.rate_limit import limiter
from app.models.user import User
from app.schemas.auth import (
    LoginRequest,
    RefreshTokenRequest,
    RegisterRequest,
    TokenRefreshResponse,
    TokenResponse,
)
from app.schemas.user import UserResponse
from app.services import auth_service

router = APIRouter()

DbSession = Annotated[Session, Depends(get_db)]
CurrentUser = Annotated[User, Depends(get_current_user)]


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new recruiter account",
)
def register(
    data: RegisterRequest,
    db: DbSession,
) -> UserResponse:
    """
    Register a new recruiter account.

    Emails are trimmed and lowercased. Role is strictly assigned as 'recruiter'.
    Passwords must be 8-128 characters and are hashed with Argon2id.
    """
    user = auth_service.register_user(db=db, data=data)
    return UserResponse.model_validate(user)


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="User login with JSON credentials",
)
@limiter.limit("5/minute")
def login(
    request: Request,
    data: LoginRequest,
    db: DbSession,
) -> TokenResponse:
    """
    Authenticate user credentials via JSON body and receive JWT access + refresh tokens.

    Protected against brute-force attacks via SlowAPI rate limiting (5 requests/minute).
    """
    return auth_service.authenticate_user(db=db, data=data)


@router.post(
    "/refresh",
    response_model=TokenRefreshResponse,
    status_code=status.HTTP_200_OK,
    summary="Exchange refresh token for fresh access token",
)
def refresh(
    data: RefreshTokenRequest,
    db: DbSession,
) -> TokenRefreshResponse:
    """
    Verify a valid refresh token and issue a new access token.

    Access and refresh tokens are strictly distinct and non-interchangeable.
    Stale token versions (after account deactivation or password change) are rejected.
    """
    return auth_service.refresh_access_token(
        db=db, refresh_token_str=data.refresh_token
    )


@router.get(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Get current authenticated user profile",
)
def get_me(
    current_user: CurrentUser,
) -> UserResponse:
    """
    Retrieve profile details for the currently authenticated user.

    Uses HTTPBearer authorization header.
    """
    return UserResponse.model_validate(current_user)
