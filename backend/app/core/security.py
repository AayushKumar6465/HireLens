"""
Security utilities: password hashing (Argon2id via argon2-cffi) and JWT handling.

Note: passlib was intentionally not used. Python 3.13+ removed the `crypt` standard
library module that passlib depends on for some backends, and passlib is no longer
actively maintained. argon2-cffi is actively maintained and provides Argon2id directly.
"""

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError

# Argon2id hasher with sensible defaults (time_cost=2, memory_cost=65536, parallelism=2)
_ph = PasswordHasher()


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


def needs_rehash(hashed: str) -> bool:
    """Return True if the stored hash should be upgraded (parameters changed)."""
    return _ph.check_needs_rehash(hashed)
