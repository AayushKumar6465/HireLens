"""
Hybrid candidate ranking engine and explainability explainer.

Formula:
    total = 0.40 * skill_score
          + 0.30 * semantic_score
          + 0.20 * experience_score
          + 0.10 * education_score

Features:
- Pure python scoring function: no PII inputs, no database access
- Config-driven and per-job weight overrides (must sum to 1.0)
- Missing component handling: proportionally renormalizes remaining weights and records explanation notes
- Full ScoreBreakdown explanation object (never bare scores)
- Scoring version tracking ("1.0.0")
"""

from __future__ import annotations

import csv
import io
import uuid
from typing import Any

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging import get_logger, log_event
from app.models.candidate import Candidate
from app.models.job import Job
from app.models.match_result import MatchResult
from app.models.resume import ParsedResume, Resume
from app.models.user import User
from app.services.matching.education_matcher import calculate_education_score
from app.services.matching.experience_matcher import calculate_experience_score
from app.services.matching.semantic_matcher import calculate_semantic_similarity
from app.services.matching.skill_matcher import match_skills
from app.utils.csv_sanitize import sanitize_csv_cell

logger = get_logger(__name__)

SCORING_VERSION = "1.0.0"


def compute_match_breakdown(
    job_requirements: list[dict[str, Any]],
    job_description: str,
    job_min_experience: float | None,
    job_education_level: str | None,
    resume_skills: list[dict[str, Any]],
    resume_raw_text: str,
    resume_experience_years: float | None,
    resume_highest_degree: str | None,
    weights_override: dict[str, float] | None = None,
) -> dict[str, Any]:
    """
    Pure Python scoring and explainability calculation.

    Takes de-identified job requirements and parsed candidate data, calculates all sub-scores,
    renormalizes weights if components are missing, and produces the complete explanation object.
    """
    # 1. Base weights from config or job override
    default_weights = {
        "skills": settings.weight_skills,
        "semantic": settings.weight_semantic,
        "experience": settings.weight_experience,
        "education": settings.weight_education,
    }

    raw_weights = default_weights.copy()
    if weights_override:
        for k in ("skills", "semantic", "experience", "education"):
            if k in weights_override:
                raw_weights[k] = float(weights_override[k])

    # 2. Compute individual sub-scores
    notes: list[str] = []

    # Skill matching
    skill_score, matched_skills, missing_req, missing_pref, extra_skills = match_skills(
        job_requirements=job_requirements,
        candidate_skills=resume_skills,
    )
    if skill_score is None:
        notes.append(
            "No specific skills defined for this job; skill score was excluded."
        )
    else:
        for m_req in missing_req:
            notes.append(f"Required skill '{m_req}' was not found in candidate resume.")

    # Semantic similarity
    semantic_score = calculate_semantic_similarity(job_description, resume_raw_text)
    if semantic_score is None:
        notes.append(
            "Insufficient job description or resume text; semantic score was excluded."
        )

    # Experience scoring
    exp_score, exp_details = calculate_experience_score(
        resume_experience_years, job_min_experience
    )
    if exp_score is None:
        notes.append(
            "No minimum experience requirement defined; experience score was excluded."
        )

    # Education scoring
    edu_score, edu_details = calculate_education_score(
        resume_highest_degree, job_education_level
    )
    if edu_score is None:
        notes.append("No education requirement defined; education score was excluded.")

    sub_scores = {
        "skills": skill_score,
        "semantic": semantic_score,
        "experience": exp_score,
        "education": edu_score,
    }

    # 3. Proportional weight re-normalization for missing components
    active_weights: dict[str, float] = {}
    weights_used: dict[str, float | None] = {}

    for comp, score in sub_scores.items():
        if score is not None:
            active_weights[comp] = raw_weights[comp]
        else:
            weights_used[comp] = None

    active_weight_sum = sum(active_weights.values())

    if active_weight_sum > 0:
        for comp, w in active_weights.items():
            normalized_w = round(w / active_weight_sum, 4)
            weights_used[comp] = normalized_w
    else:
        # All components missing: default total score to 0.0
        for comp in sub_scores:
            weights_used[comp] = None

    # 4. Calculate total score
    total_score = 0.0
    if active_weight_sum > 0:
        for comp in active_weights:
            norm_w_val = weights_used[comp]
            score_val = sub_scores[comp]
            if norm_w_val is not None and score_val is not None:
                total_score += norm_w_val * score_val

    total_score = round(min(100.0, max(0.0, total_score)), 1)

    return {
        "total_score": total_score,
        "sub_scores": sub_scores,
        "weights_used": weights_used,
        "matched_skills": matched_skills,
        "missing_required": missing_req,
        "missing_preferred": missing_pref,
        "extra_skills": extra_skills,
        "experience": exp_details,
        "education": edu_details,
        "notes": notes,
        "scoring_version": SCORING_VERSION,
    }


