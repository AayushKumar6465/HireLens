"""
Resume and upload Pydantic schemas.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ResumeUploadItemResult(BaseModel):
    """Result for an individual successfully staged resume upload."""

    resume_id: uuid.UUID
    candidate_id: uuid.UUID
    original_filename: str
    status: str = "pending"


class ResumeDuplicateItemResult(BaseModel):
    """Result for an individual detected duplicate upload."""

    original_filename: str
    sha256: str
    existing_resume_id: uuid.UUID
    message: str = "Duplicate file detected. Already uploaded previously."


class ResumeFailedItemResult(BaseModel):
    """Result for an individual rejected upload."""

    original_filename: str
    error_code: str
    message: str


class BatchUploadResponse(BaseModel):
    """Structured response summarizing multi-file resume upload."""

    uploaded: list[ResumeUploadItemResult] = Field(default_factory=list)
    duplicates: list[ResumeDuplicateItemResult] = Field(default_factory=list)
    failed: list[ResumeFailedItemResult] = Field(default_factory=list)
    total_uploaded: int = 0
    total_duplicates: int = 0
    total_failed: int = 0


class ResumeStatusResponse(BaseModel):
    """Status polling response for an uploaded resume."""

    id: uuid.UUID
    parse_status: str
    parse_error: str | None = None
    candidate_id: uuid.UUID
    job_id: uuid.UUID | None = None
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ResumeResponse(BaseModel):
    """Detailed resume metadata response."""

    id: uuid.UUID
    candidate_id: uuid.UUID
    job_id: uuid.UUID | None = None
    original_filename: str
    mime_type: str
    size_bytes: int
    sha256: str
    parse_status: str
    parse_error: str | None = None
    created_at: datetime
    updated_at: datetime
    parsed_data: dict[str, Any] | None = None

    model_config = ConfigDict(from_attributes=True)
