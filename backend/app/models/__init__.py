"""
SQLAlchemy ORM models package.

All application models are imported here so that Alembic autogenerate
can discover the complete schema via Base.metadata.
"""

from app.models.app_setting import AppSetting
from app.models.audit_log import AuditLog
from app.models.candidate import Candidate
from app.models.job import Job, JobRequirement
from app.models.match_result import MatchResult
from app.models.resume import ParsedResume, Resume
from app.models.user import User

__all__ = [
    "AppSetting",
    "AuditLog",
    "Candidate",
    "Job",
    "JobRequirement",
    "MatchResult",
    "ParsedResume",
    "Resume",
    "User",
]
