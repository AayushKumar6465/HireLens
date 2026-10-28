"""
System and scoring weight configuration endpoints (/api/v1/settings).
"""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.core.logging import get_logger, log_event
from app.models.app_setting import AppSetting
from app.models.audit_log import AuditLog
from app.models.job import Job
from app.models.user import User
from app.schemas.setting import ScoringWeightsSchema, ScoringWeightsUpdate
from app.services.matching import ranker

logger = get_logger(__name__)

router = APIRouter()

CurrentUser = Annotated[User, Depends(get_current_user)]
DbSession = Annotated[Session, Depends(get_db)]

DEFAULT_WEIGHTS = {
    "skills": 0.45,
    "semantic": 0.25,
    "experience": 0.15,
    "education": 0.15,
}


@router.get(
    "/scoring-weights",
    response_model=ScoringWeightsSchema,
    status_code=status.HTTP_200_OK,
    summary="Get active scoring weights",
)
def get_scoring_weights(
    current_user: CurrentUser,
    db: DbSession,
) -> dict[str, float]:
    """Retrieve active scoring weights from app_settings or defaults."""
    setting = db.query(AppSetting).filter(AppSetting.key == "scoring_weights").first()
    if setting and isinstance(setting.value, dict):
        return {
            "skills": float(setting.value.get("skills", 0.45)),
            "semantic": float(setting.value.get("semantic", 0.25)),
            "experience": float(setting.value.get("experience", 0.15)),
            "education": float(setting.value.get("education", 0.15)),
        }
    return DEFAULT_WEIGHTS


@router.put(
    "/scoring-weights",
    response_model=ScoringWeightsSchema,
    status_code=status.HTTP_200_OK,
    summary="Update default scoring weights",
)
def update_scoring_weights(
    payload: ScoringWeightsUpdate,
    current_user: CurrentUser,
    db: DbSession,
) -> dict[str, float]:
    """
    Update default scoring weights. Weights must sum to 1.0 (enforced by schema).
    Logs audit log entry.
    """
    weights_dict = {
        "skills": round(payload.skills, 3),
        "semantic": round(payload.semantic, 3),
        "experience": round(payload.experience, 3),
        "education": round(payload.education, 3),
    }

    setting = db.query(AppSetting).filter(AppSetting.key == "scoring_weights").first()
    if not setting:
        setting = AppSetting(
            key="scoring_weights",
            value=weights_dict,
            updated_by=current_user.id,
        )
        db.add(setting)
    else:
        setting.value = weights_dict
        setting.updated_by = current_user.id

    audit = AuditLog(
        user_id=current_user.id,
        action="scoring_weights_updated",
        entity_type="app_setting",
        entity_id="scoring_weights",
        meta=weights_dict,
    )
    db.add(audit)
    db.commit()

    log_event(
        logger,
        "scoring_weights_updated",
        user_id=str(current_user.id),
        weights=weights_dict,
    )
    return weights_dict


@router.post(
    "/re-score-all",
    status_code=status.HTTP_200_OK,
    summary="Re-score all candidates across user's jobs",
)
def rescore_all_candidates(
    current_user: CurrentUser,
    db: DbSession,
) -> dict[str, Any]:
    """
    Recalculate match scores across all active jobs owned by the current recruiter
    using updated scoring weights.
    """
    # Fetch active weights
    weights = get_scoring_weights(current_user=current_user, db=db)

    jobs = db.query(Job).filter(Job.owner_id == current_user.id).all()
    total_re_scored = 0

    for job in jobs:
        scored = ranker.score_candidates_for_job(
            db=db,
            user=current_user,
            job_id=job.id,
            weights=weights,
        )
        total_re_scored += scored

    log_event(
        logger,
        "all_candidates_rescored",
        user_id=str(current_user.id),
        total_rescored=total_re_scored,
    )
    return {
        "total_jobs": len(jobs),
        "total_candidates_rescored": total_re_scored,
        "message": f"Successfully re-scored {total_re_scored} candidates across {len(jobs)} jobs.",
    }
