"""
Candidate Pydantic schemas.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class CandidateStatusUpdate(BaseModel):
    """Schema for updating a single candidate's recruitment status."""

    status: str = Field(
        ...,
        pattern="^(new|screening|interview|offer|rejected)$",
        description="Recruitment status: new, screening, interview, offer, rejected",
    )
    notes: str | None = Field(
        None, max_length=2000, description="Optional recruiter notes"
    )


class CandidateBulkStatusUpdate(BaseModel):
    """Schema for updating status across multiple candidates at once."""

    candidate_ids: list[uuid.UUID] = Field(
        ...,
        min_length=1,
        max_length=100,
        description="List of candidate UUIDs to update",
    )
    status: str = Field(
        ...,
        pattern="^(new|screening|interview|offer|rejected)$",
        description="Target status",
    )


class CandidateDetailResponse(BaseModel):
    """Detailed candidate profile response."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    full_name: str
    email: str | None = None
    phone: str | None = None
    links: dict[str, Any] | list[Any] | None = None
    status: str
    notes: str | None = None
    created_at: datetime
    updated_at: datetime
