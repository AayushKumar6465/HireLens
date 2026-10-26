"""
Authentication service implementing registration, credential verification, and token refresh.

Security controls:
- Passwords hashed using Argon2id via argon2-cffi
- Timing protection: unknown emails perform dummy Argon2id verification
- Uniform 401 responses for unknown email and wrong password
- Registration always assigns the 'recruiter' role; client-supplied role values are ignored
- Refresh token validation enforces token_version revocation checking
- PII-safe logging (logs event names and internal IDs only; no emails, IPs, or credentials)
"""

from __future__ import annotations

import uuid

import jwt
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.logging import get_logger, log_event
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    dummy_verify_password,
    hash_password,
    verify_password,
)
from app.models.user import User
from app.schemas.auth import (
    LoginRequest,
    RegisterRequest,
    TokenRefreshResponse,
    TokenResponse,
)

logger = get_logger(__name__)


def register_user(db: Session, data: RegisterRequest) -> User:
    """
    Register a new recruiter account.

    Always forces role to 'recruiter' and enforces unique email constraint.
    """
    normalized_email = data.email.strip().lower()

    # Reject duplicate registrations with standard 409 Conflict
    existing = db.query(User).filter(User.email == normalized_email).first()
    if existing:
        log_event(logger, "auth_register_conflict")
        raise HTTPException(
            status_code=409,
            detail={
                "code": "conflict",
                "message": "An account with this email already exists.",
            },
        )

    hashed = hash_password(data.password)
    new_user = User(
        email=normalized_email,
        hashed_password=hashed,
        full_name=data.full_name.strip(),
        role="recruiter",  # Client-requested role is always ignored
        is_active=True,
        token_version=1,
    )
    db.add(new_user)
    db.flush()

    log_event(logger, "auth_register_success", user_id=str(new_user.id))
    return new_user


def authenticate_user(db: Session, data: LoginRequest) -> TokenResponse:
    """
    Authenticate user credentials and issue access + refresh JWT pair.

    Applies dummy hash verification to unknown users to mitigate timing attacks.
    """
    normalized_email = data.email.strip().lower()
    user = db.query(User).filter(User.email == normalized_email).first()

    if user is None:
        dummy_verify_password(data.password)
        log_event(logger, "auth_login_failed_user_not_found")
        raise HTTPException(
            status_code=401,
            detail={"code": "unauthorized", "message": "Invalid email or password."},
        )

    if not verify_password(data.password, user.hashed_password):
        log_event(logger, "auth_login_failed_invalid_password", user_id=str(user.id))
        raise HTTPException(
            status_code=401,
            detail={"code": "unauthorized", "message": "Invalid email or password."},
        )

    if not user.is_active:
        log_event(logger, "auth_login_failed_inactive_user", user_id=str(user.id))
        raise HTTPException(
            status_code=401,
            detail={"code": "unauthorized", "message": "Account is inactive."},
        )

    access_token = create_access_token(user.id, user.role)
    refresh_token = create_refresh_token(user.id, user.token_version)

    log_event(logger, "auth_login_success", user_id=str(user.id))
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
    )


def refresh_access_token(db: Session, refresh_token_str: str) -> TokenRefreshResponse:
    """
    Validate refresh token claims and version, issuing a fresh access token.

    Access and refresh tokens are strictly distinct via the 'type' claim.
    """
    try:
        payload = decode_token(refresh_token_str)
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=401,
            detail={"code": "unauthorized", "message": "Refresh token has expired."},
        ) from None
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=401,
            detail={"code": "unauthorized", "message": "Invalid refresh token."},
        ) from None

    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=401,
            detail={
                "code": "unauthorized",
                "message": "Invalid token type: refresh token required.",
            },
        )

    sub = payload.get("sub")
    token_version = payload.get("version")
    if not sub or token_version is None:
        raise HTTPException(
            status_code=401,
            detail={
                "code": "unauthorized",
                "message": "Malformed token payload claims.",
            },
        )

    try:
        user_id = uuid.UUID(sub)
    except ValueError:
        raise HTTPException(
            status_code=401,
            detail={
                "code": "unauthorized",
                "message": "Invalid user ID format in token.",
            },
        ) from None

    user = db.get(User, user_id)
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=401,
            detail={
                "code": "unauthorized",
                "message": "User account no longer active or found.",
            },
        )

    if user.token_version != int(token_version):
        log_event(logger, "auth_refresh_revoked", user_id=str(user.id))
        raise HTTPException(
            status_code=401,
            detail={
                "code": "unauthorized",
                "message": "Refresh token has been revoked or invalidated.",
            },
        )

    new_access_token = create_access_token(user.id, user.role)
    log_event(logger, "auth_refresh_success", user_id=str(user.id))
    return TokenRefreshResponse(
        access_token=new_access_token,
        token_type="bearer",
    )
