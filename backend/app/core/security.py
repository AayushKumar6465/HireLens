"""
Security utilities: password hashing (Argon2id via argon2-cffi) and JWT handling.

Note: passlib was intentionally not used. Python 3.13+ removed the `crypt` standard
library module that passlib depends on for some backends, and passlib is no longer
actively maintained. argon2-cffi is actively maintained and provides Argon2id directly.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError

from app.core.config import settings

# Argon2id hasher with sensible defaults (time_cost=2, memory_cost=65536, parallelism=2)
_ph = PasswordHasher()

# Pre-computed dummy hash to prevent timing attacks when verifying non-existent users
_DUMMY_HASH = _ph.hash("hirelens-dummy-timing-protection-credential")


def hash_password(plain: str) -> str:
    """Hash a plaintext password with Argon2id. Returns the encoded hash string."""
    return _ph.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    """
    Verify a plaintext password against an Argon2id hash.

    Returns True on success, False on mismatch or invalid hash.
    Never raises — callers may safely use the bool result directly.
    """
    try:
        return _ph.verify(hashed, plain)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False


def dummy_verify_password(plain: str) -> bool:
    """Perform dummy Argon2id verification to equalize timing for unknown users."""
    try:
        _ph.verify(_DUMMY_HASH, plain)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        pass
    return False


def needs_rehash(hashed: str) -> bool:
    """Return True if the stored hash should be upgraded (parameters changed)."""
    return _ph.check_needs_rehash(hashed)


def create_access_token(user_id: uuid.UUID | str, role: str) -> str:
    """
    Issue short-lived access JWT containing user subject and role.

    Tokens are signed with HS256 and include type="access".
    """
    now = datetime.now(UTC)
    expire = now + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {
        "sub": str(user_id),
        "role": role,
        "type": "access",
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


def create_refresh_token(user_id: uuid.UUID | str, token_version: int) -> str:
    """
    Issue long-lived refresh JWT carrying subject, token_version, and a unique jti.

    Includes type="refresh" to ensure access and refresh tokens cannot be interchanged.
    """
    now = datetime.now(UTC)
    expire = now + timedelta(days=settings.refresh_token_expire_days)
    payload = {
        "sub": str(user_id),
        "type": "refresh",
        "jti": str(uuid.uuid4()),
        "version": token_version,
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


def decode_token(token: str) -> dict[str, Any]:
    """
    Decode and verify JWT signature and expiration.

    Raises jwt.PyJWTError subclasses on failure.
    """
    return jwt.decode(
        token,
        settings.jwt_secret,
        algorithms=["HS256"],
        options={"require": ["exp", "iat", "sub", "type"]},
    )
