"""
Job and JobRequirement Pydantic schemas.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class JobRequirementBase(BaseModel):
    """Base schema for a job skill requirement."""

    skill: str = Field(
        ..., min_length=1, max_length=255, description="Canonical skill name"
    )
    importance: str = Field(
        default="required",
        pattern="^(required|preferred)$",
        description="Requirement priority",
    )
    weight: float = Field(default=1.0, ge=0.0, le=10.0, description="Relative weight")


class JobRequirementCreate(JobRequirementBase):
    """Schema for adding a requirement to a job."""


class JobRequirementResponse(JobRequirementBase):
    """Schema for returning requirement details."""

    id: uuid.UUID
    job_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class JobBase(BaseModel):
    """Base schema for job postings."""

    title: str = Field(..., min_length=1, max_length=255, description="Job title")
    description: str = Field(..., min_length=1, description="Full job description")
    department: str | None = Field(default=None, max_length=255)
    location: str | None = Field(default=None, max_length=255)
    min_experience_years: float | None = Field(default=None, ge=0.0)
    education_level: str | None = Field(default=None, max_length=100)
    weights_override: dict[str, Any] | None = None


class JobCreate(JobBase):
    """Schema for creating a new job opening."""

    requirements: list[JobRequirementCreate] = Field(
        default_factory=list,
        description="Optional initial requirements for the job",
    )


class JobUpdate(BaseModel):
    """Schema for updating an existing job opening."""

    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, min_length=1)
    department: str | None = Field(default=None, max_length=255)
    location: str | None = Field(default=None, max_length=255)
    min_experience_years: float | None = Field(default=None, ge=0.0)
    education_level: str | None = Field(default=None, max_length=100)
    status: str | None = Field(default=None, pattern="^(open|closed)$")
    weights_override: dict[str, Any] | None = None
    requirements: list[JobRequirementCreate] | None = None


class JobResponse(JobBase):
    """Schema for returning job opening details with its requirements."""

    id: uuid.UUID
    owner_id: uuid.UUID
    status: str
    created_at: datetime
    updated_at: datetime
    requirements: list[JobRequirementResponse] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class PaginatedJobsResponse(BaseModel):
    """Paginated container for job listings."""

    items: list[JobResponse]
    total: int
    page: int
    page_size: int

    model_config = ConfigDict(from_attributes=True)


class ExtractedSkillItem(BaseModel):
    """Suggested requirement extracted from job text."""

    skill: str
    importance: str = "required"
    suggested_weight: float = 1.0
    match_type: str = "exact"


class ExtractRequirementsResponse(BaseModel):
    """Extraction recommendations from job description."""

    job_id: uuid.UUID
    extracted_skills: list[ExtractedSkillItem]
    suggested_min_experience_years: float | None = None
    suggested_education_level: str | None = None
