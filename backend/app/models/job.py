"""
Job and JobRequirement ORM models.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import DateTime, Float, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.match_result import MatchResult
    from app.models.resume import Resume
    from app.models.user import User


class Job(Base):
    """Job vacancy posting created and managed by recruiters."""

    __tablename__ = "jobs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid(),
    )
    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    department: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    location: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    min_experience_years: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )
    education_level: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="open",
        server_default="open",
    )
    weights_override: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB,
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    owner: Mapped[User] = relationship(
        "User",
        back_populates="jobs",
    )
    requirements: Mapped[list[JobRequirement]] = relationship(
        "JobRequirement",
        back_populates="job",
        cascade="all, delete-orphan",
    )
    match_results: Mapped[list[MatchResult]] = relationship(
        "MatchResult",
        back_populates="job",
        cascade="all, delete-orphan",
    )
    resumes: Mapped[list[Resume]] = relationship(
        "Resume",
        back_populates="job",
    )


class JobRequirement(Base):
    """Specific skill requirement attached to a job opening."""

    __tablename__ = "job_requirements"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid(),
    )
    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("jobs.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    skill: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    importance: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="required",
        server_default="required",
    )
    weight: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=1.0,
        server_default="1.0",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    job: Mapped[Job] = relationship(
        "Job",
        back_populates="requirements",
    )
