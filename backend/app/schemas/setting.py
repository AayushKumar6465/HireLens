"""
Application settings and scoring weights schemas.
"""

from __future__ import annotations

from pydantic import BaseModel, Field, model_validator


class ScoringWeightsSchema(BaseModel):
    """Component scoring weights."""

    skills: float = Field(default=0.45, ge=0.0, le=1.0)
    semantic: float = Field(default=0.25, ge=0.0, le=1.0)
    experience: float = Field(default=0.15, ge=0.0, le=1.0)
    education: float = Field(default=0.15, ge=0.0, le=1.0)

    @model_validator(mode="after")
    def validate_sum(self) -> ScoringWeightsSchema:
        total = round(self.skills + self.semantic + self.experience + self.education, 3)
        if total != 1.0:
            raise ValueError(f"Scoring weights must sum to 1.0 (current sum: {total})")
        return self


class ScoringWeightsUpdate(BaseModel):
    """Schema for updating default scoring weights."""

    skills: float = Field(..., ge=0.0, le=1.0)
    semantic: float = Field(..., ge=0.0, le=1.0)
    experience: float = Field(..., ge=0.0, le=1.0)
    education: float = Field(..., ge=0.0, le=1.0)

    @model_validator(mode="after")
    def validate_sum(self) -> ScoringWeightsUpdate:
        total = round(self.skills + self.semantic + self.experience + self.education, 3)
        if total != 1.0:
            raise ValueError(f"Scoring weights must sum to 1.0 (current sum: {total})")
        return self
