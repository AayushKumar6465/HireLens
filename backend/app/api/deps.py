"""
FastAPI dependency functions shared across routes.

Responsibilities:
- Database session lifecycle (get_db) with commit on success and rollback on error
- Current user extraction from HTTPBearer access JWT
- Role enforcement (require_role)
- IDOR protection via owner-scoped querying (apply_owner_scope)
"""

from __future__ import annotations

import uuid
from collections.abc import Callable, Generator
from typing import Annotated, Any

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.security import decode_token
from app.db.session import SessionLocal
from app.models.user import User

# HTTPBearer scheme configured for Swagger UI Authorize support
security_scheme = HTTPBearer(auto_error=False)


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency yielding a database session per request.

    Commits on completion, rolls back on any exception, and always closes the session.
    """
    if SessionLocal is None:
        raise HTTPException(
            status_code=500,
            detail={"code": "internal_error", "message": "Database is not configured."},
        )
    db: Session = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


DbSession = Annotated[Session, Depends(get_db)]
AuthCredentials = Annotated[
    HTTPAuthorizationCredentials | None, Depends(security_scheme)
]


def get_current_user(
    auth: AuthCredentials,
    db: DbSession,
) -> User:
    """
    Extract and validate the current authenticated user from Bearer access JWT.

    Ensures token type is 'access' and that the user account is active.
    """
    if auth is None or not auth.credentials:
        raise HTTPException(
            status_code=401,
            detail={
                "code": "unauthorized",
                "message": "Authentication token required.",
            },
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = auth.credentials
    try:
        payload = decode_token(token)
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=401,
            detail={
                "code": "unauthorized",
                "message": "Authentication token has expired.",
            },
            headers={"WWW-Authenticate": "Bearer"},
        ) from None
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=401,
            detail={"code": "unauthorized", "message": "Invalid authentication token."},
            headers={"WWW-Authenticate": "Bearer"},
        ) from None

    if payload.get("type") != "access":
        raise HTTPException(
            status_code=401,
            detail={
                "code": "unauthorized",
                "message": "Invalid token type: access token required.",
            },
            headers={"WWW-Authenticate": "Bearer"},
        )

    sub = payload.get("sub")
    if not sub:
        raise HTTPException(
            status_code=401,
            detail={"code": "unauthorized", "message": "Token subject is missing."},
            headers={"WWW-Authenticate": "Bearer"},
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
            headers={"WWW-Authenticate": "Bearer"},
        ) from None

    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(
            status_code=401,
            detail={
                "code": "unauthorized",
                "message": "User account no longer exists.",
            },
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=401,
            detail={"code": "unauthorized", "message": "User account is inactive."},
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_role(required_role: str) -> Callable[[User], User]:
    """
    Dependency factory enforcing role-based access control.

    Returns HTTP 403 with standard Section 8 error if current user's role does not match.
    """

    def role_checker(current_user: CurrentUser) -> User:
        if current_user.role != required_role:
            raise HTTPException(
                status_code=403,
                detail={
                    "code": "forbidden",
                    "message": "Insufficient permissions to access this resource.",
                },
            )
        return current_user

    return role_checker


def apply_owner_scope(query: Any, model: Any, user: User) -> Any:
    """
    Enforce IDOR protection by filtering queries to the current user's owner_id.

    Note: Admins do NOT bypass owner scoping per Section 8 and Section 10 design rules.
    """
    return query.filter(model.owner_id == user.id)


def get_owner_scoped_resource(
    db: Session,
    model: Any,
    resource_id: uuid.UUID,
    user: User,
) -> Any:
    """
    Retrieve an entity by primary key ensuring it belongs to the current user.

    Returns HTTP 404 (not 403) for foreign resources to prevent resource enumeration.
    """
    resource = (
        db.query(model)
        .filter(model.id == resource_id, model.owner_id == user.id)
        .first()
    )
    if resource is None:
        raise HTTPException(
            status_code=404,
            detail={"code": "not_found", "message": f"{model.__name__} not found."},
        )
    return resource
