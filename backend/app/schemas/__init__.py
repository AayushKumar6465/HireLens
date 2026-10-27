"""
Pydantic schemas package.
"""

from app.schemas.auth import (
    LoginRequest,
    RefreshTokenRequest,
    RegisterRequest,
    TokenRefreshResponse,
    TokenResponse,
)
from app.schemas.job import (
    ExtractedSkillItem,
    ExtractRequirementsResponse,
    JobCreate,
    JobRequirementCreate,
    JobRequirementResponse,
    JobResponse,
    JobUpdate,
    PaginatedJobsResponse,
)
from app.schemas.resume import (
    BatchUploadResponse,
    ResumeDuplicateItemResult,
    ResumeFailedItemResult,
    ResumeResponse,
    ResumeStatusResponse,
    ResumeUploadItemResult,
)
from app.schemas.user import PaginatedUsersResponse, UserResponse

__all__ = [
    "BatchUploadResponse",
    "ExtractRequirementsResponse",
    "ExtractedSkillItem",
    "JobCreate",
    "JobRequirementCreate",
    "JobRequirementResponse",
    "JobResponse",
    "JobUpdate",
    "LoginRequest",
    "PaginatedJobsResponse",
    "PaginatedUsersResponse",
    "RefreshTokenRequest",
    "RegisterRequest",
    "ResumeDuplicateItemResult",
    "ResumeFailedItemResult",
    "ResumeResponse",
    "ResumeStatusResponse",
    "ResumeUploadItemResult",
    "TokenRefreshResponse",
    "TokenResponse",
    "UserResponse",
]
