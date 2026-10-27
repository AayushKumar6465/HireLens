"""
Job management and requirement extraction service.

Responsibilities:
- Job CRUD operations strictly scoped to the authenticated owner.
- Search and pagination.
- Requirement association and updates.
- Automatic requirement extraction from job description text.
- IDOR defense: foreign job IDs raise HTTP 404, with no admin bypass.
"""

from __future__ import annotations

import re
import uuid

from fastapi import HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.logging import get_logger, log_event
from app.models.job import Job, JobRequirement
from app.models.user import User
from app.schemas.job import (
    ExtractedSkillItem,
    ExtractRequirementsResponse,
    JobCreate,
    JobRequirementCreate,
    JobUpdate,
)

logger = get_logger(__name__)

# Core tech skills catalog for reliable offline extraction in Phase 2A
COMMON_SKILLS_CATALOG = [
    ("Python", ["python", "py"]),
    ("JavaScript", ["javascript", "js", "ecmascript"]),
    ("TypeScript", ["typescript", "ts"]),
    ("React", ["react", "reactjs", "react.js"]),
    ("Node.js", ["nodejs", "node.js", "node"]),
    ("FastAPI", ["fastapi"]),
    ("Django", ["django"]),
    ("Flask", ["flask"]),
    ("SQL", ["sql"]),
    ("PostgreSQL", ["postgresql", "postgres"]),
    ("MySQL", ["mysql"]),
    ("MongoDB", ["mongodb", "mongo"]),
    ("Redis", ["redis"]),
    ("Docker", ["docker"]),
    ("Kubernetes", ["kubernetes", "k8s"]),
    ("AWS", ["aws", "amazon web services"]),
    ("Azure", ["azure", "microsoft azure"]),
    ("GCP", ["gcp", "google cloud platform", "google cloud"]),
    ("Git", ["git", "github", "gitlab"]),
    ("Linux", ["linux", "unix"]),
    ("CI/CD", ["ci/cd", "cicd", "continuous integration"]),
    ("GraphQL", ["graphql"]),
    ("REST API", ["rest api", "restful api", "rest APIs"]),
    ("Java", ["java"]),
    ("C++", ["c++", "cpp"]),
    ("C#", ["c#", "csharp"]),
    ("Go", ["golang", "go"]),
    ("Rust", ["rust"]),
    ("HTML", ["html", "html5"]),
    ("CSS", ["css", "css3", "tailwind", "sass", "scss"]),
    ("Machine Learning", ["machine learning", "ml"]),
    ("Deep Learning", ["deep learning"]),
    ("Data Analysis", ["data analysis", "pandas", "numpy"]),
    ("Agile", ["agile", "scrum", "kanban"]),
    ("Microservices", ["microservices"]),
]


def create_job(db: Session, user: User, data: JobCreate) -> Job:
    """Create a new job posting owned by the authenticated user."""
    job = Job(
        owner_id=user.id,
        title=data.title.strip(),
        description=data.description.strip(),
        department=data.department.strip() if data.department else None,
        location=data.location.strip() if data.location else None,
        min_experience_years=data.min_experience_years,
        education_level=data.education_level.strip().lower()
        if data.education_level
        else None,
        weights_override=data.weights_override,
    )
    db.add(job)
    db.flush()

    for req in data.requirements:
        requirement = JobRequirement(
            job_id=job.id,
            skill=req.skill.strip(),
            importance=req.importance,
            weight=req.weight,
        )
        db.add(requirement)

    db.commit()
    db.refresh(job)
    log_event(logger, "job_created", job_id=str(job.id), user_id=str(user.id))
    return job


