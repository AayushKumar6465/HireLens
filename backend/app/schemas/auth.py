"""
Authentication Pydantic schemas.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class RegisterRequest(BaseModel):
    """Payload for recruiter account registration."""

    email: EmailStr
    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="Password between 8 and 128 characters",
    )
    full_name: str = Field(
        ..., min_length=1, max_length=255, description="Full display name"
    )
    role: str | None = Field(
        default=None,
        description="Client role specification (always ignored/forced to recruiter)",
    )

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        """Trim whitespace and lowercase email."""
        if isinstance(v, str):
            return v.strip().lower()
        return v

    @field_validator("full_name", mode="before")
    @classmethod
    def trim_name(cls, v: str) -> str:
        """Trim whitespace from name."""
        if isinstance(v, str):
            return v.strip()
        return v


class LoginRequest(BaseModel):
    """Payload for user login authentication via JSON."""

    email: EmailStr
    password: str = Field(..., min_length=1, description="Account password")

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        """Trim whitespace and lowercase email."""
        if isinstance(v, str):
            return v.strip().lower()
        return v


class TokenResponse(BaseModel):
    """JWT credentials returned on successful authentication."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"

    model_config = ConfigDict(from_attributes=True)


class RefreshTokenRequest(BaseModel):
    """Payload for issuing a new access token from an existing refresh token."""

    refresh_token: str = Field(..., min_length=1, description="Long-lived refresh JWT")


class TokenRefreshResponse(BaseModel):
    """Single newly minted access token returned from refresh flow."""

    access_token: str
    token_type: str = "bearer"

    model_config = ConfigDict(from_attributes=True)