def score_resume_for_job(
    db: Session,
    user: User,
    job_id: uuid.UUID,
    resume_id: uuid.UUID,
) -> MatchResult:
    """
    Score a single parsed resume against a job opening and persist the match result.

    Owner-scoped: returns 404 if job or resume does not belong to user.
    """
    job = db.query(Job).filter(Job.id == job_id, Job.owner_id == user.id).first()
    if not job:
        raise HTTPException(
            status_code=404,
            detail={"code": "not_found", "message": "Job not found."},
        )

    resume = (
        db.query(Resume)
        .join(Candidate, Resume.candidate_id == Candidate.id)
        .filter(Resume.id == resume_id, Candidate.owner_id == user.id)
        .first()
    )
    if not resume:
        raise HTTPException(
            status_code=404,
            detail={"code": "not_found", "message": "Resume not found."},
        )

    if not resume.parsed_resume:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "bad_request",
                "message": "Resume has not been parsed yet.",
            },
        )

    pr: ParsedResume = resume.parsed_resume

    # Format requirements
    reqs = [
        {"skill": r.skill, "importance": r.importance, "weight": r.weight}
        for r in job.requirements
    ]

    breakdown = compute_match_breakdown(
        job_requirements=reqs,
        job_description=job.description,
        job_min_experience=job.min_experience_years,
        job_education_level=job.education_level,
        resume_skills=pr.skills or [],
        resume_raw_text=pr.raw_text or "",
        resume_experience_years=pr.total_experience_years,
        resume_highest_degree=pr.highest_degree,
        weights_override=job.weights_override,
    )

    # Upsert match result
    match_record = (
        db.query(MatchResult)
        .filter(MatchResult.job_id == job.id, MatchResult.resume_id == resume.id)
        .first()
    )
    if not match_record:
        match_record = MatchResult(
            job_id=job.id,
            candidate_id=resume.candidate_id,
            resume_id=resume.id,
            total_score=breakdown["total_score"],
            skill_score=breakdown["sub_scores"]["skills"],
            semantic_score=breakdown["sub_scores"]["semantic"],
            experience_score=breakdown["sub_scores"]["experience"],
            education_score=breakdown["sub_scores"]["education"],
            breakdown=breakdown,
            scoring_version=breakdown["scoring_version"],
        )
        db.add(match_record)
    else:
        match_record.total_score = breakdown["total_score"]
        match_record.skill_score = breakdown["sub_scores"]["skills"]
        match_record.semantic_score = breakdown["sub_scores"]["semantic"]
        match_record.experience_score = breakdown["sub_scores"]["experience"]
        match_record.education_score = breakdown["sub_scores"]["education"]
        match_record.breakdown = breakdown
        match_record.scoring_version = breakdown["scoring_version"]

    db.commit()
    db.refresh(match_record)
    log_event(logger, "candidate_scored", job_id=str(job.id), resume_id=str(resume.id))
    return match_record


def score_all_resumes_for_job(
    db: Session,
    user: User,
    job_id: uuid.UUID,
) -> list[MatchResult]:
    """Score all parsed resumes attached to the job or owned by the user."""
    job = db.query(Job).filter(Job.id == job_id, Job.owner_id == user.id).first()
    if not job:
        raise HTTPException(
            status_code=404,
            detail={"code": "not_found", "message": "Job not found."},
        )

    # Find resumes associated with this job or candidate pool
    resumes = (
        db.query(Resume)
        .join(Candidate, Resume.candidate_id == Candidate.id)
        .filter(
            Candidate.owner_id == user.id,
            Resume.parse_status == "done",
            Resume.job_id == job.id,
        )
        .all()
    )

    results: list[MatchResult] = []
    for r in resumes:
        if r.parsed_resume:
            mr = score_resume_for_job(db, user, job.id, r.id)
            results.append(mr)

    return results