def list_jobs(
    db: Session,
    user: User,
    page: int = 1,
    page_size: int = 10,
    q: str | None = None,
    status: str | None = None,
) -> tuple[list[Job], int]:
    """List jobs belonging strictly to the current user with pagination and search."""
    query = db.query(Job).filter(Job.owner_id == user.id)

    if status:
        query = query.filter(Job.status == status.strip().lower())

    if q and q.strip():
        search_pattern = f"%{q.strip()}%"
        query = query.filter(
            or_(
                Job.title.ilike(search_pattern),
                Job.description.ilike(search_pattern),
                Job.department.ilike(search_pattern),
                Job.location.ilike(search_pattern),
            )
        )

    total = query.count()
    jobs = (
        query.order_by(Job.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return jobs, total


def get_job(db: Session, user: User, job_id: uuid.UUID) -> Job:
    """
    Retrieve a job by ID ensuring strict owner scoping.

    Returns HTTP 404 for foreign or non-existent jobs (admins do not bypass).
    """
    job = db.query(Job).filter(Job.id == job_id, Job.owner_id == user.id).first()
    if job is None:
        raise HTTPException(
            status_code=404,
            detail={"code": "not_found", "message": "Job not found."},
        )
    return job


def update_job(db: Session, user: User, job_id: uuid.UUID, data: JobUpdate) -> Job:
    """Update a job opening owned by the current user."""
    job = get_job(db, user, job_id)

    if data.title is not None:
        job.title = data.title.strip()
    if data.description is not None:
        job.description = data.description.strip()
    if data.department is not None:
        job.department = data.department.strip() if data.department else None
    if data.location is not None:
        job.location = data.location.strip() if data.location else None
    if data.min_experience_years is not None:
        job.min_experience_years = data.min_experience_years
    if data.education_level is not None:
        job.education_level = (
            data.education_level.strip().lower() if data.education_level else None
        )
    if data.status is not None:
        job.status = data.status.strip().lower()
    if data.weights_override is not None:
        job.weights_override = data.weights_override

    if data.requirements is not None:
        # Replace existing requirements
        db.query(JobRequirement).filter(JobRequirement.job_id == job.id).delete()
        for req in data.requirements:
            new_req = JobRequirement(
                job_id=job.id,
                skill=req.skill.strip(),
                importance=req.importance,
                weight=req.weight,
            )
            db.add(new_req)

    db.commit()
    db.refresh(job)
    log_event(logger, "job_updated", job_id=str(job.id), user_id=str(user.id))
    return job


def delete_job(db: Session, user: User, job_id: uuid.UUID) -> None:
    """
    Delete a job owned by the current user.

    Cascades requirements and match results; sets resumes.job_id to null via database FK.
    """
    job = get_job(db, user, job_id)
    db.delete(job)
    db.commit()
    log_event(logger, "job_deleted", job_id=str(job_id), user_id=str(user.id))


def add_requirement(
    db: Session, user: User, job_id: uuid.UUID, data: JobRequirementCreate
) -> JobRequirement:
    """Add a requirement to an existing job owned by the current user."""
    job = get_job(db, user, job_id)
    req = JobRequirement(
        job_id=job.id,
        skill=data.skill.strip(),
        importance=data.importance,
        weight=data.weight,
    )
    db.add(req)
    db.commit()
    db.refresh(req)
    return req


def delete_requirement(
    db: Session, user: User, job_id: uuid.UUID, requirement_id: uuid.UUID
) -> None:
    """Delete a single requirement from a job owned by the current user."""
    get_job(db, user, job_id)  # Verifies job ownership
    req = (
        db.query(JobRequirement)
        .filter(JobRequirement.id == requirement_id, JobRequirement.job_id == job_id)
        .first()
    )
    if req is None:
        raise HTTPException(
            status_code=404,
            detail={"code": "not_found", "message": "Requirement not found."},
        )
    db.delete(req)
    db.commit()


def extract_requirements_from_description(
    db: Session, user: User, job_id: uuid.UUID, save: bool = False
) -> ExtractRequirementsResponse:
    """
    Extract suggested skills, experience years, and degree level from a job description.

    If save=True, updates the job requirements with the extracted skills.
    """
    job = get_job(db, user, job_id)
    text = f"{job.title}\n{job.description}"

    extracted_skills: list[ExtractedSkillItem] = []
    seen_skills: set[str] = set()

    # Determine preferred vs required sections in text
    preferred_pattern = re.compile(
        r"(preferred|nice to have|plus|bonus|desirable|optional)", re.IGNORECASE
    )

    # Split into lines/sentences to detect context
    sentences = re.split(r"[\n\.\?!;•\-\*]", text)

    for canonical_name, aliases in COMMON_SKILLS_CATALOG:
        for alias in aliases:
            # Word boundary regex pattern
            escaped_alias = re.escape(alias)
            pattern = re.compile(rf"(?<!\w){escaped_alias}(?!\w)", re.IGNORECASE)

            match_found = False
            is_preferred = False

            for sentence in sentences:
                if pattern.search(sentence):
                    match_found = True
                    if preferred_pattern.search(sentence):
                        is_preferred = True
                    break

            if match_found and canonical_name not in seen_skills:
                seen_skills.add(canonical_name)
                importance = "preferred" if is_preferred else "required"
                suggested_weight = 0.5 if is_preferred else 1.0
                match_type = (
                    "exact" if alias.lower() == canonical_name.lower() else "alias"
                )

                extracted_skills.append(
                    ExtractedSkillItem(
                        skill=canonical_name,
                        importance=importance,
                        suggested_weight=suggested_weight,
                        match_type=match_type,
                    )
                )
                break

    # Extract suggested min experience years
    suggested_exp: float | None = None
    exp_match = re.search(
        r"(\d+(?:\.\d+)?)\+?\s*(?:-\s*\d+\s*)?(?:years?|yrs?)(?:\s+of)?(?:\s+experience)?",
        text,
        re.IGNORECASE,
    )
    if exp_match:
        try:
            suggested_exp = float(exp_match.group(1))
        except ValueError:
            pass

    # Extract suggested degree level
    suggested_edu: str | None = None
    if re.search(r"\b(phd|doctorate)\b", text, re.IGNORECASE):
        suggested_edu = "doctorate"
    elif re.search(r"\b(master|m\.s\.|m\.tech|mca|mba)\b", text, re.IGNORECASE):
        suggested_edu = "master"
    elif re.search(
        r"\b(bachelor|b\.s\.|b\.tech|bca|undergraduate)\b", text, re.IGNORECASE
    ):
        suggested_edu = "bachelor"

    if save and extracted_skills:
        # Overwrite or append requirements
        existing_skills = {
            r.skill.lower()
            for r in db.query(JobRequirement)
            .filter(JobRequirement.job_id == job.id)
            .all()
        }
        for item in extracted_skills:
            if item.skill.lower() not in existing_skills:
                db.add(
                    JobRequirement(
                        job_id=job.id,
                        skill=item.skill,
                        importance=item.importance,
                        weight=item.suggested_weight,
                    )
                )
        if suggested_exp is not None and job.min_experience_years is None:
            job.min_experience_years = suggested_exp
        if suggested_edu is not None and job.education_level is None:
            job.education_level = suggested_edu
        db.commit()
        db.refresh(job)

    return ExtractRequirementsResponse(
        job_id=job.id,
        extracted_skills=extracted_skills,
        suggested_min_experience_years=suggested_exp,
        suggested_education_level=suggested_edu,
    )
