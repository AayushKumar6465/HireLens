"""
MatchResult ORM model.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import DateTime, Float, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.candidate import Candidate
    from app.models.job import Job
    from app.models.resume import Resume


class MatchResult(Base):
    """Screening and explainability match scores comparing a resume against a job."""

    __tablename__ = "match_results"
    __table_args__ = (
        UniqueConstraint("job_id", "resume_id", name="uq_match_results_job_resume"),
    )

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
    candidate_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("candidates.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    resume_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("resumes.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    total_score: Mapped[float] = mapped_column(
        Float,
        index=True,
        nullable=False,
    )
    skill_score: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )
    semantic_score: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )
    experience_score: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )
    education_score: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )
    breakdown: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
    )
    scoring_version: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="1.0.0",
        server_default="1.0.0",
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
        back_populates="match_results",
    )
    candidate: Mapped[Candidate] = relationship(
        "Candidate",
        back_populates="match_results",
    )
    resume: Mapped[Resume] = relationship(
        "Resume",
        back_populates="match_results",
    )