def get_job_ranking(
    db: Session,
    user: User,
    job_id: uuid.UUID,
    min_score: float | None = None,
    skill_filter: str | None = None,
    min_exp: float | None = None,
    status_filter: str | None = None,
    page: int = 1,
    page_size: int = 10,
) -> tuple[list[dict[str, Any]], int]:
    """
    Retrieve ranked candidates for a job opening with filtering and pagination.

    Owner-scoped: returns 404 for foreign jobs (admins cannot bypass).
    """
    job = db.query(Job).filter(Job.id == job_id, Job.owner_id == user.id).first()
    if not job:
        raise HTTPException(
            status_code=404,
            detail={"code": "not_found", "message": "Job not found."},
        )

    query = (
        db.query(MatchResult, Candidate, Resume)
        .join(Candidate, MatchResult.candidate_id == Candidate.id)
        .join(Resume, MatchResult.resume_id == Resume.id)
        .filter(MatchResult.job_id == job.id, Candidate.owner_id == user.id)
    )

    if min_score is not None:
        query = query.filter(MatchResult.total_score >= min_score)

    if status_filter:
        query = query.filter(Candidate.status == status_filter.strip().lower())

    if min_exp is not None:
        query = query.filter(MatchResult.experience_score >= min_exp)

    # Order by total_score descending
    query = query.order_by(MatchResult.total_score.desc())

    all_matches = query.all()

    # Skill in-memory filtering if requested
    if skill_filter and skill_filter.strip():
        filter_lower = skill_filter.strip().lower()
        filtered = []
        for mr, cand, res in all_matches:
            matched_skills = mr.breakdown.get("matched_skills", [])
            has_skill = any(
                s.get("skill", "").lower() == filter_lower for s in matched_skills
            )
            if has_skill:
                filtered.append((mr, cand, res))
        all_matches = filtered

    total = len(all_matches)
    start = (page - 1) * page_size
    paged = all_matches[start : start + page_size]

    items: list[dict[str, Any]] = []
    for mr, cand, res in paged:
        items.append(
            {
                "match_id": str(mr.id),
                "job_id": str(mr.job_id),
                "candidate_id": str(cand.id),
                "candidate_name": cand.full_name,
                "candidate_email": cand.email,
                "candidate_phone": cand.phone,
                "candidate_status": cand.status,
                "resume_id": str(res.id),
                "total_score": mr.total_score,
                "skill_score": mr.skill_score,
                "semantic_score": mr.semantic_score,
                "experience_score": mr.experience_score,
                "education_score": mr.education_score,
                "breakdown": mr.breakdown,
                "created_at": mr.created_at.isoformat(),
            }
        )

    return items, total


def export_ranking_csv(
    db: Session,
    user: User,
    job_id: uuid.UUID,
) -> str:
    """
    Export ranking table to CSV format with formula injection protection.
    """
    items, _ = get_job_ranking(db, user, job_id, page=1, page_size=1000)

    output = io.StringIO()
    writer = csv.writer(output)

    # Header
    writer.writerow(
        [
            "Rank",
            "Candidate Name",
            "Email",
            "Status",
            "Total Score",
            "Skill Score",
            "Semantic Score",
            "Experience Score",
            "Education Score",
            "Matched Skills",
            "Missing Required Skills",
        ]
    )

    for i, item in enumerate(items, 1):
        breakdown = item.get("breakdown", {})
        matched = ", ".join(
            s.get("skill", "") for s in breakdown.get("matched_skills", [])
        )
        missing = ", ".join(breakdown.get("missing_required", []))

        writer.writerow(
            [
                str(i),
                sanitize_csv_cell(item.get("candidate_name", "")),
                sanitize_csv_cell(item.get("candidate_email", "")),
                sanitize_csv_cell(item.get("candidate_status", "")),
                str(item.get("total_score", 0)),
                str(item.get("skill_score", "") or "N/A"),
                str(item.get("semantic_score", "") or "N/A"),
                str(item.get("experience_score", "") or "N/A"),
                str(item.get("education_score", "") or "N/A"),
                sanitize_csv_cell(matched),
                sanitize_csv_cell(missing),
            ]
        )

    return output.getvalue()
