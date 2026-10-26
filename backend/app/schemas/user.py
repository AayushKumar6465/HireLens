"""
User Pydantic schemas.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class UserResponse(BaseModel):
    """Sanitized public user details omitting password hashes and security tokens."""

    id: uuid.UUID
    email: str
    full_name: str
    role: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PaginatedUsersResponse(BaseModel):
    """Standard paginated container for user listings."""

    items: list[UserResponse]
    total: int
    page: int
    page_size: int

    model_config = ConfigDict(from_attributes=True)
