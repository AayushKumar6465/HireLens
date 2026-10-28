"""
Pydantic schemas package.
"""

from app.schemas.analytics import (
    DashboardStatsResponse,
    RecentCandidateItem,
    ScoreBucket,
    StatusFunnelItem,
)
from app.schemas.auth import (
    LoginRequest,
    RefreshTokenRequest,
    RegisterRequest,
    TokenRefreshResponse,
    TokenResponse,
)
from app.schemas.candidate import (
    CandidateBulkStatusUpdate,
    CandidateDetailResponse,
    CandidateStatusUpdate,
)
from app.schemas.compare import (
    CandidateCompareItem,
    CompareRequest,
    CompareResponse,
    SkillMatrixRow,
)
from app.schemas.job import (
    ExtractedSkillItem,
    ExtractRequirementsResponse,
    JobCreate,
    JobRequirementCreate,
    JobRequirementResponse,
    JobResponse,
    JobUpdate,
    MatchSummaryResponse,
    PaginatedJobsResponse,
    PaginatedRankingResponse,
    RankedCandidateItem,
)
from app.schemas.resume import (
    BatchUploadResponse,
    ResumeDuplicateItemResult,
    ResumeFailedItemResult,
    ResumeResponse,
    ResumeStatusResponse,
    ResumeUploadItemResult,
)
from app.schemas.setting import (
    ScoringWeightsSchema,
    ScoringWeightsUpdate,
)
from app.schemas.user import PaginatedUsersResponse, UserResponse

__all__ = [
    "BatchUploadResponse",
    "CandidateBulkStatusUpdate",
    "CandidateCompareItem",
    "CandidateDetailResponse",
    "CandidateStatusUpdate",
    "CompareRequest",
    "CompareResponse",
    "DashboardStatsResponse",
    "ExtractRequirementsResponse",
    "ExtractedSkillItem",
    "JobCreate",
    "JobRequirementCreate",
    "JobRequirementResponse",
    "JobResponse",
    "JobUpdate",
    "LoginRequest",
    "MatchSummaryResponse",
    "PaginatedJobsResponse",
    "PaginatedRankingResponse",
    "PaginatedUsersResponse",
    "RankedCandidateItem",
    "RecentCandidateItem",
    "RefreshTokenRequest",
    "RegisterRequest",
    "ResumeDuplicateItemResult",
    "ResumeFailedItemResult",
    "ResumeResponse",
    "ResumeStatusResponse",
    "ResumeUploadItemResult",
    "ScoreBucket",
    "ScoringWeightsSchema",
    "ScoringWeightsUpdate",
    "SkillMatrixRow",
    "StatusFunnelItem",
    "TokenRefreshResponse",
    "TokenResponse",
    "UserResponse",
]
